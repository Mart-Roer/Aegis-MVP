"""
parties.py  --  the actors: member banks and the Aegis router
==============================================================
Roles, in plain terms:

  MemberBank  -- a consortium bank. It (a) keeps a private list of high-risk
                 people, committed to a Merkle root registered with Aegis, and
                 (b) can act as the QUERIER asking about one person, or as a
                 RESPONDER answering a routed query.

  Aegis       -- the neutral router. It holds a private map root->bank (for
                 onboarding/governance only) and publishes the UNLABELLED set of
                 valid roots so queriers can check answers come from real members.
                 It routes opaque blobs and CANNOT read them.

WHO LEARNS WHAT (this is the whole point):
  * Responding banks  : learn the entity (they must, to check their list); do
                        NOT learn which bank asked.   [hiding the entity from
                        them is the OPRF/PSI upgrade -- see identity.py]
  * Aegis             : learns that bank X ran a query and that every member
                        replied; CANNOT read the entity or the recipes, so it
                        cannot tell who matched.
  * Querying bank     : learns how many members flag the person, and which
                        (unlabelled) roots matched -- NOT which banks.
"""

from . import channel
from .identity import shared_identifier
from .merkle import FlaggedSet, verify_recipe


class MemberBank:
    def __init__(self, name: str, consortium_key: bytes, broadcast_key: bytes):
        self.name = name
        self._consortium_key = consortium_key      # for computing shared ids
        self._broadcast_key = broadcast_key        # shared among banks, not Aegis
        self._flagged = FlaggedSet([])             # empty until populated

    # ----- setup: commit this bank's high-risk people --------------------
    def set_high_risk(self, records: list[dict]):
        """`records` are raw identity dicts. We convert each to its shared code
        and commit them to a Merkle root. Raw data never leaves the bank."""
        ids = [shared_identifier(r, self._consortium_key) for r in records]
        self._flagged = FlaggedSet(ids)

    @property
    def root(self) -> bytes:
        return self._flagged.root

    # ----- as RESPONDER: answer a routed query ---------------------------
    def answer(self, broadcast_blob: bytes) -> dict:
        """Open the routed query, check our committed list, and seal a reply to
        the querier. We ALWAYS reply (a real recipe or a NO_MATCH token) so the
        router cannot tell matchers from non-matchers."""
        query = channel.broadcast_open(self._broadcast_key, broadcast_blob)
        identifier = query["identifier"]
        reply_pub = query["reply_pub"]

        recipe = self._flagged.make_recipe(identifier)
        if recipe is not None:
            payload = {"status": "MATCH", "root": self.root.hex(), "recipe": recipe}
        else:
            payload = {"status": "NO_MATCH"}
        return channel.reply_seal(reply_pub, payload)

    # ----- as QUERIER: build a query ------------------------------------
    def make_query(self, person: dict):
        """Compute the person's shared code and seal a broadcast for the banks.
        Returns (broadcast_blob, reply_private_key, identifier)."""
        identifier = shared_identifier(person, self._consortium_key)
        reply_priv, reply_pub = channel.new_reply_keypair()
        blob = channel.broadcast_seal(
            self._broadcast_key, {"identifier": identifier, "reply_pub": reply_pub})
        return blob, reply_priv, identifier

    # ----- as QUERIER: read the routed replies --------------------------
    def read_replies(self, identifier, reply_priv, sealed_replies, valid_roots):
        """Open each reply, keep those that (a) cite a genuine registered root and
        (b) contain a recipe that really proves this person is on that list.
        Returns the count of confirmed members and the matched (unlabelled) roots."""
        matched_roots = []
        for sealed in sealed_replies:
            payload = channel.reply_open(reply_priv, sealed)
            if payload.get("status") != "MATCH":
                continue
            root = bytes.fromhex(payload["root"])
            if root in valid_roots and verify_recipe(root, identifier, payload["recipe"]):
                matched_roots.append(payload["root"])
        return len(matched_roots), matched_roots


class Aegis:
    """The neutral router. Sees only opaque blobs."""

    def __init__(self):
        self._registry = {}      # bank_name -> root  (PRIVATE: governance only)

    def register(self, bank: MemberBank):
        """Onboard a member by recording its committed root (done once, up front)."""
        self._registry[bank.name] = bank.root

    def published_roots(self) -> set:
        """The UNLABELLED set of valid member roots, shared with queriers so they
        can confirm a reply comes from a genuine member -- without learning which."""
        return set(self._registry.values())

    def route(self, broadcast_blob: bytes, members: list[MemberBank]) -> list[dict]:
        """Forward the opaque query to every member and collect every sealed
        reply. Aegis can read NONE of this. It shuffles the replies so their
        order leaks nothing, and returns the bundle to the querier."""
        import random
        replies = [m.answer(broadcast_blob) for m in members]
        random.shuffle(replies)
        return replies

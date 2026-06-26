"""
merkle.py  --  a bank's committed list of high-risk people, and the "recipe"
============================================================================
WHAT THIS IS FOR
----------------
Each bank turns its private list of high-risk shared-identifiers into ONE short
fingerprint (the Merkle "root"). The root is registered with Aegis BEFORE any
query, which freezes the list: the bank cannot quietly add or remove people
later. To answer a query the bank produces a "recipe" -- a short proof that one
specific person sits behind that frozen fingerprint. The querying bank checks
the recipe against the root and learns ONLY that this one person is on the list;
it learns nothing about anyone else on it.

This is the part that emulates the zero-knowledge property: prove one entry is
present, reveal nothing about the rest.

THE PIECES
----------
  leaf  = hash(random salt + identifier)   one per high-risk person. The salt
          hides the entry; even an identical identifier looks different here.
  node  = hash(left child + right child)    combine upward in pairs...
  root  = the single hash at the top.       ...until one value remains.
  recipe = the salt of the matched leaf + the sibling hashes on the path to the
           root. Enough to recompute the root, nothing more.

WHY A BANK CANNOT FAKE A FLAG
-----------------------------
The root is registered in advance. A valid recipe can only be built by someone
who actually placed that person in the committed tree (they need the secret salt
and the real path). A bank cannot invent a person after being asked, because the
recomputed root would not match the one it already registered.
"""

import hashlib
import secrets


def _leaf(salt: bytes, identifier: str) -> bytes:
    return hashlib.sha256(b"\x00" + salt + identifier.encode()).digest()


def _node(a: bytes, b: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + a + b).digest()


class FlaggedSet:
    """One bank's frozen, committed set of high-risk shared-identifiers."""

    def __init__(self, identifiers: list[str]):
        self._salts = {i: secrets.token_bytes(16) for i in identifiers}
        self._order = list(identifiers)
        leaves = [_leaf(self._salts[i], i) for i in self._order]
        self.root, self._levels = self._build(leaves)

    @staticmethod
    def _build(leaves: list[bytes]):
        if not leaves:
            return hashlib.sha256(b"empty-list").digest(), [[]]
        level = list(leaves)
        levels = [level]
        while len(level) > 1:
            if len(level) % 2 == 1:
                level = level + [level[-1]]          # duplicate last if odd
            level = [_node(level[i], level[i + 1]) for i in range(0, len(level), 2)]
            levels.append(level)
        return levels[-1][0], levels

    def make_recipe(self, identifier: str):
        """Return a membership recipe for `identifier`, or None if not on the list."""
        if identifier not in self._salts:
            return None
        index = self._order.index(identifier)
        path = []
        for level in self._levels[:-1]:
            if len(level) % 2 == 1:
                level = level + [level[-1]]
            sibling = index ^ 1
            side = "right" if index % 2 == 0 else "left"
            path.append([level[sibling].hex(), side])
            index //= 2
        return {"salt": self._salts[identifier].hex(), "path": path}


def verify_recipe(root: bytes, identifier: str, recipe: dict) -> bool:
    """Recompute the root from (identifier + recipe) and compare. True = the
    person really is on the list behind this exact registered root."""
    if not recipe:
        return False
    h = _leaf(bytes.fromhex(recipe["salt"]), identifier)
    for sibling_hex, side in recipe["path"]:
        sib = bytes.fromhex(sibling_hex)
        h = _node(h, sib) if side == "right" else _node(sib, h)
    return h == root

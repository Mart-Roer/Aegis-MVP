"""
aegis_backend.py  --  bridge between the dashboard and the real aegis protocol
==============================================================================
The dashboard performs two cryptographic checks:

  Stage 1  "Consortium Match Check"  -> how many members have this entity present
  Stage 2  "Risk Attestation"        -> how many members attest it as high-risk

This module performs BOTH for real, using the `aegis` package: it builds a
consortium, commits each member's list to a Merkle root, routes a sealed query
through the blind Aegis router, and verifies the returned recipes. The dashboard
no longer reads hardcoded numbers -- it displays the verified output of this code.

How the synthetic cases map onto real crypto: each case carries an intended
scenario (how many members hold the entity, how many attest high-risk). We seed
a consortium to that scenario and let the REAL protocol recompute the counts. If
the cryptography is correct the recomputed count equals the scenario; if it ever
broke, the dashboard would show a different number -- so the check is genuine,
not a passthrough.

NOTE on what is actually implemented: both stages use the SAME primitive -- a
membership check against each member's committed Merkle set. "Presence" (Stage 1)
and "high-risk" (Stage 2) are a labelling/data distinction, not two different
mechanisms here. In production Stage 1 is full Private Set Intersection over each
bank's customer base (see identity.py); this MVP models it with the same
committed-set membership used for the high-risk attestation.

The UI calls only `get_backend().stage1_match_count(...)` and
`.stage2_attestation(...)`. Nothing here imports Streamlit, so it is testable
on its own (see the __main__ block).
"""

import os

from aegis import MemberBank, Aegis
from aegis.channel import new_broadcast_key

QUERIER = "Bank Alpha"                       # matches the dashboard's flagging bank
_POOL = ["Rabobank", "ABN AMRO", "ING", "Triodos", "bunq",
         "Volksbank", "Knab", "SNS", "NIBC", "ASN"]


def _identity_for(seed: str) -> dict:
    """A stable synthetic identity derived from a case seed (no real PII)."""
    return {"family_name": seed, "given_name": "case",
            "birth_date": "2000-01-01", "national_id": seed}


class ConsortiumBackend:
    """Runs the real sealed/routed membership protocol for the dashboard."""

    def __init__(self):
        # Consortium-wide secrets, fixed for the process. NOT known to Aegis.
        self._consortium_key = os.urandom(32)
        self._broadcast_key = new_broadcast_key()
        self._cache = {}

    def _verified_count(self, seed: str, n_holders: int) -> int:
        """Build a consortium where `n_holders` members hold the entity on their
        committed list, run the real query lifecycle (seal -> blind route ->
        sealed replies -> verify against registered roots), and return the count
        of cryptographically verified matches."""
        if seed in self._cache:
            return self._cache[seed]

        person = _identity_for(seed)
        n_total = max(n_holders + 2, 4)       # include a few non-holders
        responders = [MemberBank(name, self._consortium_key, self._broadcast_key)
                      for name in _POOL[:n_total]]
        for i, bank in enumerate(responders):
            bank.set_high_risk([person] if i < n_holders else [])

        aegis = Aegis()
        for bank in responders:
            aegis.register(bank)
        valid_roots = aegis.published_roots()

        querier = MemberBank(QUERIER, self._consortium_key, self._broadcast_key)
        blob, reply_priv, identifier = querier.make_query(person)
        replies = aegis.route(blob, responders)            # Aegis sees only blobs
        count, _ = querier.read_replies(identifier, reply_priv, replies, valid_roots)

        self._cache[seed] = count
        return count

    def stage1_match_count(self, case_id: str, scenario_present: int) -> int:
        """Stage 1: verified number of members where the entity is present."""
        return self._verified_count(f"{case_id}|present", scenario_present)

    def stage2_attestation(self, case_id: str, scenario_confirm: int):
        """Stage 2: verified number of anonymous high-risk confirmations, plus a
        derived aggregate concern (>=2 High, 1 Medium, 0 Low)."""
        count = self._verified_count(f"{case_id}|risk", scenario_confirm)
        risk = "High" if count >= 2 else "Medium" if count == 1 else "Low"
        return count, risk


_BACKEND = None


def get_backend() -> ConsortiumBackend:
    """One backend per process; survives Streamlit reruns (module stays imported)."""
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = ConsortiumBackend()
    return _BACKEND


if __name__ == "__main__":
    # Self-test against the dashboard's three synthetic cases.
    b = get_backend()
    cases = {"CUST-1047": (3, 2), "CUST-2198": (0, 0), "CUST-3321": (1, 0)}
    for cid, (present, confirm) in cases.items():
        m = b.stage1_match_count(cid, present)
        c, risk = b.stage2_attestation(cid, confirm)
        ok = (m == present) and (c == confirm)
        print(f"{cid}: stage1 match={m} (want {present}), "
              f"stage2 confirm={c} (want {confirm}), risk={risk}  "
              f"[{'OK' if ok else 'MISMATCH'}]")

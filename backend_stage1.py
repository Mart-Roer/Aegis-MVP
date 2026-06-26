"""
backend_stage1.py -- Stage 1 (Consortium Match Check), backed by REAL crypto.

Drop-in replacement for the earlier simulated PSI-cardinality model. It keeps the
exact function name and return shape that app.py expects, but the match count is
now produced by the real aegis protocol -- a sealed query routed blindly through
the Aegis router, with membership proofs verified against each member's
pre-registered Merkle root (see the aegis/ package and aegis_backend.py).

NOTE: in this MVP "presence" (Stage 1) is modelled with the same committed-set
membership primitive used for Stage 2's high-risk attestation. Production Stage 1
is full Private Set Intersection (see aegis/identity.py); the structure is
identical, only the matching primitive is upgraded.
"""

import hashlib

from aegis_backend import get_backend

# Synthetic demo scenarios: how many OTHER consortium members hold the entity.
_SCENARIO_PRESENT = {"CUST-1047": 2, "CUST-2198": 0, "CUST-3321": 1}


def _normalize_entity(entity_id: str) -> str:
    return entity_id.strip().upper()


def run_stage1_psi_cardinality(entity_id: str, querying_bank: str) -> dict:
    """Return the Stage-1 match result. `matched_bank_count` is the count of
    cryptographically verified matches from the real protocol; bank identities
    are never returned."""
    normalized = _normalize_entity(entity_id)
    scenario = _SCENARIO_PRESENT.get(normalized, 0)
    matched = get_backend().stage1_match_count(normalized, scenario)   # REAL
    token = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return {
        "stage": 1,
        "entity_id": normalized,
        "querying_bank": querying_bank,
        "matched_bank_count": int(matched),
        "disclosure_level": "count_only",
        "technology_modelled": "real_membership_proof_via_blind_router",
        "technical_trace": {
            "query_token_preview": token[:8],
            "backend_received": [
                "sealed query blob",
                "sealed replies (one per member)",
                "verified match count",
            ],
            "backend_did_not_disclose": [
                "raw customer lists",
                "matched bank names",
                "per-bank match results",
                "non-matching records",
            ],
        },
    }


if __name__ == "__main__":
    for cid in ("CUST-1047", "CUST-2198", "CUST-3321"):
        r = run_stage1_psi_cardinality(cid, "Bank Alpha")
        print(cid, "-> matched_bank_count =", r["matched_bank_count"])

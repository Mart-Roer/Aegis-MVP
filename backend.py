"""
backend.py -- Stage 2 (Risk Attestation), backed by REAL crypto.

Drop-in replacement for the earlier simulated ZKP layer. Same function name and
return shape that app.py expects; the confirmation count is produced by the real
aegis protocol (membership proofs verified against pre-registered Merkle roots)
via aegis_backend.

The aggregate risk label is derived from the verified count
(0 -> "None", 1 -> "Low", >=2 -> "High"). In this MVP only the COUNT of
confirmations is cryptographically verified; per-bank severity levels are not
carried by the membership proof, so the aggregate is a derived label.
"""

from aegis_backend import get_backend

# Synthetic demo scenarios: anonymous high-risk confirmations per entity.
_SCENARIO_CONFIRM = {"CUST-1047": 2, "CUST-2198": 0, "CUST-3321": 1}


def run_zkp_attestation(entity_id: str, querying_bank: str = "BANK-ALPHA") -> dict:
    """Return the Stage-2 attestation. `anonymous_confirmations` is the verified
    count from the real protocol; source banks are never returned."""
    normalized = entity_id.strip().upper()
    scenario = _SCENARIO_CONFIRM.get(normalized, 0)
    count, _ = get_backend().stage2_attestation(normalized, scenario)   # REAL
    aggregate = "High" if count >= 2 else "Low" if count == 1 else "None"
    return {
        "entity_id": normalized,
        "anonymous_confirmations": int(count),
        "aggregate_risk": aggregate,
        "passed": count >= 1 and aggregate in ("High", "Critical"),
        "anonymous_signals": [],   # per-bank severity not exposed in this MVP
    }


if __name__ == "__main__":
    for cid in ("CUST-1047", "CUST-2198", "CUST-3321"):
        print(cid, "->", run_zkp_attestation(cid))

import hashlib
import random
from typing import Dict

# MVP simulation only. This is a toy model of PSI-cardinality behavior.
# It is not production cryptography and should not be used as a real secure PSI protocol.

_MODULUS = 2 ** 16

# Synthetic per-bank entity sets.
# CUST-1047 appears at exactly two other banks besides Bank Alpha.
# CUST-2198 appears nowhere else.
# CUST-3321 appears at exactly one other bank.
_SYNTHETIC_BANK_ENTITIES = {
    "Bank Alpha": {"CUST-1047", "CUST-2198", "CUST-3321"},
    "Bank Beta": {"CUST-3321"},
    "Bank Gamma": {"CUST-1047"},
    "Bank Delta": {"CUST-1047"},
    "Bank Zeta": {"CUST-9999"},
    "Bank Eta": {"CUST-0001"},
    "Bank Theta": {"CUST-4444"},
}


def _normalize_entity(entity_id: str) -> str:
    return entity_id.strip().upper()


def _tokenize_entity(entity_id: str) -> str:
    normalized = _normalize_entity(entity_id)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def run_stage1_psi_cardinality(entity_id: str, querying_bank: str) -> Dict:
    """
    Simulate PSI-cardinality for Stage 1.
    Only return the count of other banks holding the same entity.
    Do not reveal matched bank names, IDs, or per-bank results.
    """
    normalized = _normalize_entity(entity_id)
    token = _tokenize_entity(normalized)

    # Participating banks exclude the querying bank for the final count.
    participating_banks = [
        bank for bank in _SYNTHETIC_BANK_ENTITIES.keys() if bank != querying_bank
    ]

    # Each bank computes a local 0/1 match check.
    local_matches = []
    for bank in participating_banks:
        local_set = _SYNTHETIC_BANK_ENTITIES.get(bank, set())
        local_matches.append(1 if normalized in local_set else 0)

    # Secret-share each local match bit into two random-looking shares.
    shares_a = []
    shares_b = []
    for match in local_matches:
        r = random.randint(0, _MODULUS - 1)
        shares_a.append(r)
        shares_b.append((match - r) % _MODULUS)

    # Backend receives aggregate shares only, not individual matches.
    aggregate_share_total_a = sum(shares_a) % _MODULUS
    aggregate_share_total_b = sum(shares_b) % _MODULUS
    reconstructed_match_count = (aggregate_share_total_a + aggregate_share_total_b) % _MODULUS

    return {
        "stage": 1,
        "entity_id": normalized,
        "querying_bank": querying_bank,
        "matched_bank_count": int(reconstructed_match_count),
        "disclosure_level": "count_only",
        "technology_modelled": "simulated_psi_cardinality_with_secret_sharing",
        "technical_trace": {
            "query_token_preview": token[:8],
            "participating_bank_count": len(participating_banks),
            "backend_received": [
                "aggregate_share_total_a",
                "aggregate_share_total_b",
                "reconstructed_match_count",
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
    result = run_stage1_psi_cardinality("CUST-1047", "Bank Alpha")
    print(result)
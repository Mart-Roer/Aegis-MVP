"""
backend.py — Aegis consortium simulation layer

Simulates what a production system would implement with real PSI, ZKP, and MPC
cryptography. All logic here uses hashed identifiers and aggregate outputs so the
structural GDPR argument holds even in this demo: raw entity data never leaves the
owning institution.
"""

import hashlib

# ---------------------------------------------------------------------------
# Consortium member registry
# ---------------------------------------------------------------------------

BANKS = {
    "BANK-ALPHA":   {"name": "Bank Alpha",   "country": "NL"},
    "BANK-BETA":    {"name": "Bank Beta",    "country": "DE"},
    "BANK-GAMMA":   {"name": "Bank Gamma",   "country": "FR"},
    "BANK-DELTA":   {"name": "Bank Delta",   "country": "BE"},
    "BANK-EPSILON": {"name": "Bank Epsilon", "country": "ES"},
}

# ---------------------------------------------------------------------------
# Per-bank flagged-entity sets (stored as hashed IDs)
#
# In production each bank holds only its own set locally. Aegis never receives
# the raw sets — it only learns intersection counts via the PSI protocol.
# ---------------------------------------------------------------------------

def _h(entity_id: str) -> str:
    """SHA-256 truncated to 16 hex chars — simulates the token a real PSI would use."""
    return hashlib.sha256(entity_id.encode()).hexdigest()[:16]


_FLAGGED: dict[str, set[str]] = {
    "BANK-ALPHA": {_h(e) for e in [
        "CUST-1047", "CUST-2198", "CUST-3321",
        "CUST-0092", "CUST-0188", "CUST-0451", "CUST-0607",
    ]},
    "BANK-BETA": {_h(e) for e in [
        "CUST-1047", "CUST-3321",
        "CUST-0092", "CUST-0712", "CUST-0831",
    ]},
    "BANK-GAMMA": {_h(e) for e in [
        "CUST-1047",
        "CUST-0188", "CUST-0451", "CUST-0903",
    ]},
    "BANK-DELTA": {_h(e) for e in [
        "CUST-1047",
        "CUST-0607", "CUST-0712",
    ]},
    "BANK-EPSILON": {_h(e) for e in [
        "CUST-0092", "CUST-0451", "CUST-0831", "CUST-0903",
    ]},
}

# ---------------------------------------------------------------------------
# Per-bank internal risk assessments
#
# Each bank's assessment is its own — never shared directly. The ZKP stage
# aggregates these into a single category without attributing any signal to
# a specific institution.
# ---------------------------------------------------------------------------

_RISK: dict[str, dict[str, str]] = {
    "CUST-1047": {
        "BANK-BETA":  "High",
        "BANK-GAMMA": "High",
        "BANK-DELTA": "Medium",
    },
    "CUST-2198": {},
    "CUST-3321": {
        "BANK-BETA": "Low",
    },
}

# ---------------------------------------------------------------------------
# Synthetic transaction graphs (Stage 3 — demo data only)
# ---------------------------------------------------------------------------

_GRAPHS: dict[str, list[dict]] = {
    "CUST-1047": [
        {"from": "CUST-1047", "to": "Entity A",   "amount": 25_000, "note": "Recurring trade payments"},
        {"from": "Entity A",  "to": "Account B",  "amount": 24_000, "note": "Circular transfer"},
        {"from": "Account B", "to": "Entity C",   "amount": 23_000, "note": "High-frequency outbound"},
        {"from": "Entity C",  "to": "CUST-1047",  "amount": 22_000, "note": "Return flow"},
    ],
    "CUST-2198": [
        {"from": "CUST-2198", "to": "ACC-2198-1", "amount": 1_200, "note": "Single transfer"},
    ],
    "CUST-3321": [
        {"from": "CUST-3321",  "to": "ACC-3321-1", "amount": 4_000, "note": "Cash flow"},
        {"from": "ACC-3321-1", "to": "ACC-3321-2", "amount": 3_900, "note": "Transfer"},
    ],
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_psi_query(entity_id: str, querying_bank: str = "BANK-ALPHA") -> dict:
    """
    PSI simulation.

    Returns how many *other* consortium banks have this entity in their flagged
    set. Does not reveal which banks matched or any details about their data.

    In production this would use a cryptographic PSI protocol (e.g. OPRF-based)
    so Aegis never learns the raw sets either — only the intersection size.
    """
    token = _h(entity_id)
    match_count = sum(
        1
        for bank_id, entity_set in _FLAGGED.items()
        if bank_id != querying_bank and token in entity_set
    )
    return {
        "entity_id":   entity_id,
        "match_count": match_count,
        "passed":      match_count >= 1,
        # bank_identities intentionally absent
    }


def run_zkp_attestation(entity_id: str, querying_bank: str = "BANK-ALPHA") -> dict:
    """
    ZKP / anonymous risk attestation simulation.

    Aggregates risk signals from member banks without attributing any signal to
    a specific institution. The querying bank learns only: how many confirmations
    exist and what the aggregate risk category is.

    In production this would use zero-knowledge proofs or ring-signature schemes
    so individual bank attestations remain unlinkable.
    """
    signals = [
        level
        for bank_id, level in _RISK.get(entity_id, {}).items()
        if bank_id != querying_bank
    ]

    if "High" in signals or "Critical" in signals:
        aggregate = "High"
    elif "Medium" in signals:
        aggregate = "Medium"
    elif signals:
        aggregate = "Low"
    else:
        aggregate = "None"

    passed = bool(signals) and aggregate in ("High", "Critical")

    return {
        "entity_id":              entity_id,
        "anonymous_confirmations": len(signals),
        "aggregate_risk":         aggregate,
        "passed":                 passed,
        # source_banks intentionally absent
    }


def get_transaction_graph(entity_id: str) -> list[dict]:
    """Returns the synthetic transaction graph for Stage 3 (demo data only)."""
    return _GRAPHS.get(entity_id, [])


def get_consortium_stats() -> dict:
    """
    Returns per-bank aggregate stats for the Consortium Network dashboard.
    Only exposes counts — never raw entity IDs.
    """
    return {
        bank_id: {
            **info,
            "monitored_count": len(_FLAGGED.get(bank_id, set())),
        }
        for bank_id, info in BANKS.items()
    }

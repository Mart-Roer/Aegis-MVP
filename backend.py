"""
backend.py — Aegis consortium simulation layer

Simulates what a production system would implement with real PSI, ZKP, and MPC
cryptography. Hashed identifiers and aggregate outputs are used throughout so
the structural GDPR argument holds: raw entity data never leaves the owning bank.
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
# Helpers
# ---------------------------------------------------------------------------

def _h(entity_id: str) -> str:
    """SHA-256 truncated to 16 hex chars — simulates the PSI token."""
    return hashlib.sha256(entity_id.encode()).hexdigest()[:16]

# ---------------------------------------------------------------------------
# Per-bank entity databases
#
# Each bank holds only its own internal representation. The same real-world
# entity appears under different internal IDs and names at different banks.
#
# Fields:
#   id          — canonical identifier used for PSI hashing (never shown in UI)
#   display_id  — bank-specific internal ID (what the bank itself sees)
#   name        — entity display name (synthetic demo data)
#   type        — entity classification
#   country     — country of registration or residence
#   risk        — internal risk level
#   flag        — one-line flag reason
# ---------------------------------------------------------------------------

_ENTITY_DB: dict[str, list[dict]] = {
    "BANK-ALPHA": [
        {"id": "CUST-1047", "display_id": "CUST-1047", "name": "Horizon Trade Solutions BV", "type": "Corporation",   "country": "NL", "risk": "High",   "flag": "Trade payments inconsistent with business profile"},
        {"id": "CUST-2198", "display_id": "CUST-2198", "name": "Marcus van der Berg",         "type": "Individual",    "country": "NL", "risk": "Medium", "flag": "Structured deposits, rapid outbound transfers"},
        {"id": "CUST-3321", "display_id": "CUST-3321", "name": "Bluewave Retail BV",          "type": "SME",           "country": "NL", "risk": "High",   "flag": "Dormant account reactivated with rapid flows"},
        {"id": "CUST-0092", "display_id": "CUST-0092", "name": "North Sea Logistics Group",   "type": "Corporation",   "country": "NL", "risk": "Medium", "flag": "Complex layered transaction structures"},
        {"id": "CUST-0188", "display_id": "CUST-0188", "name": "Carla M. Hendriksen",        "type": "Individual",    "country": "NL", "risk": "Low",    "flag": "Unusual cash deposit pattern"},
        {"id": "CUST-0451", "display_id": "CUST-0451", "name": "Meridian Imports NL",        "type": "Import/Export", "country": "NL", "risk": "High",   "flag": "High-value cross-border payments"},
        {"id": "CUST-0607", "display_id": "CUST-0607", "name": "Delta Finance Partners",     "type": "Corporation",   "country": "NL", "risk": "Medium", "flag": "Multi-account rapid fund movement"},
    ],
    "BANK-BETA": [
        {"id": "CUST-1047", "display_id": "DE-4521", "name": "Horizon Trade GmbH",           "type": "Corporation",   "country": "DE", "risk": "High",   "flag": "Unusual supplier payment patterns"},
        {"id": "CUST-3321", "display_id": "DE-2089", "name": "Bluewave Handel GmbH",         "type": "SME",           "country": "DE", "risk": "Low",    "flag": "Suspicious cash transaction activity"},
        {"id": "CUST-0092", "display_id": "DE-0318", "name": "Nordsee Logistik AG",          "type": "Corporation",   "country": "DE", "risk": "Medium", "flag": "Shell company indicators detected"},
        {"id": "CUST-0712", "display_id": "DE-1177", "name": "Rainer Holst",                 "type": "Individual",    "country": "DE", "risk": "High",   "flag": "Rapid cross-border transfers"},
        {"id": "CUST-0831", "display_id": "DE-2934", "name": "Baltic Trade Holdings AG",     "type": "Corporation",   "country": "DE", "risk": "High",   "flag": "Complex beneficial ownership structure"},
    ],
    "BANK-GAMMA": [
        {"id": "CUST-1047", "display_id": "FR-8801", "name": "Horizon Commerce SARL",        "type": "Corporation",   "country": "FR", "risk": "High",   "flag": "Trade-based laundering indicators"},
        {"id": "CUST-0188", "display_id": "FR-3341", "name": "Claire Fontaine",              "type": "Individual",    "country": "FR", "risk": "Medium", "flag": "Unusual cross-border transfer patterns"},
        {"id": "CUST-0451", "display_id": "FR-6612", "name": "Meridian France SAS",          "type": "Import/Export", "country": "FR", "risk": "High",   "flag": "Anomalous trade invoice discrepancies"},
        {"id": "CUST-0903", "display_id": "FR-9923", "name": "Lyon Capital Group SA",        "type": "Corporation",   "country": "FR", "risk": "High",   "flag": "Layered ownership, complex fund flows"},
    ],
    "BANK-DELTA": [
        {"id": "CUST-1047", "display_id": "BE-D012", "name": "Horizon Trading BE SPRL",      "type": "Corporation",   "country": "BE", "risk": "Medium", "flag": "Inconsistent trade documentation"},
        {"id": "CUST-0607", "display_id": "BE-D047", "name": "Delta Finance Belgie NV",      "type": "Corporation",   "country": "BE", "risk": "Medium", "flag": "Multi-account fund movements"},
        {"id": "CUST-0712", "display_id": "BE-D205", "name": "Rainer Holst",                 "type": "Individual",    "country": "BE", "risk": "High",   "flag": "Cross-border high-frequency payments"},
    ],
    "BANK-EPSILON": [
        {"id": "CUST-0092", "display_id": "ES-1101", "name": "North Sea Global SL",          "type": "Corporation",   "country": "ES", "risk": "Medium", "flag": "Offshore account linkages"},
        {"id": "CUST-0451", "display_id": "ES-2287", "name": "Meridian Imports Spain SL",    "type": "Import/Export", "country": "ES", "risk": "High",   "flag": "High-value cash transactions"},
        {"id": "CUST-0831", "display_id": "ES-3308", "name": "Henrik Vasquez",               "type": "Individual",    "country": "ES", "risk": "High",   "flag": "Structured cash deposit activity"},
        {"id": "CUST-0903", "display_id": "ES-4419", "name": "Lyon Capital España SA",       "type": "Corporation",   "country": "ES", "risk": "High",   "flag": "Complex beneficial ownership"},
    ],
}

# Derive flagged hash sets from entity DB — no separate hardcoding needed
_FLAGGED: dict[str, set[str]] = {
    bank_id: {_h(e["id"]) for e in entities}
    for bank_id, entities in _ENTITY_DB.items()
}

# ---------------------------------------------------------------------------
# Risk attestations — each bank's private internal assessment
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
# Synthetic transaction graphs (Stage 3)
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
    PSI simulation — returns intersection count and PSI token only.
    Bank identities and raw data are structurally absent from the return value.
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
        "psi_token":   token,           # shown in the demo for transparency
    }


def run_zkp_attestation(entity_id: str, querying_bank: str = "BANK-ALPHA") -> dict:
    """
    ZKP attestation simulation — aggregates risk signals without attribution.
    Source banks are structurally absent from the return value.
    anonymous_signals preserves signal levels but discards bank identity.
    """
    _rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
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

    return {
        "entity_id":               entity_id,
        "anonymous_confirmations": len(signals),
        "aggregate_risk":          aggregate,
        "passed":                  bool(signals) and aggregate in ("High", "Critical"),
        "anonymous_signals":       sorted(signals, key=lambda x: _rank.get(x, 9)),
    }


def get_transaction_graph(entity_id: str) -> list[dict]:
    """Synthetic transaction graph for Stage 3 (demo data only)."""
    return _GRAPHS.get(entity_id, [])


def get_bank_entities(bank_id: str) -> list[dict]:
    """
    Display-ready entity list for a given bank.
    Uses display_id — canonical IDs are never exposed.
    """
    return [
        {
            "ID":          e["display_id"],
            "Name":        e["name"],
            "Type":        e["type"],
            "Country":     e["country"],
            "Risk":        e["risk"],
            "Flag reason": e["flag"],
        }
        for e in _ENTITY_DB.get(bank_id, [])
    ]


def get_consortium_stats() -> dict:
    """Per-bank aggregate stats. Exposes counts only — no raw entity data."""
    return {
        bank_id: {
            **info,
            "monitored_count": len(_ENTITY_DB.get(bank_id, [])),
        }
        for bank_id, info in BANKS.items()
    }

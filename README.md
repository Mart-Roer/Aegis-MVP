# Aegis — Investigator MVP

**Cross-institutional anti-money-laundering, built for the EU AML framework.**

Aegis lets a bank check whether a flagged customer is also flagged elsewhere in
a consortium of banks — **without** any bank exposing its customer data, without
revealing **which** other banks hold a match, and without the Aegis operator
learning **who** is being investigated. This repository is a working MVP: a rich
Streamlit investigator dashboard whose Stage-1 and Stage-2 checks are performed
by **real cryptography** running in the background.

It implements the conceptual innovation from Assignment 1: a **graduated,
three-stage disclosure protocol** in which each stage's intrusion is licensed by
the previous stage's result — mapping onto the proportionality structure that
AMLR Article 75 requires.

## The three-stage workflow (the dashboard)

`app.py` (Streamlit + Plotly) is an investigator workspace for Bank Alpha, with
a case queue. Each case is gated through three stages:

1. **Stage 1 — Consortium Match Check.** Is this entity present elsewhere?
   Returns only a **match count** — never institution identities.
2. **Stage 2 — Risk Attestation.** Do anonymous high-risk confirmations exist?
   Returns an **aggregate count + concern level**; source banks stay hidden.
3. **Stage 3 — Controlled Network View.** Only after Stages 1–2 pass, a
   controlled cross-institutional transaction graph is revealed (Plotly).

A stage is locked until the prior one passes, and a case timeline records the
workflow — the gating *is* the innovation: whether sharing is justified is
assessed before anything is shared.

## What runs underneath (real cryptography)

The dashboard calls two entry points — `run_stage1_psi_cardinality` (in
`backend_stage1.py`) and `run_zkp_attestation` (in `backend.py`). These are thin
adapters: they preserve the interface the UI expects but obtain their counts from
the real protocol in the `aegis/` package, via `aegis_backend.py`:

- **Shared identifier** (`aegis/identity.py`) — every bank derives the same
  opaque code from a person's identity fields; banks match on the code, not on
  names. (Keyed-hash **stand-in for an OPRF** — see the file's note.)
- **Committed list** (`aegis/merkle.py`) — each bank commits its high-risk codes
  to one Merkle **root**, registered before any query, and answers with a
  membership **recipe** that proves one entry without revealing the rest.
- **Sealed channels + blind routing** (`aegis/channel.py`, `aegis/parties.py`) —
  the query is sealed so the operator only relays opaque blobs; every member
  always replies (real recipe or encrypted `NO_MATCH`) so the operator can't tell
  who matched; replies are sealed to the querying bank alone.

The verified count the dashboard shows is the *output* of this protocol, not a
hardcoded value — if the crypto broke, the number would change.

### Who learns what

| Party | Learns | Does **not** learn |
|-------|--------|--------------------|
| Responding banks | the entity (to check their list) | which bank asked |
| Aegis (router) | that a query happened; that all members replied | the entity; the recipes; who matched |
| Querying bank | how many members flag the entity | which banks |

## Repository layout

```
Aegis-MVP/
├── app.py                # Streamlit + Plotly investigator dashboard (UI)
├── backend_stage1.py     # Stage 1 entry point -> real crypto via aegis_backend
├── backend.py            # Stage 2 entry point -> real crypto via aegis_backend
├── aegis_backend.py      # builds a consortium per case, runs the real protocol
├── aegis/                # the cryptographic core
│   ├── identity.py       # shared cross-bank identifier (OPRF stand-in)
│   ├── merkle.py         # committed high-risk list (root) + membership recipe
│   ├── channel.py        # sealed channels that keep the router blind
│   └── parties.py        # MemberBank (querier/responder) + Aegis (blind router)
├── .streamlit/config.toml
├── requirements.txt
├── AGENTS.md             # AI-agent instructions / orchestration
└── README.md
```

## Run

Requires Python 3.10+.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Sanity-check the crypto layer directly:

```bash
python backend_stage1.py   # CUST-1047 -> 2, CUST-2198 -> 0, CUST-3321 -> 1
python backend.py          # verified confirmation counts + aggregate risk
python aegis_backend.py     # self-test of the underlying protocol
```

## What is real vs. an MVP simplification

1. **The shared identifier is re-identifiable.** It is a keyed hash standing in
   for an Oblivious PRF (the engine of Stage-1 PSI); production swaps that one
   function so identifiers can't be brute-forced offline.
2. **Matching is exact.** Strict canonicalisation and stable identifiers (LEI for
   companies; national id + DOB where lawful) are required.
3. **Router-blindness rests on a trust assumption:** member banks share the
   broadcast key with each other but not the operator (production uses per-bank
   public keys).
4. **Soundness rests on the registry:** a recipe is trusted only if its root was
   pre-registered — operational trust in a neutral utility instead of a
   per-message signature.
5. **Only the COUNT is cryptographically verified** at Stage 2; per-bank severity
   levels are a derived label. Stage-1 presence is modelled with the same
   membership primitive (full PSI is the production upgrade), and the Stage-3
   graph is synthetic demo data.

## Security considerations

**Operator (Aegis):** stays blind because queries and replies are sealed and all
members always reply; the root registry is the trust anchor and must be governed;
until the OPRF is deployed, the operator (like any member) could attempt to
brute-force identifiers, so the OPRF is a launch prerequisite.

**Users (banks / data subjects):** the broadcast currently reveals the entity to
responding banks (tipping-off risk) until Stage-1 PSI blinding is added; exact
matching can cause false negatives; per AMLR Article 75(4)(c) a member must do its
own assessment and may not rely solely on consortium signals.

## Topic tags

`aml` · `privacy-preserving-computation` · `zero-knowledge` · `merkle-tree` ·
`private-set-intersection` · `fintech` · `streamlit` · `python`

---

*Prototype environment · No live customer data.*

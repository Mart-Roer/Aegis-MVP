# Aegis — Investigator MVP

**Cross-institutional anti-money-laundering, built for the EU AML framework.**

Aegis lets a bank check whether a flagged customer is also flagged elsewhere in
a consortium of banks — **without** any bank exposing its customer data, without
revealing **which** other banks hold a match, and without the Aegis operator
learning **who** is being investigated. This repository is a working MVP of the
investigator-facing workflow, with the privacy-preserving checks performed by
real cryptography running in the background.

It is the MVP for the business model in *Assignment 1* and implements the core
conceptual innovation: a **graduated, three-stage disclosure protocol** in which
each stage's intrusion is licensed by the previous stage's result, mapping onto
the proportionality structure that AMLR Article 75 requires.

---

## What you see: the three-stage workflow

The dashboard (`app.py`, Streamlit) is an investigator workspace with a case
queue. Each case moves through three gated stages:

1. **Stage 1 — Consortium Match Check.** Is this entity present elsewhere in the
   consortium? Returns only a **match count** — never institution identities.
   The case can only escalate if there is at least one match.
2. **Stage 2 — Risk Attestation.** Do anonymous high-risk confirmations exist for
   this entity? Returns an **aggregate count + concern level**; source banks stay
   hidden. Escalation requires a sufficient, verified attestation.
3. **Stage 3 — Controlled Network View.** Only after Stages 1–2 pass, a controlled
   cross-institutional view is opened. (In production this is secure multi-party
   graph analytics; in the MVP it is a controlled disclosure panel.)

Each stage is locked until the prior one passes, and a case timeline records the
workflow. This gating *is* the conceptual innovation: the assessment of whether
sharing is justified is itself performed before any data is shared.

---

## What runs underneath: the privacy-preserving checks

Stages 1 and 2 are not hardcoded — they are computed by the `aegis` package and
exposed to the dashboard through `aegis_backend.py`. The mechanism, in plain
terms:

- **A shared identifier** (`aegis/identity.py`). Every bank turns a person's
  identity fields into the same opaque code via one agreed function, so banks
  match on the code, never on raw names.
- **A committed list** (`aegis/merkle.py`). Each bank hashes its high-risk codes
  into a single Merkle **root**, registered with Aegis *before any query*. This
  freezes the list, so a bank cannot invent a flag after being asked.
- **A blind query** (`aegis/channel.py`, `aegis/parties.py`). The querying bank
  seals its question so only member banks can read it; the Aegis router only ever
  forwards opaque blobs. Every bank always replies (a real membership **recipe**
  or an encrypted `NO_MATCH`), so the router cannot tell who matched.
- **Local verification.** The querying bank opens the sealed replies (sealed to
  it alone), checks each recipe against the *registered* roots, and counts the
  genuine matches — learning the count, not which banks.

The key property emulated here is the zero-knowledge one: **prove a single entry
is on a list, reveal nothing about the rest of the list.** No digital signatures
or ring are used — anonymity comes from blind routing, and trust from
pre-registered commitments plus membership proofs.

### Who learns what

| Party | Learns | Does **not** learn |
|-------|--------|--------------------|
| Responding banks | the entity (to check their list) | which bank asked |
| Aegis (router) | that a query happened; that all members replied | the entity; the recipes; who matched |
| Querying bank | how many members flag the entity (genuine members) | which banks |

---

## Repository layout

```
Aegis-MVP/
├── app.py              # Streamlit dashboard (UI + three-stage workflow)
├── aegis_backend.py    # bridge: realises each stage via the real protocol
├── aegis/              # the cryptographic core
│   ├── identity.py     # shared cross-bank identifier (OPRF stand-in)
│   ├── merkle.py       # committed high-risk list (root) + membership recipe
│   ├── channel.py      # sealed channels that keep the router blind
│   └── parties.py      # MemberBank (querier/responder) + Aegis (blind router)
├── requirements.txt
├── AGENTS.md           # AI-agent orchestration notes
└── README.md
```

The dashboard reads only two backend calls — `stage1_match_count(...)` and
`stage2_attestation(...)` — so the cryptography is fully decoupled from the UI.

---

## Run it

Requires Python 3.10+.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints. Select a case in the sidebar and step
through the stages.

To run the cryptographic protocol on its own (self-test against the case
scenarios):

```bash
python aegis_backend.py     # verified counts must match each case's scenario
```

---

## What is real vs. an MVP simplification

Stated openly, with the production upgrade path:

1. **The shared identifier is re-identifiable.** It is a keyed hash of low-entropy
   identity fields, which a party holding the key could brute-force; under GDPR it
   is still personal data. **Production replaces `shared_identifier` with an
   Oblivious PRF** — the engine of Stage-1 Private Set Intersection — so codes
   cannot be computed for guesses offline. The codebase calls one function, so the
   swap is local.
2. **Matching is exact.** A typo or changed field yields a different code and a
   silent miss; hence strict canonicalisation and stable identifiers (LEI for
   companies; national id + DOB where lawful), aligned with AMLA's data standards.
3. **Router-blindness rests on a trust assumption:** member banks share the
   broadcast key with each other but not with the operator. Production uses
   per-bank public keys (same structure, no shared secret).
4. **Soundness rests on the registry:** a recipe is trusted only if its root was
   pre-registered. This is operational trust in a neutral utility (the SWIFT /
   EBA Clearing model) in place of a per-message signature.
5. **Stage 3 is a controlled-disclosure panel**, standing in for the production
   secure multi-party graph analytics.

---

## Security considerations

**For the operator (Aegis).** The router must remain blind: queries and replies
are sealed so it relays only opaque blobs, and all members always reply so reply
patterns leak nothing. The registry of valid roots is the trust anchor and must
be governed (onboarding, key management, availability / DoS protection). Until the
OPRF is deployed, the operator — like any member — could attempt to brute-force
identifiers, so the OPRF is a launch prerequisite, not optional hardening.

**For the users (member banks and data subjects).** The current broadcast reveals
the queried entity to all responding banks (tipping-off risk) until Stage-1 PSI
blinding is in place. Exact matching can cause false negatives. And per AMLR
Article 75(4)(c), a member must perform its own assessment and may not rely solely
on consortium-derived signals for decisions affecting customers — the system
provides attested signals, not decisions.

---

## AI-agent orchestration

This MVP was developed with AI coding agents; see `AGENTS.md` for the agent
instructions and how work was orchestrated across the dashboard and the
cryptographic core.

---

## Topic tags

`aml` · `privacy-preserving-computation` · `zero-knowledge` · `merkle-tree` ·
`private-set-intersection` · `fintech` · `streamlit` · `python`

---

*Prototype environment · No live customer data.*

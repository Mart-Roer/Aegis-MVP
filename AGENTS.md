# AGENTS.md — Aegis AML MVP

## Project Purpose

This repository contains a minimal Streamlit MVP for **Aegis**, a privacy-preserving AML consortium platform.

The goal is to demonstrate the core business logic of Aegis: a **graduated disclosure protocol** for anti-money laundering collaboration between banks. Each stage only reveals more information when the previous stage has justified escalation.

This MVP is for an educational product demo. It should be simple, readable, and investor-demo friendly.

## Core Concept

Aegis chains privacy-preserving technologies into a three-stage workflow:

1. Stage 1 — Private Set Intersection (PSI) simulation
2. Stage 2 — Zero-Knowledge Proof (ZKP) / anonymous risk attestation simulation
3. Stage 3 — Conditional transaction graph disclosure

The legal logic and the technical logic should stay aligned:

* Stage 1 answers whether the entity appears elsewhere.
* Stage 2 answers whether anonymous risk confirmations exist.
* Stage 3 only unlocks wider transaction graph information after Stages 1 and 2 justify escalation.

The main architectural idea is **graduated disclosure**: the system assesses whether sharing is necessary before sharing sensitive information.

## Important Limitation

This MVP does **not** implement production-grade cryptography.

Do not claim that the software performs real PSI, real ZKP, ring signatures, threshold cryptography, or live AML detection.

Instead, the MVP simulates the outputs of these cryptographic stages using synthetic data so that the workflow, user experience, and business logic can be demonstrated.

Use wording such as:

* “PSI simulation”
* “ZKP attestation simulation”
* “anonymous risk attestation simulation”
* “synthetic transaction graph”
* “production version would require audited cryptographic libraries”

## Minimal File Structure

Keep the project as simple as possible.

Preferred files:

* `app.py` — main Streamlit app
* `README.md` — human-readable project explanation and run instructions
* `AGENTS.md` — AI-agent instructions
* `session-log.md` — short record of AI-agent use
* `requirements.txt` — Python dependencies
* `.gitignore` — ignored local files

Do not create extra folders or extra files unless they are clearly necessary.

Keep most or all code in `app.py` for the first MVP.

## MVP Features to Implement

The Streamlit app should show a simple investigator dashboard for an AML analyst at **Bank Alpha**.

The app should not appear to scan all customers. It should start from customers that have already been flagged by Bank Alpha’s internal AML monitoring system.

## Dashboard

Create a dashboard with multiple internally flagged customer cases.

Each case should include:

* Customer ID
* Customer type
* Internal flag reason
* Internal risk level
* Current Aegis workflow status
* Button or selection option to open the case

Use synthetic demo cases.

### Case A — Full Escalation

* Customer ID: `CUST-1047`
* Type: Import/export business
* Flag reason: Unusual trade payments
* Internal risk: High
* Stage 1 result: Match found at 3 other banks
* Stage 2 result: Positive anonymous risk attestation, High risk
* Outcome: Stage 3 unlocks

### Case B — Stops After Stage 1

* Customer ID: `CUST-2198`
* Type: Individual customer
* Flag reason: Rapid incoming and outgoing transfers
* Internal risk: Medium
* Stage 1 result: No match
* Outcome: Stage 2 and Stage 3 remain locked

### Case C — Stops After Stage 2

* Customer ID: `CUST-3321`
* Type: SME
* Flag reason: Cash-intensive activity
* Internal risk: High
* Stage 1 result: Match found at 1 other bank
* Stage 2 result: Negative or Low risk attestation
* Outcome: Stage 3 remains locked

## Case Workflow

After selecting a customer, show a three-stage workflow.

Use clear headings:

* Stage 1 — PSI Simulation
* Stage 2 — Anonymous Risk Attestation
* Stage 3 — Conditional Transaction Graph

Each stage should have:

* A short explanation
* A button to run the stage
* A loading or processing message
* A result card
* A clear locked, unlocked, or completed status

The user should always understand:

* What information is being checked
* What is revealed
* What remains hidden
* Why the next stage is or is not unlocked

## Stage 1 — PSI Simulation

The user should be able to run a Stage 1 check for the selected flagged customer.

The app should show whether the entity is present at other consortium banks.

The app may show:

* Entity found elsewhere: Yes/No
* Number of other banks: X
* Bank identities: Hidden

Required privacy rule:

* Do not reveal individual bank names in Stage 1 output.

Example output:

* Entity found elsewhere: Yes
* Number of other banks: 3
* Bank identities: Hidden

If Stage 1 is positive, Stage 2 unlocks.

If Stage 1 is negative, Stage 2 and Stage 3 stay locked.

## Stage 2 — Anonymous Risk Attestation Simulation

Stage 2 is only available if Stage 1 shows cross-institutional presence.

The app should show:

* Whether anonymous risk confirmations exist
* A simple aggregate risk category, such as Low, Medium, or High
* A verification status, such as “Attestation verified”
* No individual bank identities
* No dates, rationales, or bank-specific risk details

Required privacy rule:

* Do not reveal which banks flagged, investigated, or denied service to the entity.

Example output:

* Anonymous risk confirmations: 2
* Aggregate risk category: High
* Source banks: Hidden
* Attestation status: Verified

If Stage 2 is positive and the aggregate risk category is High, Stage 3 unlocks.

If Stage 2 is negative or Low risk, Stage 3 stays locked.

## Stage 3 — Conditional Transaction Graph Disclosure

Stage 3 should stay locked unless Stage 1 and Stage 2 pass the required thresholds.

If Stage 3 unlocks, the app can show a simple synthetic transaction graph or transaction table.

The purpose of Stage 3 is to demonstrate that deeper knowledge sharing only happens after privacy-preserving checks justify escalation.

Example output:

* Stage 3 unlocked
* Synthetic related accounts
* Synthetic transaction amounts
* Simplified suspicious network view

For `CUST-1047`, show a simple synthetic network such as:

* `CUST-1047` connected to Entity A through repeated trade payments
* Entity A connected to Account B through circular transfers
* Account B connected to Entity C through high-frequency payments

Risk indicators:

* Possible trade-based laundering pattern
* Circular transaction flow
* Cross-institutional network activity

Required rule:

* Use synthetic data only.
* Make clear that this is a demo graph, not real transaction data.

## Suggested Thresholds

Use simple demo thresholds:

* Stage 1 passes if the entity appears at 1 or more other banks.
* Stage 2 passes if anonymous risk confirmations are 1 or more and aggregate risk is High.
* Stage 3 unlocks only if both Stage 1 and Stage 2 pass.

These thresholds are for the MVP only and should be described as configurable in a real product.

## UX Rules

The app should be easy to understand for a non-technical viewer.

The product demo should feel investor-oriented.

Emphasize:

* Reduced duplicated AML investigations
* Privacy-preserving collaboration
* Proportional disclosure
* Detection of cross-bank suspicious networks

Use clear visual indicators:

* Locked stages
* Unlocked stages
* Completed stages
* Risk badges
* Result cards
* Short privacy explanations

## Coding Rules

* Keep the code simple and readable.
* Prefer plain Python and Streamlit.
* Use synthetic in-code data if that avoids extra files.
* Add short comments for important business logic.
* Avoid overengineering.
* Avoid unnecessary classes.
* Avoid unnecessary folders.
* Avoid external APIs.
* Avoid real customer data.
* Avoid complex cryptographic libraries in the MVP.
* Do not expose individual bank identities in Stage 1 or Stage 2.

## Recommended Dependencies

Use only minimal dependencies.

Preferred `requirements.txt`:

```text
streamlit
pandas
```

Only add another package if absolutely necessary.

## Testing Instructions

Before committing, run:

```bash
streamlit run app.py
```

Check that:

* The dashboard loads.
* A user can select each demo customer.
* Stage 1 can be run.
* Stage 2 only unlocks after a positive Stage 1 result.
* Stage 3 only unlocks after a positive/high-risk Stage 2 result.
* Cases B and C stop earlier as intended.
* No individual bank names are revealed in Stage 1 or Stage 2.

## Main Demo Path

The app should support a short demonstration showing:

1. Open the dashboard.
2. Select `CUST-1047`.
3. Run Stage 1.
4. Show that Stage 2 unlocks after a match.
5. Run Stage 2.
6. Show that Stage 3 unlocks after high-risk attestation.
7. Request and view the controlled transaction graph.
8. Return to the dashboard.
9. Open another case where escalation stops earlier.

The key message of the MVP:

> Aegis helps banks investigate cross-institutional AML risk while minimizing unnecessary data sharing. It does not begin with broad data pooling. It begins with an internally flagged customer and escalates only when justified.

## Cryptographic Backend (`aegis/` package and `aegis_backend.py`)

> This section supersedes the earlier "keep everything in `app.py`" and "avoid
> cryptographic libraries" guidance **for the privacy-check layer only**. The MVP
> was extended by the coding agent so that Stage 1 and Stage 2 are backed by a
> genuine membership-proof protocol instead of reading hardcoded case values.
> The dashboard must stay visually unchanged; only the *source* of the numbers
> changes.

### Goal

Implement the privacy checks behind Stages 1 and 2 as real cryptography — a
shared identifier, committed Merkle roots, membership proofs ("recipes"), sealed
channels, and a blind router — and expose them to `app.py` through a single
bridge module. The agent should generate this as a small, self-contained package
inside the repository, with each module documented in plain language.

### Files the agent should create (keep each small and single-purpose)

* `aegis/identity.py` — the shared cross-bank identifier.
* `aegis/merkle.py` — a bank's committed high-risk list and the membership recipe.
* `aegis/channel.py` — the sealed channels that keep the router blind.
* `aegis/parties.py` — `MemberBank` (querier/responder) and `Aegis` (blind router).
* `aegis_backend.py` — the bridge the dashboard calls.
* `demo.py` — a standalone lifecycle + adversarial self-test.

### Module-by-module instructions

* **`identity.py`** — Implement `canonicalize(attrs)` to normalise identity
  fields (lowercase, trimmed, fixed order) and `shared_identifier(attrs, key)` as
  a keyed hash (HMAC-SHA256) so the same person yields the same opaque code at
  every bank. Document clearly that this is a **stand-in for an Oblivious PRF**;
  the whole codebase must call this one function so the upgrade is local.
* **`merkle.py`** — Implement a `FlaggedSet` that hashes each high-risk code into
  a salted leaf and builds a Merkle `root`. Provide `make_recipe(identifier)`
  (salt + sibling path) and `verify_recipe(root, identifier, recipe)`. The root
  must be one-way and binding; entries other than the queried one must never be
  revealed.
* **`channel.py`** — Provide two sealed channels using the `cryptography` library:
  a symmetric broadcast seal readable by member banks but not the operator, and a
  reply seal to the querying bank's one-time public key. Keep this file short.
* **`parties.py`** — Implement `MemberBank.make_query`, `MemberBank.answer`
  (always reply: a real recipe or an encrypted `NO_MATCH`), `MemberBank.read_replies`
  (accept only roots registered with Aegis **and** recipes that verify), and an
  `Aegis` router that forwards opaque blobs and publishes the unlabelled set of
  valid roots.
* **`aegis_backend.py`** — Expose exactly `stage1_match_count(case_id, n)` and
  `stage2_attestation(case_id, n)`; build a consortium per case, run the real
  sealed/routed query, and return the verified counts (with a derived aggregate
  risk). Use a cached singleton via `get_backend()`.

### Dashboard integration (no visual change)

In `app.py`, replace the reads of `entity["matching_banks"]` and
`entity["anonymous_confirmations"]` with `get_backend().stage1_match_count(...)`
and `get_backend().stage2_attestation(...)`. Do **not** change any text, layout,
styling, or stage-gating logic. Add a `.streamlit/config.toml` theme so button
colours stay readable across Streamlit versions.

### Real vs. simulated boundary (state this honestly)

* **Real:** the Merkle membership proofs, the sealed channels, the blind routing,
  and verification against pre-registered roots.
* **Stand-ins:** the shared identifier is a keyed hash standing in for an OPRF;
  full Stage-1 PSI and Stage-3 MPC graph analytics remain simulated.
* Do **not** claim full production PSI or MPC; the membership-proof layer is real,
  the surrounding stages are simplified.

### Dependencies

Add `cryptography` to `requirements.txt` (used only by `channel.py`). Everything
else stays standard library. `streamlit` and `pandas` remain for the dashboard.

### Testing this layer

```bash
python aegis_backend.py   # self-test: verified counts match each case scenario
python demo.py            # full lifecycle + adversarial checks
streamlit run app.py      # confirm the dashboard behaves exactly as before
```

The adversarial checks must show: a forged (unregistered) root is rejected, a
mistyped identity correctly returns no match, and the router cannot read the
traffic it relays.

### Conventions for this package

* Pure standard library plus `cryptography`; no other cryptographic dependencies.
* One responsibility per module; the dashboard depends only on `aegis_backend`.
* Every public function carries a docstring linking it to its business-plan role.
* Never expose which bank matched, never reveal the queried entity to the
  operator, and never disclose any member's full list.

## Session Log Requirement

After every meaningful coding session or major change, update `session-log.md`.

The session log should record the AI-assisted development process in a clear chronological format.

For each session, include:

* Date or session number
* User instruction or goal
* AI/code-agent actions
* Files created or modified
* Errors encountered
* Fixes applied
* Human decisions

Do not invent actions that did not happen.

Keep the log concise but specific enough to show the collaboration history.

Use this format:

```markdown
## Session X — Short title

### User instruction / goal

Briefly summarize what the user asked the AI agent to do.

### AI/code-agent actions

- List the main actions performed by the AI agent.
- Mention important files edited, such as `app.py`, `README.md`, `AGENTS.md`, or `requirements.txt`.

### Errors or issues

- Mention errors encountered, if any.
- Mention fixes applied.

### Human decisions

- List decisions made by the human user, such as choosing Streamlit, changing the UI style, or deciding to use a step-by-step workflow.
```

Before finishing any coding task, check whether `session-log.md` should be updated.

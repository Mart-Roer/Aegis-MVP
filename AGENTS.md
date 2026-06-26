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
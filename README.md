# Aegis-MVP
# Aegis

Aegis is a FinTech MVP that demonstrates a privacy-conscious, cross-institutional anti-money laundering workflow for banks. The project shows how financial institutions could collaborate on suspicious cases without immediately sharing sensitive customer or transaction data.

The MVP is based on a staged disclosure model. A bank starts from a customer it has already flagged internally. The system then checks whether the customer appears elsewhere in a simulated banking consortium, whether other institutions have anonymous risk signals, and only then unlocks a limited network view.

## Project Purpose

Money laundering is often a cross-institutional network problem, but individual banks usually only see their own part of the activity. This creates fragmented visibility and makes suspicious patterns harder to detect. At the same time, broad pooling of customer data creates privacy and proportionality concerns.

Aegis addresses this tension by demonstrating a workflow where collaboration only escalates when there is enough justification.

The MVP shows:

* how a bank can begin from an internally flagged customer;
* how cross-bank presence can be checked without revealing full customer lists;
* how anonymous risk confirmations can increase suspicion;
* how a controlled network view can reveal patterns that were previously hidden;
* how privacy and proportionality can be reflected in software architecture.

## Concept

Aegis is designed as a consortium-style utility for banks. Instead of one third-party platform owning or controlling the data, participating banks would act as members of a shared infrastructure.

The concept is inspired by financial infrastructure models such as SWIFT or EBA Clearing. The goal is not to create a high-margin data platform, but a trusted industry utility that helps banks cooperate while respecting privacy constraints.

The MVP shows the back-end of Aegis, while the demo shows the concept from the perspective of one investigating bank.

## MVP Workflow

The application follows three main stages.

### Stage 1: Match Check

The investigating bank selects a customer that has already been flagged internally by its own anti-money laundering process.

The system then checks whether this customer appears at other consortium banks. The MVP simulates Private Set Intersection logic by returning only the number of matches at other banks, without revealing customer lists or bank identities.

### Stage 2: Anonymous Risk Attestation

If a match exists, the system checks whether other banks also have risk signals related to the same entity.

The MVP simulates zero-knowledge-style attestation by showing aggregate confirmation without revealing the underlying details or the source banks.

### Stage 3: Controlled Network View

If the risk threshold is reached, the system unlocks a limited network view showing related institutions, intermediary entities, and transaction patterns that were previously hidden.

The Stage 3 view may include:

* the originating institution;
* matched institutions;
* intermediary entities;
* transaction flows;
* recurring transaction values;
* a broader suspicious pattern across the network.

This stage represents the highest disclosure level in the MVP.

## How to Run the Project

```bash
# 1. Clone the repository
git clone https://github.com/Mart-Roer/Aegis-MVP.git

# 2. Move into the project folder
cd Aegis-MVP

# 3. Install requirements
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## How to Use the Demo

1. Open the application.
2. Select a flagged customer case.
3. Review the internal case summary.
4. Run Stage 1 to check for cross-bank presence.
5. If Stage 1 finds a match, continue to Stage 2.
6. Run Stage 2 to check for anonymous risk confirmations.
7. If the concern threshold is met, unlock Stage 3.
8. Review the controlled network graph and metrics.
9. Use the output to explain how staged disclosure reveals a broader anti-money laundering pattern.

## Authors

* Mart Roerdink
* Nicole Eggens


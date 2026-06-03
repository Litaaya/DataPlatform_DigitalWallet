# Business Problem and Scope

## Document Changelog
| Version | Author  | Description                                   |
|:--------|:--------|:----------------------------------------------|
| v1.0    | Litaaya | Initial draft for Core Single-Currency Wallet |

---

## 1. Context & Business Entities

The goal of this platform is to manage the transactional data lifecycle of a digital wallet ecosystem. The domain model is limited to two core business entities:

* **Customer:** Represents the legal owner of the wallet (the end-user). A customer must have a unique identifier and basic profile attributes.
* **Wallet Account:** Represents the actual financial account holding the monetary value. 
  * Each Customer can own one Wallet Account.
  * The account operates strictly in a single currency: **United States Dollar (USD)**.
  * The account balance is **derived**, meaning it is dynamically calculated from historical records rather than stored as a static, editable value.

---

## 2. Problem Statement

Modern financial data platforms require absolute data integrity and auditability. This platform will contain three critical engineering challenges:

1. **Loss of Audit Trail:** Direct updates overwrite the historical state, making it impossible to trace the exact sequence of events that led to the current balance.
2. **Data Tampering Risks:** If a balance row is altered maliciously or corrupted due to a system crash, there is no deterministic mechanism to verify its authenticity.
3. **Reconciliation Failures:** Without a centralized, unalterable transaction ledger, internal data cannot be verified against external bank partners, leading to undetected financial leaks.

This project solves these challenges by implementing a **Ledger-First Architecture**, ensuring that every financial movement is permanently etched, verifiable, and compliance-ready.

---

## 3. Product Scope

### 3.1 In-Scope (Core Financial Operations)

The platform supports exactly five core transaction types. Every event must be classified into one of these types and adhere to the strict direction rules below:

* **`TOPUP` (Credit / +):** Money enters the wallet ecosystem from an external funding source (e.g., a linked bank card). This increases the account balance.
* **`PURCHASE` (Debit / -):** Money leaves the wallet ecosystem to pay for a service or goods. This decreases the account balance.
* **`REFUND` (Credit / +):** Reverses a prior `PURCHASE` transaction. Money is returned to the user's wallet.
  * *Constraint:* Must contain a reference ID (`ref_txn_id`) pointing back to the original purchase transaction.
* **`TRANSFER` (Double-Entry / Split):** Internal movement of money from one wallet account to another. 
  * *Constraint:* Must generate exactly **two ledger entries** atomically: a `DEBIT` from the sender's account and a `CREDIT` to the receiver's account. Both entries must share a unique `transfer_id`.
* **`ADJUSTMENT` (Manual Correction):** Executed exclusively by system administrators or customer operations to correct technical anomalies. Can be either a `CREDIT` or a `DEBIT`.
  * *Constraint:* Requires a mandatory audit reason text field and an administrator ID.

### 3.2 Out-of-Scope (Future Enhancements)

To guarantee timely delivery and avoid scope creep, the following features are strictly excluded from the current phase:
* **Multi-Currency Support:** No exchange rates or multi-currency wallets (Locked to USD).
* **Overdraft Limits:** Accounts are not allowed to go below zero (Negative balances are out of scope for standard users).
* **Loyalty & Rewards:** No cashback, loyalty points, or voucher sub-ledgers.
* **Real-time Fraud Triggers:** No inline transaction blocking; the platform focuses entirely on ingestion, data warehousing, and post-event auditing.

---

## 4. Core Domain Principles (Data Semantics)

Every component built downstream (Data Models, Kafka topics, dbt transformations) must satisfy these two architectural pillars:

### Pillar 1: Ledger Immutability (Append-Only)
The data platform enforces a strict **write-once, read-many** policy. 
* Financial transactions are final. 
* `UPDATE` or `DELETE` statements are physically and logically banned from the ledger layer. 
* Human errors or system glitches must be resolved by issuing a counter-balancing transaction (`REFUND`, `REVERSAL`, or `ADJUSTMENT`), never by editing history.

### Pillar 2: Balance Derivation
A wallet's balance is not the absolute source of truth; it is merely a representation of the ledger's history. The platform must compute the balance at any given timestamp $T$ using the deterministic formula:

$$Balance_T = \sum (Credits) - \sum (Debits)$$

Any snapshot or cached balance stored in the analytical layer must be completely reproducible by replaying the ledger entries from day zero up to timestamp $T$.
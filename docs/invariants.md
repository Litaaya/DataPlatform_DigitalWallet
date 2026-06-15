# Data Invariants and Quality Rules

## Document Changelog

| Version | Author  | Description                                             |
|:--------|:--------|:--------------------------------------------------------|
| v1.0    | Litaaya | Initial draft for Core Financial Data Invariants        |
| v1.1    | Litaaya | Aligned financial invariants with immutable ledger DDL  |

---

## 1. System-Wide Invariants (The Ultimate Rules)

These rules apply across all data layers: **Bronze (Postgres `raw` schema)**, **Silver**, and **Gold**.

* **Transaction Uniqueness:** Every transaction event must have a globally unique identifier (`transaction_id`). Duplicated IDs are strictly treated as data corruption or replay attacks.
* **Positivity of Values:** The financial `amount` of any transaction must be strictly greater than zero ($amount > 0$). Zero-value or negative-value transactions are logically invalid.
* **Temporal Logic:** Every event must capture two essential timestamps:
    * `event_time`: The exact moment the user initiated the transaction on their app.
    * `ingest_time` (mapped as `loaded_at` in the raw layer): The exact moment the platform persisted the event into the database.
    * *Constraint:* `ingest_time` must always be greater than or equal to `event_time` ($ingest\_time \ge event\_time$).

---

## 2. Account-Level Invariants (Balance Protection)

* **No Negative Balances:** Since overdraft functionality is out of scope, a Wallet Account's derived cumulative balance must never fall below zero at any snapshot interval or historical timestamp $T$:
    $$Balance_T \ge 0$$
* **Account Referencing:** Every transaction must map to a valid, pre-existing `account_id` and `customer_id`. Orphaned transactions (transactions without an owner) are completely banned.

---

## 3. Transaction-Specific Rules & Structural Integrity

### 3.1 `TRANSFER` Integrity (Double-Entry Balanced Rule)
A single internal transfer event from User A to User B must be atomic and perfectly balanced.
* **Line Count:** One transfer operation must generate exactly **two distinct rows** in the `gold_ledger_entries` layer.
* **Sign Normalization:** In compliance with financial audit standards, `amount` remains an absolute positive value for both rows, while the impact is driven by the `direction` column (`DEBIT` for the sender, `CREDIT` for the receiver).
* **Zero-Sum Equation:** For any unique `transfer_id`, the absolute credit amount must perfectly offset the absolute debit amount:
    $$Amount_{CREDIT} - Amount_{DEBIT} = 0$$

### 3.2 `REFUND` Linkage Rule
* A `REFUND` transaction cannot exist in isolation.
* The `ref_txn_id` field must not be null and must successfully join with a historical `transaction_id` whose type was `PURCHASE`.
* The refund amount cannot exceed the original purchase amount.

---

## 4. Data Quality Action Matrix (For Phase 6 dbt Testing)

When dbt runs daily batch validations, any records violating the rules above will be handled based on severity:

| Invariant Violated         | Severity Level | System Action                                                      |
|:---------------------------|:---------------|:-------------------------------------------------------------------|
| Duplicate `transaction_id` | Critical       | Quarantine row in Silver layer, exclude from Gold Ledger.          |
| `amount` $\le$ 0           | Critical       | Drop or flag as `INVALID_AMOUNT`.                                  |
| Missing `account_id`       | Critical       | Quarantine as orphaned transaction, trigger immediate Slack Alert. |
| Derived Balance < 0        | High           | Log error in `gold_reconciliation_results` as `BAL_NEGATIVE`.      |
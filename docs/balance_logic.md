# Balance Derivation Logic

## Document Changelog

| Version  | Author | Description                                           |
|:---------|:-------|:------------------------------------------------------|
| v1.0     | Litaaya| Initial pseudo-SQL for balance computation & snapshots|

---

## 1. Core Logic Overview

As defined in the business scope, the account balance is a **derived metric** and not a static source of truth. Since the `gold_ledger_entries` layer already normalizes signs (positive for `CREDIT`, negative for `DEBIT`), the mathematical calculation for any balance is a simple cumulative sum:

$$Balance = \sum (amount)$$

---

## 2. Pseudo-SQL Implementation (dbt Target)

### 2.1. Current Real-time Balance (Point-in-Time)
To find the exact balance of a specific wallet account at any given timestamp $T$:

```sql
SELECT 
    account_id,
    SUM(amount) AS current_balance
FROM gold_ledger_entries
WHERE event_time <= '2026-06-04 23:59:59' -- Target Timestamp T
GROUP BY account_id;
```

### 2.2. Daily EOD (End of day) Snapshot Generation

To generate the historical daily snapshots for the `gold_balance_snapshot_daily` table:

```sql
SELECT 
    CONCAT(account_id, '_', CAST(event_time AS DATE)) AS snapshot_id,
    account_id,
    CAST(event_time AS DATE) AS snapshot_date,
    SUM(amount) AS end_of_day_balance,
    CURRENT_TIMESTAMP AS computed_at
FROM gold_ledger_entries
GROUP BY account_id, CAST(event_time AS DATE);
```

## 3. Rushed Late-Arriving Event Policy (WIP)

- Challenge: Transactions delayed at the source app might arrive hours late into the data lake.

- MVP Strategy: To ensure speed and simplicity for the demo, the platform will backfill snapshots based strictly on `event_time`. When the daily batch dbt pipeline runs, it will recalculate the entire history (Full-Refresh processing) to guarantee absolute accuracy on the dashboard. Advanced incremental partitioning will be optimized in later phases.

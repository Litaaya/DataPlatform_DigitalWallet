{{ config(
    materialized='table',
    schema='gold'
) }}

WITH daily_net_changes AS (
    SELECT
        account_id,
        DATE(event_time) AS snapshot_date,
        SUM(amount) AS daily_net_change
    FROM {{ ref('gold_ledger_entries') }}
    GROUP BY 1, 2
),

cumulative_balances AS (
    SELECT
        account_id,
        snapshot_date,
        SUM(daily_net_change) OVER (
            PARTITION BY account_id
            ORDER BY snapshot_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS end_of_day_balance
    FROM daily_net_changes
)

SELECT
    CONCAT(account_id, '_', snapshot_date) AS snapshot_id,
    account_id,
    snapshot_date,
    end_of_day_balance,
    CURRENT_TIMESTAMP AS computed_at
FROM cumulative_balances
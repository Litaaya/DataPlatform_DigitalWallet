{{ config(
    materialized='table',
    schema='gold'
) }}

WITH clean_silver AS (
    SELECT * FROM {{ ref('silver_wallet_transactions') }}
    WHERE is_valid = TRUE
)

SELECT
    transaction_id AS entry_id,
    transaction_id,
    account_id,

    CASE
        WHEN direction = 'CREDIT' THEN amount
        WHEN direction = 'DEBIT' THEN -amount
        ELSE 0
    END AS amount,

    direction,
    transfer_id,
    transaction_at AS event_time

FROM clean_silver
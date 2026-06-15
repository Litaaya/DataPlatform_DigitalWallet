{{ config(
    materialized='table',
    schema='silver'
) }}

WITH raw_data AS (
    SELECT
        -- Cast data types from raw JSON to explicit columns
        (raw_payload->>'event_id')::varchar(50) AS transaction_id,
        (raw_payload->>'account_id')::varchar(50) AS account_id,
        (raw_payload->>'customer_id')::varchar(50) AS customer_id,
        (raw_payload->>'txn_type')::varchar(20) AS transaction_type,
        (raw_payload->>'amount')::numeric(18, 2) AS amount,
        (raw_payload->>'direction')::varchar(10) AS direction,
        (raw_payload->>'ref_txn_id')::varchar(50) AS reference_transaction_id,
        (raw_payload->>'transfer_id')::varchar(50) AS transfer_id,
        (raw_payload->>'event_time')::timestamp AS transaction_at,
        loaded_at
    FROM {{ source('bronze', 'wallet_transactions_raw') }}
),

deduplicated AS (
    SELECT
        *,
        -- Number the files sequentially to filter duplicates by transaction ID, prioritizing files uploaded later
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id
            ORDER BY loaded_at DESC
        ) AS row_num
    FROM raw_data
)

SELECT
    transaction_id,
    account_id,
    customer_id,
    transaction_type,
    amount,
    direction,
    reference_transaction_id,
    transfer_id,
    transaction_at,
    loaded_at
FROM deduplicated
-- Only retrieve unique records (completely remove duplicate rows)
WHERE row_num = 1 AND amount > 0
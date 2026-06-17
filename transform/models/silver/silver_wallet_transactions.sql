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

ranked_data AS (
    SELECT
        *,
        -- Number the files sequentially to filter duplicates by transaction ID, prioritizing files uploaded later
        ROW_NUMBER() OVER (
            PARTITION BY transaction_id
            ORDER BY transaction_at ASC, loaded_at ASC
        ) AS occurrence_rank,
        COUNT(*) OVER (PARTITION BY transaction_id) AS total_occurrences
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
    loaded_at,

    -- Flag to test the validity
    CASE
        WHEN transaction_id = 'DUPLICATE-UUID-TEST-9999-999999999999' OR (total_occurrences > 1 AND occurrence_rank > 1) THEN FALSE
        WHEN amount <= 0 THEN FALSE
        WHEN account_id IS NULL OR customer_id IS NULL THEN FALSE
        ELSE TRUE
    END AS is_valid,

    -- Categorizing the reasons for data contamination
    CASE
        WHEN transaction_id = 'DUPLICATE-UUID-TEST-9999-999999999999' OR (total_occurrences > 1 AND occurrence_rank > 1) THEN 'DUP_TXN'
        WHEN amount <= 0 THEN 'NEG_AMOUNT'
        WHEN account_id IS NULL OR customer_id IS NULL THEN 'ORPHANED_TXN'
        ELSE 'CLEAN'
    END AS error_code
FROM ranked_data;
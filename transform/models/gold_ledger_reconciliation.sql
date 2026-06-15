{{ config(
    materialized='table',
    schema='gold'
) }}

WITH debit_side AS (
    SELECT
        transfer_id,
        account_id AS sender_account,
        customer_id AS sender_customer,
        amount AS debit_amount,
        transaction_at AS transfer_at
    FROM {{ ref('silver_wallet_transactions') }}
    WHERE transaction_type = 'TRANSFER' AND direction = 'DEBIT'
),

credit_side AS (
    SELECT
        transfer_id,
        account_id AS receiver_account,
        customer_id AS receiver_customer,
        amount AS credit_amount
    FROM {{ ref('silver_wallet_transactions') }}
    WHERE transaction_type = 'TRANSFER' AND direction = 'CREDIT'
)

SELECT
    d.transfer_id,
    d.sender_account,
    d.sender_customer,
    c.receiver_account,
    c.receiver_customer,
    d.debit_amount,
    c.credit_amount,
    (d.debit_amount - c.credit_amount) AS balance_difference,

    CASE
        WHEN c.transfer_id IS NULL THEN 'MISSING_CREDIT_SIDE'
        WHEN d.debit_amount = c.credit_amount THEN 'BALANCED'
        ELSE 'DISCREPANCY'
    END AS audit_status,

    d.transfer_at
FROM debit_side d
LEFT JOIN credit_side c ON d.transfer_id = c.transfer_id
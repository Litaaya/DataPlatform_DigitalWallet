{{ config(
    materialized='table',
    schema='gold'
) }}

WITH silver_data AS (
    SELECT * FROM {{ ref('silver_wallet_transactions') }}
)

SELECT
    DATE(transaction_at) AS report_date,
    transaction_type,
    direction,

    COUNT(transaction_id) AS total_transactions,
    SUM(amount) AS total_financial_volume,
    ROUND(AVG(amount), 2) AS avg_transaction_value,

    COUNT(DISTINCT customer_id) AS unique_active_customers

FROM silver_data
GROUP BY 1, 2, 3
ORDER BY report_date DESC, total_financial_volume DESC
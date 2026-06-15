from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default parameters of the system
default_args = {
    'owner': 'minh_quan',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# Init pipeline
with DAG(
    'digital_wallet_data_pipeline',
    default_args=default_args,
    description='The pipeline automatically feeds raw data from MinIO and casts the Silver/Gold stage via dbt',
    schedule_interval=None,
    start_date=datetime(2026, 2, 14),
    catchup=False,
    tags=['fintech', 'wallet', 'dbt'],
) as dag:

    run_loader = BashOperator(
        task_id='ingest_bronze_to_postgres_raw',
        bash_command='cd /opt/airflow/project && python loader/main.py',
    )

    run_dbt_transform = BashOperator(
        task_id='dbt_transform_silver_gold',
        bash_command='cd /opt/airflow/project/transform && dbt run --profiles-dir .',
    )

    run_loader >> run_dbt_transform
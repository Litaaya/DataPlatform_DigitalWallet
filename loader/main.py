import os
import json
import logging
import boto3
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Log display configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5433")
MINIO_HOST = os.getenv("MINIO_HOST", "localhost")

# Configuration parameters
MINIO_CONFIG = {
    "endpoint_url": f"http://{MINIO_HOST}:9000",
    "aws_access_key_id": os.getenv("MINIO_ROOT_USER"),
    "aws_secret_access_key": os.getenv("MINIO_ROOT_PASSWORD"),
    "bucket_name": "wallet-analytics"
}

POSTGRES_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB")
}

def init_postgres_table(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.wallet_transactions_raw (
                id SERIAL PRIMARY KEY,
                file_name VARCHAR(255),
                raw_payload JSONB,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.ingestion_logs (
                file_name VARCHAR(255) PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    logging.info("Postgres raw_layer table structure initialized successfully!")

def get_already_processed_files(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT file_name FROM raw.ingestion_logs;")
        return set(row[0] for row in cur.fetchall())


def load_minio_to_postgres():
    s3_client = boto3.client('s3', **{k: v for k, v in MINIO_CONFIG.items() if k != 'bucket_name'})
    pg_conn = None

    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        init_postgres_table(pg_conn)
        processed_files = get_already_processed_files(pg_conn)

        bucket = MINIO_CONFIG["bucket_name"]
        paginator = s3_client.get_paginator('list_objects_v2')

        logging.info(f"Scanning data files in the data lake bucket '{bucket}'...")

        records_to_insert = []
        files_to_log = []

        for page in paginator.paginate(Bucket=bucket):
            if 'Contents' not in page:
                logging.info("Bucket empty")
                return

            for obj in page['Contents']:
                file_key = obj['Key']

                if "wallet-transactions" in file_key and file_key.endswith(".json"):
                    if file_key in processed_files:
                        continue

                    logging.info(f"New file detected: {file_key} | Processing...")

                    s3_response = s3_client.get_object(Bucket=bucket, Key=file_key)
                    file_content = s3_response['Body'].read().decode('utf-8')

                    for line in file_content.strip().split('\n'):
                        if line:
                            json_data = json.loads(line)
                            records_to_insert.append((file_key, json.dumps(json_data)))

                    files_to_log.append((file_key,))

        if records_to_insert:
            with pg_conn.cursor() as cur:
                execute_values(
                    cur,
                    "INSERT INTO raw.wallet_transactions_raw (file_name, raw_payload) VALUES %s",
                    records_to_insert
                )
                execute_values(
                    cur,
                    "INSERT INTO raw.ingestion_logs (file_name) VALUES %s ON CONFLICT DO NOTHING",
                    files_to_log
                )
                pg_conn.commit()
            logging.info(f"Top-up successful {len(records_to_insert)} Raw logs into Postgres")
        else:
            logging.info("No new files need to be loaded. Data has been fully synchronized")

    except Exception as e:
        pg_conn.rollback()
        logging.error(f"Data loading process failed: {e}")
    finally:
        pg_conn.close()


if __name__ == "__main__":
    load_minio_to_postgres()
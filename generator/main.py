import json
import time
import uuid
import random
import logging
from datetime import datetime, timezone
from confluent_kafka import Producer

# Logging system configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka infrastructure
KAFKA_CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'wallet_generator_producer'
}

TOPIC_NAME = 'wallet-transactions'

# Kafka producer
try:
    producer = Producer(KAFKA_CONFIG)
    logging.info("Kafka Producer successfully launched!")
except Exception as e:
    logging.error(f"Kafka Producer launch error: {e}")
    exit(1)

def delivery_report(err, msg):
    if err is not None:
        logging.error(f"Message sent failed: {err}")
    else:
        logging.info(f"Successfully sent to {msg.topic()} [Partition: {msg.partition()}]")

past_purchases = []

# Mock Data engine
def generate_transaction():
    global past_purchases
    txn_types = ['TOPUP', 'PURCHASE', 'REFUND', 'TRANSFER', 'ADJUSTMENT']
    chosen_type = random.choice(txn_types)

    if chosen_type == 'REFUND' and not past_purchases:
        chosen_type = 'PURCHASE'

    event_id = str(uuid.uuid4())
    customer_id = f"CUST_{random.randint(1000, 1999)}"
    account_id = f"ACC_{customer_id.split('_')[1]}"
    amount = round(random.uniform(5.0, 500.0), 2)
    event_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    direction = 'CREDIT' if chosen_type in ['TOPUP', 'REFUND'] else 'DEBIT'
    transfer_id = f"TRF_{random.randint(100000, 999999)}" if chosen_type == 'TRANSFER' else None

    ref_txn_id = None
    if chosen_type == 'REFUND':
        ref_txn_id = random.choice(past_purchases)

    # Anomaly injection
    anomaly_dice = random.random()
    error_note = "CLEAN"

    if anomaly_dice < 0.05:
        amount = -amount
        error_note = "ANOMALY: NEGATIVE AMOUNT"
    elif anomaly_dice < 0.10:
        event_id = "DUPLICATE-UUID-TEST-9999-999999999999"
        error_note = "ANOMALY: DUPLICATE TRANSACTION ID"

    txn_payload = {
        "event_id": event_id,
        "account_id": account_id,
        "customer_id": customer_id,
        "txn_type": chosen_type,
        "amount": amount,
        "direction": direction,
        "ref_txn_id": ref_txn_id,
        "transfer_id": transfer_id,
        "event_time": event_time
    }

    if chosen_type == 'ADJUSTMENT':
        txn_payload["admin_id"] = f"ADM_00{random.randint(1, 5)}"
        txn_payload["audit_reason"] = random.choice([
            "Technical correction due to network gateway timeout",
            "Manual wallet re-balancing requested by customer support",
            "Clearing operational ledger discrepancy anomalies"
        ])

    return txn_payload, error_note, chosen_type

# Main streaming pipeline
logging.info(f"Start transfer data to Topic: '{TOPIC_NAME}'...")
try:
    while True:
        payload, note, txn_type = generate_transaction()

        if txn_type == 'TRANSFER' and "ANOMALY" not in note:
            payload['ref_txn_id'] = None
            payload['direction'] = 'DEBIT'
            producer.produce(TOPIC_NAME, key=payload['event_id'], value=json.dumps(payload), callback=delivery_report)

            receiver_payload = payload.copy()
            receiver_payload['event_id'] = str(uuid.uuid4())
            receiver_payload['account_id'] = f"ACC_{random.randint(2000, 2999)}"
            receiver_payload['customer_id'] = f"CUST_{receiver_payload['account_id'].split('_')[1]}"
            receiver_payload['direction'] = 'CREDIT'
            receiver_payload['ref_txn_id'] = None
            producer.produce(TOPIC_NAME, key=receiver_payload['event_id'], value=json.dumps(receiver_payload), callback=delivery_report)
        else:
            producer.produce(TOPIC_NAME, key=payload['event_id'], value=json.dumps(payload), callback=delivery_report)
            if txn_type == 'PURCHASE' and note == "CLEAN":
                past_purchases.append(payload['event_id'])

        if note != "CLEAN":
            logging.warning(f"Deliberate error has been intentionally created: {note} | ID: {payload['event_id']}")

        producer.poll(0)
        time.sleep(1.5)

# Graceful Shutdown method
except KeyboardInterrupt:
    logging.info("Received a stop request from the user. Clearing the queue...")
finally:
    producer.flush()
    logging.info("Safely disconnected from Kafka.")
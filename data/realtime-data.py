from kafka import KafkaProducer
import json
from faker import Faker
import time

fake = Faker()
producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def send_transaction():
    while True:
        transaction = {
            "transaction_id": fake.uuid4(),
            "user_id": f"U{fake.random_int(1000, 3000)}",
            "product_id": f"P{fake.random_int(100, 999)}",
            "action": fake.random_element(elements=("click", "purchase", "refund")),
            "transaction_amount": round(fake.random_number(digits=2), 2),
            "timestamp": fake.iso8601(),
        }
        producer.send('transactions', transaction)
        print(f"Sent: {transaction}")
        time.sleep(1)

send_transaction()

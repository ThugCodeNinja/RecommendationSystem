import pandas as pd
from faker import Faker
import random

fake = Faker()
Faker.seed(42)

def generate_transactions(num_records=1000):
    transactions = []
    for _ in range(num_records):
        transaction = {
            "transaction_id": fake.uuid4(),
            "user_id": f"U{random.randint(1000, 3000)}",
            "product_id": f"P{random.randint(100, 999)}",
            "action": random.choice(["click", "purchase", "refund"]),
            "transaction_amount": round(random.uniform(5, 500), 2),
            "timestamp": fake.date_time_between(start_date="-1y", end_date="now"),
            "status": random.choice(["completed", "pending"])
        }
        transactions.append(transaction)
    
    return pd.DataFrame(transactions)

df_transactions = generate_transactions(20000)
df_transactions.to_csv("historical_transactions.csv", index=False)

import pandas as pd
from faker import Faker
import random

fake = Faker()
Faker.seed(42)

categories = ["Electronics", "Clothing", "Sportswear", "Groceries", "Books"]
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

# df_transactions = generate_transactions(20000)
# df_transactions.to_csv("historical_transactions.csv", index=False)
def generate_coupons(num_records=2000):
    coupons = []
    for _ in range(num_records):
        coupon = {
            "coupon_id": f"C{random.randint(1000, 9999)}",
            "code": fake.bothify(text="SAVE###"),
            "discount_percentage": random.choice([5, 10, 15, 20, 50, 100]),
            "valid_from": fake.date_this_year(),
            "valid_till": fake.date_between(start_date="today", end_date="+6m"),
            "usage_limit": random.randint(50, 500),
            "usage_count": random.randint(0, 50),
            "category": random.choice(categories),
            "status": "active"
        }
        coupons.append(coupon)
    
    return pd.DataFrame(coupons)

df_coupons = generate_coupons(2000)
df_coupons.to_csv("coupons.csv", index=False)

def generate_products(num_records=500):
    products = []
    categories = ["Electronics", "Clothing", "Sportswear", "Groceries", "Books"]
    
    for _ in range(num_records):
        product = {
            "product_id": f"P{random.randint(100, 999)}",
            "name": fake.catch_phrase(),
            "description": fake.text(max_nb_chars=100),
            "category": random.choice(categories),
            "price": round(random.uniform(10, 1000), 2),
            "created_at": fake.date_time_between(start_date="-2y", end_date="now"),
            "updated_at": fake.date_time_this_year()
        }
        products.append(product)
    
    return pd.DataFrame(products)

df_products = generate_products(1000)
df_products.to_csv("products.csv", index=False)


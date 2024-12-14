from snowflake.snowpark import Session
from snowflake.snowpark.functions import current_timestamp
from config import *

# Connection parameters
connection_parameters = {
    "account": account,
    "user": user,
    "password": password,
    "database": database,
    "schema": schema,
    "role": role,
    "warehouse": warehouse
}

# Create the Snowflake session
new_session = Session.builder.configs(connection_parameters).create()

coupons_df = new_session.sql("""
    SELECT DISTINCT
        'COUPON_' || "user_id" || '_' || "product_id" AS coupon_id,
        "user_id",
        "product_id",
        ROUND(10 + (RANDOM() * 20), 2) AS discount,
        DATEADD('DAY', 30, CURRENT_DATE) AS expiration_date,
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM user_transactions
""")

# Write the generated coupons to the 'coupons' table
coupons_df.write.mode("append").save_as_table("coupons")

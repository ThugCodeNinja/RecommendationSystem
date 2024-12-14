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

# Use the specified warehouse, database, and schema
new_session.sql("USE WAREHOUSE compute_wh").collect()
new_session.sql("USE DATABASE histransactions").collect()
new_session.sql("USE SCHEMA public").collect()
new_session.sql("""
    INSERT INTO users (user_id, name, email, created_at, updated_at)
    SELECT DISTINCT
        "user_id",
        'User_' || "user_id" AS name,
        "user_id" || '@example.com' AS email,
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM user_transactions
    WHERE "user_id" NOT IN (SELECT user_id FROM users)
""").collect()

from snowflake.snowpark import Session
import pandas as pd
from query import create_tables
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

create_tables()
# Create the Snowflake session
new_session = Session.builder.configs(connection_parameters).create()
# Use the specified database and schema
new_session.sql("USE WAREHOUSE compute_wh").collect()
new_session.sql("USE DATABASE histransactions").collect()
new_session.sql("USE SCHEMA public").collect()

# Load CSV into a Pandas DataFrame
df = pd.read_csv('historical_transactions.csv')
if df.empty:
    raise ValueError("The DataFrame is empty. Please check the CSV file.")
# Convert columns to their appropriate data types
for f in ["transaction_id","user_id","product_id","action"]:
    df[f] = df[f].astype(str)
# Convert 'transaction_amount' to float
df['transaction_amount'] = pd.to_numeric(df['transaction_amount'], errors='coerce')
# Convert 'timestamp' to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
snow_df = new_session.create_dataframe(df.iloc[1:].reset_index())
snow_df.write.mode("append").save_as_table("user_transactions")

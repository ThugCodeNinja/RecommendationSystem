from snowflake.snowpark import Session
import pandas as pd
from config import *

def create_tables():
# Updated connection parameters with additional required fields
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

# Use the specified database and schema
    new_session.sql("USE DATABASE histransactions").collect()
    new_session.sql("USE SCHEMA public").collect()

# Create the 'products' table first
    new_session.sql("""
    CREATE TABLE IF NOT EXISTS products (
        product_id STRING PRIMARY KEY,
        name STRING,
        description STRING,
        category STRING,
        price DECIMAL(10, 2),
        created_at TIMESTAMP,
        updated_at TIMESTAMP);""").collect()

# Create the 'users' table
    new_session.sql("""
    CREATE TABLE IF NOT EXISTS users (
        user_id STRING PRIMARY KEY,
        name STRING,
        email STRING,
        created_at TIMESTAMP,
        updated_at TIMESTAMP);""").collect()

# Create the 'user_transactions' table
    new_session.sql("""
    CREATE TABLE IF NOT EXISTS user_transactions (
        transaction_id STRING PRIMARY KEY,
        user_id STRING REFERENCES users(user_id),
        product_id STRING REFERENCES products(product_id),
        action STRING,
        transaction_amount DECIMAL(10, 2),
        timestamp TIMESTAMP);""").collect()


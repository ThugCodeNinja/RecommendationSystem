import pandas as pd
from snowflake.snowpark import Session
from config import *
from tqdm import tqdm
from bs4 import BeautifulSoup

tqdm.pandas()
connection_parameters = {
    "account": account,
    "user": user,
    "password": password,
    "database": database,
    "schema": schema,
    "role": role,
    "warehouse": warehouse
}
new_session = Session.builder.configs(connection_parameters).create()
new_session.sql("CREATE DATABASE IF NOT EXISTS cortex_search_db").collect()
new_session.sql("USE DATABASE cortex_search_db").collect()
new_session.sql("USE SCHEMA query_search").collect()

def read_data(path):
    df = pd.read_csv(path)
    return df

def preprocess_data(row):
    """Remove HTML tags and unnecessary whitespace."""
    if pd.isnull(row):
        return ""
    return BeautifulSoup(row, 'html.parser').get_text().strip()


new_session.sql("""CREATE OR REPLACE TABLE question_answers (
    title VARCHAR,
    question VARCHAR,
    answer VARCHAR);""").collect()

data= read_data("Dataset_huggingface_libraries.csv")

cols=["title","question","answer"]
for col in cols:
    data[col] = data[col].apply(preprocess_data)

snow_df = new_session.create_dataframe(data.iloc[1:][cols].reset_index(drop=True))
snow_df.write.mode("append").save_as_table("question_answers")
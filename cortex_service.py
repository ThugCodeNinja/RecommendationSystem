from snowflake.snowpark import Session
from config import *

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
new_session.sql("""ALTER TABLE query_search.question_answers SET
  CHANGE_TRACKING = TRUE;""").collect()




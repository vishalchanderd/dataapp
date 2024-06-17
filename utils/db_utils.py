# db_utils.py

import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

def create_db_engine():
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')

    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={db_host};DATABASE={db_name};UID={db_user};PWD={db_password}"
    params = quote_plus(conn_str)
    sqlalchemy_conn_str = f"mssql+pyodbc:///?odbc_connect={params}"
    
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    return engine
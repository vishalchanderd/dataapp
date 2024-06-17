# loginauth.py

import streamlit as st
from sqlalchemy import text
from utils.db_utils import create_db_engine  # Updated import statement


def authenticate_user(username, password):
    engine = create_db_engine()
    query = text("SELECT * FROM tr_work.dbo.dataapp_auth WHERE username = :username AND password = :password")
    with engine.connect() as connection:
        result = connection.execute(query, username=username, password=password)
        row = result.fetchone()
    
    return bool(row)

def show_login_form():
    with st.form(key='loginauth'):
        username = st.text_input('Username', key='username_login')
        password = st.text_input('Password', type='password', key='password_login')
        submitted = st.form_submit_button('Login')
        if submitted:
            return username, password
    return None, None

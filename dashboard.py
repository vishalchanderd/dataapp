import streamlit as st
from tabs.data_view_tab import Data_Tab as show_data_view
from tabs.data_ai_tab import smartDataChat as show_ai

def show_dashboard(username):
    st.sidebar.title("Smart Data App")
    st.sidebar.write(f"Welcome to the dashboard, {username}!")
    with st.expander("Data Table", expanded=True):  # Optionally set one section to be expanded by default
      st.session_state['dataexpander'] = st.expander
      show_data_view(username)
    show_ai()
import streamlit as st
import tempfile
import pyreadstat
import os
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from utils.db_utils import create_db_engine  # Updated import statement
from utils.Create_Table_Utils import create_table_name_from_filename  # Updated import statement
from datetime import datetime, timedelta


def Data_Tab(username):
    if 'during_initial_loading' not in st.session_state:
        st.session_state['during_initial_loading'] = []
        if 'SQL_ENGINE' not in st.session_state:
               st.session_state['SQL_ENGINE'] = create_db_engine()             
    # Set up a header and file uploader widget in the main content area.
    st.sidebar.header("Upload SPSS File")
    # Initialize a session state variable to keep track of files that have been processed.
    # This prevents re-processing the same file within the same session.
    if 'processed_files' not in st.session_state:
        st.session_state['processed_files'] = []
    uploaded_file = st.sidebar.file_uploader("Drag and Drop or Click to Upload an SPSS File", type=["sav"], key="file_uploader")     
    # Check if a file has been uploaded.
    if uploaded_file:
        # Retrieve the name of the uploaded file.
        file_name = uploaded_file.name
        # Check if this file has already been processed to avoid duplicate processing.
        if file_name not in st.session_state['processed_files']:
            # Load the data from the uploaded SPSS file.
            data = load_data_from_spss(uploaded_file, username, st.session_state['SQL_ENGINE'])
            # If data loading is successful, mark the file as processed and display the data.
            if data is not None:
                st.session_state['processed_files'].append(file_name)  # Add the file to the list of processed files
    create_sidebar_with_files(st.session_state['SQL_ENGINE'], username)

def load_data_from_spss(uploaded_file,username,engine):   
    if uploaded_file is not None:
        st.session_state.pop('sidebar_files', None)  # Remove cached file list
        st.session_state.pop('current_sanitised_tablename', None)  # Remove cached file list
        st.session_state.pop('cache_key', None)  # Remove cached file list    
        st.session_state.pop('current_sanitised_tablename', None)  # Remove cached file list     
        st.session_state['messages'] = []  # Reset messages list
        st.session_state['dataframes'] = {}  # Reset dataframes dict       

        file_name, file_extension = os.path.splitext(uploaded_file.name) # Extract file name without extension and the extension itself
        sanitized_table_name = create_table_name_from_filename(file_name)
        file_size = uploaded_file.size               

        if check_filename_exists(engine, file_name, username):
            st.error("This file has already been uploaded and processed.")
            return
            None, None  # Stop further processing and return immediately
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sav") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        try:
            df, meta = pyreadstat.read_sav(tmp_file_path)
            df_labeled = apply_value_labels(df, meta,engine,sanitized_table_name)            
            #st.write(df)  # Display the loaded data in the main content area.            
            log_file_upload(engine, username, file_name, sanitized_table_name, file_extension, file_size) # Log the successful upload and table creation            
            create_table_and_insert_data(df_labeled, sanitized_table_name, engine)  # Insert data into SQL table                            
            return df, meta
        except Exception as e:
            st.error(f"An error occurred while loading the SPSS file: {e}")
            return None, None
    else:
        return None, None
    
def check_filename_exists(engine, original_filename, username):
    """
    Check if a given filename already exists in the UploadedFiles table for a specific user.

    :param engine: The SQLAlchemy engine to use for the database connection.
    :param original_filename: The original filename to check.
    :param username: The username associated with the file.
    :return: True if the filename exists, False otherwise.
    """
    query = text("SELECT COUNT(*) FROM tr_work.dbo.dataapp_UploadedFiles WHERE Original_Filename = :original_filename AND Username = :username")
    result = engine.execute(query, original_filename=original_filename, username=username).scalar()
    
    return result > 0

# def apply_value_labels(df, meta,engine,ref_table_name):
#     # Apply value labels to each column in the dataframe
#     # Optionally, rename columns to more descriptive names
#     # Map original column names to new labels, truncating any label over 128 characters    
#     for col in df.columns:
#         if col in meta.variable_value_labels:
#             # Create a mapping of codes to labels
#             label_map = meta.variable_value_labels[col]
#             # Apply the mapping
#             df[col] = df[col].map(label_map)            
#     # renamed_columns = {original: label[:128] for original, label in zip(meta.column_names, meta.column_labels)}
#     # # Rename the DataFrame columns with the updated mapping
#     # df.rename(columns=renamed_columns, inplace=True)
#     return df

def apply_value_labels(df, meta, engine, ref_table_name):
    """
    Applies value labels to columns in the DataFrame and creates a reference table in SQL 
    database within the 'tr_work.dbo' schema, mapping original column names to descriptive labels,
    removing any content before and including the first '-' in the descriptive labels.

    Parameters:
    - df: The DataFrame to process.
    - meta: Metadata object containing mappings for value labels and column labels.
    - engine: SQLAlchemy engine for database connection.
    - ref_table_name: Base name for the reference table to be created in the SQL database.
    """
    # Apply value labels to each column in the dataframe
    for col in df.columns:
        if col in meta.variable_value_labels:
            label_map = meta.variable_value_labels[col]
            df[col] = df[col].map(label_map)
            
    # Prepare data for the reference table
    ref_data = {
        "OriginalColumnName": meta.column_names,
        # Remove everything before and including the first "-" for each label, if present
        "DescriptiveLabel": [label.split(" - ", 1)[-1][:4000] if " - " in label else label[:4000] for label in meta.column_labels]
    }
    ref_df = pd.DataFrame(ref_data)
    
    # Generate a unique table name by appending a fixed identifier
    refer_columns_name = "ref"
    unique_ref_table_name = f"{ref_table_name}_{refer_columns_name}"
    # Create the reference table in the SQL database, specifying the schema
    ref_df.to_sql(name=unique_ref_table_name, con=engine, schema='tr_work.dbo', if_exists='replace', index=False)
    
    return df

def log_file_upload(engine, username, original_filename, sanitized_tablename, file_type, file_size):
    """
    Inserts a log entry into the UploadedFiles table, including file size and type.
    
    :param engine: SQLAlchemy engine connected to the database.
    :param username: The username who uploaded the file.
    :param original_filename: The original name of the uploaded file.
    :param sanitized_tablename: The sanitized name used as the SQL table name.
    :param file_type: The type of the uploaded file (extension or MIME type).
    :param file_size: The size of the uploaded file in bytes.
    """
    insert_query = text("""
        INSERT INTO tr_work.dbo.dataapp_UploadedFiles 
        (Username, Original_Filename, Sanitized_Tablename, Upload_Timestamp, File_Size, File_Type)
        VALUES (:username, :original_filename, :sanitized_tablename, GETDATE(), :file_size, :file_type)
    """)
    
    try:
        with engine.connect() as connection:
            connection.execute(insert_query, username=username, original_filename=original_filename, sanitized_tablename=sanitized_tablename, file_size=file_size, file_type=file_type)
            print("Upload log successfully inserted.")
    except Exception as e:
        print(f"Failed to log upload: {e}")

def create_table_and_insert_data(df, table_name, engine):
    # Assuming df is your DataFrame loaded from the SPSS file and table_name is a string
    try:
        df.to_sql(name=table_name, con=engine, schema='tr_work.dbo', if_exists='replace', index=False)
    except Exception as e:
        print(f"An error occurred: {e}")

# def categorize_by_date(upload_timestamp):
#     """Categorize the upload timestamp into a human-readable category."""
#     today = datetime.now().date()
#     yesterday = today - timedelta(days=1)
#     last_week = today - timedelta(days=7)

#     if upload_timestamp.date() == today:
#         return 'Today'
#     elif upload_timestamp.date() == yesterday:
#         return 'Yesterday'
#     elif today - timedelta(days=7) < upload_timestamp.date() <= yesterday:
#         return 'Last Week'
#     else:
#         return 'Older'

# def create_sidebar_with_files(engine, username):
#     if 'sidebar_files' not in st.session_state:
#         query = text("""
#             SELECT Original_Filename, Sanitized_Tablename, Upload_Timestamp
#             FROM tr_work.dbo.dataapp_UploadedFiles
#             WHERE Username = :username
#         """)
#         with engine.connect() as connection:
#             result = connection.execute(query, username=username).fetchall()
#         st.session_state['sidebar_files'] = [(row[0], row[1], categorize_by_date(row[2])) for row in result]
#     else:
#         print("Using cached sidebar_files")

#     grouped_files = {}
#     for original_filename, sanitized_tablename, category in st.session_state['sidebar_files']:
#         if category not in grouped_files:
#             grouped_files[category] = []
#         grouped_files[category].append((original_filename, sanitized_tablename))

#     for category in ['Today', 'Yesterday', 'Last Week', 'Older']:
#         if category in grouped_files:
#             st.sidebar.write(f"## {category}")
#             for original_filename, sanitized_tablename in grouped_files[category]:
#                 unique_key = f"{original_filename}_{sanitized_tablename}"
#                 if st.sidebar.button(original_filename, key=unique_key):
#                     st.session_state['current_sanitised_tablename'] = sanitized_tablename
#                     loadDataFromSQL(engine, sanitized_tablename)
#                     st.session_state['already_not_loaded'] = False

#     if 'current_sanitised_tablename' in st.session_state and st.session_state['already_not_loaded']:
#         print("Rerun: Loading data for", st.session_state['current_sanitised_tablename'])
#         loadDataFromSQL(engine, st.session_state['current_sanitised_tablename'])
#         st.session_state['already_not_loaded'] = False

def create_sidebar_with_files(engine, username):
    # Check and load sidebar_files from the database if not in session_state
    if 'sidebar_files' not in st.session_state:
        query = text("""
            SELECT Original_Filename, Sanitized_Tablename
            FROM tr_work.dbo.dataapp_UploadedFiles
            WHERE Username = :username
        """)
        with engine.connect() as connection:
            result = connection.execute(query, username=username).fetchall()
        st.session_state['sidebar_files'] = result
    else:
        print("Using cached sidebar_files")
        
    result = st.session_state['sidebar_files']   
    st.session_state['already_not_loaded'] = True
    # Loop through the query results to create sidebar buttons
    for index, (original_filename, sanitized_tablename) in enumerate(result):
        unique_key = f"{original_filename}_{sanitized_tablename}_{index}"
        if st.sidebar.button(original_filename, key=unique_key):
            st.session_state['current_sanitised_tablename'] = sanitized_tablename
            loadDataFromSQL(engine, sanitized_tablename)
            st.session_state['already_not_loaded'] = False            
    
    # Handle data load on rerun if a tablename was previously selected
    if 'current_sanitised_tablename' in st.session_state and st.session_state['current_sanitised_tablename']:
        print("Rerun: Loading data for", st.session_state['current_sanitised_tablename'])
        if(st.session_state['already_not_loaded']):
            loadDataFromSQL(engine, st.session_state['current_sanitised_tablename'])
            st.session_state['already_not_loaded'] = True    


    
def loadDataFromSQL(engine, sanitized_tablename):    
    st.session_state.currentdf = None

    # Cache key based on sanitized_tablename for caching the DataFrame
    cache_key = f"data_{sanitized_tablename}"
    st.session_state['current_sanitised_tablename'] = sanitized_tablename
    if cache_key not in st.session_state:
        # Load data from SQL if not cached
        query_string = f"SELECT * FROM tr_work.dbo.{sanitized_tablename}"
        with engine.connect() as connection:
            result = connection.execute(text(query_string)).fetchall()
        df = pd.DataFrame(result, columns=[col for col in result[0].keys()]) if result else pd.DataFrame()
        st.session_state[cache_key] = df  # Cache the loaded DataFrame
          

    
    # Use the cached or just-loaded DataFrame
    df = st.session_state[cache_key]
    
    # Display DataFrame if not empty
    if not df.empty:
        st.header(sanitized_tablename)        
        st.dataframe(df)
        st.session_state.currentdf = df
  
    else:
        st.write(f"No data found for {sanitized_tablename}.")

# def create_sidebar_with_files(engine, username):
#     if 'sidebar_files' not in st.session_state:
#         query = text("""
#             SELECT Original_Filename, Sanitized_Tablename
#             FROM tr_work.dbo.dataapp_UploadedFiles
#             WHERE Username = :username
#         """)
#         with engine.connect() as connection:
#             result = connection.execute(query, username=username).fetchall()
#         st.session_state['sidebar_files'] = result
#     else:
#         print("Using cached sidebar_files")
    
#     result = st.session_state['sidebar_files']   
#     st.session_state['already_not_loaded'] = True
    
#     for index, (original_filename, sanitized_tablename) in enumerate(result):
#         unique_key = f"{original_filename}_{sanitized_tablename}_{index}"
#         col1, col2 = st.sidebar.columns([0.8, 0.2])
#         if col1.button(original_filename, key=unique_key):
#             st.session_state['current_sanitised_tablename'] = sanitized_tablename
#             loadDataFromSQL(engine, sanitized_tablename)
#             st.session_state['already_not_loaded'] = False

#         descriptive_button_key = f"info_{index}"
#         if col2.button("ℹ️", key=descriptive_button_key):
#             st.session_state[descriptive_button_key] = not st.session_state.get(descriptive_button_key, False)
    
#     if any(st.session_state.get(f"info_{i}", False) for i in range(len(result))):
#         for i, (original_filename, sanitized_tablename) in enumerate(result):
#             descriptive_button_key = f"info_{i}"
#             if st.session_state.get(descriptive_button_key):
#                 descriptive_names_table = f"{sanitized_tablename}_ref"
#                 descriptive_names_query = f"""
#                     SELECT OriginalColumnName, DescriptiveLabel
#                     FROM tr_work.dbo.{descriptive_names_table}
#                 """
#                 with engine.connect() as connection:
#                     descriptive_names_result = connection.execute(text(descriptive_names_query)).fetchall()
                
#                 descriptive_text = "\n".join([f"{row[0]}: {row[1]}" for row in descriptive_names_result])
#                 st.write(f"Column descriptions for {original_filename}:")
#                 st.text_area("Descriptions", value=descriptive_text, height=300)
#                 if st.button("Close", key=f"close_{i}"):
#                     st.session_state[descriptive_button_key] = False

#     if 'current_sanitised_tablename' in st.session_state and st.session_state['already_not_loaded']:
#         print("Rerun: Loading data for", st.session_state['current_sanitised_tablename'])
#         loadDataFromSQL(engine, st.session_state['current_sanitised_tablename'])
#         st.session_state['already_not_loaded'] = False


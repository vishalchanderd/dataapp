import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from pandasai import SmartDataframe
from pandasai.llm.openai import OpenAI
import matplotlib.pyplot as plt
from matplotlib.figure import Figure



# Load the OpenAI API key from the .env file
load_dotenv()
client = OpenAI()
openai_api_key = os.getenv('OPENAI_API_KEY')

# Ensure the OpenAI API key is loaded
if not openai_api_key:
    raise ValueError("The OpenAI API key is not set in the environment variables.")

def smartDataChat():    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "dataframes" not in st.session_state:
        st.session_state["dataframes"] = {}  # Ready for multiple dataframes

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Convert all message content to string to ensure compatibility with string methods
            content = str(message["content"])
            
            # Attempt to identify and handle dataframe references within the content
            try:
                if content.startswith("[DATAFRAME-"):
                    df_id = content.replace("[DATAFRAME-", "").replace("]", "")
                    df = st.session_state["dataframes"].get(df_id, None)
                    if df is not None:
                        st.dataframe(df)
                    else:
                        st.markdown("Dataframe is not available.")
                else:
                    st.markdown(content)
            except AttributeError as e:
                # Log or handle the unexpected content type
                st.markdown(f"Error processing message content: {e}")



    prompt = st.chat_input("What's on your mind?")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        
        st.session_state.messages.append({"role": "user", "content": prompt})

        if "currentdf" in st.session_state and st.session_state["currentdf"] is not None:
            result = chat_with_data(st.session_state["currentdf"], prompt)
            if isinstance(result, pd.DataFrame):
                # Generate a unique identifier for the new dataframe
                df_id = f"df_{len(st.session_state['dataframes'])}"  # Unique identifier for the dataframe
                st.session_state["dataframes"][df_id] = result  # Store the dataframe
                st.dataframe(result)
                response = f"[DATAFRAME-{df_id}]"
            elif isinstance(result, dict) and result.get("type") == "plot":
                print("************************ PLOT ***********************")
                # Assuming 'value' contains the path to the plot image
                plot_path = result.get("value")
                if plot_path:
                    # Display the plot image using Streamlit's st.image
                    st.image(plot_path)
                    response = f"Displayed plot: {plot_path}"
                else:
                    response = "Plot path not found."
                # Optionally, append a message about displaying the plot
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # Result is textual
                response = result
                with st.chat_message("assistant"):
                    st.markdown(response)   
        else:
            response = "Select the data file to generate the responses"
            
                          
        
        st.session_state.messages.append({"role": "assistant", "content": response})



def chat_with_data(df, user_prompt, system_message="As an AI with expertise in language and data analysis, your task is to analyze the data of the dataframe.", temperature=0, model_version="GPT-4"):
    llm = OpenAI(api_token=openai_api_key, temperature=temperature, model_version=model_version)
    smart_df = SmartDataframe(df, config={"llm": llm})    
    result = smart_df.chat(user_prompt)  # Pass the messages list
    print(smart_df.last_code_generated)
    if isinstance(result, dict) and result.get("type") == "plot":
        print("************************ PLOT ***********************")
        # Assuming 'value' contains the path to the plot image
        plot_path = result.get("value")
        if plot_path:
            # Display the plot image using Streamlit's st.image
            st.image(plot_path)
            response = f"Displayed plot: {plot_path}"
        else:
            response = "Plot path not found."
        # Optionally, append a message about displaying the plot
        st.session_state.messages.append({"role": "assistant", "content": response})
    return result
import streamlit as st
from loginauth import authenticate_user, show_login_form
from dashboard import show_dashboard

st.set_page_config (layout='wide', initial_sidebar_state='expanded')

st.markdown("""
<style>
div[data-testid="stForm"] {
    width: 30% !important;
    margin: auto; 
}
[data-testid="StyledLinkIconContainer"] {
    font-size: 16px; /* Example: Change the font size */
    color: #333; /* Example: Change the font color */
    text-align: center;
    /* Add more styles as needed */
}
[data-testid="stSidebarUserContent"] {
    padding: 0rem 1.5rem;
}
button[data-testid="stMarkdownContainer"] > div {
    border: 2px solid #4CAF50 !important; /* Green border */
    background-color: #4CAF50 !important; /* Green background */
    color: white !important; /* White text */
    padding: 10px 24px !important; /* Some padding */
    border-radius: 8px !important; /* Rounded corners */
    font-size: 12px !important; /* Larger font size */
}
.st-emotion-cache-qcqlej ea3mdgi1{
  background-image: url('contbg.jpg'); /* Replace 'image-url.jpg' with the actual path to your image */
  background-size: cover; /* This will make sure your image covers the whole div */
  background-position: center; /* This centers the background image */
  width: 100%; /* Adjust the width as needed */
  height: 500px; /* Adjust the height as needed */
}
button[data-testid="stMarkdownContainer"]:hover > div {
    background-color: #45a049 !important; /* Darker green background on hover */
}
body {
    display: flex;
    justify-content: center; /* Center horizontally */
    align-items: center; /* Center vertically */
    height: 100vh; /* Full viewport height */
    margin: 0; /* Remove default margin */
}   
</style>
""", unsafe_allow_html=True)

def main():
    # Check if the user is already logged in
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        # Display the login form and wait for user input
        username, password = show_login_form()
        if username is not None and password is not None:
            # Attempt to authenticate the user
            if authenticate_user(username, password):
                # Update session state to indicate successful login
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                # Optionally clear any previous success or error messages
                st.rerun()
            else:
                # Show an error message on failed login attempt
                st.error("Incorrect Username/Password")
    
    # User is logged in, show the dashboard
    if 'logged_in' in st.session_state and st.session_state['logged_in']:
        show_dashboard(st.session_state['username'])



if __name__ == "__main__":
    #ollamatest()
    main()
    #show_dashboard('Vish')

import streamlit as st

def app():
    if 'username' not in st.session_state:
        st.session_state['username'] = ''

    if st.session_state['username'] == '':
        st.title("Welcome to the Financial Planning Hub")
        st.write("Please log in to continue.")
        
        with st.form(key='login_form'):
            username = st.text_input("Username")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if username != '':
                    st.session_state['username'] = username
                    st.success(f"Welcome, {st.session_state['username']}!")
                else:
                    st.error("Please enter a valid username.")
    else:
        st.title(f"Welcome to the Financial Planning Hub, {st.session_state['username']}")
        
        st.write("""
            This hub allows you to manage your financial expenses and track your spending habits.
            
            You can:
            - Add Expenses
            - View Expenses
            - Track your total expenses
            - Get insights into your financial health
        """)
        
        st.markdown("### Navigate through the options on the sidebar to get started.")
        st.button("Log Out", on_click=log_out)

def log_out():
    st.session_state['username'] = ''
    st.success("You have been logged out successfully.")

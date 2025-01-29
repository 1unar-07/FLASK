import streamlit as st

def app():
    st.subheader('About Intelligent Financial Hub')
    st.write("""
        The **Intelligent Financial Hub** is an advanced platform designed to help individuals efficiently manage their personal finances. 
        It offers a seamless experience for tracking, categorizing, and budgeting expenses while providing detailed insights into spending behavior. 

        ### Key Features:
        - **Expense Tracking**: Easily log and categorize daily expenses.
        - **Budget Management**: Set budgets for different categories (e.g., food, utilities, entertainment) and manage them.
        - **Financial Insights**: View personalized insights into spending habits through reports and charts.
        - **Account Management**: Secure user login and authentication via Firebase, ensuring personal data is protected.
        - **Real-time Updates**: Get notified of your spending limits and track progress against budgets in real-time.

        The **Intelligent Financial Hub** simplifies personal finance management by offering all the tools necessary to take control of your financial health. Whether you want to keep track of monthly expenses or analyze trends over time, this platform is your go-to solution for all things financial.
    """)


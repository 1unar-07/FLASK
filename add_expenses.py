import os
import sqlite3
import pandas as pd
import google.generativeai as genai
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini API Configuration
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Predefined categories
CATEGORIES = [
    'Food', 'Transport', 'Entertainment', 
    'Utilities', 'Others', 'Stocks/Mutual Fund'
]

# Connect to SQLite database
conn = sqlite3.connect('expenses.db', check_same_thread=False)
c = conn.cursor()

# Create expenses table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        amount REAL,
        description TEXT,
        date TEXT
    )
''')
conn.commit()

# Function to classify transaction using Gemini API
def classify_transaction(description):
    prompt = f"""
    Categorize the following transaction description into one of these categories: {', '.join(CATEGORIES)}.

    Transaction: "{description}"

    Respond with only the category name.
    """
    try:
        response = genai.chat(prompt)
        category = response.text.strip()
        if category not in CATEGORIES:
            return "Others"
        return category
    except Exception as e:
        st.error(f"Error categorizing transaction: {str(e)}")
        return "Others"

# Function to plot expense summary
def plot_expense_summary():
    c.execute('SELECT category, SUM(amount) FROM expenses GROUP BY category')
    data = c.fetchall()
    
    if not data:
        st.warning("No expenses recorded yet.")
        return
    
    categories, amounts = zip(*data)
    plt.figure(figsize=(6, 6))
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff','#99ff99','#ffcc99', '#c2c2f0', '#ffb3e6'])
    plt.title("Spending Summary")
    st.pyplot(plt)

# Streamlit App
def app():
    st.title("AI-Powered Expense Categorization")

    option = st.selectbox("Select how to add expenses:", ["Enter Data Manually", "Upload CSV"])

    if option == "Enter Data Manually":
        with st.form(key="manual_entry"):
            amount = st.number_input("Amount", min_value=1, step=1)
            description = st.text_input("Description")
            date = st.date_input("Date", value=datetime.today())

            submit_button = st.form_submit_button("Add Expense")

            if submit_button:
                category = classify_transaction(description)

                c.execute('INSERT INTO expenses (category, amount, description, date) VALUES (?, ?, ?, ?)',
                          (category, amount, description, date.strftime('%Y-%m-%d')))
                conn.commit()

                st.success(f"Expense added! {category} - ₹{amount} on {date.strftime('%Y-%m-%d')}")
                plot_expense_summary()

    elif option == "Upload CSV":
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip()

            required_columns = ['amount', 'description', 'date']
            if all(col.lower() in [column.lower() for column in df.columns] for col in required_columns):
                df['category'] = df['description'].apply(classify_transaction)

                for _, row in df.iterrows():
                    c.execute('INSERT INTO expenses (category, amount, description, date) VALUES (?, ?, ?, ?)',
                              (row['category'], row['amount'], row['description'], row['date']))
                conn.commit()

                st.success(f"CSV uploaded and categorized successfully with {len(df)} entries!")
                plot_expense_summary()
            else:
                st.error("CSV must contain 'amount', 'description', and 'date' columns.")

    st.subheader("Expense Summary")
    plot_expense_summary()

if __name__ == "__main__":
    app()

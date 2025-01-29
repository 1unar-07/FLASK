import os
import sqlite3
import pandas as pd
import google.generativeai as genai
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_GENAI_API_KEY")

# Configure Google Generative AI
genai.configure(api_key=api_key)

# Initialize Gemini Model
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# Predefined categories and limits
CATEGORIES = {
    'Food & Groceries': 50000,
    'Transport': 15000,
    'Entertainment': 10000,
    'Utilities': 12000,
    'Others': 5000,
    'Stocks/Mutual Fund': 30000
}

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
    You are an AI assistant trained to categorize financial transactions. 
    Categorize the following transaction description into one of these categories: {', '.join(CATEGORIES.keys())}.

    Transaction Description: "{description}"

    Respond with only the category name from the provided list.
    """
    try:
        response = model.generate_content(prompt)
        category = response.text.strip()
        
        if category not in CATEGORIES:
            return "Others"  # Default category if Gemini fails to match

        return category
    except Exception as e:
        st.error(f"Error categorizing transaction: {str(e)}")
        return "Others"

# Function to calculate total spent in a category
def get_total_spent(category):
    c.execute('SELECT SUM(amount) FROM expenses WHERE category=?', (category,))
    total = c.fetchone()[0] or 0  # If no records, default to 0
    return total

# Streamlit App
def app():
    st.title("AI-Powered Expense Categorization")

    # Option to add expense manually or upload CSV
    option = st.selectbox("Select how to add expenses:", ["Enter Data Manually", "Upload CSV"])

    if option == "Enter Data Manually":
        with st.form(key="manual_entry"):
            amount = st.number_input("Amount", min_value=1, step=1)
            description = st.text_input("Description")
            date = st.date_input("Date", value=datetime.today())

            submit_button = st.form_submit_button("Add Expense")

            if submit_button:
                category = classify_transaction(description)

                # Insert data into the database
                c.execute('INSERT INTO expenses (category, amount, description, date) VALUES (?, ?, ?, ?)',
                          (category, amount, description, date.strftime('%Y-%m-%d')))
                conn.commit()

                # Calculate total spent in the category after adding the expense
                total_spent = get_total_spent(category)

                # Show alert if total spent exceeds the limit for the category
                if total_spent > CATEGORIES[category]:
                    st.warning(f"ALERT: You have exceeded the limit for {category}! Total spent: ₹{total_spent}")

                st.success(f"Expense added! {category} - ₹{amount} on {date.strftime('%Y-%m-%d')}")

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

                    # Calculate total spent in the category after adding the expense
                    total_spent = get_total_spent(row['category'])

                    # Show alert if total spent exceeds the limit for the category
                    if total_spent > CATEGORIES[row['category']]:
                        st.warning(f"ALERT: You have exceeded the limit for {row['category']}! Total spent: ₹{total_spent}")

                st.success(f"CSV uploaded and categorized successfully with {len(df)} entries!")
            else:
                st.error("CSV must contain 'amount', 'description', and 'date' columns.")

if __name__ == "__main__":
    app()

import streamlit as st
import sqlite3
import pandas as pd

# Create or connect to an SQLite database
conn = sqlite3.connect('expenses.db', check_same_thread=False)
c = conn.cursor()

def app():
    if 'username' not in st.session_state or st.session_state['username'] == '':
        st.warning('Please login first to view your expenses.')
        return 

    st.title('View Expenses - ' + st.session_state['username'])

    try:
        c.execute('SELECT id, category, amount, description, date FROM expenses')
        expenses = c.fetchall()

        if len(expenses) > 0:
            df = pd.DataFrame(expenses, columns=['ID', 'Category', 'Amount', 'Description', 'Date'])

            # Display the expense data in the table
            table_placeholder = st.empty()
            table_placeholder.dataframe(df)

            # Use multiselect to allow multiple expense selections
            expenses_to_delete = st.multiselect('Select expenses to delete:', df['ID'].tolist())

            if st.button('Delete Selected Expenses'):
                if expenses_to_delete:
                    # Delete all selected expenses
                    c.executemany('DELETE FROM expenses WHERE id = ?', [(expense_id,) for expense_id in expenses_to_delete])
                    conn.commit()
                    st.success(f'{len(expenses_to_delete)} expenses have been deleted.')

                    # Clear the previous table and show the updated table
                    table_placeholder.empty()  # Clear the previous table

                    # Fetch the updated expenses list after deletion
                    c.execute('SELECT id, category, amount, description, date FROM expenses')
                    expenses = c.fetchall()
                    df = pd.DataFrame(expenses, columns=['ID', 'Category', 'Amount', 'Description', 'Date'])

                    # Display the updated dataframe in place of the old one
                    table_placeholder.dataframe(df)
                else:
                    st.warning('Please select at least one expense to delete.')
        else:
            st.warning('No expenses found.')

    except Exception as e:
        st.error(f"An error occurred: {e}")

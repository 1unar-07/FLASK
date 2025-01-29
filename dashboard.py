import streamlit as st
import sqlite3
import pandas as pd
import os
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("GOOGLE_GENAI_API_KEY")

# Configure Google Generative AI
genai.configure(api_key=api_key)

# Create or connect to an SQLite database
conn = sqlite3.connect('expenses.db', check_same_thread=False)
c = conn.cursor()

# Retrieve expenses data from the database
def get_expenses_data():
    query = "SELECT * FROM expenses"
    df = pd.read_sql(query, conn)
    return df

# Function to remove unwanted symbols
def clean_report(report_text):
    cleaned_text = re.sub(r'[^\w\s.,!?]', '', report_text)
    return cleaned_text

def generate_report(salary, expenses_summary):
    prompt = f"""
    I have the following expenses summary:
    {expenses_summary}

    My monthly salary is: {salary}

    Please create a financial report summarizing my expenses and how much I can save from my salary. Include insights on spending patterns, possible savings, and suggestions on managing finances better.
    """
    
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    response = model.generate_content(prompt)
    
    cleaned_report = clean_report(response.text)
    
    return cleaned_report

def create_plotly_plots(df):
    # Convert 'date' column to datetime if not already in datetime format
    df['date'] = pd.to_datetime(df['date']).dt.date  # Extract date only (no time)

    # Scatter Plot with color coding
    scatter_fig = px.scatter(df, x='date', y='amount', color='category', title="Scatter Plot of Spending Over Time", 
                             labels={'date': 'Date', 'amount': 'Amount'})

    # Modify x-axis to display dates correctly (as categorical)
    scatter_fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=df['date'].unique(),
            ticktext=[str(date) for date in df['date'].unique()],
        )
    )

    # Pie Chart (Proportions by Category)
    category_sum = df.groupby('category')['amount'].sum().reset_index()
    pie_fig = px.pie(category_sum, names='category', values='amount', title='Proportion of Spending by Category')

    # Bar Plot (Total Spending by Category) with different colors for each category
    bar_fig = px.bar(category_sum, x='category', y='amount', title='Total Spending by Category', 
                     labels={'category': 'Category', 'amount': 'Total Amount'},
                     color='category',  # Assign colors based on the 'category' column
                     color_discrete_sequence=px.colors.qualitative.Set1)  # Use a predefined color set

    return scatter_fig, pie_fig, bar_fig



def create_matplotlib_plots(df):
    # Ensure that the 'date' column is in datetime format
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort the dataframe by date to ensure the trend line is plotted in chronological order
    df = df.sort_values(by='date')

    # Scale the marker size based on the 'amount'
    size_scale = 100  # Adjust this value to scale the circle size appropriately
    sizes = df['amount'] * size_scale / df['amount'].max()

    # Scatter Plot (Amount vs Date)
    fig, ax = plt.subplots(figsize=(8.5, 3))
    
    # Color mapping for categories
    category_colors = df['category'].astype('category').cat.codes
    unique_categories = df['category'].unique()
    cmap = plt.get_cmap('tab10')  # Use a colormap for categories

    # Scatter plot with color-coding
    scatter = ax.scatter(df['date'], df['amount'], c=category_colors, cmap=cmap, s=sizes, label='Spending')

    # Adding Line Plot (Trend of spending over time)
    ax.plot(df['date'], df['amount'], color='black', linewidth=2, label='Trend Line')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Amount')
    ax.set_title('Scatter Plot of Spending Over Time with Trend Line')

    # Creating a custom legend based on categories
    handles, labels = [], []
    for i, category in enumerate(unique_categories):
        handle = plt.Line2D([0], [0], marker='o', color='w', label=category, 
                            markerfacecolor=cmap(i / len(unique_categories)), markersize=8)
        handles.append(handle)
        labels.append(category)

    ax.legend(handles=handles, labels=labels, title='Categories')

    # Add color bar (optional, to show the category mapping)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Category')

    scatter_image = BytesIO()
    FigureCanvas(fig).print_png(scatter_image)
    scatter_image.seek(0)
    
    # Pie Chart (Proportions by Category)
    category_sum = df.groupby('category')['amount'].sum().reset_index()
    fig, ax = plt.subplots(figsize=(8.5, 3))
    ax.pie(category_sum['amount'], labels=category_sum['category'], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    ax.set_title('Proportion of Spending by Category')

    pie_image = BytesIO()
    FigureCanvas(fig).print_png(pie_image)
    pie_image.seek(0)

    # Bar Plot (Total Spending by Category)
    fig, ax = plt.subplots(figsize=(8.5, 3))
    ax.bar(category_sum['category'], category_sum['amount'], color='skyblue')
    ax.set_xlabel('Category')
    ax.set_ylabel('Total Amount')
    ax.set_title('Total Spending by Category')

    bar_image = BytesIO()
    FigureCanvas(fig).print_png(bar_image)
    bar_image.seek(0)

    return scatter_image, pie_image, bar_image


# Function to save the financial report with charts as a PDF using Matplotlib
def save_pdf(report, scatter_image, pie_image, bar_image, expenses_summary, expenses_df):
    pdf_output = BytesIO()

    with PdfPages(pdf_output) as pdf:
        # First page: Insert the charts vertically
        fig, axs = plt.subplots(3, 1, figsize=(8.5, 11))  # Adjusted size for vertical plots

        # Scatter plot image
        axs[0].imshow(plt.imread(scatter_image), aspect='auto')
        axs[0].axis('off')
        
        # Pie chart image
        axs[1].imshow(plt.imread(pie_image), aspect='auto')
        axs[1].axis('off')
        
        # Bar chart image
        axs[2].imshow(plt.imread(bar_image), aspect='auto')
        axs[2].axis('off')

        pdf.savefig(fig)
        plt.close(fig)

        # Second page: Insert Table 2 (Detailed Expenses)
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.text(0.5, 0.95, 'Detailed Expenses Table', ha='center', va='top', fontsize=16)
        ax.axis('off')
        ax.table(cellText=expenses_df.values, colLabels=expenses_df.columns, loc='center', cellLoc='center')

        pdf.savefig(fig)
        plt.close(fig)

        # Third page: Insert Table 1 (Summary of Spending by Category)
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.text(0.5, 0.95, 'Spending Summary Table', ha='center', va='top', fontsize=16)
        ax.axis('off')
        ax.table(cellText=expenses_summary.values, colLabels=expenses_summary.columns, loc='center', cellLoc='center')

        pdf.savefig(fig)
        plt.close(fig)

    pdf_output.seek(0)
    return pdf_output

def app():
    st.subheader('Dashboard')

    # Check if the user is logged in
    if st.session_state.get('signedout') and st.session_state.get('username'):
        st.success(f"Welcome, {st.session_state['username']}!")

        # Fetch expenses data from the database
        df = get_expenses_data()

        if df.empty:
            st.warning('No expense data available.')
            return

        # Generate the Plotly charts for the web app
        scatter_fig, pie_fig, bar_fig = create_plotly_plots(df)

        # Display the scatter plot
        st.write('### Scatter Plot (Amount vs Date)')
        st.plotly_chart(scatter_fig)

        # Display the pie chart
        st.write('### Spending Proportions by Category')
        st.plotly_chart(pie_fig)

        # Display the bar chart
        st.write('### Total Spending by Category')
        st.plotly_chart(bar_fig)

        expenses_summary = df.groupby('category').agg(
            total_amount=('amount', 'sum'),
            expense_count=('amount', 'count')
        ).reset_index()

        salary = st.number_input("Enter your monthly salary:", min_value=0, step=1000)

        if st.button("Generate Financial Report"):
            if salary > 0:
                report = generate_report(salary, expenses_summary)
                st.text_area("Generated Report", value=report, height=300)
                scatter_image, pie_image, bar_image = create_matplotlib_plots(df)
                pdf_output = save_pdf(report, scatter_image, pie_image, bar_image, expenses_summary, df)
                st.download_button(
                    label="Download Report as PDF",
                    data=pdf_output,
                    file_name="financial_report.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Please enter a valid salary.")
    else:
        # User is not logged in, show a warning
        st.warning("Please login to access the financial dashboard.")

# Run the Streamlit app
if __name__ == "__main__":
    app()

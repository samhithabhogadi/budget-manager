import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import os
from io import StringIO

# Set page configuration
st.set_page_config(page_title="Finora: Wealth Management", layout="wide", page_icon="💼")

# Custom CSS for professional styling
st.markdown(
    """
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f5f7fa;
            color: #1e2a44;
        }
        .stApp {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        .block-container {
            max-width: 1200px;
            margin: auto;
        }
        .sidebar .sidebar-content {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            border-radius: 10px;
        }
        .stButton>button {
            background-color: #3b82f6;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #2563eb;
        }
        .section {
            border-left: 5px solid #22c55e;
            padding: 1rem;
            margin-bottom: 1.5rem;
            background: #f0fdf4;
            border-radius: 8px;
        }
        .scrollbox {
            overflow-x: auto;
            white-space: nowrap;
            padding: 1rem;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }
        .metric-card {
            background: #ffffff;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Database setup
def init_db():
    conn = sqlite3.connect('finora.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT, password TEXT, user_id INTEGER PRIMARY KEY AUTOINCREMENT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (user_id INTEGER, date TEXT, type TEXT, category TEXT, amount REAL, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals 
                 (user_id INTEGER, goal TEXT, target_amount REAL, saved_amount REAL, deadline TEXT)''')
    conn.commit()
    conn.close()

init_db()

# User authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_user(username, password):
    conn = sqlite3.connect('finora.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE username = ? AND password = ?", 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def register_user(username, password):
    conn = sqlite3.connect('finora.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = None

# Login/Register page
if not st.session_state['logged_in']:
    st.title("🔒 Finora: Login or Register")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                user = check_user(username, password)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user[0]
                    st.session_state['username'] = username
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                if register_user(new_username, new_password):
                    st.success("Registered successfully! Please login.")
                else:
                    st.error("Username already exists.")
    st.stop()

# Load data from database
def load_transactions(user_id):
    conn = sqlite3.connect('finora.db')
    df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id = ?", conn, params=(user_id,))
    conn.close()
    return df

def load_goals(user_id):
    conn = sqlite3.connect('finora.db')
    df = pd.read_sql_query("SELECT * FROM goals WHERE user_id = ?", conn, params=(user_id,))
    conn.close()
    return df

# Save data to database
def save_transaction(user_id, date, t_type, category, amount, notes):
    conn = sqlite3.connect('finora.db')
    c = conn.cursor()
    c.execute("INSERT INTO transactions (user_id, date, type, category, amount, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, date, t_type, category, amount, notes))
    conn.commit()
    conn.close()

def save_goal(user_id, goal, target, saved, deadline):
    conn = sqlite3.connect('finora.db')
    c = conn.cursor()
    c.execute("INSERT INTO goals (user_id, goal, target_amount, saved_amount, deadline) VALUES (?, ?, ?, ?, ?)",
              (user_id, goal, target, saved, deadline))
    conn.commit()
    conn.close()

def update_transaction(user_id, index, date, t_type, category, amount, notes):
    conn = sqlite3.connect('finora.db')
    c = conn.cursor()
    c.execute("UPDATE transactions SET date = ?, type = ?, category = ?, amount = ?, notes = ? WHERE user_id = ? AND rowid = ?",
              (date, t_type, category, amount, notes, user_id, index + 1))
    conn.commit()
    conn.close()

def delete_transaction(user_id, index):
    conn = sqlite3.connect('finora.db')
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE user_id = ? AND rowid = ?", (user_id, index + 1))
    conn.commit()
    conn.close()

# Sidebar navigation
st.sidebar.title(f"👋 Welcome, {st.session_state['username']}")
st.sidebar.markdown("### Wealth Management Dashboard")
page = st.sidebar.radio("Navigate", ["Dashboard", "Transactions", "Goals", "Reports", "Investments", "Export Data"])

# Financial Education
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Financial Education")
st.sidebar.markdown("""
**Equity Investments**:
- Stocks: Ownership in companies
- ETFs: Diversified market exposure
- High risk, high reward

**Debt Investments**:
- Bonds: Government or corporate
- Fixed Deposits: Bank-backed
- Low risk, stable returns

**Hybrid Options**:
- Mutual Funds: Professionally managed
- SIPs: Systematic investments
- Balanced risk-reward
""")

# Dashboard Page
if page == "Dashboard":
    st.title("📊 Financial Dashboard")
    df = load_transactions(st.session_state['user_id'])
    goals = load_goals(st.session_state['user_id'])
    
    income = df[df['type'] == 'Income']['amount'].sum()
    expense = df[df['type'] == 'Expense']['amount'].sum()
    savings = income - expense
    
    st.markdown("### 💼 Financial Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Income", f"₹{income:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Expenses", f"₹{expense:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Net Savings", f"₹{savings:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    if not goals.empty:
        st.markdown("### 🎯 Goal Progress")
        for _, row in goals.iterrows():
            progress = (row['saved_amount'] / row['target_amount']) * 100
            st.progress(min(progress / 100, 1.0))
            st.write(f"{row['goal']}: ₹{row['saved_amount']:,.2f} / ₹{row['target_amount']:,.2f} ({progress:.1f}%)")
    
    if not df.empty:
        st.markdown("### 🧾 Recent Transactions")
        st.markdown('<div class="scrollbox">', unsafe_allow_html=True)
        st.dataframe(df.sort_values(by='date', ascending=False).head(10))
        st.markdown('</div>', unsafe_allow_html=True)

# Transactions Page
elif page == "Transactions":
    st.title("💸 Manage Transactions")
    with st.form("transaction_form"):
        date = st.date_input("Date", datetime.today())
        t_type = st.selectbox("Type", ["Income", "Expense"])
        category = st.selectbox("Category", ["Salary", "Food", "Transport", "Rent", "Utilities", "Entertainment", "Investment", "Miscellaneous"])
        amount = st.number_input("Amount (₹)", min_value=0.0, format="%0.2f")
        notes = st.text_input("Notes")
        submitted = st.form_submit_button("Add Transaction")
        
        if submitted:
            if amount <= 0:
                st.error("Amount must be positive.")
            else:
                save_transaction(st.session_state['user_id'], date, t_type, category, amount, notes)
                st.success("Transaction added!")
    
    st.subheader("Transaction History")
    df = load_transactions(st.session_state['user_id'])
    if not df.empty:
        st.dataframe(df)
        
        st.subheader("Edit/Delete Transaction")
        with st.form("edit_transaction_form"):
            index = st.number_input("Transaction Index to Edit/Delete", min_value=0, max_value=len(df)-1, step=1)
            date = st.date_input("Edit Date", value=pd.to_datetime(df.iloc[index]['date']))
            t_type = st.selectbox("Edit Type", ["Income", "Expense"], index=0 if df.iloc[index]['type'] == 'Income' else 1)
            category = st.selectbox("Edit Category", ["Salary", "Food", "Transport", "Rent", "Utilities", "Entertainment", "Investment", "Miscellaneous"], 
                                  index=["Salary", "Food", "Transport", "Rent", "Utilities", "Entertainment", "Investment", "Miscellaneous"].index(df.iloc[index]['category']))
            amount = st.number_input("Edit Amount (₹)", min_value=0.0, value=float(df.iloc[index]['amount']), format="%0.2f")
            notes = st.text_input("Edit Notes", value=df.iloc[index]['notes'])
            col1, col2 = st.form_submit_button("Update"), st.form_submit_button("Delete")
            
            if col1:
                if amount <= 0:
                    st.error("Amount must be positive.")
                else:
                    update_transaction(st.session_state['user_id'], index, date, t_type, category, amount, notes)
                    st.success("Transaction updated!")
            if col2:
                delete_transaction(st.session_state['user_id'], index)
                st.success("Transaction deleted!")

# Goals Page
elif page == "Goals":
    st.title("🎯 Manage Financial Goals")
    with st.form("goal_form"):
        goal_name = st.text_input("Goal Name")
        target = st.number_input("Target Amount (₹)", min_value=100.0, format="%0.2f")
        saved = st.number_input("Current Saved Amount (₹)", min_value=0.0, format="%0.2f")
        deadline = st.date_input("Deadline")
        submitted = st.form_submit_button("Add Goal")
        
        if submitted:
            if not goal_name:
                st.error("Goal name is required.")
            elif target <= saved:
                st.error("Target amount must be greater than saved amount.")
            else:
                save_goal(st.session_state['user_id'], goal_name, target, saved, deadline)
                st.success("Goal added!")
    
    st.subheader("Your Goals")
    goals = load_goals(st.session_state['user_id'])
    if not goals.empty:
        st.dataframe(goals)

# Reports Page
elif page == "Reports":
    st.title("📊 Financial Reports")
    df = load_transactions(st.session_state['user_id'])
    if df.empty:
        st.warning("No transactions available.")
    else:
        st.subheader("Expenses by Category")
        exp_df = df[df['type'] == 'Expense']
        if not exp_df.empty:
            category_summary = exp_df.groupby('category')['amount'].sum().reset_index()
            fig = px.bar(category_summary, x='category', y='amount', title="Expenses by Category")
            st.plotly_chart(fig)
        
        st.subheader("Monthly Trends")
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)
        monthly = df.groupby(['month', 'type'])['amount'].sum().unstack().fillna(0)
        fig = px.line(monthly, title="Income vs Expenses Over Time")
        st.plotly_chart(fig)

# Investments Page
elif page == "Investments":
    st.title("💡 Investment Portfolio")
    st.markdown("""
    ### Suggested Investments
    - **SIPs in Equity Mutual Funds**: Long-term wealth creation.
    - **Fixed Deposits**: Secure, guaranteed returns.
    - **Digital Gold**: Hedge against inflation.
    - **PPF**: Tax-saving, risk-free option.
    """)
    
    st.subheader("Track Stocks")
    stock_symbols = st.text_input("Enter Stock Symbols (comma-separated, e.g., AAPL,TSLA)", "AAPL").split(',')
    stock_symbols = [s.strip().upper() for s in stock_symbols]
    
    for symbol in stock_symbols:
        try:
            stock = yf.Ticker(symbol)
            stock_data = stock.history(period="1mo")
            if not stock_data.empty:
                st.write(f"**{symbol} Performance**")
                st.dataframe(stock_data[['Open', 'High', 'Low', 'Close', 'Volume']])
                fig = px.line(stock_data, y='Close', title=f"{symbol} Closing Price")
                st.plotly_chart(fig)
            else:
                st.warning(f"No data available for {symbol}.")
        except:
            st.error(f"Invalid symbol: {symbol}")

# Export Data Page
elif page == "Export Data":
    st.title("📥 Export Data")
    df = load_transactions(st.session_state['user_id'])
    goals = load_goals(st.session_state['user_id'])
    
    if not df.empty:
        st.subheader("Export Transactions")
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Transactions as CSV",
            data=csv,
            file_name="transactions.csv",
            mime="text/csv"
        )
    
    if not goals.empty:
        st.subheader("Export Goals")
        csv = goals.to_csv(index=False)
        st.download_button(
            label="Download Goals as CSV",
            data=csv,
            file_name="goals.csv",
            mime="text/csv"
        )

# Logout button
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = None
    st.rerun()

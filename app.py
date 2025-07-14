import streamlit as st
import pandas as pd
import os
import mysql.connector
from datetime import datetime
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------------------------
# MySQL Database Setup
# ---------------------------
def create_connection():
    return mysql.connector.connect(
        host='sql12.freesqldatabase.com',
        port=3306,
        user='sql12789825',
        password='QFHEeX2hwG',
        database='sql12789825'
    )

conn = create_connection()
c = conn.cursor()

# ---------------------------
# Ensure Tables Exist
# ---------------------------
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100)
)''')
c.execute('''CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50),
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    gender VARCHAR(20),
    company VARCHAR(100),
    joined_date DATE
)''')
c.execute('''CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50),
    product VARCHAR(100),
    amount FLOAT,
    sale_date DATE
)''')
conn.commit()

# ---------------------------
# UI Styling and Config
# ---------------------------
st.set_page_config(page_title="📊 Relatrix - Corporate CRM Dashboard", layout="centered")
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #ffe6f0, #e6ccff);
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center;'>
        <h1 style='font-size: 44px; color:#6C63FF; font-family:monospace;'>📊 Relatrix</h1>
        <p style='font-size: 24px; color: deeppink; font-family: "Comic Sans MS", cursive; font-weight: bold;'>📈 Where Relationships Drive Results.</p>
        <p style='font-size: 22px; font-family: "Comic Sans MS", cursive; font-weight: bold;'>🏢 A Corporate CRM Dashboard</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='position: fixed; bottom: 10px; left: 20px; background-color: #C71585;
                padding: 12px 20px; border-radius: 12px; box-shadow: 0 0 15px #C71585;'>
        <p style='font-size: 20px; color: white; font-family: "Comic Sans MS", cursive; margin: 0;'>Created by Sarmistha Sen</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------
# Session & Auth
# ---------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True
    st.session_state.name = "Sarmistha Sen"

if st.session_state.logged_in:
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f"👤 Logged in as: **{st.session_state.name}**")
    with col2:
        if st.button("🚪 Logout"):
            st.success("👋 Thank you for using Relatrix. Logging out...")
            st.markdown("""
                <script>
                const body = window.parent.document.querySelector('body');
                body.style.transition = 'opacity 0.8s ease-out';
                body.style.opacity = '0.2';
                setTimeout(() => {
                    window.location.reload();
                }, 800);
                </script>
            """, unsafe_allow_html=True)
            st.session_state.logged_in = False
            st.stop()

    def fetch_customers():
        return pd.read_sql("SELECT * FROM customers", conn)

    def fetch_sales():
        return pd.read_sql("SELECT * FROM sales", conn)

    def insert_customer(row):
        sql = """INSERT INTO customers (customer_id, name, email, phone, address, city, state, gender, company, joined_date)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        c.execute(sql, row)
        conn.commit()

    def update_customer(row):
        sql = """UPDATE customers SET customer_id=%s, name=%s, email=%s, phone=%s, address=%s, city=%s, 
                 state=%s, gender=%s, company=%s, joined_date=%s WHERE id=%s"""
        c.execute(sql, row)
        conn.commit()

    def delete_customer(cid):
        c.execute("DELETE FROM customers WHERE id=%s", (cid,))
        conn.commit()

    def insert_sale(row):
        sql = "INSERT INTO sales (customer_id, product, amount, sale_date) VALUES (%s, %s, %s, %s)"
        c.execute(sql, row)
        conn.commit()

    def update_sale(row):
        sql = "UPDATE sales SET customer_id=%s, product=%s, amount=%s, sale_date=%s WHERE id=%s"
        c.execute(sql, row)
        conn.commit()

    def delete_sale(sid):
        c.execute("DELETE FROM sales WHERE id=%s", (sid,))
        conn.commit()

    menu = st.sidebar.selectbox("Choose Action", [
        "Show Customers", "Customer Profiles", "Add Customer", "Edit Customer", "Delete Customer",
        "Sales Report", "Add Sale", "Edit Sale", "Delete Sale"
    ])

    if menu == "Show Customers":
        st.header("📋 All Customers")
        data = fetch_customers()
        st.dataframe(data)

    elif menu == "Customer Profiles":
        st.header("🧍 Customer Profile Dashboard")
        data = fetch_customers()
        if data.empty:
            st.warning("No customers available.")
        else:
            selected = st.selectbox("Select Customer", data['name'])
            cust = data[data['name'] == selected].iloc[0]

            st.subheader("📞 Contact Information")
            st.markdown(f"""
            - **Customer ID:** {cust['customer_id']}
            - **Email:** {cust['email']}
            - **Phone:** {cust['phone']}
            - **Address:** {cust['address']}, {cust['city']}, {cust['state']}
            - **Company:** {cust['company']}
            """)

            sales_df = pd.read_sql_query("SELECT * FROM sales WHERE customer_id = ?", conn, params=(cust['customer_id'],))
            if sales_df.empty:
                st.info("No sales found for this customer.")
            else:
                total = sales_df['amount'].sum()
                last_date = sales_df['sale_date'].max()
                st.markdown(f"💰 **Total Purchases:** ₹{total:.2f}")
                st.markdown(f"🕒 **Last Purchase Date:** {last_date}")

                chart = px.bar(sales_df, x="sale_date", y="amount", title="📈 Purchase History", labels={"amount": "Amount (₹)"})
                st.plotly_chart(chart)


    elif menu == "Add Customer":
        st.header("➕ Add Customer")
        with st.form("add_customer"):
            cid = st.text_input("Customer ID")
            name = st.text_input("Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            address = st.text_input("Address")
            city = st.text_input("City")
            state = st.text_input("State")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            company = st.text_input("Company")
            joined = st.date_input("Joined Date")
            submit = st.form_submit_button("Add")
            if submit:
                insert_customer((cid, name, email, phone, address, city, state, gender, company, joined))
                st.success("✅ Customer added")

    elif menu == "Edit Customer":
        df = fetch_customers()
        selected = st.selectbox("Choose Customer ID", df['id'])
        row = df[df['id'] == selected].iloc[0]
        with st.form("edit_customer"):
            cid = st.text_input("Customer ID", value=row['customer_id'])
            name = st.text_input("Name", value=row['name'])
            email = st.text_input("Email", value=row['email'])
            phone = st.text_input("Phone", value=row['phone'])
            address = st.text_input("Address", value=row['address'])
            city = st.text_input("City", value=row['city'])
            state = st.text_input("State", value=row['state'])
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(row['gender']))
            company = st.text_input("Company", value=row['company'])
            joined = st.date_input("Joined Date", value=row['joined_date'])
            submit = st.form_submit_button("Update")
            if submit:
                update_customer((cid, name, email, phone, address, city, state, gender, company, joined, selected))
                st.success("✅ Customer updated")

    elif menu == "Delete Customer":
        df = fetch_customers()
        selected = st.selectbox("Choose Customer to Delete", df['id'])
        if st.button("Delete"):
            delete_customer(selected)
            st.success("🗑️ Deleted successfully")

    elif menu == "Sales Report":
        st.header("📊 Sales Report")
        sales = fetch_sales()
        st.dataframe(sales)
        if not sales.empty:
            product_chart = px.bar(sales.groupby("product")["amount"].sum().reset_index(),
                                   x="product", y="amount", title="💰 Sales by Product",
                                   color="product", text_auto=True)
            st.plotly_chart(product_chart)

            date_chart = px.line(sales.groupby("sale_date")["amount"].sum().reset_index(),
                                 x="sale_date", y="amount", title="📆 Daily Sales Trend")
            st.plotly_chart(date_chart)

            csv = sales.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", data=csv, file_name="sales_report.csv", mime="text/csv")

    elif menu == "Add Sale":
        st.header("🧾 Add Sale")
        customers = fetch_customers()
        with st.form("add_sale"):
            customer_id = st.selectbox("Select Customer", customers['customer_id'])
            product = st.text_input("Product")
            amount = st.number_input("Amount", min_value=0.0)
            sale_date = st.date_input("Sale Date")
            submit = st.form_submit_button("Add")
            if submit:
                insert_sale((customer_id, product, amount, sale_date))
                st.success("✅ Sale recorded")

    elif menu == "Edit Sale":
        df = fetch_sales()
        selected = st.selectbox("Select Sale to Edit", df['id'])
        row = df[df['id'] == selected].iloc[0]
        with st.form("edit_sale"):
            customer_id = st.text_input("Customer ID", value=row['customer_id'])
            product = st.text_input("Product", value=row['product'])
            amount = st.number_input("Amount", value=row['amount'], min_value=0.0)
            sale_date = st.date_input("Sale Date", value=row['sale_date'])
            submit = st.form_submit_button("Update")
            if submit:
                update_sale((customer_id, product, amount, sale_date, selected))
                st.success("✅ Sale updated")

    elif menu == "Delete Sale":
        df = fetch_sales()
        selected = st.selectbox("Select Sale to Delete", df['id'])
        if st.button("Delete"):
            delete_sale(selected)
            st.success("🗑️ Sale deleted")

import streamlit as st
import pandas as pd
import os
import mysql.connector
from datetime import datetime
import time
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------------------------
# Database Setup
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

# ✅ Safely ensure 'users' table has 'password' column
try:
    c.execute("ALTER TABLE users ADD COLUMN password VARCHAR(100)")
    conn.commit()
except mysql.connector.errors.ProgrammingError:
    pass  # Column already exists

# ---------------------------
# Ensure Tables Exist
# ---------------------------
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

def fetch_customers():
    return pd.read_sql_query("SELECT * FROM customers", conn)

# ---------------------------
# User Authentication Setup
# ---------------------------
AUTHENTICATED_EMAILS = ["sarmisthaexample@gmail.com", "admin@relatrix.com"]

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100)
)''')
conn.commit()

c.execute('''CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(50),
    product VARCHAR(100),
    amount FLOAT,
    sale_date DATE
)''')
conn.commit()


def signup_user(name, email, password):
    try:
        c.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        return False

def authenticate_user(email, password):
    c.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    return c.fetchone()

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

# ---------------------------
# UI Setup
# ---------------------------
st.set_page_config(page_title="📊 Relatrix - Corporate CRM Dashboard", layout="centered")
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='font-size: 44px; color:#6C63FF; font-family:monospace;'>📊 Relatrix</h1>
        <p style='font-size: 24px; color: deeppink; font-family: "Comic Sans MS", cursive; font-weight: bold;'>📈 Where Relationships Drive Results.</p>
        <p style='font-size: 22px; font-family: "Comic Sans MS", cursive; font-weight: bold;'>🏢 A Corporate CRM Dashboard</p>
    </div>
""", unsafe_allow_html=True)

if st.session_state.get("logged_in", False) and st.session_state.get("page") == "auth":
    st.session_state.page = "dashboard"
    st.rerun()

# ---------------------------
# Session State
# ---------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.name = ""
    st.session_state.is_admin = False
    st.session_state.page = "auth"

# ---------------------------
# Login / Signup Page
# ---------------------------
if st.session_state.page == "auth":
    st.subheader("🔐 Login or Sign Up")
    auth_action = st.radio("Choose Action", ["Login", "Sign Up"])

    if auth_action == "Sign Up":
        with st.form("signup_form"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            signup_btn = st.form_submit_button("Sign Up")
            if signup_btn:
                if signup_user(new_name, new_email, new_password):
                    st.success("✅ Signed up successfully! Please login.")
                else:
                    st.error("❌ Email already registered.")

    else:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            if login_btn:
                with st.spinner("🔄 Logging you in, please wait..."):
                    user = authenticate_user(email, password)
                    if user:
                        st.success("✅ Login successful! Redirecting...")
                        time.sleep(1)
                        st.session_state.logged_in = True
                        st.session_state.name = user[1]
                        st.session_state.email = user[2]
                        st.session_state.is_admin = user[2] in AUTHENTICATED_EMAILS
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials.")

# ---------------------------
# Dashboard Page (Post-login)
# ---------------------------
if st.session_state.page == "dashboard" and st.session_state.logged_in:
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f"👤 Logged in as: **{st.session_state.name}**")
    with col2:
        if st.button("🚪 Logout"):
            st.success("👋 Thank you for using Relatrix. Logging out...")

            # Reset session state after animation
            st.session_state.logged_in = False
            st.session_state.page = "auth"
            st.session_state.email = ""
            st.session_state.name = ""
            st.session_state.is_admin = False

            st.stop()


    menu_options = ["Show Customers","Sales Report"]
    if st.session_state.is_admin:
        menu_options += ["Add Customer", "Edit Customer", "Delete Customer", "Add Sale", "Edit Sale", "Delete Sale"]

    menu = st.selectbox("📂 Choose Action", menu_options)
    data = fetch_customers()

    if menu == "Show Customers":
        st.header("📋 All Customers")
        data = fetch_customers()
        st.dataframe(data)

        if not data.empty:
            st.subheader("📊 Gender-wise Distribution")
            gender_counts = data['gender'].value_counts().reset_index()
            gender_counts.columns = ['Gender', 'Count']
            fig = px.pie(gender_counts, values='Count', names='Gender', title='Customer Gender Ratio',
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig)

            st.subheader("⬇️ Download Customer Data")
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv, file_name="customers.csv", mime="text/csv")

            def generate_pdf(dataframe):
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, "📄 Relatrix - Customer Report")
                c.setFont("Helvetica", 10)
                y = height - 80
                for _, row in dataframe.iterrows():
                    text = f"{row['customer_id']} | {row['name']} | {row['email']} | {row['gender']} | {row['company']}"
                    c.drawString(50, y, text)
                    y -= 15
                    if y < 50:
                        c.showPage()
                        y = height - 50
                c.save()
                buffer.seek(0)
                return buffer

            pdf_data = generate_pdf(data)
            st.download_button("📄 Download PDF", data=pdf_data, file_name="customers_report.pdf", mime="application/pdf")

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

        if customers.empty:
            st.warning("Please add customers first.")
        else:
            with st.form("sale_form"):
                selected_customer = st.selectbox(
                    "Select Customer",
                    customers["customer_id"],
                    format_func=lambda cid: f"{cid} - {customers.loc[customers['customer_id'] == cid, 'name'].values[0]}"
                )
                product = st.text_input("Product")
                amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
                sale_date = st.date_input("Sale Date", datetime.today())

                submit_sale = st.form_submit_button("Add Sale")
                if submit_sale:
                    insert_sale({
                        "Customer ID": selected_customer,
                        "Product": product,
                        "Amount": amount,
                        "Sale Date": sale_date.strftime("%Y-%m-%d")
                    })
                    st.success(f"✅ Sale of ₹{amount:.2f} added for {selected_customer}")

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

    elif menu == "Sales Report":
        st.header("📊 Sales Report")
        sales = fetch_sales()
        st.dataframe(sales)

        if sales.empty:
            st.warning("No sales data available.")
        else:
            st.dataframe(sales)

            # 🧁 Grouped Sales by Product
            product_chart = px.bar(sales.groupby("product")["amount"].sum().reset_index(),
                                   x="product", y="amount", title="💰 Sales by Product",
                                   color="product", text_auto=True)
            st.plotly_chart(product_chart)

            # 📅 Sales by Date
            date_chart = px.line(sales.groupby("sale_date")["amount"].sum().reset_index(),
                                 x="sale_date", y="amount", title="📆 Daily Sales Trend")
            st.plotly_chart(date_chart)

            # 🔻 Download CSV
            csv = sales.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", data=csv, file_name="sales_report.csv", mime="text/csv")

            # 📄 PDF Export
            def generate_sales_pdf(dataframe):
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, "📄 Relatrix - Sales Report")
                c.setFont("Helvetica", 10)
                y = height - 80
                for _, row in dataframe.iterrows():
                    text = f"{row['customer_id']} | {row['product']} | ₹{row['amount']} | {row['sale_date']}"
                    c.drawString(50, y, text)
                    y -= 15
                    if y < 50:
                        c.showPage()
                        y = height - 50
                c.save()
                buffer.seek(0)
                return buffer

            pdf = generate_sales_pdf(sales)
            st.download_button("📄 Download PDF", data=pdf, file_name="sales_report.pdf", mime="application/pdf")


# ---------------------------
# Footer
# ---------------------------
st.markdown("""
    <div style='position: fixed; bottom: 10px; left: 20px; background-color: #C71585;
                padding: 12px 20px; border-radius: 12px; box-shadow: 0 0 15px #C71585;'>
        <p style='font-size: 20px; color: white; font-family: "Comic Sans MS", cursive; margin: 0;'>Created by Sarmistha Sen</p>
    </div>
""", unsafe_allow_html=True)

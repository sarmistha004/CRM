import streamlit as st
import pandas as pd
import os
import time
import mysql.connector
from datetime import datetime
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import os

# ---------------------------
# Database Setup
# ---------------------------
@st.cache_resource
def get_connection():
    try:
        conn = mysql.connector.connect(
            host='sql12.freesqldatabase.com',
            port=3306,
            user='sql12789825',
            password='QFHEeX2hwG',
            database='sql12789825'
        )
        if conn.is_connected():
            return conn
        else:
            st.error("❌ Unable to connect to the database.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        st.stop()

conn = get_connection()
if not conn or not conn.is_connected():
    st.error("❌ Lost connection to the database.")
    st.stop()

c = conn.cursor(buffered=True)

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

# ✅ Add follow_up_date column if not already present
try:
    c.execute("ALTER TABLE customers ADD COLUMN follow_up_date DATE")
    conn.commit()
except mysql.connector.errors.ProgrammingError:
    pass  # Column already exists

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
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM customers")
    rows = c.fetchall()
    return pd.DataFrame(rows)

def fetch_sales():
    c = conn.cursor(dictionary=True)
    c.execute("SELECT * FROM sales")
    rows = c.fetchall()
    if not rows:
        # Ensures columns exist even if no data
        df = pd.DataFrame(columns=['id', 'customer_id', 'product', 'amount', 'sale_date'])
    else:
        df = pd.DataFrame(rows)
    df.rename(columns=lambda col: col.strip().lower(), inplace=True)
    return df

def insert_customer(row):
        sql = """INSERT INTO customers (customer_id, name, email, phone, address, city, state, gender, company, joined_date, follow_up_date)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        c.execute(sql, row)
        conn.commit()

def update_customer(row):
    sql = """UPDATE customers SET customer_id=%s, name=%s, email=%s, phone=%s, address=%s, city=%s, 
             state=%s, gender=%s, company=%s, joined_date=%s, follow_up_date=%s WHERE id=%s"""
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

def show_customer_profile(customer_id):
    customer_df = fetch_customers()
    sales_df = fetch_sales()
    
    # Debugging outputs
    st.write("🧪 sales_df Preview:", sales_df.head())
    st.write("🔎 Searching for customer_id:", customer_id)
    st.write("🧩 Columns in sales_df:", sales_df.columns.tolist())

    # Strip and lowercase column names safely
    sales_df.columns = sales_df.columns.str.strip().str.lower()

    # Defensive check
    if 'customer_id' not in sales_df.columns:
        st.error("❌ 'customer_id' column missing in sales data.")
        return

    # Get customer info
    customer = customer_df[customer_df['customer_id'] == customer_id]
    if customer.empty:
        st.warning("Customer not found.")
        return

    customer = customer.iloc[0]
    st.subheader(f"🧑‍💼 Profile: {customer['name']}")
    st.markdown(f"**Email:** {customer['email']}")
    st.markdown(f"**Phone:** {customer['phone']}")
    st.markdown(f"**Address:** {customer['address']}, {customer['city']}, {customer['state']}")
    st.markdown(f"**Gender:** {customer['gender']}")
    st.markdown(f"**Company:** {customer['company']}")
    st.markdown(f"**Joined:** {customer['joined_date']}")

    # Filter sales for the customer
    sales = sales_df[sales_df['customer_id'] == customer_id]
    total_purchases = sales['amount'].sum()
    last_purchase_date = sales['sale_date'].max() if not sales.empty else "N/A"
    st.markdown(f"**Total Purchases:** ₹{total_purchases:.2f}")
    st.markdown(f"**Last Purchase Date:** {last_purchase_date}")

    # Chart
    if not sales.empty:
        fig = px.bar(sales, x='sale_date', y='amount', title='🪙 Purchase History')
        st.plotly_chart(fig)
        
# ---------------------------
# UI Setup
# ---------------------------
st.set_page_config(page_title="📊 Relatrix - Corporate CRM Dashboard", layout="centered")

# ---------------------------
# Page Config & Logo (Only on login page)
# ---------------------------
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    
    # Show welcome message + logo only on login/signup screen
    st.markdown("<h1 style='text-align: center;'>🔐 Welcome to Relatrix </h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("logo.png", width=250)

# 🌈 Background and Hide Header/Footer
st.markdown("""
    <style>
        body { 
            background: linear-gradient(to right, #ffe6f0, #e6ccff); 
        }
        header, footer {
            visibility: hidden;
        }
    </style>
""", unsafe_allow_html=True)
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("email", "")
st.session_state.setdefault("name", "")
st.session_state.setdefault("is_admin", False)
st.session_state.setdefault("page", "auth")


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
    st.markdown("<h1 style='text-align: center; font-size: 44px; color:#6C63FF; font-family:monospace;'>📊 Relatrix</h1>", unsafe_allow_html=True)
    # Center the logo image using HTML
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(
        f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{data}" width="250"/>
        </div>
        """,
        unsafe_allow_html=True
    st.markdown("<p style='text-align: center; font-size: 24px; color: deeppink; font-family: \"Comic Sans MS\", cursive; font-weight: bold;'>📈 Where Relationships Drive Results.</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 22px; font-family: \"Comic Sans MS\", cursive; font-weight: bold;'>🏢 A Corporate CRM Dashboard</p>",unsafe_allow_html=True)
            
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


    menu_options = ["Show Customers","Sales Report","View Customer Profile"]
    if st.session_state.is_admin:
        menu_options += ["Add Customer", "Edit Customer", "Delete Customer", "Add Sale", "Edit Sale", "Delete Sale", "Follow-Up Reminders"]

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
            follow_up_date = st.date_input("Follow-Up Date (Optional)", value=None)
            submit = st.form_submit_button("Add")
            if submit:
                insert_customer((cid, name, email, phone, address, city, state, gender, company, joined, follow_up_date))
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
            follow_up_date = st.date_input("Follow-Up Date", value=row.get('follow_up_date'))
            submit = st.form_submit_button("Update")
            if submit:
                update_customer((cid, name, email, phone, address, city, state, gender, company, joined, follow_up_date, selected))
                st.success("✅ Customer updated")

    elif menu == "Delete Customer":
        df = fetch_customers()
        selected = st.selectbox("Choose Customer to Delete", df['id'])
        if st.button("Delete"):
            delete_customer(selected)
            st.success("🗑️ Deleted successfully")

    elif menu == "View Customer Profile":
        if 'customer_id' in data.columns and not data.empty:
            selected_profile = st.selectbox("🔍 View Customer Profile", data['customer_id'])
            if st.button("View Profile", key="view_profile_btn"):
                show_customer_profile(selected_profile)
        else:
            st.warning("⚠️ No customers found or 'customer_id' column missing.")

    elif menu == "Add Sale":
        customers = fetch_customers()
        if customers.empty:
            st.warning("Please add customers first.")
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                    <div style='padding: 25px; border: 2px solid #6C63FF; border-radius: 12px;
                                background-color: #f9f9ff; box-shadow: 0 0 10px #d3d3ff;'>
                        <h2 style='color:#6C63FF;'>🧾 Add Sale</h2>
                    </div>
                """, unsafe_allow_html=True)

                # --- Sale Form ---
                with st.form("sale_form"):
                    st.markdown("### 🎯 Sale Entry Form")
                    selected_customer = st.selectbox(
                        "👥 Select Customer",
                        customers["customer_id"],
                        format_func=lambda cid: f"{cid} - {customers.loc[customers['customer_id'] == cid, 'name'].values[0]}"
                    )
                    product = st.text_input("📦 Product")
                    amount = st.number_input("💰 Amount (₹)", min_value=0.0, format="%.2f")
                    sale_date = st.date_input("📅 Sale Date", datetime.today())
                    submit_sale = st.form_submit_button("✅ Add Sale")

            # --- Handle Sale Submission outside the form ---
            if submit_sale:
                insert_sale((selected_customer, product, amount, sale_date))
                st.success(f"✅ Sale of ₹{amount:.2f} added for {selected_customer}")
            
                customer = customers[customers["customer_id"] == selected_customer].iloc[0]

                # 📄 Generate PDF
                buffer = BytesIO()
                pdf = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter

                pdf.setFont("Helvetica-Bold", 20)
                pdf.setFillColorRGB(0.2, 0.2, 0.8)
                pdf.drawString(200, height - 50, "Relatrix Invoice")

                pdf.setFont("Helvetica", 12)
                pdf.setFillColorRGB(0, 0, 0)
                invoice_id = f"INV-{int(time.time())}"
                gstin = "29ABCDE1234F2Z5"
                pdf.drawString(50, height - 100, f"Invoice ID: {invoice_id}")
                pdf.drawString(300, height - 100, f"GSTIN: {gstin}")

                pdf.drawString(50, height - 120, "From: Relatrix CRM Pvt. Ltd.")
                pdf.drawString(50, height - 135, "Email: support@relatrix.com")
                pdf.drawString(50, height - 160, f"To: {customer['name']}")
                pdf.drawString(50, height - 175, f"Email: {customer['email']}")
                pdf.drawString(50, height - 190, f"Phone: {customer['phone']}")

                pdf.drawString(50, height - 220, f"Customer ID: {selected_customer}")
                pdf.drawString(50, height - 235, f"Product: {product}")
                pdf.drawString(50, height - 250, f"Amount: ₹{amount:.2f}")
                pdf.drawString(50, height - 265, f"Date: {sale_date}")

                pdf.setFont("Helvetica-Oblique", 10)
                pdf.drawString(50, 40, "Thank you for your business!")
                pdf.save()
                buffer.seek(0)

                # ✅ This is now safe: Outside the form
                st.download_button(
                    "📄 Download Invoice PDF",
                    data=buffer,
                    file_name=f"invoice_{selected_customer}_{sale_date}.pdf",
                    mime="application/pdf"
                )

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
            sales['sale_date'] = pd.to_datetime(sales['sale_date']).dt.date  # 👈 This cleans the date
            daily_sales = sales.groupby("sale_date")["amount"].sum().reset_index()

            date_chart = px.line(
                daily_sales, x="sale_date", y="amount",
                title="📆 Daily Sales Trend", markers=True
            )
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

    elif menu == "Follow-Up Reminders":
        st.header("📅 Upcoming Follow-Up Reminders")
        df = fetch_customers()

        if 'follow_up_date' not in df.columns:
            st.warning("⚠️ 'follow_up_date' column not found.")
        else:
            df['follow_up_date'] = pd.to_datetime(df['follow_up_date'], errors='coerce')
            df = df[df['follow_up_date'].notna()]  # ✅ Ignore empty/missing dates

            upcoming = df[df['follow_up_date'].between(datetime.today(), datetime.today() + pd.Timedelta(days=7))]
            upcoming = upcoming.sort_values("follow_up_date")  # ✅ Sort reminders by date

            if upcoming.empty:
                    st.info("✅ No follow-ups due in the next 7 days.")
            else:
                st.success(f"🔔 {len(upcoming)} follow-up(s) due in next 7 days:")
                st.dataframe(upcoming[["customer_id", "name", "email", "phone", "follow_up_date"]])


# ---------------------------
# Footer
# ---------------------------
st.markdown("""
    <div style='position: fixed; bottom: 10px; left: 20px; background-color: #C71585;
                padding: 12px 20px; border-radius: 12px; box-shadow: 0 0 15px #C71585;'>
        <p style='font-size: 20px; color: white; font-family: "Comic Sans MS", cursive; margin: 0;'>Created by Sarmistha Sen</p>
    </div>
""", unsafe_allow_html=True)

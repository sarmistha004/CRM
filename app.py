import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------------------------
# Database Setup
# ---------------------------
DB_FILE = "customers.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT,
    name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    gender TEXT,
    company TEXT,
    joined_date TEXT
)''')
conn.commit()

def fetch_customers():
    return pd.read_sql_query("SELECT * FROM customers", conn)

# ---------------------------
# User Authentication Setup
# ---------------------------
AUTHENTICATED_EMAILS = ["sarmisthaexample@gmail.com", "admin@relatrix.com"]

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT
)''')
conn.commit()

# 🔥 NEW: Create sales table
c.execute('''CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT,
    product TEXT,
    amount REAL,
    sale_date TEXT
)''')
conn.commit()


def signup_user(name, email, password):
    try:
        c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(email, password):
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    return c.fetchone()

def insert_customer(row):
    c.execute('''INSERT INTO customers
                 (customer_id, name, email, phone, address, city, state, gender, company, joined_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (row['Customer ID'], row['Name'], row['Email'], row['Phone'],
               row['Address'], row['City'], row['State'], row['Gender'],
               row['Company'], row['Joined Date']))
    conn.commit()

def update_customer(index, row):
    c.execute('''UPDATE customers SET customer_id=?, email=?, phone=?, address=?, city=?,
                 state=?, gender=?, company=?, joined_date=? WHERE id=?''',
              (row['Customer ID'], row['Email'], row['Phone'], row['Address'],
               row['City'], row['State'], row['Gender'], row['Company'],
               row['Joined Date'], index))
    conn.commit()

def delete_customer(index):
    c.execute("DELETE FROM customers WHERE id=?", (index,))
    conn.commit()

def insert_sale(row):
    c.execute('''INSERT INTO sales (customer_id, product, amount, sale_date)
                 VALUES (?, ?, ?, ?)''',
              (row['Customer ID'], row['Product'], row['Amount'], row['Sale Date']))
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
                        st.session_state.logged_in = True
                        st.session_state.name = user[1]
                        st.session_state.email = user[2]
                        st.session_state.is_admin = user[2] in AUTHENTICATED_EMAILS
                        st.success("✅ Login successful! Redirecting...")
                        st.session_state.page = "dashboard"
                       
                        st.markdown("""
                            <script>
                                const body = window.parent.document.querySelector('body');
                                body.style.transition = 'opacity 0.6s ease-in';
                                body.style.opacity = '0.2';
                                setTimeout(() => {
                                    window.location.reload();
                                }, 600);
                                </script>
                         """, unsafe_allow_html=True)

                        st.session_state.page = "dashboard"
                        st.rerun()
                        st.stop()
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

            # Inject animation using JavaScript
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
        st.header("➕ Add New Customer")
        with st.form("add_form"):
            cid = st.text_input("Customer ID")
            name = st.text_input("Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            address = st.text_input("Address")
            city = st.text_input("City")
            state = st.text_input("State")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            company = st.text_input("Company")
            joined = st.date_input("Joined Date", datetime.today())
            submitted = st.form_submit_button("Add Customer")
            if submitted:
                insert_customer({
                    'Customer ID': cid, 'Name': name, 'Email': email, 'Phone': phone,
                    'Address': address, 'City': city, 'State': state,
                    'Gender': gender, 'Company': company, 'Joined Date': joined.strftime("%Y-%m-%d")
                })
                st.success(f"Customer {name} added!")

    elif menu == "Edit Customer":
        st.header("✏️ Edit Customer")
        if not data.empty:
            selected_id = st.selectbox("Select customer to edit", data['id'], 
                                       format_func=lambda i: data[data['id'] == i]['name'].values[0])
            row = data[data['id'] == selected_id].iloc[0]
            with st.form("edit_form"):
                cid = st.text_input("Customer ID", value=row['customer_id'])
                st.text_input("Name (not editable)", value=row['name'], disabled=True)
                email = st.text_input("Email", value=row['email'])
                phone = st.text_input("Phone", value=row['phone'])
                address = st.text_input("Address", value=row['address'])
                city = st.text_input("City", value=row['city'])
                state = st.text_input("State", value=row['state'])
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], 
                                      index=["Male", "Female", "Other"].index(row['gender']))
                company = st.text_input("Company", value=row['company'])
                joined = st.date_input("Joined Date", datetime.strptime(row['joined_date'], "%Y-%m-%d"))
                updated = st.form_submit_button("Update Customer")
                if updated:
                    update_customer(selected_id, {
                        'Customer ID': cid, 'Email': email, 'Phone': phone,
                        'Address': address, 'City': city, 'State': state,
                        'Gender': gender, 'Company': company, 'Joined Date': joined.strftime("%Y-%m-%d")
                    })
                    st.success(f"Customer '{row['name']}' updated successfully!")
                    st.rerun()


    elif menu == "Delete Customer":
        st.header("🗑️ Delete Customer")
        if not data.empty:
            del_id = st.selectbox("Select customer to delete", data['id'],
                                  format_func=lambda i: data[data['id'] == i]['name'].values[0])
            if st.button("Delete Customer"):
                delete_customer(del_id)
                st.success(f"Customer {data[data['id'] == del_id]['name'].values[0]} deleted!")
                st.rerun()

    elif menu == "Add Sale":
        st.header("🧾 Add New Sale")

        customers = pd.read_sql_query("SELECT customer_id, name FROM customers", conn)

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
        st.header("✏️ Edit Sale")
        sales_df = pd.read_sql_query("SELECT * FROM sales", conn)
        if sales_df.empty:
            st.warning("No sales data available.")
        else:
            selected_id = st.selectbox("Select Sale", sales_df['id'],
                                       format_func=lambda i: f"{sales_df[sales_df['id'] == i]['customer_id'].values[0]} - {sales_df[sales_df['id'] == i]['product'].values[0]} on {sales_df[sales_df['id'] == i]['sale_date'].values[0]}")
            row = sales_df[sales_df['id'] == selected_id].iloc[0]
            with st.form("edit_sale_form"):
                product = st.text_input("Product", value=row['product'])
                amount = st.number_input("Amount", value=row['amount'], min_value=0.0, format="%.2f")
                sale_date = st.date_input("Sale Date", datetime.strptime(row['sale_date'], "%Y-%m-%d"))
                update_btn = st.form_submit_button("Update Sale")

                if update_btn:
                    c.execute('''UPDATE sales SET product=?, amount=?, sale_date=? WHERE id=?''',
                              (product, amount, sale_date.strftime("%Y-%m-%d"), selected_id))
                    conn.commit()
                    st.success(f"✅ Sale updated successfully!")
                    st.rerun()


    elif menu == "Delete Sale":
        st.header("🗑️ Delete Sale")
        sales_df = pd.read_sql_query("SELECT * FROM sales", conn)
        if sales_df.empty:
            st.warning("No sales data available.")
        else:
            selected_id = st.selectbox("Select Sale to Delete", sales_df['id'],
                                       format_func=lambda i: f"{sales_df[sales_df['id'] == i]['customer_id'].values[0]} - {sales_df[sales_df['id'] == i]['product'].values[0]} on {sales_df[sales_df['id'] == i]['sale_date'].values[0]}")
            if st.button("Delete Sale"):
                c.execute("DELETE FROM sales WHERE id=?", (selected_id,))
                conn.commit()
                st.success("✅ Sale deleted successfully!")
                st.rerun()


    elif menu == "Sales Report":
        st.header("📊 Sales Report")

        sales_df = pd.read_sql_query("SELECT * FROM sales", conn)

        if sales_df.empty:
            st.warning("No sales data available.")
        else:
            st.dataframe(sales_df)

            # 🧁 Grouped Sales by Product
            product_chart = px.bar(sales_df.groupby("product")["amount"].sum().reset_index(),
                                   x="product", y="amount", title="💰 Sales by Product",
                                   color="product", text_auto=True)
            st.plotly_chart(product_chart)

            # 📅 Sales by Date
            date_chart = px.line(sales_df.groupby("sale_date")["amount"].sum().reset_index(),
                                 x="sale_date", y="amount", title="📆 Daily Sales Trend")
            st.plotly_chart(date_chart)

            # 🔻 Download CSV
            csv = sales_df.to_csv(index=False).encode("utf-8")
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

            pdf = generate_sales_pdf(sales_df)
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

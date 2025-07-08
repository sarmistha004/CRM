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

menu = st.selectbox("📂 Choose Action", ["Show Customers", "Add Customer", "Edit Customer", "Delete Customer"])
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
        selected = st.selectbox("Select customer to edit", data.index, format_func=lambda i: data.at[i, 'name'])
        row = data.loc[selected]
        with st.form("edit_form"):
            cid = st.text_input("Customer ID", value=row['customer_id'])
            st.text_input("Name (not editable)", value=row['name'], disabled=True)
            email = st.text_input("Email", value=row['email'])
            phone = st.text_input("Phone", value=row['phone'])
            address = st.text_input("Address", value=row['address'])
            city = st.text_input("City", value=row['city'])
            state = st.text_input("State", value=row['state'])
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(row['gender']))
            company = st.text_input("Company", value=row['company'])
            joined = st.date_input("Joined Date", datetime.strptime(row['joined_date'], "%Y-%m-%d"))
            updated = st.form_submit_button("Update Customer")
            if updated:
                update_customer(row['id'], {
                    'Customer ID': cid, 'Email': email, 'Phone': phone,
                    'Address': address, 'City': city, 'State': state,
                    'Gender': gender, 'Company': company, 'Joined Date': joined.strftime("%Y-%m-%d")
                })
                st.success(f"Customer '{row['name']}' updated successfully!")

elif menu == "Delete Customer":
    st.header("🗑️ Delete Customer")
    if not data.empty:
        del_index = st.selectbox("Select customer to delete", data.index, format_func=lambda i: data.at[i, 'name'])
        if st.button("Delete Customer"):
            delete_customer(data.loc[del_index]['id'])
            st.success(f"Customer {data.loc[del_index]['name']} deleted!")

# ---------------------------
# Footer
# ---------------------------
st.markdown("""
    <div style='position: fixed; bottom: 10px; left: 20px; background-color: #C71585;
                padding: 12px 20px; border-radius: 12px; box-shadow: 0 0 15px #C71585;'>
        <p style='font-size: 20px; color: white; font-family: "Comic Sans MS", cursive; margin: 0;'>Created by Sarmistha Sen</p>
    </div>
""", unsafe_allow_html=True)

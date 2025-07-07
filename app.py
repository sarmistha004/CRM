import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

CSV_FILE = "customers.csv"

# Load existing customer data or create an empty DataFrame
def load_customers():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'Customer ID', 'Name', 'Email', 'Phone', 'Address',
            'City', 'State', 'Gender', 'Company', 'Joined Date'
        ])

# Save customer data to CSV
def save_customers(df):
    df.to_csv(CSV_FILE, index=False)


# ✅ Set Page Config
st.set_page_config(page_title="Relatrix - Corporate CRM Dashboard", layout="centered")

# ✅ Stylish Title with Emoji & Tagline
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='font-size: 44px; color:#6C63FF; font-family:monospace;'>📊 Relatrix</h1>
        <p style='font-size: 24px; color: deeppink; font-family: "Comic Sans MS", cursive; font-weight: bold;'>📈 Where Relationships Drive Results.</p>
        <p style='font-size: 22px; font-family: "Comic Sans MS", cursive; font-weight: bold;'>🏢 A Corporate CRM Dashboard</p>
    </div>
""", unsafe_allow_html=True)

# ✅ Background & UI Custom Styles
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #ffe6f0, #e6ccff);
    }
    header, footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Initialize session state
# ---------------------------
if 'customers' not in st.session_state:
    st.session_state.customers = load_customers()

# ---------------------------
# Add New Customer
# ---------------------------

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
        new_row = {
            'Customer ID': cid, 'Name': name, 'Email': email, 'Phone': phone,
            'Address': address, 'City': city, 'State': state,
            'Gender': gender, 'Company': company, 'Joined Date': joined.strftime("%Y-%m-%d")
        }
        st.session_state.customers.loc[len(st.session_state.customers)] = new_row
        save_customers(st.session_state.customers)  # ✅ Save after add
        st.success(f"Customer {name} added!")


# ---------------------------
# Edit Customer (Name is non-editable)
# ---------------------------
st.header("✏️ Edit Customer")

if not st.session_state.customers.empty:
    selected_index = st.selectbox("Select customer to edit", st.session_state.customers.index, format_func=lambda x: st.session_state.customers.at[x, 'Name'])
    row = st.session_state.customers.loc[selected_index]

    with st.form("edit_form"):
        cid = st.text_input("Customer ID", value=row['Customer ID'])
        st.text_input("Name (not editable)", value=row['Name'], disabled=True)
        email = st.text_input("Email", value=row['Email'])
        phone = st.text_input("Phone", value=row['Phone'])
        address = st.text_input("Address", value=row['Address'])
        city = st.text_input("City", value=row['City'])
        state = st.text_input("State", value=row['State'])
        gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(row['Gender']))
        company = st.text_input("Company", value=row['Company'])
        joined = st.date_input("Joined Date", datetime.strptime(row['Joined Date'], "%Y-%m-%d"))
        updated = st.form_submit_button("Update Customer")

        if updated:
            st.session_state.customers.loc[selected_index] = [
                cid, row['Name'], email, phone, address, city, state, gender, company, joined.strftime("%Y-%m-%d")
            ]
            save_customers(st.session_state.customers)  # ✅ Save after edit
            st.success(f"Customer '{row['Name']}' updated successfully!")


# ---------------------------
# Delete Customer
# ---------------------------
st.header("🗑️ Delete Customer")

if not st.session_state.customers.empty:
    del_index = st.selectbox("Select customer to delete", st.session_state.customers.index, format_func=lambda x: st.session_state.customers.at[x, 'Name'])
    if st.button("Delete Customer"):
        deleted_name = st.session_state.customers.at[del_index, 'Name']
        st.session_state.customers.drop(index=del_index, inplace=True)
        st.session_state.customers.reset_index(drop=True, inplace=True)
        save_customers(st.session_state.customers)  # ✅ save to CSV
        st.success(f"Customer {deleted_name} deleted!")


# ---------------------------
# Display Customers
# ---------------------------
st.header("📋 All Customers")
st.dataframe(st.session_state.customers.reset_index(drop=True))

# ---------------------------
# 📊 Gender-wise Pie Chart
# ---------------------------
st.header("📊 Gender-wise Distribution")
if not st.session_state.customers.empty:
    gender_counts = st.session_state.customers['Gender'].value_counts().reset_index()
    gender_counts.columns = ['Gender', 'Count']
    fig = px.pie(gender_counts, values='Count', names='Gender', title='Customer Gender Ratio', color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig)

# ---------------------------
# 📁 Download CSV & PDF
# ---------------------------
st.header("⬇️ Download Customer Data")

# Download CSV
csv = st.session_state.customers.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", data=csv, file_name="customers.csv", mime="text/csv")

# Generate PDF
def generate_pdf(dataframe):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "📄 Relatrix - Customer Report")
    c.setFont("Helvetica", 10)

    y = height - 80
    for index, row in dataframe.iterrows():
        text = f"{row['Customer ID']} | {row['Name']} | {row['Email']} | {row['Gender']} | {row['Company']}"
        c.drawString(50, y, text)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

pdf_data = generate_pdf(st.session_state.customers)
st.download_button("📄 Download PDF", data=pdf_data, file_name="customers_report.pdf", mime="application/pdf")

# ✅ Custom Footer
st.markdown("""
    <div style='
        position: fixed;
        bottom: 10px;
        left: 20px;
        background-color: #C71585;
        padding: 12px 20px;
        border-radius: 12px;
        box-shadow: 0 0 15px #C71585;
    '>
        <p style='font-size: 20px; color: white; font-family: "Comic Sans MS", cursive; margin: 0;'>Created by Sarmistha Sen</p>
    </div>
""", unsafe_allow_html=True)

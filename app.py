import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Relatrix - Corporate CRM Dashboard", layout="centered")
# ✅ App Title
    st.markdown("""
        <div style='text-align: center;'>
            <h1 style='font-size: 44px; color:#6C63FF; font-family:monospace;'>"📊 Relatrix "</h1>
            <p style='font-size: 24px; color: deeppink; font-family: "Comic Sans MS", cursive; font-weight: bold;'>📈 Where Relationships Drive Results.</p>
            <p style='font-size: 22px; font-family: "Comic Sans MS", cursive; font-weight: bold;'>🏢 A Corporate CRM Dashboard:</p>
        </div>
    """, unsafe_allow_html=True)

# ✅ Background & Styles
    st.markdown("""
        <style>
        body { background: linear-gradient(to right, #ffe6f0, #e6ccff); }
        header {visibility: hidden;}
        footer {visibility: hidden;}

# ---------------------------
# Initialize session state
# ---------------------------
if 'customers' not in st.session_state:
    st.session_state.customers = pd.DataFrame(columns=[
        'Customer ID', 'Name', 'Email', 'Phone', 'Address',
        'City', 'State', 'Gender', 'Company', 'Joined Date'
    ])

# ---------------------------
# Add New Customer
# ---------------------------
st.title("🧑‍💼 CRM - Manage Customers (Add / Edit / Delete)")
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
        st.success(f"Customer {deleted_name} deleted!")

# ---------------------------
# Display Customers
# ---------------------------
st.header("📋 All Customers")
st.dataframe(st.session_state.customers.reset_index(drop=True))

# ✅ Footer
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
            <p style='font-size: 20px; color: white; font-family: "Comic Sans MS", cursive; margin: 0;'>Created By Sarmistha Sen</p>
        </div>
    """, unsafe_allow_html=True)

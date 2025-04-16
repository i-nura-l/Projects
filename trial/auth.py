# auth.py – handles login, signup, and password hashing

import streamlit as st
import bcrypt
from pyairtable import Table
from datetime import datetime

# Airtable setup for users
USER_TABLE = Table(
    'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
    'appdgbGbEz1Dtynvg',
    'users_data'
)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def email_exists(email):
    try:
        records = USER_TABLE.all()
    except Exception as e:
        st.error(f"Error accessing user table: {e}")
        return None

    for rec in records:
        if rec.get('fields', {}).get('Email', '').lower() == email.lower():
            return rec
    return None

def signup_user(email, password, username):
    if email_exists(email):
        return False, "Email already registered."

    password_hash = hash_password(password)
    try:
        USER_TABLE.create({
            'Email': email,
            'Password_Hash': password_hash,
            'Status': 'New User',
            'Username': username
        })
        return True, "Account created successfully."
    except Exception as e:
        return False, f"Signup failed: {str(e)}"

def login_user(email, password):
    rec = email_exists(email)
    if not rec:
        return None, "No user with that email."

    stored_hash = rec['fields'].get('Password_Hash')
    if not stored_hash:
        return None, "No password stored for this user."

    if not check_password(password, stored_hash):
        return None, "Incorrect password."

    user_data = {
        'id': rec['id'],
        'email': rec['fields'].get('Email'),
        'status': rec['fields'].get('Status', 'User'),
        'avatar': rec['fields'].get('Avatar_URL', ''),
        'created': rec['fields'].get('Created_At'),
        'username': rec['fields'].get('Username', '')
    }
    return user_data, None

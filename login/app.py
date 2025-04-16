import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

supabase_url = "https://tametmsnltnzvmzrorwk.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRhbWV0bXNubHRuenZtenJvcndrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM2OTkyNjYsImV4cCI6MjA1OTI3NTI2Nn0.hTLDdr7oJu_lzrg_ATmu0nfgJ6WMtDcHzVSKV2Y24Zc"
supabase: Client = create_client(supabase_url, supabase_key)

def sign_up(email, password):
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        return user
    except Exception as e:
        st.error(f"Registration failed {e}")

def sign_in(email, password):
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return user
    except Exception as e:
        st.error(f"Login failed: {e}")

def sign_out():
    try:
        supabase.auth.sign_out()
        st.session_state.user_email =  None
        st.rerun()
    except Exception as e:
        st.error(f"Logout failed: {e}")


def main_app(user_email):
    st.title("Welcome Page")
    st.success(f"Welcome, {user_email}")
    if st.button("Logout"):
        sign_out()

def auth_screeen():
    st.title('Streamlit & Supabase Auth App')
    option = st.selectbox('Choose an action:', ['Login', 'Sign Up'])
    email = st.text_input('Email')
    password = st.text_input('Password', type = 'password')

    if option == 'Sign Up' and st.button("Register"):
        user = sign_up(email, password)
        if user and user.user:
            st.success('registration successful. Please Log in')

    if option == "Login" and st.button('Login'):
        user = sign_in(email, password)
        if user and user.user:
            st.session_state.user_email = user.user.email
            st.success(f'Welcome back, {email}')
            st.rerun()

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if st.session_state.user_email:
    main_app(st.session_state.user_email)

else:
    auth_screeen()
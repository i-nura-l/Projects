# auth_ui.py – UI logic for login/signup

import streamlit as st
from auth import signup_user, login_user

def login_interface():
    st.title("🔐 Welcome to wea-rCloth")
    st.subheader("Login or Create Account")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log In")

        if submit:
            user_data, error = login_user(email, password)
            if user_data:
                st.session_state.user = user_data
                st.success(f"Welcome back, {user_data['email']}!")
                st.rerun()
            else:
                st.error(error)

    st.markdown("---")
    st.subheader("Don't have an account?")

    with st.form("signup_form"):
        new_email = st.text_input("New Email")
        new_password = st.text_input("Create Password", type="password")
        signup = st.form_submit_button("Create Account")

        if signup:
            success, message = signup_user(new_email, new_password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


def require_login():
    if 'user' not in st.session_state:
        st.warning("Please log in to continue.")
        login_interface()
        st.stop()


def logout_button():
    if 'user' in st.session_state:
        with st.sidebar.expander(f"👤 {st.session_state.user['email']}"):
            if st.button("Logout"):
                del st.session_state.user
                st.rerun()

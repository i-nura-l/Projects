# state_management.py

import streamlit as st
from constants import CUSTOM_TYPES

def init_session_state():
    if 'current_combination' not in st.session_state:
        st.session_state.current_combination = None
    if 'show_rating' not in st.session_state:
        st.session_state.show_rating = False
    if 'custom_types' not in st.session_state:
        st.session_state.custom_types = CUSTOM_TYPES
    if 'form_category' not in st.session_state:
        st.session_state.form_category = "Upper body"
    if 'type_options' not in st.session_state:
        st.session_state.type_options = CUSTOM_TYPES["Upper body"]

def update_type_options():
    category = st.session_state.category_select
    st.session_state.form_category = category
    if category in st.session_state.custom_types:
        st.session_state.type_options = st.session_state.custom_types[category]
    else:
        st.session_state.type_options = []

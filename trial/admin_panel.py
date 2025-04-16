# admin_panel.py – Admin tools for managing users

import streamlit as st
from pyairtable import Table
from pyairtable.formulas import match

USER_TABLE = Table(
    'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
    'appdgbGbEz1Dtynvg',
    'users_data'
)

WARDROBE_TABLE = Table(
    'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
    'appdgbGbEz1Dtynvg',
    'wardrobe_data'
)

COMBINATIONS_TABLE = Table(
    'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
    'appdgbGbEz1Dtynvg',
    'combinations_data'
)

def admin_panel():
    st.title("🔧 Admin Panel")

    if st.session_state.user.get("email") != "admin@example.com":
        st.error("Access denied. Admins only.")
        return

    st.subheader("📋 Registered Users")
    users = USER_TABLE.all()

    emails = [u['fields'].get('Email') for u in users]
    selected_email = st.selectbox("Select a user to manage", emails)
    selected_user = next((u for u in users if u['fields'].get('Email') == selected_email), None)

    if selected_user:
        st.write("**Email:**", selected_user['fields'].get('Email'))
        st.write("**Status:**", selected_user['fields'].get('Status'))
        st.write("**Airtable ID:**", selected_user['id'])

        if st.button("❌ Delete this user and all data"):
            try:
                wardrobe = WARDROBE_TABLE.all()
                for item in wardrobe:
                    if item['fields'].get('User_Email') == selected_email:
                        WARDROBE_TABLE.delete(item['id'])

                combos = COMBINATIONS_TABLE.all()
                for combo in combos:
                    if combo['fields'].get('User_Email') == selected_email:
                        COMBINATIONS_TABLE.delete(combo['id'])

                USER_TABLE.delete(selected_user['id'])
                st.success("User and all associated data deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete user: {e}")

    st.subheader("⭐ Toggle Favorites in Combos")
    combos = COMBINATIONS_TABLE.all()
    for combo in combos:
        fields = combo.get("fields", {})
        combo_id = fields.get("Combination_ID", "Unknown")
        is_fav = fields.get("Favorite", False)

        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"{combo_id}: {fields.get('Upper_Body')} / {fields.get('Lower_Body')} / {fields.get('Footwear')}")
        with col2:
            if st.button("⭐" if is_fav else "☆", key=combo["id"]):
                try:
                    COMBINATIONS_TABLE.update(combo["id"], {"Favorite": not is_fav})
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update favorite: {e}")
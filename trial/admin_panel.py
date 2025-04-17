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

    if st.session_state.user.get("status") != "1":
        st.error("Access denied. Admins only.")
        st.stop()

    st.subheader("📋 Registered Users")
    users = USER_TABLE.all()
    from airtable_utils import WARDROBE_TABLE, COMBINATIONS_TABLE

    wardrobe = WARDROBE_TABLE.all()
    combos = COMBINATIONS_TABLE.all()

    st.metric("👕 Total Clothing Items", len(wardrobe))
    st.metric("👗 Total Outfit Combinations", len(combos))

    emails = [u['fields'].get('Email') for u in users]
    selected_email = st.selectbox("Select a user to manage", emails)
    selected_user = next((u for u in users if u['fields'].get('Email') == selected_email), None)

    if selected_user:

        st.write("**Email:**", selected_user['fields'].get('Email'))
        st.write("**Status:**", selected_user['fields'].get('Status'))
        st.write("**Airtable ID:**", selected_user['id'])

        user_email = selected_user['fields'].get('Email')
        user_wardrobe_count = sum(1 for item in wardrobe if item['fields'].get('User_Email') == user_email)
        user_combo_count = sum(1 for c in combos if c['fields'].get('User_Email') == user_email)

        st.write(f"**Clothes by this user:** {user_wardrobe_count}")
        st.write(f"**Combinations by this user:** {user_combo_count}")

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


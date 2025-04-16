# profile_ui.py – user profile dashboard

import streamlit as st
import pandas as pd
from airtable_utils import WARDROBE_TABLE, COMBINATIONS_TABLE


def get_user_clothes(email):
    records = WARDROBE_TABLE.all()
    return [r for r in records if r['fields'].get('User_Email') == email]

def get_user_combos(email):
    records = COMBINATIONS_TABLE.all()
    return [r for r in records if r['fields'].get('User_Email') == email]

def profile_dashboard():
    user = st.session_state.user
    st.title("👤 My Profile")

    avatar_url = user.get("avatar")
    if avatar_url:
        st.image(avatar_url, width=100)
    else:
        st.image("https://avatars.githubusercontent.com/u/9919?s=200&v=4", width=100)

    st.write(f"**Name:** {user.get('username', 'Unknown')}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Status:** {user.get('status', 'User')}")
    join_date = user.get('created')
    if isinstance(join_date, str):
        st.write(f"**Joined:** {join_date[:10]}")
    else:
        st.write("**Joined:** Unknown")

    clothes = get_user_clothes(user['email'])
    combos = get_user_combos(user['email'])

    st.metric("👚 Clothes Added", len(clothes))
    st.metric("👕 Outfit Combos", len(combos))

    st.markdown("---")
    st.subheader("✏️ Update Status")
    new_status = st.text_input("Your Status", user.get("status", ""))
    if st.button("Update Status"):
        try:
            user_id = user['id']
            from auth import USER_TABLE
            USER_TABLE.update(user_id, {"Status": new_status})
            st.success("Status updated!")
            st.session_state.user["status"] = new_status
        except Exception as e:
            st.error(f"Failed to update status: {e}")

    st.markdown("---")
    st.subheader("❤️ Favorite Combinations")
    favs = [r for r in combos if r['fields'].get('Favorite') is True]

    if favs:
        df = pd.DataFrame([r['fields'] for r in favs])
        st.dataframe(df)
    else:
        st.info("You have no favorite outfits yet.")

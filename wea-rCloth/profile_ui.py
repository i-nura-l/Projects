# profile_ui.py – user profile dashboard

import streamlit as st
import pandas as pd
from airtable_utils import WARDROBE_TABLE, COMBINATIONS_TABLE
import os


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
    if avatar_url and os.path.exists(avatar_url):
        st.image(avatar_url, width=100)
    else:
        st.image("https://avatars.githubusercontent.com/u/9919?s=200&v=4", width=100)

    st.markdown("### 🖼️ Update Avatar")
    new_avatar = st.file_uploader("Upload New Avatar", type=["jpg", "jpeg", "png"])
    if new_avatar:
        os.makedirs("avatars", exist_ok=True)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{user['username']}_{timestamp}.jpg"
        avatar_path = os.path.join("avatars", filename)
        with open(avatar_path, "wb") as f:
            f.write(new_avatar.getbuffer())

        try:
            from auth import USER_TABLE
            USER_TABLE.update(user['id'], {"Avatar_URL": avatar_path})
            st.session_state.user["avatar"] = avatar_path
            st.success("Avatar updated!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to update avatar: {e}")

    st.write(f"**Name:** {user.get('username', 'Unknown')}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Bio:** {user.get('bio', 'User')}")
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
    st.subheader("✏️ Update Bio")
    new_bio = st.text_input("Your Bio", user.get("bio", ""))
    if st.button("Update Bio"):
        try:
            user_id = user['id']
            from auth import USER_TABLE
            USER_TABLE.update(user_id, {"Bio": new_bio})
            st.success("Bio updated!")
            st.session_state.user["bio"] = new_bio
        except Exception as e:
            st.error(f"Failed to update bio: {e}")

    st.markdown("---")
    st.subheader("❤️ Favorite Combinations")
    favs = [r for r in combos if r['fields'].get('Favorite') is True]

    if favs:
        df = pd.DataFrame([r['fields'] for r in favs])
        st.dataframe(df)
    else:
        st.info("You have no favorite outfits yet.")

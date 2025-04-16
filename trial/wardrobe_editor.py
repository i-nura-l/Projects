# wardrobe_editor.py – edit/delete clothing items

import streamlit as st
import pandas as pd
from airtable_utils import WARDROBE_TABLE


def wardrobe_edit_interface(email):
    st.title("🧺 My Wardrobe")

    # Load all user clothes
    all_items = WARDROBE_TABLE.all()
    user_items = [r for r in all_items if r['fields'].get('User_Email') == email]

    if not user_items:
        st.info("No clothing items found.")
        return

    df = pd.DataFrame([r['fields'] | {"_id": r['id']} for r in user_items])

    st.subheader("🧾 Your Items")
    selected = st.selectbox("Select a clothing item to edit/delete", df["Model"])
    selected_row = df[df["Model"] == selected].iloc[0]

    with st.expander("Edit This Item"):
        new_type = st.text_input("Type", selected_row.get("Type", ""))
        new_color = st.text_input("Color", selected_row.get("Color", ""))
        new_style = st.text_input("Style", selected_row.get("Style", ""))
        new_season = st.text_input("Season", selected_row.get("Season", ""))

        if st.button("💾 Save Changes"):
            try:
                WARDROBE_TABLE.update(selected_row["_id"], {
                    "Type": new_type,
                    "Color": new_color,
                    "Style": new_style,
                    "Season": new_season,
                    "User_Email": email
                })
                st.success("Item updated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating: {e}")

    if st.button("❌ Delete This Item"):
        try:
            WARDROBE_TABLE.delete(selected_row["_id"])
            st.success("Item deleted.")
            st.rerun()
        except Exception as e:
            st.error(f"Error deleting: {e}")

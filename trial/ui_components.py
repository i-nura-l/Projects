# ui_components.py

import streamlit as st
import pandas as pd

def display_outfit_combo(combo, wardrobe_df):
    upper_details = wardrobe_df[wardrobe_df['Model'] == combo['Upper_Body']]
    lower_details = wardrobe_df[wardrobe_df['Model'] == combo['Lower_Body']]
    foot_details  = wardrobe_df[wardrobe_df['Model'] == combo['Footwear']]

    st.subheader("Your Outfit Combination:")
    if not upper_details.empty:
        st.write(f"**Upper Body:** {upper_details['Model'].values[0]} - "
                 f"{upper_details['Type'].values[0]} ({upper_details['Color'].values[0]})")
    if not lower_details.empty:
        st.write(f"**Lower Body:** {lower_details['Model'].values[0]} - "
                 f"{lower_details['Type'].values[0]} ({lower_details['Color'].values[0]})")
    if not foot_details.empty:
        st.write(f"**Footwear:** {foot_details['Model'].values[0]} - "
                 f"{foot_details['Type'].values[0]} ({foot_details['Color'].values[0]})")

    st.write(f"**Chosen Season:** {', '.join(combo['Season_Match'])}")
    st.write(f"**Chosen Style:** {', '.join(combo['Style_Match'])}")

def clothing_form(type_options, style_options, season_options, form_category, wardrobe_df):
    with st.form("new_cloth_form"):
        cloth_type = st.selectbox("Type", type_options)
        selected_style = st.multiselect("Style", style_options, default=["Casual"])
        color = st.text_input("Color")
        selected_season = st.multiselect("Season", season_options, default=["Universal"])

        existing_items = wardrobe_df[
            (wardrobe_df['Category'] == form_category) &
            (wardrobe_df['Type'] == cloth_type)
        ]
        next_number = len(existing_items) + 1 if not existing_items.empty else 1

        style_code = ''.join([s[0] for s in selected_style]) if selected_style else ''
        season_code = ''.join([s[0] for s in selected_season]) if selected_season else ''
        category_code = form_category.split()[0][0]
        type_prefix = cloth_type.split("-")[0] if "-" in cloth_type else "00"
        model = f"{category_code}{type_prefix}{next_number:02d}{style_code.lower()}{season_code}"

        st.write(f"Generated Model ID: {model}")

        submitted = st.form_submit_button("Add to Wardrobe")
        if submitted:
            new_item = {
                'Model': model,
                'Category': form_category,
                'Type': cloth_type,
                'Style': selected_style,
                'Color': color,
                'Season': selected_season
            }
            return new_item
    return None

def rating_form(combo):
    with st.form("rating_form"):
        rating = st.slider("Rate this combination (0-10)", 0, 10, 5)
        save_rating = st.form_submit_button("Save Rating")
        if save_rating:
            new_combination = combo.copy()
            new_combination['Rating'] = rating
            return new_combination
    return None

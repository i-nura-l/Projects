# ui_components.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime

def display_outfit_combo(combo, wardrobe_df):
    st.subheader("Your Outfit Combination:")

    for part in ['Upper_Body', 'Lower_Body', 'Footwear']:
        item = wardrobe_df[wardrobe_df['Model'] == combo[part]]
        if not item.empty:
            model = item['Model'].values[0]
            type_ = item['Type'].values[0]
            color = item['Color'].values[0]
            image_url = item.get('Image_URL', [""]).values[0]

            st.markdown(f"**{part.replace('_', ' ')}:** {model} - {type_} ({color})")

            # ✅ SAFETY CHECK BEFORE RENDERING IMAGE
            if image_url and isinstance(image_url, str) and os.path.exists(image_url):
                try:
                    st.image(image_url, width=200)
                except Exception as e:
                    st.warning(f"Could not display image for {model}. Error: {e}")
            else:
                st.info("No image available.")


def clothing_form(type_options, style_options, season_options, form_category, wardrobe_df):
    with st.form("new_cloth_form"):
        cloth_type = st.selectbox("Type", type_options)
        selected_style = st.multiselect("Style", style_options, default=["Casual"])
        color = st.text_input("Color")
        selected_season = st.multiselect("Season", season_options, default=["Universal"])

        # 🆕 Image uploader
        uploaded_image = st.file_uploader("Upload Image (optional)", type=["png", "jpg", "jpeg"])

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
            # Save image if uploaded
            image_path = ""
            if uploaded_image is not None:
                os.makedirs("images", exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{model}_{timestamp}.jpg"
                image_path = os.path.join("images", filename)
                with open(image_path, "wb") as f:
                    f.write(uploaded_image.getbuffer())

            new_item = {
                'Model': model,
                'Category': form_category,
                'Type': cloth_type,
                'Style': selected_style,
                'Color': color,
                'Season': selected_season,
                'Image_URL': image_path if uploaded_image else ""
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

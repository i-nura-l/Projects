# app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from constants import CUSTOM_TYPES, STYLE_OPTIONS, SEASON_OPTIONS, CATEGORY_OPTIONS
from airtable_utils import load_data, save_data
from wardrobe_helpers import get_unique_values, matches_season, matches_style
from ui_components import display_outfit_combo, clothing_form, rating_form
from state_management import init_session_state, update_type_options

st.set_page_config(page_title="wea-rCloth", layout="wide")
init_session_state()

wardrobe_df, combinations_df = load_data()

st.sidebar.title("wea-rCloth")
page = st.sidebar.selectbox("Navigation", ["Main", "Wardrobe", "Combinations", "Analysis", "About"])

# MAIN PAGE
if page == "Main":
    st.title("wea-rCloth - Your Smart Wardrobe Assistant")
    col1, col2 = st.columns(2)

    # Add New Clothing Item
    with col1:
        st.subheader("Add New Clothing Item")
        category_select = st.selectbox(
            "Category",
            CATEGORY_OPTIONS,
            key="category_select",
            on_change=update_type_options
        )

        new_item = clothing_form(
            st.session_state.type_options, STYLE_OPTIONS, SEASON_OPTIONS,
            st.session_state.form_category, wardrobe_df
        )
        if new_item:
            wardrobe_df = pd.concat([wardrobe_df, pd.DataFrame([new_item])], ignore_index=True)
            st.session_state.new_item = new_item
            save_data(st.session_state)

    # Generate Outfit by Season/Style
    with col2:
        st.subheader("Generate Outfit Combination")
        with st.form("generate_outfit_form"):
            chosen_season = st.selectbox("Choose Season", SEASON_OPTIONS, index=4)
            chosen_style = st.selectbox("Choose Style", STYLE_OPTIONS, index=3)
            generate_button = st.form_submit_button("Generate Outfit")

        if generate_button:
            valid_items = wardrobe_df[
                wardrobe_df['Season'].apply(lambda x: matches_season(x, chosen_season)) &
                wardrobe_df['Style'].apply(lambda x: matches_style(x, chosen_style))
            ]

            if valid_items.empty:
                st.error("No items match your chosen Season/Style. Please add more clothes or change filters.")
            else:
                upper_df = valid_items[valid_items['Category'] == 'Upper body']
                lower_df = valid_items[valid_items['Category'] == 'Lower body']
                foot_df  = valid_items[valid_items['Category'] == 'Footwear']

                if upper_df.empty or lower_df.empty or foot_df.empty:
                    st.error("Not enough items in all categories to build a complete outfit!")
                else:
                    upper_item = upper_df.sample(1).iloc[0]
                    lower_item = lower_df.sample(1).iloc[0]
                    shoe_item  = foot_df.sample(1).iloc[0]

                    if not combinations_df.empty and 'Combination_ID' in combinations_df.columns:
                        existing_codes = [
                            code for code in combinations_df['Combination_ID']
                            if isinstance(code, str) and code.startswith('C')
                        ]
                        if existing_codes:
                            max_num = max(int(code[1:]) for code in existing_codes)
                            new_num = max_num + 1
                        else:
                            new_num = 1
                    else:
                        new_num = 1
                    combination_id = f"C{new_num:03d}"

                    st.session_state.current_combination = {
                        'Combination_ID': combination_id,
                        'Upper_Body': upper_item['Model'],
                        'Lower_Body': lower_item['Model'],
                        'Footwear': shoe_item['Model'],
                        'Season_Match': [chosen_season],
                        'Style_Match': [chosen_style]
                    }
                    st.session_state.show_rating = True

        if st.session_state.show_rating and st.session_state.current_combination:
            combo = st.session_state.current_combination
            display_outfit_combo(combo, wardrobe_df)
            new_combination = rating_form(combo)
            if new_combination:
                st.session_state.new_combination = new_combination
                save_data(st.session_state)

# ... (repeat for "Wardrobe", "Combinations", "Analysis", "About" pages, moving helper logic into modules as above)

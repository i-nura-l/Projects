# app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from auth_ui import require_login, logout_button
from profile_ui import profile_dashboard
from wardrobe_editor import wardrobe_edit_interface
from admin_panel import admin_panel
import os



from constants import CUSTOM_TYPES, STYLE_OPTIONS, SEASON_OPTIONS, CATEGORY_OPTIONS
from airtable_utils import load_data, save_data
from wardrobe_helpers import get_unique_values, matches_season, matches_style
from ui_components import display_outfit_combo, clothing_form, rating_form
from state_management import init_session_state, update_type_options

def apply_theme(theme):
    dark_mode_css = """
        <style>
        html, body, [class*="css"] {
            background-color: #0e1117;
            color: #ffffff;
        }
        .stButton>button {
            background-color: #262730;
            color: white;
        }
        .stSelectbox div, .stTextInput input {
            background-color: #1e2026;
            color: white;
        }
        </style>
    """
    light_mode_css = """
        <style>
        html, body, [class*="css"] {
            background-color: #ffffff;
            color: #000000;
        }
        </style>
    """
    st.markdown(dark_mode_css if theme == "Dark" else light_mode_css, unsafe_allow_html=True)


st.set_page_config(page_title="wea-rCloth", layout="wide")

logout_button()
require_login()

init_session_state()


wardrobe_df_full, combinations_df = load_data()
user_email = st.session_state.user['email']
wardrobe_df = wardrobe_df_full[wardrobe_df_full['User_Email'] == user_email].copy()

st.sidebar.title("wea-rCloth")
nav_options = ["Main", "Wardrobe", "Combinations", "Analysis", "Profile", "About"]
if st.session_state.user.get("status") == "1":
    nav_options.append("Admin Panel")

page = st.sidebar.selectbox("Navigation", nav_options)

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
                            code for code in combinations_df[
                                combinations_df['User_Email'] == user_email
                                ]['Combination_ID']
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


# ----------------------------
# WARDROBE PAGE
# ----------------------------
elif page == "Wardrobe":
    if 'user' in st.session_state:
        wardrobe_edit_interface(st.session_state.user['email'])
    else:
        st.warning("Please log in to view your wardrobe.")

# ----------------------------
# COMBINATIONS PAGE
# ----------------------------
elif page == "Combinations":
    st.title("Combination Records")

    user_email = st.session_state.user['email']
    if not combinations_df.empty and 'User_Email' in combinations_df.columns:
        combo_filtered_df = combinations_df[combinations_df['User_Email'] == user_email].copy()
    else:
        combo_filtered_df = pd.DataFrame()

    st.sidebar.subheader("Filter Options for Combinations")
    unique_seasons = get_unique_values(combinations_df, "Season_Match")
    unique_styles = get_unique_values(combinations_df, "Style_Match")
    filter_season = st.sidebar.multiselect("Season", unique_seasons)
    filter_style = st.sidebar.multiselect("Style", unique_styles)
    rating_range = st.sidebar.slider("Rating Range", 0, 10, (0, 10))

    def filter_list_field(cell, selected_options):
        if isinstance(cell, list):
            return any(item in cell for item in selected_options)
        elif isinstance(cell, str):
            items = [i.strip() for i in cell.split(',')]
            return any(item in items for item in selected_options)
        return False

    if filter_season:
        combo_filtered_df = combo_filtered_df[
            combo_filtered_df["Season_Match"].apply(lambda x: filter_list_field(x, filter_season))
        ]
    if filter_style:
        combo_filtered_df = combo_filtered_df[
            combo_filtered_df["Style_Match"].apply(lambda x: filter_list_field(x, filter_style))
        ]
    if "Rating" in combo_filtered_df.columns:
        combo_filtered_df = combo_filtered_df[
            combo_filtered_df["Rating"].apply(
                lambda x: x is not None and rating_range[0] <= x <= rating_range[1]
            )
        ]

    if combo_filtered_df.empty:
        st.info("You don't have any saved combinations matching the selected filters.")

        wardrobe_df_user = wardrobe_df[wardrobe_df['User_Email'] == user_email]

        st.subheader("🔧 Create a Combination Manually")
        with st.form("manual_combo_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                upper_item_id = st.selectbox("Choose Upper Body",
                                             wardrobe_df_user[wardrobe_df_user['Category'] == 'Upper body']['Model'],
                                             key="upper_select")
                if upper_item_id:
                    upper_item = wardrobe_df_user[wardrobe_df_user['Model'] == upper_item_id].iloc[0]
                    st.markdown(
                        f"**Type:** {upper_item['Type']}  \n**Color:** {upper_item['Color']}  \n**Style:** {upper_item['Style']}  \n**Season:** {upper_item['Season']}")
                    image_path = upper_item.get("Image_URL", "")
                    if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                        st.image(image_path, width=120)

            with col2:
                lower_item_id = st.selectbox("Choose Lower Body",
                                             wardrobe_df_user[wardrobe_df_user['Category'] == 'Lower body']['Model'],
                                             key="lower_select")
                if lower_item_id:
                    lower_item = wardrobe_df_user[wardrobe_df_user['Model'] == lower_item_id].iloc[0]
                    st.markdown(
                        f"**Type:** {lower_item['Type']}  \n**Color:** {lower_item['Color']}  \n**Style:** {lower_item['Style']}  \n**Season:** {lower_item['Season']}")
                    image_path = lower_item.get("Image_URL", "")
                    if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                        st.image(image_path, width=120)

            with col3:
                footwear_item_id = st.selectbox("Choose Footwear",
                                                wardrobe_df_user[wardrobe_df_user['Category'] == 'Footwear']['Model'],
                                                key="footwear_select")
                if footwear_item_id:
                    footwear_item = wardrobe_df_user[wardrobe_df_user['Model'] == footwear_item_id].iloc[0]
                    st.markdown(
                        f"**Type:** {footwear_item['Type']}  \n**Color:** {footwear_item['Color']}  \n**Style:** {footwear_item['Style']}  \n**Season:** {footwear_item['Season']}")
                    image_path = footwear_item.get("Image_URL", "")
                    if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                        st.image(image_path, width=120)

            season_match = st.multiselect("Season Match", SEASON_OPTIONS)
            style_match = st.multiselect("Style Match", STYLE_OPTIONS)
            rating = st.slider("Rate this combination", 0, 10, 5)
            mark_favorite = st.checkbox("❤️ Mark this combination as favorite")

            create_btn = st.form_submit_button("Save Combination")

        if create_btn:
            if not (upper_item_id and lower_item_id and footwear_item_id):
                st.warning("Please select an item for each category (Upper, Lower, Footwear).")
            elif not season_match:
                st.warning("Please select at least one season.")
            elif not style_match:
                st.warning("Please select at least one style.")
            else:
                # ✅ Only enter this block if everything is filled correctly
                if not combinations_df.empty and 'User_Email' in combinations_df.columns:
                    user_combos = combinations_df[combinations_df['User_Email'] == user_email]
                    existing_codes = [
                        code for code in user_combos['Combination_ID']
                        if isinstance(code, str) and code.startswith('C')
                    ]
                    new_num = max([int(code[1:]) for code in existing_codes], default=0) + 1
                else:
                    new_num = 1

                combination_id = f"C{new_num:03d}"
                st.session_state.new_combination = {
                    'Combination_ID': combination_id,
                    'Upper_Body': upper_item_id,
                    'Lower_Body': lower_item_id,
                    'Footwear': footwear_item_id,
                    'Season_Match': season_match,
                    'Style_Match': style_match,
                    'User_Email': user_email,
                    'Rating': rating,
                    'Favorite': mark_favorite
                }
                save_data(st.session_state)
                st.success("Combination saved!")
                st.rerun()
    else:
        wardrobe_df_user = wardrobe_df[wardrobe_df['User_Email'] == user_email]

        st.subheader("🔧 Create a Combination Manually")
        with st.form("manual_combo_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                upper_item_id = st.selectbox("Choose Upper Body",
                                             wardrobe_df_user[wardrobe_df_user['Category'] == 'Upper body']['Model'],
                                             key="upper_select")
                if upper_item_id:
                    upper_item = wardrobe_df_user[wardrobe_df_user['Model'] == upper_item_id].iloc[0]
                    st.markdown(
                        f"**Type:** {upper_item['Type']}  \n**Color:** {upper_item['Color']}  \n**Style:** {upper_item['Style']}  \n**Season:** {upper_item['Season']}")
                    image_path = upper_item.get("Image_URL", "")
                    if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                        st.image(image_path, width=120)

            with col2:
                lower_item_id = st.selectbox("Choose Lower Body",
                                             wardrobe_df_user[wardrobe_df_user['Category'] == 'Lower body']['Model'],
                                             key="lower_select")
                if lower_item_id:
                    lower_item = wardrobe_df_user[wardrobe_df_user['Model'] == lower_item_id].iloc[0]
                    st.markdown(
                        f"**Type:** {lower_item['Type']}  \n**Color:** {lower_item['Color']}  \n**Style:** {lower_item['Style']}  \n**Season:** {lower_item['Season']}")
                    image_path = lower_item.get("Image_URL", "")
                    if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                        st.image(image_path, width=120)

            with col3:
                footwear_item_id = st.selectbox("Choose Footwear",
                                                wardrobe_df_user[wardrobe_df_user['Category'] == 'Footwear']['Model'],
                                                key="footwear_select")
                if footwear_item_id:
                    footwear_item = wardrobe_df_user[wardrobe_df_user['Model'] == footwear_item_id].iloc[0]
                    st.markdown(
                        f"**Type:** {footwear_item['Type']}  \n**Color:** {footwear_item['Color']}  \n**Style:** {footwear_item['Style']}  \n**Season:** {footwear_item['Season']}")
                    image_path = footwear_item.get("Image_URL", "")
                    if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                        st.image(image_path, width=120)

            season_match = st.multiselect("Season Match", SEASON_OPTIONS)
            style_match = st.multiselect("Style Match", STYLE_OPTIONS)
            rating = st.slider("Rate this combination", 0, 10, 5)
            mark_favorite = st.checkbox("❤️ Mark this combination as favorite")

            create_btn = st.form_submit_button("Save Combination")

        if create_btn:
            if not (upper_item_id and lower_item_id and footwear_item_id):
                st.warning("Please select an item for each category (Upper, Lower, Footwear).")
            elif not season_match:
                st.warning("Please select at least one season.")
            elif not style_match:
                st.warning("Please select at least one style.")
            else:
                # ✅ Only enter this block if everything is filled correctly
                if not combinations_df.empty and 'User_Email' in combinations_df.columns:
                    user_combos = combinations_df[combinations_df['User_Email'] == user_email]
                    existing_codes = [
                        code for code in user_combos['Combination_ID']
                        if isinstance(code, str) and code.startswith('C')
                    ]
                    new_num = max([int(code[1:]) for code in existing_codes], default=0) + 1
                else:
                    new_num = 1

                combination_id = f"C{new_num:03d}"
                st.session_state.new_combination = {
                    'Combination_ID': combination_id,
                    'Upper_Body': upper_item_id,
                    'Lower_Body': lower_item_id,
                    'Footwear': footwear_item_id,
                    'Season_Match': season_match,
                    'Style_Match': style_match,
                    'User_Email': user_email,
                    'Rating': rating,
                    'Favorite': mark_favorite
                }
                save_data(st.session_state)
                st.success("Combination saved!")
                st.rerun()

        display_df = combo_filtered_df.drop(columns=["User_Email"]).reset_index(drop=True)
        display_df.index = [''] * len(display_df)
        st.dataframe(display_df, use_container_width=True)

        st.subheader("📊 Combination Ratings Analysis")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(combo_filtered_df['Rating'], bins=11, kde=True, ax=ax)
        ax.set_title('Distribution of Outfit Ratings')
        ax.set_xlabel('Rating')
        ax.set_ylabel('Count')
        st.pyplot(fig)

        st.subheader("🏆 Top Rated Combinations")
        top_combinations = combo_filtered_df.sort_values('Rating', ascending=False).head(5)
        st.dataframe(top_combinations.drop(columns=["User_Email"]).reset_index(drop=True), use_container_width=True)

# ----------------------------
# ANALYSIS PAGE
# ----------------------------
elif page == "Analysis":
    st.title("Wardrobe Analysis")
    if wardrobe_df.empty:
        st.info("Add some items to your wardrobe to see analysis!")
    else:
        viz_type = st.selectbox("Select Visualization Type", ["Pie Chart", "Bar Chart", "Line Chart", "Scatter Plot"])

        if viz_type in ["Pie Chart", "Bar Chart", "Line Chart"]:
            dimension = st.selectbox("Select Data Dimension", ["Category", "Type", "Style", "Color", "Season"])
            fig, ax = plt.subplots(figsize=(10, 6))

            counts = wardrobe_df[dimension].value_counts()
            if viz_type == "Pie Chart":
                ax.pie(counts, labels=counts.index, autopct='%1.1f%%')
            elif viz_type == "Bar Chart":
                counts.plot(kind='bar', ax=ax)
            elif viz_type == "Line Chart":
                counts.plot(kind='line', marker='o', ax=ax)

            ax.set_title(f'{dimension} Distribution')
            st.pyplot(fig)

        elif viz_type == "Scatter Plot":
            col1, col2 = st.columns(2)
            with col1:
                x_dimension = st.selectbox("X-Axis", ["Category", "Type", "Style", "Color", "Season"])
            with col2:
                y_dimension = st.selectbox("Y-Axis", ["Category", "Type", "Style", "Color", "Season"])

            fig, ax = plt.subplots(figsize=(10, 6))
            wardrobe_encoded = wardrobe_df.copy()
            for dim in [x_dimension, y_dimension]:
                categories = wardrobe_df[dim].unique()
                category_map = {cat: i for i, cat in enumerate(categories)}
                wardrobe_encoded[f"{dim}_encoded"] = wardrobe_df[dim].map(category_map)

            ax.scatter(
                wardrobe_encoded[f"{x_dimension}_encoded"],
                wardrobe_encoded[f"{y_dimension}_encoded"],
                c=wardrobe_encoded[f"{x_dimension}_encoded"],
                alpha=0.6
            )
            ax.set_xticks(range(len(wardrobe_df[x_dimension].unique())))
            ax.set_xticklabels(wardrobe_df[x_dimension].unique())
            ax.set_yticks(range(len(wardrobe_df[y_dimension].unique())))
            ax.set_yticklabels(wardrobe_df[y_dimension].unique())
            ax.set_xlabel(x_dimension)
            ax.set_ylabel(y_dimension)
            ax.set_title(f'{y_dimension} vs {x_dimension}')
            st.pyplot(fig)


# Profile Page
elif page == "Profile":
    profile_dashboard()

# ----------------------------
# ABOUT PAGE
# ----------------------------
elif page == "About":
    st.title("About wea-rCloth")
    st.markdown("""
    ## Your Smart Wardrobe Assistant

    **wea-rCloth** helps you:
    - Organize your wardrobe digitally
    - Generate outfit combinations based on your actual clothing items
    - Rate and track your favorite combinations
    - Analyze your wardrobe composition and preferences

    ### How to Use
    1. Add your clothing items on the Main page
    2. Generate and rate outfit combinations
    3. View your entire wardrobe on the Wardrobe page
    4. See analytics and insights on the Analysis page

    ### Future Features (Coming Soon)
    - Machine learning recommendations based on your ratings
    - Image upload for clothing items
    - Seasonal wardrobe planning
    - Outfit calendar
    - Community sharing
    - Color palette matching
    """)

elif page == "Admin Panel":
    admin_panel()



theme = st.sidebar.radio("Theme", ["Light", "Dark"], index=1)
apply_theme(theme)
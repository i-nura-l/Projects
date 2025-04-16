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


# ----------------------------
# WARDROBE PAGE
# ----------------------------
if page == "Wardrobe":
    st.title("Your Wardrobe")
    st.sidebar.subheader("Filter Options")
    filter_category = st.sidebar.multiselect("Category", wardrobe_df['Category'].unique().tolist())
    filter_style = st.sidebar.multiselect("Style", get_unique_values(wardrobe_df, 'Style'))
    filter_season = st.sidebar.multiselect("Season", get_unique_values(wardrobe_df, 'Season'))

    filtered_df = wardrobe_df.copy()
    if filter_category:
        filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]
    if filter_style:
        filtered_df = filtered_df[
            filtered_df['Style'].apply(lambda x: any(s in str(x) for s in filter_style))
        ]
    if filter_season:
        filtered_df = filtered_df[
            filtered_df['Season'].apply(lambda x: any(s in str(x) for s in filter_season))
        ]

    if not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            st.markdown(f"**{row['Model']}** — {row['Type']} ({row['Color']})")
            if 'Image_URL' in row and row['Image_URL']:
                if 'Image_URL' in row and row['Image_URL']:
                    try:
                        st.image(row['Image_URL'], width=150)
                    except Exception as e:
                        st.warning(f"Couldn't load image for {row['Model']}: {e}")

        st.write(f"Showing {len(filtered_df)} of {len(wardrobe_df)} items")
    else:
        st.info("No items found. Try different filters or add new items.")

# ----------------------------
# COMBINATIONS PAGE
# ----------------------------
elif page == "Combinations":
    st.title("Combination Records")
    st.sidebar.subheader("Filter Options for Combinations")
    unique_seasons = get_unique_values(combinations_df, "Season_Match")
    unique_styles = get_unique_values(combinations_df, "Style_Match")
    filter_season = st.sidebar.multiselect("Season", unique_seasons)
    filter_style = st.sidebar.multiselect("Style", unique_styles)
    rating_range = st.sidebar.slider("Rating Range", 0, 10, (0, 10))

    combo_filtered_df = combinations_df.copy()

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

    st.dataframe(combo_filtered_df)
    st.write(f"Showing {len(combo_filtered_df)} of {len(combinations_df)} combination records.")

    if not combinations_df.empty:
        st.subheader("Combination Ratings Analysis")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(combinations_df['Rating'], bins=11, kde=True, ax=ax)
        ax.set_title('Distribution of Outfit Ratings')
        ax.set_xlabel('Rating')
        ax.set_ylabel('Count')
        st.pyplot(fig)

        st.subheader("Top Rated Combinations")
        top_combinations = combinations_df.sort_values('Rating', ascending=False).head(5)
        st.dataframe(top_combinations)

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
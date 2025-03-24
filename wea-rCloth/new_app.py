import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pyairtable import Table

# Set page config
st.set_page_config(page_title="wea-rCloth", layout="wide")

# Initialize session state
if 'current_combination' not in st.session_state:
    st.session_state.current_combination = None
if 'show_rating' not in st.session_state:
    st.session_state.show_rating = False
if 'custom_types' not in st.session_state:
    st.session_state.custom_types = {
        "Upper body": [
            "01-Shirt", "02-TShirt", "03-Sweater", "04-Jacket", "05-Coat",
            "06-Hoodie", "07-Polo", "08-Vest", "09-Cardigan", "10-Blouse",
            "11-Turtleneck", "12-TankTop", "13-Sweatshirt", "14-Blazer",
            "15-CropTop", "16-Tunic", "17-Bodysuit", "18-Flannel", "19-Windbreaker"
        ],
        "Lower body": [
            "01-Jeans", "02-Trousers", "03-Shorts", "04-Skirt",
            "05-Sweatpants", "06-Leggings", "07-CargoPants", "08-Chinos",
            "09-CutOffs", "10-WideLeg"
        ],
        "Footwear": [
            "01-Sneakers", "02-Formal", "03-Boots", "04-Sandals",
            "05-Loafers", "06-Moccasins", "07-Espadrilles", "08-SlipOns",
            "09-HikingBoots", "10-RunningShoes"
        ]
    }
if 'form_category' not in st.session_state:
    st.session_state.form_category = "Upper body"
if 'type_options' not in st.session_state:
    st.session_state.type_options = st.session_state.custom_types["Upper body"]

# Initialize Airtable tables
wardrobe_table = Table(
    'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
    'appdgbGbEz1Dtynvg',
    'wardrobe_data'
)
combinations_table = Table(
    'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
    'appdgbGbEz1Dtynvg',
    'combinations_data'
)

def load_data():
    """Fetch data from Airtable instead of local CSVs."""
    wardrobe_records = wardrobe_table.all()
    combinations_records = combinations_table.all()

    # Create DataFrames from records
    loaded_wardrobe_df = pd.DataFrame(
        [rec['fields'] for rec in wardrobe_records if 'fields' in rec and rec['fields']]
    ) if wardrobe_records else pd.DataFrame()

    loaded_combinations_df = pd.DataFrame(
        [{'id': rec['id'], **rec['fields']} for rec in combinations_records if 'fields' in rec and rec['fields']]
    ) if combinations_records else pd.DataFrame()

    # Reset index to start from 1
    if not loaded_wardrobe_df.empty:
        loaded_wardrobe_df = loaded_wardrobe_df.reset_index(drop=True)
        loaded_wardrobe_df.index = loaded_wardrobe_df.index + 1

    if not loaded_combinations_df.empty:
        loaded_combinations_df = loaded_combinations_df.reset_index(drop=True)
        loaded_combinations_df.index = loaded_combinations_df.index + 1

    # Ensure all expected columns exist
    expected_columns = ['Model', 'Category', 'Type', 'Style', 'Color', 'Season']
    for col in expected_columns:
        if col not in loaded_wardrobe_df.columns:
            loaded_wardrobe_df[col] = None

    # Convert multi-select fields to string representation if needed
    multi_select_columns = ['Style', 'Season']
    for col in multi_select_columns:
        if col in loaded_wardrobe_df.columns:
            loaded_wardrobe_df[col] = loaded_wardrobe_df[col].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )

    return loaded_wardrobe_df, loaded_combinations_df

def get_unique_values(df, column):
    """Get unique values from a column that may contain comma-separated values."""
    if df is None or df.empty or column not in df.columns:
        return []

    all_values = set()
    for value in df[column].dropna():
        if isinstance(value, list):
            for item in value:
                all_values.add(item)
        elif isinstance(value, str):
            if ',' in value:
                for item in value.split(','):
                    all_values.add(item.strip())
            else:
                all_values.add(value)
    return sorted(list(all_values))

def save_data():
    """
    Save new items/combos from session state to Airtable.
    """
    # Save new clothing item if available
    if 'new_item' in st.session_state:
        new_item_data = st.session_state.new_item
        row_dict = {}
        for key, value in new_item_data.items():
            if isinstance(value, list) and value:
                row_dict[key] = value
            elif pd.notna(value):
                row_dict[key] = value
        try:
            wardrobe_table.create(row_dict)
            st.success(f"Added {row_dict.get('Model', 'item')} to your wardrobe!")
            del st.session_state.new_item
        except Exception as e:
            st.error(f"Error saving to Airtable: {str(e)}")
            st.error("Check if all field names match your Airtable schema")

    # Save new outfit combination if available
    if 'new_combination' in st.session_state:
        new_combination_data = st.session_state.new_combination
        row_dict = {}
        for key, value in new_combination_data.items():
            if isinstance(value, list) and value:
                row_dict[key] = value
            elif pd.notna(value):
                row_dict[key] = value

        try:
            combinations_table.create(row_dict)
            st.success("Saved rating for this combination!")
            del st.session_state.new_combination
            st.session_state.show_rating = False  # Reset rating UI state
        except Exception as e:
            st.error(f"Error saving combination to Airtable: {str(e)}")
            st.error(f"Data being sent: {row_dict}")

def update_type_options():
    """Update the type options based on the selected category."""
    category = st.session_state.category_select
    st.session_state.form_category = category
    if category in st.session_state.custom_types:
        st.session_state.type_options = st.session_state.custom_types[category]
    else:
        st.session_state.type_options = []

# Load data
wardrobe_df, combinations_df = load_data()

# Sidebar navigation
st.sidebar.title("wea-rCloth")
page = st.sidebar.selectbox("Navigation", ["Main", "Wardrobe", "Combinations", "Analysis", "About"])

# ---------------------------------------------------------------------------
# PAGE: MAIN
# ---------------------------------------------------------------------------
if page == "Main":
    st.title("wea-rCloth - Your Smart Wardrobe Assistant")

    col1, col2 = st.columns(2)

    # ============== COLUMN 1: Add New Clothing ==============
    with col1:
        st.subheader("Add New Clothing Item")

        category_select = st.selectbox(
            "Category",
            ["Upper body", "Lower body", "Footwear"],
            key="category_select",
            on_change=update_type_options
        )

        with st.form("new_cloth_form"):
            cloth_type = st.selectbox("Type", st.session_state.type_options)
            selected_style = st.multiselect(
                "Style", ["Casual", "Formal", "Trendy", "Universal"], default=["Casual"]
            )
            color = st.text_input("Color")
            selected_season = st.multiselect(
                "Season", ["Winter", "Vernal", "Summer", "Autumn", "Universal"],
                default=["Universal"]
            )

            existing_items = wardrobe_df[
                (wardrobe_df['Category'] == st.session_state.form_category) &
                (wardrobe_df['Type'] == cloth_type)
            ]
            next_number = len(existing_items) + 1 if not existing_items.empty else 1

            # Auto-generate model name
            style_code = ''.join([s[0] for s in selected_style]) if selected_style else ''
            season_code = ''.join([s[0] for s in selected_season]) if selected_season else ''
            category_code = st.session_state.form_category.split()[0][0]
            type_prefix = cloth_type.split("-")[0] if "-" in cloth_type else "00"
            model = f"{category_code}{type_prefix}{next_number:02d}{style_code.lower()}{season_code}"

            st.write(f"Generated Model ID: {model}")

            submitted = st.form_submit_button("Add to Wardrobe")
            if submitted:
                new_item = {
                    'Model': model,
                    'Category': st.session_state.form_category,
                    'Type': cloth_type,
                    'Style': selected_style,
                    'Color': color,
                    'Season': selected_season
                }
                # Update local DF for immediate UI feedback
                wardrobe_df = pd.concat([wardrobe_df, pd.DataFrame([new_item])], ignore_index=True)
                st.session_state.new_item = new_item
                save_data()

    # ============== COLUMN 2: Generate Outfit by Season/Style ==============
    with col2:
        st.subheader("Generate Outfit Combination")

        # 1) User picks a single Season + Style (or you could do multi-select)
        with st.form("generate_outfit_form"):
            chosen_season = st.selectbox(
                "Choose Season",
                ["Winter", "Vernal", "Summer", "Autumn", "Universal"],
                index=4  # default to "Universal"
            )
            chosen_style = st.selectbox(
                "Choose Style",
                ["Casual", "Formal", "Trendy", "Universal"],
                index=3  # default to "Universal"
            )
            generate_button = st.form_submit_button("Generate Outfit")

        if generate_button:
            try:
                # Helper functions
                def matches_season(item_season_str, season_choice):
                    if season_choice == "Universal":
                        return True
                    if not isinstance(item_season_str, str):
                        return False
                    item_season_list = [s.strip() for s in item_season_str.split(',')]
                    # True if the item is "Universal" or contains the chosen season
                    return ("Universal" in item_season_list) or (season_choice in item_season_list)

                def matches_style(item_style_str, style_choice):
                    if style_choice == "Universal":
                        return True
                    if not isinstance(item_style_str, str):
                        return False
                    item_style_list = [s.strip() for s in item_style_str.split(',')]
                    # True if the item is "Universal" or contains the chosen style
                    return ("Universal" in item_style_list) or (style_choice in item_style_list)

                # 2) Filter entire wardrobe by chosen season & style
                valid_items = wardrobe_df[
                    wardrobe_df['Season'].apply(lambda x: matches_season(x, chosen_season)) &
                    wardrobe_df['Style'].apply(lambda x: matches_style(x, chosen_style))
                ]

                if valid_items.empty:
                    st.error("No items match your chosen Season/Style. Please add more clothes or change filters.")
                else:
                    # 3) Randomly pick one item from each category, if available
                    upper_df = valid_items[valid_items['Category'] == 'Upper body']
                    lower_df = valid_items[valid_items['Category'] == 'Lower body']
                    foot_df  = valid_items[valid_items['Category'] == 'Footwear']

                    if upper_df.empty or lower_df.empty or foot_df.empty:
                        st.error("Not enough items in all categories to build a complete outfit!")
                    else:
                        upper_item = upper_df.sample(1).iloc[0]
                        lower_item = lower_df.sample(1).iloc[0]
                        shoe_item  = foot_df.sample(1).iloc[0]

                        # 4) Generate a new Combination_ID
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

                        # 5) Save to session for display & rating
                        st.session_state.current_combination = {
                            'Combination_ID': combination_id,
                            'Upper_Body': upper_item['Model'],
                            'Lower_Body': lower_item['Model'],
                            'Footwear': shoe_item['Model'],
                            'Season_Match': [chosen_season],  # or you can store all matched
                            'Style_Match': [chosen_style]
                        }
                        st.session_state.show_rating = True

            except Exception as e:
                st.error("Error generating outfit combination: " + str(e))

        # ========== Display the newly generated combination + rating form ==========
        if st.session_state.show_rating and st.session_state.current_combination:
            combo = st.session_state.current_combination

            # Fetch details from local DF
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

            with st.form("rating_form"):
                rating = st.slider("Rate this combination (0-10)", 0, 10, 5)
                save_rating = st.form_submit_button("Save Rating")
                if save_rating:
                    new_combination = combo.copy()
                    new_combination['Rating'] = rating
                    st.session_state.new_combination = new_combination
                    save_data()

# ---------------------------------------------------------------------------
# PAGE: WARDROBE
# ---------------------------------------------------------------------------
elif page == "Wardrobe":
    st.title("Your Wardrobe")

    st.sidebar.subheader("Filter Options")
    filter_category = st.sidebar.multiselect(
        "Category",
        wardrobe_df['Category'].unique().tolist() if not wardrobe_df.empty else []
    )
    filter_style = st.sidebar.multiselect("Style", get_unique_values(wardrobe_df, 'Style'))
    filter_season = st.sidebar.multiselect("Season", get_unique_values(wardrobe_df, 'Season'))

    filtered_df = wardrobe_df.copy()
    if filter_category:
        filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]

    if filter_style and 'Style' in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df['Style'].apply(
                lambda x: any(s in str(x) for s in filter_style) if pd.notna(x) else False
            )
        ]

    if filter_season and 'Season' in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df['Season'].apply(
                lambda x: any(s in str(x) for s in filter_season) if pd.notna(x) else False
            )
        ]

    if not filtered_df.empty:
        st.dataframe(filtered_df)
        st.write(f"Showing {len(filtered_df)} of {len(wardrobe_df)} items")
    else:
        st.info("No items in your wardrobe yet. Add some from the Main page!")

# ---------------------------------------------------------------------------
# PAGE: COMBINATIONS
# ---------------------------------------------------------------------------
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

    # st.subheader("Delete Duplicate Combinations")
    # if not combinations_df.empty:
    #     def get_combination_signature(row):
    #         upper = row.get("Upper_Body", "")
    #         lower = row.get("Lower_Body", "")
    #         season_vals = row.get("Season_Match", [])
    #         style_vals = row.get("Style_Match", [])
    #
    #         if isinstance(season_vals, str):
    #             season_vals = [s.strip() for s in season_vals.split(',')]
    #         if isinstance(style_vals, str):
    #             style_vals = [s.strip() for s in style_vals.split(',')]
    #
    #         season_sig = "|".join(sorted(season_vals))
    #         style_sig = "|".join(sorted(style_vals))
    #         return f"{upper}-{lower}-{season_sig}-{style_sig}"
    #
    #     combinations_df["signature"] = combinations_df.apply(get_combination_signature, axis=1)
    #     duplicate_groups = combinations_df.groupby("signature").filter(lambda x: len(x) > 1)
    #
    #     if duplicate_groups.empty:
    #         st.write("No duplicate combinations found.")
    #     else:
    #         st.write("The following duplicate groups were found:")
    #         for sig, group in combinations_df.groupby("signature"):
    #             if len(group) > 1:
    #                 st.write(f"**Signature:** {sig}")
    #                 st.dataframe(group)
    #                 if st.button(f"Delete duplicates for signature {sig}"):
    #                     duplicates = group.sort_values("id").iloc[1:]
    #                     for rid in duplicates["id"]:
    #                         try:
    #                             combinations_table.delete(rid)
    #                             st.write(f"Deleted record ID: {rid}")
    #                         except Exception as e:
    #                             st.error(f"Error deleting record {rid}: {e}")
    #                     st.success("Duplicates deleted for this group. Please refresh the page.")
    # else:
    #     st.write("No combination records available.")

# ---------------------------------------------------------------------------
# PAGE: ANALYSIS
# ---------------------------------------------------------------------------
elif page == "Analysis":
    st.title("Wardrobe Analysis")

    if wardrobe_df.empty:
        st.info("Add some items to your wardrobe to see analysis!")
    else:
        viz_type = st.selectbox("Select Visualization Type", ["Pie Chart", "Bar Chart", "Line Chart", "Scatter Plot"])

        if viz_type in ["Pie Chart", "Bar Chart", "Line Chart"]:
            dimension = st.selectbox("Select Data Dimension", ["Category", "Type", "Style", "Color", "Season"])
            fig, ax = plt.subplots(figsize=(10, 6))

            if viz_type == "Pie Chart":
                counts = wardrobe_df[dimension].value_counts()
                ax.pie(counts, labels=counts.index, autopct='%1.1f%%')
                ax.set_title(f'Distribution of {dimension}')

            elif viz_type == "Bar Chart":
                counts = wardrobe_df[dimension].value_counts()
                counts.plot(kind='bar', ax=ax)
                ax.set_title(f'{dimension} Counts')
                ax.set_xlabel(dimension)
                ax.set_ylabel('Count')

            elif viz_type == "Line Chart":
                if dimension == "Type":
                    type_counts = wardrobe_df[dimension].value_counts().sort_index()
                    type_counts.plot(kind='line', marker='o', ax=ax)
                else:
                    wardrobe_df[dimension].value_counts().plot(kind='line', marker='o', ax=ax)
                ax.set_title(f'Trend of {dimension}')
                ax.set_xlabel(dimension)
                ax.set_ylabel('Count')

            st.pyplot(fig)

        elif viz_type == "Scatter Plot":
            colA, colB = st.columns(2)
            with colA:
                x_dimension = st.selectbox("X-Axis", ["Category", "Type", "Style", "Color", "Season"])
            with colB:
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
            x_cats = wardrobe_df[x_dimension].unique()
            y_cats = wardrobe_df[y_dimension].unique()
            ax.set_xticks(range(len(x_cats)))
            ax.set_yticks(range(len(y_cats)))
            ax.set_xticklabels(x_cats)
            ax.set_yticklabels(y_cats)
            ax.set_xlabel(x_dimension)
            ax.set_ylabel(y_dimension)
            ax.set_title(f'{y_dimension} vs {x_dimension}')
            st.pyplot(fig)

        # If we have combinations, show rating analysis
        if not combinations_df.empty:
            st.subheader("Combination Ratings Analysis")
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(combinations_df['Rating'], bins=11, kde=True, ax=ax)
            ax.set_title('Distribution of Outfit Ratings')
            ax.set_xlabel('Rating')
            ax.set_ylabel('Count')
            st.pyplot(fig)

            # Top rated
            st.subheader("Top Rated Combinations")
            top_combinations = combinations_df.sort_values('Rating', ascending=False).head(5)
            st.dataframe(top_combinations)

# ---------------------------------------------------------------------------
# PAGE: ABOUT
# ---------------------------------------------------------------------------
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
    """)

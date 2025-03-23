import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from airtable  import airtable
import random
import os

# Set page config
st.set_page_config(page_title="wea-rCloth", layout="wide")

# Initialize session state
if 'current_combination' not in st.session_state:
    st.session_state.current_combination = None


# # Functions for file operations
# def load_data():
#     try:
#         wardrobe_df = pd.read_csv('wardrobe_data.csv')
#         combinations_df = pd.read_csv('combinations_data.csv')
#     except FileNotFoundError:
#         wardrobe_df = pd.DataFrame(columns=[
#             'Model', 'Category', 'Type', 'TypeNumber', 'Style', 'Color', 'Season'
#         ])
#         combinations_df = pd.DataFrame(columns=[
#             'CombinationID', 'UpperBody', 'LowerBody', 'Footwear', 'Season', 'Style', 'Rating'
#         ])
#     return wardrobe_df, combinations_df
#
#
# def save_data(wardrobe_df, combinations_df):
#     wardrobe_df.to_csv('wardrobe_data.csv', index=False)
#     combinations_df.to_csv('combinations_data.csv', index=False)


# Initialize Airtable tables
wardrobe_table = airtable.Airtable(base_id = 'appdgbGbEz1Dtynvg', api_key = 'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea', table_name = 'wardrobe_data')
combinations_table = airtable.Airtable(base_id = 'appdgbGbEz1Dtynvg', api_key = 'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea', table_name = 'combinations_data')


def load_data():
    """Fetch data from Airtable instead of local CSVs."""
    wardrobe_records = wardrobe_table.all()
    combinations_records = combinations_table.all()

    wardrobe_df = pd.DataFrame([rec['fields'] for rec in wardrobe_records]) if wardrobe_records else pd.DataFrame()
    combinations_df = pd.DataFrame(
        [rec['fields'] for rec in combinations_records]) if combinations_records else pd.DataFrame()

    return wardrobe_df, combinations_df


def save_data(wardrobe_df, combinations_df):
    """Save data to Airtable instead of CSV files."""
    for _, row in wardrobe_df.iterrows():
        wardrobe_table.create(row.to_dict())
    for _, row in combinations_df.iterrows():
        combinations_table.create(row.to_dict())


# Load data
wardrobe_df, combinations_df = load_data()

# Sidebar navigation
st.sidebar.title("wea-rCloth")
page = st.sidebar.selectbox("Navigation", ["Main", "Wardrobe", "Analysis", "About"])

if page == "Main":
    st.title("wea-rCloth - Your Smart Wardrobe Assistant")

    # Two columns layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Add New Clothing Item")

        # Form for adding new clothing
        with st.form("new_cloth_form"):
            category = st.selectbox("Category", ["Upper body", "Lower body", "Footwear"])

            # Type selection based on category
            type_options = {
                "Upper body": ["1-Shirt", "2-T-shirt", "3-Sweater", "4-Jacket", "5-Coat"],
                "Lower body": ["1-Pants", "2-Jeans", "3-Shorts", "4-Skirt"],
                "Footwear": ["1-Sneakers", "2-Boots", "3-Sandals", "4-Formal shoes"]
            }
            cloth_type = st.selectbox("Type", type_options[category])

            # Get the next type number
            type_prefix = cloth_type.split("-")[0]
            existing_items = wardrobe_df[(wardrobe_df['Category'] == category) &
                                         (wardrobe_df['Type'] == cloth_type)]
            next_number = len(existing_items) + 1
            type_number = f"{next_number:02d}"

            style = st.selectbox("Style", ["Casual", "Formal", "Trendy", "Universal"])
            color = st.text_input("Color")
            season = st.selectbox("Season", ["Winter", "Vernal", "Summer", "Autumn", "Universal"])

            # Auto-generate model name
            style_code = ''.join([s[0] for s in style.split()])
            season_code = ''.join([s[0] for s in season.split()])
            category_code = category.split()[0][0]
            model = f"{category_code}{type_prefix}{type_number}{style_code}{season_code}"

            st.write(f"Generated Model ID: {model}")

            submitted = st.form_submit_button("Add to Wardrobe")

            # In your form submit handler:
            if submitted:
                new_item = {
                    'Model': model,
                    'Category': category,
                    'Type': cloth_type,
                    'TypeNumber': type_number,
                    'Style': style,
                    'Color': color,
                    'Season': season
                }
                wardrobe_df = pd.concat([wardrobe_df, pd.DataFrame([new_item])], ignore_index=True)
                st.session_state.new_item = new_item  # Store the new item
                save_data(wardrobe_df, combinations_df)

    with col2:
        st.subheader("Generate Outfit Combination")

        if st.button("Generate New Combination"):
            # Check if we have enough items
            categories = ["Upper body", "Lower body", "Footwear"]
            has_all_categories = all(len(wardrobe_df[wardrobe_df['Category'] == cat]) > 0 for cat in categories)

            if has_all_categories:
                # Get one item from each category
                upper = wardrobe_df[wardrobe_df['Category'] == 'Upper body'].sample(1)
                lower = wardrobe_df[wardrobe_df['Category'] == 'Lower body'].sample(1)
                footwear = wardrobe_df[wardrobe_df['Category'] == 'Footwear'].sample(1)

                # Determine season compatibility
                seasons = []
                for item in [upper, lower, footwear]:
                    if item['Season'].values[0] != 'Universal':
                        seasons.append(item['Season'].values[0][0])  # First letter of season

                # Create combined season code
                if not seasons:
                    combined_season = 'U'  # Universal
                else:
                    combined_season = ''.join(sorted(set(seasons)))

                # Determine combined style
                styles = []
                for item in [upper, lower, footwear]:
                    if item['Style'].values[0] != 'Universal':
                        styles.append(item['Style'].values[0][0].lower())  # First letter of style

                if not styles:
                    combined_style = 'u'  # Universal
                else:
                    combined_style = ''.join(sorted(set(styles)))

                # Create combination ID
                combination_id = f"{upper['Model'].values[0]}_{lower['Model'].values[0]}_{footwear['Model'].values[0]}"

                # Store current combination in session state
                st.session_state.current_combination = {
                    'CombinationID': combination_id,
                    'UpperBody': upper['Model'].values[0],
                    'LowerBody': lower['Model'].values[0],
                    'Footwear': footwear['Model'].values[0],
                    'Season': combined_season,
                    'Style': combined_style
                }

                # Display the combination
                st.subheader("Your Outfit Combination:")
                st.write(
                    f"**Upper Body:** {upper['Model'].values[0]} - {upper['Type'].values[0]} ({upper['Color'].values[0]})")
                st.write(
                    f"**Lower Body:** {lower['Model'].values[0]} - {lower['Type'].values[0]} ({lower['Color'].values[0]})")
                st.write(
                    f"**Footwear:** {footwear['Model'].values[0]} - {footwear['Type'].values[0]} ({footwear['Color'].values[0]})")
                st.write(f"**Season Compatibility:** {combined_season}")
                st.write(f"**Style Compatibility:** {combined_style}")

                # Rating slider
                rating = st.slider("Rate this combination (0-10)", 0, 10, 5)

                if st.button("Save Rating"):
                    # Check if combination already exists
                    exists = combination_id in combinations_df['CombinationID'].values

                    if exists:
                        # Update existing combination
                        combinations_df.loc[combinations_df['CombinationID'] == combination_id, 'Rating'] = rating
                    else:
                        # Add new combination
                        new_combination = st.session_state.current_combination.copy()
                        new_combination['Rating'] = rating
                        combinations_df = pd.concat([combinations_df, pd.DataFrame([new_combination])],
                                                    ignore_index=True)

                    save_data(wardrobe_df, combinations_df)
                    st.success(f"Saved rating ({rating}/10) for this combination!")
            else:
                st.error("You need at least one item in each category to generate a combination!")

elif page == "Wardrobe":
    st.title("Your Wardrobe")

    # Filter options
    st.sidebar.subheader("Filter Options")
    filter_category = st.sidebar.multiselect("Category",
                                             wardrobe_df['Category'].unique().tolist() if not wardrobe_df.empty else [])
    filter_style = st.sidebar.multiselect("Style",
                                          wardrobe_df['Style'].unique().tolist() if not wardrobe_df.empty else [])
    filter_season = st.sidebar.multiselect("Season",
                                           wardrobe_df['Season'].unique().tolist() if not wardrobe_df.empty else [])

    # Apply filters
    filtered_df = wardrobe_df.copy()
    if filter_category:
        filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]
    if filter_style:
        filtered_df = filtered_df[filtered_df['Style'].isin(filter_style)]
    if filter_season:
        filtered_df = filtered_df[filtered_df['Season'].isin(filter_season)]

    # Display wardrobe items
    if not filtered_df.empty:
        st.dataframe(filtered_df)
        st.write(f"Showing {len(filtered_df)} of {len(wardrobe_df)} items")
    else:
        st.info("No items in your wardrobe yet. Add some from the Main page!")

elif page == "Analysis":
    st.title("Wardrobe Analysis")

    if wardrobe_df.empty:
        st.info("Add some items to your wardrobe to see analysis!")
    else:
        # Select visualization type
        viz_type = st.selectbox("Select Visualization Type", ["Pie Chart", "Bar Chart", "Line Chart", "Scatter Plot"])

        if viz_type in ["Pie Chart", "Bar Chart", "Line Chart"]:
            # Select data dimension
            dimension = st.selectbox("Select Data Dimension",
                                     ["Category", "Type", "Style", "Color", "Season"])

            # Create figure
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
                # For line chart, use chronological ordering if possible
                if dimension == "Type":
                    # Extract type number for ordering
                    type_counts = wardrobe_df[dimension].value_counts().sort_index()
                    type_counts.plot(kind='line', marker='o', ax=ax)
                else:
                    wardrobe_df[dimension].value_counts().plot(kind='line', marker='o', ax=ax)
                ax.set_title(f'Trend of {dimension}')
                ax.set_xlabel(dimension)
                ax.set_ylabel('Count')

            st.pyplot(fig)

        elif viz_type == "Scatter Plot":
            # For scatter plot, need two dimensions
            col1, col2 = st.columns(2)

            with col1:
                x_dimension = st.selectbox("X-Axis", ["Category", "Type", "Style", "Color", "Season"])

            with col2:
                y_dimension = st.selectbox("Y-Axis", ["Category", "Type", "Style", "Color", "Season"])

            # Need to encode categorical variables numerically for scatter plot
            fig, ax = plt.subplots(figsize=(10, 6))

            # Create encoded versions for plotting
            wardrobe_encoded = wardrobe_df.copy()
            for dim in [x_dimension, y_dimension]:
                categories = wardrobe_df[dim].unique()
                category_map = {cat: i for i, cat in enumerate(categories)}
                wardrobe_encoded[f"{dim}_encoded"] = wardrobe_df[dim].map(category_map)

            # Create scatter plot with categorical encoding
            scatter = ax.scatter(
                wardrobe_encoded[f"{x_dimension}_encoded"],
                wardrobe_encoded[f"{y_dimension}_encoded"],
                c=wardrobe_encoded[f"{x_dimension}_encoded"],
                alpha=0.6
            )

            # Set tick labels to original categories
            x_categories = wardrobe_df[x_dimension].unique()
            y_categories = wardrobe_df[y_dimension].unique()
            ax.set_xticks(range(len(x_categories)))
            ax.set_yticks(range(len(y_categories)))
            ax.set_xticklabels(x_categories)
            ax.set_yticklabels(y_categories)

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

            # Top rated combinations
            st.subheader("Top Rated Combinations")
            top_combinations = combinations_df.sort_values('Rating', ascending=False).head(5)
            st.dataframe(top_combinations)

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

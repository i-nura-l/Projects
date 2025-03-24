import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pyairtable import Table
import random
import os

# Set page config
st.set_page_config(page_title="wea-rCloth", layout="wide")

# Initialize session state
if 'current_combination' not in st.session_state:
    st.session_state.current_combination = None
if 'show_rating' not in st.session_state:
    st.session_state.show_rating = False
if 'custom_types' not in st.session_state:
    st.session_state.custom_types = {
        "Upper body": ["01-Shirt", "02-TShirt", "03-Sweater", "04-Jacket", "05-Coat",
                       "06-Hoodie", "07-Polo", "08-Vest", "09-Cardigan", "10-Blouse",
                       "11-Turtleneck", "12-TankTop", "13-Sweatshirt", "14-Blazer",
                       "15-CropTop", "16-Tunic", "17-Bodysuit", "18-Flannel", "19-Windbreaker"],
        "Lower body": [
            "01-Jeans", "02-Trousers", "03-Shorts", "04-Skirt",
            "05-Sweatpants", "06-Leggings", "07-CargoPants", "08-Chinos",
            "09-CutOffs", "10-WideLeg"
        ],
        "Footwear": [
            "01-Sneakers", "02-Formal", "03-Boots", "04-Sandals",
            "05-Loafers", "06-Moccasins", "07-Espadrilles", "08-SlipOns",
            "09-HikingBoots", "10-RunningShoes"]
    }
if 'form_category' not in st.session_state:
    st.session_state.form_category = "Upper body"
if 'type_options' not in st.session_state:
    st.session_state.type_options = st.session_state.custom_types["Upper body"]

# Initialize Airtable tables
wardrobe_table = Table('patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
                       'appdgbGbEz1Dtynvg', 'wardrobe_data')
combinations_table = Table('patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
                           'appdgbGbEz1Dtynvg', 'combinations_data')


def load_data():
    """Fetch data from Airtable instead of local CSVs."""
    wardrobe_records = wardrobe_table.all()
    combinations_records = combinations_table.all()

    # Create DataFrames from records
    wardrobe_df = pd.DataFrame([rec['fields'] for rec in wardrobe_records if
                                'fields' in rec and rec['fields']]) if wardrobe_records else pd.DataFrame()
    combinations_df = pd.DataFrame([rec['fields'] for rec in combinations_records if
                                    'fields' in rec and rec['fields']]) if combinations_records else pd.DataFrame()

    # Reset index to start from 1
    if not wardrobe_df.empty:
        wardrobe_df = wardrobe_df.reset_index(drop=True)
        wardrobe_df.index = wardrobe_df.index + 1

    if not combinations_df.empty:
        combinations_df = combinations_df.reset_index(drop=True)
        combinations_df.index = combinations_df.index + 1

    # Ensure all expected columns exist
    expected_columns = ['Model', 'Category', 'Type', 'Style', 'Color', 'Season']
    for col in expected_columns:
        if col not in wardrobe_df.columns:
            wardrobe_df[col] = None

    # Convert multi-select fields to string representation if needed
    multi_select_columns = ['Style', 'Season']
    for col in multi_select_columns:
        if col in wardrobe_df.columns:
            # Convert lists to strings if they are lists
            wardrobe_df[col] = wardrobe_df[col].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )

    return wardrobe_df, combinations_df


def get_unique_values(df, column):
    """Get unique values from a column that may contain comma-separated values."""
    if df is None or df.empty or column not in df.columns:
        return []

    # Handle both list values and string values
    all_values = set()

    for value in df[column].dropna():
        if isinstance(value, list):
            # If it's still a list, add each item
            for item in value:
                all_values.add(item)
        elif isinstance(value, str):
            # If it's a string that might be comma-separated
            if ',' in value:
                for item in value.split(','):
                    all_values.add(item.strip())
            else:
                all_values.add(value)

    return sorted(list(all_values))

def save_data(wardrobe_df, combinations_df):
    """Save data to Airtable instead of CSV files."""
    # Save new clothing item if available
    if 'new_item' in st.session_state:
        new_item = st.session_state.new_item
        row_dict = {}
        for key, value in new_item.items():
            # Skip the 'TypeNumber' field
            if key == 'TypeNumber':
                continue
            # If value is a list (e.g., multi-select fields)
            if isinstance(value, list):
                if value:  # only add if list is not empty
                    row_dict[key] = value
            else:
                # For non-list values, check if not missing
                if pd.notna(value):
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
        new_combination = st.session_state.new_combination
        row_dict = {}
        for key, value in new_combination.items():
            if isinstance(value, list):
                if value:
                    row_dict[key] = value
            else:
                if pd.notna(value):
                    row_dict[key] = value

        try:
            combinations_table.create(row_dict)
            st.success("Saved rating for this combination!")
            del st.session_state.new_combination
            st.session_state.show_rating = False  # Reset rating UI state
        except Exception as e:
            st.error(f"Error saving combination to Airtable: {str(e)}")
            st.error(f"Data being sent: {row_dict}")


# Function to update type options based on selected category
def update_type_options():
    category = st.session_state.category_select
    st.session_state.form_category = category
    # Update the type options based on the selected category
    if category in st.session_state.custom_types:
        st.session_state.type_options = st.session_state.custom_types[category]
    else:
        st.session_state.type_options = []


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

        # Category selection outside the form
        category = st.selectbox(
            "Category",
            ["Upper body", "Lower body", "Footwear"],
            key="category_select",
            on_change=update_type_options
        )

        # Form for adding new clothing
        with st.form("new_cloth_form"):
            # Use the stored category value inside the form
            cloth_type = st.selectbox("Type", st.session_state.type_options)

            style = st.multiselect("Style", ["Casual", "Formal", "Trendy", "Universal"], default=["Casual"])
            color = st.text_input("Color")
            season = st.multiselect("Season", ["Winter", "Vernal", "Summer", "Autumn", "Universal"], default=["Universal"])

            # Get the number of items of this type
            existing_items = wardrobe_df[(wardrobe_df['Category'] == st.session_state.form_category) &
                                         (wardrobe_df['Type'] == cloth_type)]
            next_number = len(existing_items) + 1 if not existing_items.empty else 1

            # Auto-generate model name
            style_code = ''.join([s[0] for s in style]) if style else ''
            season_code = ''.join([s[0] for s in season]) if season else ''
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
                    'Style': style,
                    'Color': color,
                    'Season': season
                }
                wardrobe_df = pd.concat([wardrobe_df, pd.DataFrame([new_item])], ignore_index=True)
                st.session_state.new_item = new_item
                save_data(wardrobe_df, combinations_df)

    with col2:
        st.subheader("Generate Outfit Combination")
        try:
            if st.button("Generate New Combination"):
                # Step 1: Select an Upper Body item
                upper_df = wardrobe_df[wardrobe_df['Category'] == 'Upper body']
                if upper_df.empty:
                    st.error("No Upper Body items available!")
                else:
                    upper = upper_df.sample(1)
                    # Ensure Season and Style are valid strings; default to "Universal" if missing
                    upper_season_val = upper['Season'].values[0]
                    upper_season_str = upper_season_val if isinstance(upper_season_val, str) and pd.notna(
                        upper_season_val) else "Universal"

                    upper_style_val = upper['Style'].values[0]
                    upper_style_str = upper_style_val if isinstance(upper_style_val, str) and pd.notna(
                        upper_style_val) else "Universal"

                    # Convert comma-separated string to a list (e.g., "Summer, Spring" -> ["Summer", "Spring"])
                    upper_seasons = [s.strip() for s in upper_season_str.split(',')]
                    upper_styles = [s.strip() for s in upper_style_str.split(',')]


                    # Helper functions with error-checking
                    def matches_season(candidate_season_str, upper_seasons):
                        if not isinstance(candidate_season_str, str):
                            return False
                        candidate_seasons = [s.strip() for s in candidate_season_str.split(',')]
                        if "Universal" in candidate_seasons:
                            return True
                        return any(s in upper_seasons for s in candidate_seasons)


                    def matches_style(candidate_style_str, upper_styles):
                        if not isinstance(candidate_style_str, str):
                            return False
                        candidate_styles = [s.strip() for s in candidate_style_str.split(',')]
                        if "Universal" in candidate_styles:
                            return True
                        return any(s in upper_styles for s in candidate_styles)


                    # Step 2: Filter Lower Body and Footwear items by Season
                    lower_df = wardrobe_df[wardrobe_df['Category'] == 'Lower body']
                    footwear_df = wardrobe_df[wardrobe_df['Category'] == 'Footwear']

                    lower_filtered = lower_df[lower_df['Season'].apply(lambda x: matches_season(x, upper_seasons))]
                    footwear_filtered = footwear_df[
                        footwear_df['Season'].apply(lambda x: matches_season(x, upper_seasons))]

                    # Fallback if no candidates after season filtering
                    if lower_filtered.empty:
                        lower_filtered = lower_df
                    if footwear_filtered.empty:
                        footwear_filtered = footwear_df

                    # Step 3: Optionally enforce strict style matching
                    enforce_style = True  # Set to False to disable strict style matching
                    if enforce_style:
                        lower_filtered = lower_filtered[
                            lower_filtered['Style'].apply(lambda x: matches_style(x, upper_styles))]
                        footwear_filtered = footwear_filtered[
                            footwear_filtered['Style'].apply(lambda x: matches_style(x, upper_styles))]
                        # Fallback to season filtering if style filtering leaves no candidates
                        if lower_filtered.empty:
                            lower_filtered = lower_df[
                                lower_df['Season'].apply(lambda x: matches_season(x, upper_seasons))]
                        if footwear_filtered.empty:
                            footwear_filtered = footwear_df[
                                footwear_df['Season'].apply(lambda x: matches_season(x, upper_seasons))]

                    # Step 4: Randomly select one Lower Body and one Footwear item
                    lower = lower_filtered.sample(1)
                    footwear = footwear_filtered.sample(1)

                    # Create a combination ID
                    combination_id = f"{upper['Model'].values[0]}_{lower['Model'].values[0]}_{footwear['Model'].values[0]}"

                    # Save the combination in session state
                    st.session_state.current_combination = {
                        'Combination_ID': combination_id,
                        'Upper_Body': upper['Model'].values[0],
                        'Lower_Body': lower['Model'].values[0],
                        'Footwear': footwear['Model'].values[0],
                        'Season_Match': upper_season_str,
                        'Style_Match': upper_style_str
                    }
                    st.session_state.show_rating = True
        except Exception as e:
            st.error("Error generating outfit combination: " + str(e))

        # Display the combination if available
        if st.session_state.show_rating and st.session_state.current_combination:

            combination = st.session_state.current_combination

            # Get item details
            upper_details = wardrobe_df[wardrobe_df['Model'] == combination['Upper_Body']]
            lower_details = wardrobe_df[wardrobe_df['Model'] == combination['Lower_Body']]
            footwear_details = wardrobe_df[wardrobe_df['Model'] == combination['Footwear']]

            # Display the combination
            st.subheader("Your Outfit Combination:")

            if not upper_details.empty:
                st.write(
                    f"**Upper Body:** {upper_details['Model'].values[0]} - {upper_details['Type'].values[0]} ({upper_details['Color'].values[0]})")
            else:
                st.write(f"**Upper Body:** {combination['Upper_Body']}")

            if not lower_details.empty:
                st.write(
                    f"**Lower Body:** {lower_details['Model'].values[0]} - {lower_details['Type'].values[0]} ({lower_details['Color'].values[0]})")
            else:
                st.write(f"**Lower Body:** {combination['Lower_Body']}")

            if not footwear_details.empty:
                st.write(
                    f"**Footwear:** {footwear_details['Model'].values[0]} - {footwear_details['Type'].values[0]} ({footwear_details['Color'].values[0]})")
            else:
                st.write(f"**Footwear:** {combination['Footwear']}")

            st.write(f"**Season Compatibility:** {combination['Season_Match']}")
            st.write(f"**Style Compatibility:** {combination['Style_Match']}")

            # Rating section with separate form
            with st.form("rating_form"):
                rating = st.slider("Rate this combination (0-10)", 0, 10, 5)
                save_rating = st.form_submit_button("Save Rating")

                if save_rating:
                    # Add rating to the combination
                    new_combination = combination.copy()
                    new_combination['Rating'] = rating

                    st.session_state.new_combination = new_combination
                    save_data(wardrobe_df, combinations_df)

elif page == "Wardrobe":
    st.title("Your Wardrobe")

    # Filter options
    st.sidebar.subheader("Filter Options")

    filter_category = st.sidebar.multiselect(
        "Category",
        wardrobe_df['Category'].unique().tolist() if not wardrobe_df.empty and 'Category' in wardrobe_df.columns else []
    )

    filter_style = st.sidebar.multiselect("Style", get_unique_values(wardrobe_df, 'Style'))

    filter_season = st.sidebar.multiselect("Season", get_unique_values(wardrobe_df, 'Season'))

    # Apply filters
    filtered_df = wardrobe_df.copy()

    if filter_category:
        filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]

    if filter_style:
        # For multi-select fields, we need to check if any of the selected values are in the field
        if not filtered_df.empty and 'Style' in filtered_df.columns:
            mask = filtered_df['Style'].apply(
                lambda x: any(style in str(x) for style in filter_style) if pd.notna(x) else False
            )
            filtered_df = filtered_df[mask]

    if filter_season:
        # Same approach for Season
        if not filtered_df.empty and 'Season' in filtered_df.columns:
            mask = filtered_df['Season'].apply(
                lambda x: any(season in str(x) for season in filter_season) if pd.notna(x) else False
            )
            filtered_df = filtered_df[mask]
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
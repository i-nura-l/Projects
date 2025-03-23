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

    wardrobe_df = pd.DataFrame([rec['fields'] for rec in wardrobe_records]) if wardrobe_records else pd.DataFrame()
    combinations_df = pd.DataFrame(
        [rec['fields'] for rec in combinations_records]) if combinations_records else pd.DataFrame()

    # Load custom types from existing wardrobe data
    if not wardrobe_df.empty and 'Type' in wardrobe_df.columns and 'Category' in wardrobe_df.columns:
        # Group types by category
        for category in wardrobe_df['Category'].unique():
            types = wardrobe_df[wardrobe_df['Category'] == category]['Type'].unique().tolist()
            # Update custom types only if we found some
            if types:
                # Merge with existing types without duplicates
                if category in st.session_state.custom_types:
                    all_types = list(set(st.session_state.custom_types[category] + types))
                    st.session_state.custom_types[category] = sorted(all_types)
                else:
                    st.session_state.custom_types[category] = sorted(types)

    return wardrobe_df, combinations_df


def save_data(wardrobe_df, combinations_df):
    """Save data to Airtable instead of CSV files."""
    if 'new_item' in st.session_state:
        new_item = st.session_state.new_item

        # Remove any fields that don't exist in Airtable
        # Ensure field names match exactly what's in Airtable
        row_dict = {}
        for k, v in new_item.items():
            if k != 'TypeNumber' and pd.notna(v):  # Skip TypeNumber field
                row_dict[k] = v

        # Convert Style field from comma-separated string to list for Airtable multi-select
        if 'Style' in row_dict and isinstance(row_dict['Style'], str):
            row_dict['Style'] = [style.strip() for style in row_dict['Style'].split(',')]

        # Color
        if 'Color' in row_dict and isinstance(row_dict['Color'], str):
            row_dict['Color'] = [color.strip() for color in row_dict['Color'].split(',')]


        # Similarly for Season if it's also a multi-select field
        if 'Season' in row_dict and isinstance(row_dict['Season'], str):
            row_dict['Season'] = [season.strip() for season in row_dict['Season'].split(',')]

        # Convert any numpy data types to Python native types
        for key, value in row_dict.items():
            if hasattr(value, 'item'):
                row_dict[key] = value.item()

        try:
            wardrobe_table.create(row_dict)
            st.success(f"Added {row_dict.get('Model', 'item')} to your wardrobe!")
            del st.session_state.new_item
        except Exception as e:
            st.error(f"Error saving to Airtable: {str(e)}")
            st.error(f"Problematic data: {row_dict}")  # Add this to see the exact data being sent
            st.error("Check if all field names match your Airtable schema")

    # For combinations
    if 'new_combination' in st.session_state:
        new_combination = st.session_state.new_combination

        # Ensure we're using the correct field names for Airtable
        row_dict = {}
        for k, v in new_combination.items():
            if pd.notna(v):
                row_dict[k] = v

        # Convert any numpy data types to Python native types
        for key, value in row_dict.items():
            if hasattr(value, 'item'):
                row_dict[key] = value.item()

        try:
            combinations_table.create(row_dict)
            st.success(f"Saved rating for this combination!")
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

            style = st.selectbox("Style", ["Casual", "Formal", "Trendy", "Universal"])
            color = st.text_input("Color")
            season = st.selectbox("Season", ["Winter", "Vernal", "Summer", "Autumn", "Universal"])

            # Get the number of items of this type
            existing_items = wardrobe_df[(wardrobe_df['Category'] == st.session_state.form_category) &
                                         (wardrobe_df['Type'] == cloth_type)]
            next_number = len(existing_items) + 1 if not existing_items.empty else 1

            # Auto-generate model name
            style_code = ''.join([s[0] for s in style.split()])
            season_code = ''.join([s[0] for s in season.split()])
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

    # In the Main page section where you handle outfit generation
    with col2:
        st.subheader("Generate Outfit Combination")

        # Add some filtering options for the generation
        with st.expander("Generation Options", expanded=False):
            # Allow filtering by season
            season_filter = st.multiselect(
                "Season Preference",
                ["Winter", "Vernal", "Summer", "Autumn", "Universal"],
                default=["Universal"]
            )

            # Allow filtering by style
            style_filter = st.multiselect(
                "Style Preference",
                ["Casual", "Formal", "Trendy", "Universal"],
                default=["Universal"]
            )

            # Option to try to match colors
            color_harmony = st.checkbox("Attempt Color Harmony", value=True)

        if st.button("Generate New Combination"):
            # Check if we have enough items
            categories = ["Upper body", "Lower body", "Footwear"]

            # Filter the wardrobe based on season and style if specified
            filtered_wardrobe = wardrobe_df.copy()

            if season_filter and 'Season' in filtered_wardrobe.columns:
                # Filter items that match any of the selected seasons
                season_mask = filtered_wardrobe['Season'].apply(
                    lambda x: any(season in x for season in season_filter) if isinstance(x, str) else False
                )
                filtered_wardrobe = filtered_wardrobe[season_mask]

            if style_filter and 'Style' in filtered_wardrobe.columns:
                # Filter items that match any of the selected styles
                style_mask = filtered_wardrobe['Style'].apply(
                    lambda x: any(style in x for style in style_filter) if isinstance(x, str) else False
                )
                filtered_wardrobe = filtered_wardrobe[style_mask]

            # Verify we have at least one item of each category after filtering
            has_all_categories = all(
                len(filtered_wardrobe[filtered_wardrobe['Category'] == cat]) > 0 for cat in categories)

            if has_all_categories:
                # Get one item from each category
                upper = filtered_wardrobe[filtered_wardrobe['Category'] == 'Upper body'].sample(1)
                lower = filtered_wardrobe[filtered_wardrobe['Category'] == 'Lower body'].sample(1)
                footwear = filtered_wardrobe[filtered_wardrobe['Category'] == 'Footwear'].sample(1)

                # If color harmony is enabled, try to select complementary colors
                if color_harmony and 'Color' in filtered_wardrobe.columns:
                    # First, select upper body item
                    upper = filtered_wardrobe[filtered_wardrobe['Category'] == 'Upper body'].sample(1)

                    # Then try to find lower body items with complementary colors
                    if 'Color' in upper.columns and not pd.isna(upper['Color'].values[0]):
                        upper_color = upper['Color'].values[0]

                        # Get lower body options
                        lower_options = filtered_wardrobe[filtered_wardrobe['Category'] == 'Lower body']

                        # Try to find items with complementary colors (simple implementation)
                        # This could be enhanced with a proper color theory algorithm
                        if not lower_options.empty:
                            # Prioritize neutral colors like black, white, grey, beige with any upper
                            neutral_colors = ['black', 'white', 'grey', 'gray', 'beige', 'tan', 'navy', 'charcoal']
                            neutral_mask = lower_options['Color'].apply(
                                lambda x: any(
                                    color.lower() in str(x).lower() for color in neutral_colors) if not pd.isna(
                                    x) else False
                            )

                            if neutral_mask.any():
                                lower = lower_options[neutral_mask].sample(1)
                            else:
                                # If no neutrals, just random selection
                                lower = lower_options.sample(1)

                        # Now select footwear that goes with both
                        footwear_options = filtered_wardrobe[filtered_wardrobe['Category'] == 'Footwear']

                        if not footwear_options.empty:
                            # Prioritize neutral colors for footwear
                            neutral_mask = footwear_options['Color'].apply(
                                lambda x: any(
                                    color.lower() in str(x).lower() for color in neutral_colors) if not pd.isna(
                                    x) else False
                            )

                            if neutral_mask.any():
                                footwear = footwear_options[neutral_mask].sample(1)
                            else:
                                # If no neutrals, just random selection
                                footwear = footwear_options.sample(1)
                    else:
                        # If no color data for upper, select randomly
                        lower = filtered_wardrobe[filtered_wardrobe['Category'] == 'Lower body'].sample(1)
                        footwear = filtered_wardrobe[filtered_wardrobe['Category'] == 'Footwear'].sample(1)

                # Determine season compatibility
                seasons = []
                for item in [upper, lower, footwear]:
                    if 'Season' in item and not pd.isna(item['Season'].values[0]):
                        item_seasons = item['Season'].values[0]
                        if isinstance(item_seasons, str):
                            if ',' in item_seasons:
                                # Handle comma-separated list
                                item_seasons_list = [s.strip() for s in item_seasons.split(',')]
                                seasons.extend(item_seasons_list)
                            else:
                                seasons.append(item_seasons.strip())
                        elif isinstance(item_seasons, list):
                            # Handle list of seasons
                            seasons.extend(item_seasons)

                # Create combined season code
                if not seasons:
                    combined_season = 'Universal'
                else:
                    # Get unique seasons and sort them
                    unique_seasons = sorted(set(seasons))
                    combined_season = ', '.join(unique_seasons)

                # Determine combined style
                styles = []
                for item in [upper, lower, footwear]:
                    if 'Style' in item and not pd.isna(item['Style'].values[0]):
                        item_styles = item['Style'].values[0]
                        if isinstance(item_styles, str):
                            if ',' in item_styles:
                                # Handle comma-separated list
                                item_styles_list = [s.strip() for s in item_styles.split(',')]
                                styles.extend(item_styles_list)
                            else:
                                styles.append(item_styles.strip())
                        elif isinstance(item_styles, list):
                            # Handle list of styles
                            styles.extend(item_styles)

                if not styles:
                    combined_style = 'Universal'
                else:
                    # Get unique styles and sort them
                    unique_styles = sorted(set(styles))
                    combined_style = ', '.join(unique_styles)

                # Count how many combinations we already have to generate a new ID
                combination_count = len(combinations_df) if not combinations_df.empty else 0
                new_combination_id = f"C{combination_count + 1:03d}"

                # Create combination ID with item models
                item_combination_id = f"{upper['Model'].values[0]}_{lower['Model'].values[0]}_{footwear['Model'].values[0]}"

                # Store current combination in session state
                st.session_state.current_combination = {
                    'Combination_ID': new_combination_id,
                    'Item_Combination': item_combination_id,
                    'Upper_Body': upper['Model'].values[0],
                    'Lower_Body': lower['Model'].values[0],
                    'Footwear': footwear['Model'].values[0],
                    'Season_Match': combined_season,
                    'Style_Match': combined_style
                }

                # Set flag to show rating UI
                st.session_state.show_rating = True
            else:
                st.error(
                    "Not enough items in your wardrobe with the selected filters. Please add more items or adjust your filters.")

        # Display the combination if available
        if st.session_state.show_rating and st.session_state.current_combination:

            combination = st.session_state.current_combination

            # Get item details
            upper_details = wardrobe_df[wardrobe_df['Model'] == combination['Upper_Body']]
            lower_details = wardrobe_df[wardrobe_df['Model'] == combination['Lower_Body']]
            footwear_details = wardrobe_df[wardrobe_df['Model'] == combination['Footwear']]

            # Display the combination
            st.subheader("Your Outfit Combination:")

            col_upper, col_lower, col_foot = st.columns(3)

            with col_upper:
                st.markdown("### Upper Body")
                if not upper_details.empty:
                    st.write(f"**Model:** {upper_details['Model'].values[0]}")
                    st.write(f"**Type:** {upper_details['Type'].values[0]}")
                    if 'Color' in upper_details.columns and not pd.isna(upper_details['Color'].values[0]):
                        st.write(f"**Color:** {upper_details['Color'].values[0]}")
                else:
                    st.write(f"**Model:** {combination['Upper_Body']}")
                    st.write("Item details not found")

            with col_lower:
                st.markdown("### Lower Body")
                if not lower_details.empty:
                    st.write(f"**Model:** {lower_details['Model'].values[0]}")
                    st.write(f"**Type:** {lower_details['Type'].values[0]}")
                    if 'Color' in lower_details.columns and not pd.isna(lower_details['Color'].values[0]):
                        st.write(f"**Color:** {lower_details['Color'].values[0]}")
                else:
                    st.write(f"**Model:** {combination['Lower_Body']}")
                    st.write("Item details not found")

            with col_foot:
                st.markdown("### Footwear")
                if not footwear_details.empty:
                    st.write(f"**Model:** {footwear_details['Model'].values[0]}")
                    st.write(f"**Type:** {footwear_details['Type'].values[0]}")
                    if 'Color' in footwear_details.columns and not pd.isna(footwear_details['Color'].values[0]):
                        st.write(f"**Color:** {footwear_details['Color'].values[0]}")
                else:
                    st.write(f"**Model:** {combination['Footwear']}")
                    st.write("Item details not found")

            st.markdown("---")
            st.write(f"**Combination ID:** {combination['Combination_ID']}")
            st.write(f"**Season Compatibility:** {combination['Season_Match']}")
            st.write(f"**Style Compatibility:** {combination['Style_Match']}")

            # Rating section with separate form
            with st.form("rating_form"):
                st.write("### Rate this combination")
                rating = st.slider("Rating (0-10)", 0, 10, 5)
                notes = st.text_area("Notes (optional)", "")
                save_rating = st.form_submit_button("Save Rating")

                if save_rating:
                    # Add rating to the combination
                    new_combination = combination.copy()
                    new_combination['Rating'] = rating
                    new_combination['Notes'] = notes

                    st.session_state.new_combination = new_combination
                    save_data(wardrobe_df, combinations_df)

            # Option to generate another combination
            if st.button("Generate Another Combination"):
                st.session_state.show_rating = False
                st.experimental_rerun()

elif page == "Wardrobe":
    st.title("Your Wardrobe")

    # Filter options
    st.sidebar.subheader("Filter Options")

    # Safe access to columns
    categories = wardrobe_df['Category'].astype(
        str).unique().tolist() if not wardrobe_df.empty and 'Category' in wardrobe_df.columns else []
    styles = wardrobe_df['Style'].astype(
        str).unique().tolist() if not wardrobe_df.empty and 'Style' in wardrobe_df.columns else []
    seasons = wardrobe_df['Season'].astype(
        str).unique().tolist() if not wardrobe_df.empty and 'Season' in wardrobe_df.columns else []

    filter_category = st.sidebar.multiselect("Category", categories)
    filter_style = st.sidebar.multiselect("Style", styles)
    filter_season = st.sidebar.multiselect("Season", seasons)

    # Apply filters
    filtered_df = wardrobe_df.copy()
    if filter_category and 'Category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]
    if filter_style and 'Style' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Style'].isin(filter_style)]
    if filter_season and 'Season' in filtered_df.columns:
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
        # Check if we have necessary columns
        required_columns = ["Category", "Type", "Style", "Color", "Season"]
        missing_columns = [col for col in required_columns if col not in wardrobe_df.columns]

        if missing_columns:
            st.warning(f"Missing columns in your data: {', '.join(missing_columns)}. Some visualizations may not work.")

        # Available columns for visualization
        available_columns = [col for col in required_columns if col in wardrobe_df.columns]

        if not available_columns:
            st.error("No suitable columns found for visualization")
        else:
            # Select visualization type
            viz_type = st.selectbox("Select Visualization Type",
                                    ["Pie Chart", "Bar Chart", "Line Chart", "Scatter Plot"])

            if viz_type in ["Pie Chart", "Bar Chart", "Line Chart"]:
                # Select data dimension
                dimension = st.selectbox("Select Data Dimension", available_columns)

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

            elif viz_type == "Scatter Plot" and len(available_columns) >= 2:
                # For scatter plot, need two dimensions
                col1, col2 = st.columns(2)

                with col1:
                    x_dimension = st.selectbox("X-Axis", available_columns)

                with col2:
                    y_dimension = st.selectbox("Y-Axis", available_columns, index=min(1, len(available_columns) - 1))

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
        if not combinations_df.empty and 'Rating' in combinations_df.columns:
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
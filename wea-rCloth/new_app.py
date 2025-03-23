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
if 'type_options' not in st.session_state:
    st.session_state.type_options = st.session_state.custom_types["Upper body"]

# Initialize Airtable tables
wardrobe_table = Table('patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
                       'appdgbGbEz1Dtynvg', 'wardrobe_data')
combinations_table = Table('patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
                           'appdgbGbEz1Dtynvg', 'combinations_data')


def load_data():
    """Fetch data from Airtable."""
    try:
        wardrobe_records = wardrobe_table.all()
        combinations_records = combinations_table.all()

        wardrobe_df = pd.DataFrame([rec['fields'] for rec in wardrobe_records]) if wardrobe_records else pd.DataFrame()
        combinations_df = pd.DataFrame(
            [rec['fields'] for rec in combinations_records]) if combinations_records else pd.DataFrame()

        # Ensure required columns exist in the dataframe
        required_columns = ['Model', 'Category', 'Type', 'Style', 'Color', 'Season']
        for col in required_columns:
            if col not in wardrobe_df.columns:
                wardrobe_df[col] = ''

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
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(columns=['Model', 'Category', 'Type', 'Style', 'Color', 'Season']), pd.DataFrame()


def save_data(wardrobe_df, combinations_df):
    """Save data to Airtable."""
    if 'new_item' in st.session_state:
        new_item = st.session_state.new_item

        # Convert list values to comma-separated strings for Airtable
        row_dict = {}
        for k, v in new_item.items():
            if k != 'TypeNumber' and pd.notna(v):  # Skip TypeNumber field
                if isinstance(v, list):
                    row_dict[k] = ", ".join(v)
                else:
                    row_dict[k] = v

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
            st.error("Check if all field names match your Airtable schema")

    # For combinations
    if 'new_combination' in st.session_state:
        new_combination = st.session_state.new_combination

        # Ensure we're using the correct field names for Airtable
        row_dict = {}
        for k, v in new_combination.items():
            if pd.notna(v):
                # Convert lists to comma-separated strings
                if isinstance(v, list):
                    row_dict[k] = ", ".join(v)
                else:
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


# Helper function to update type options when category changes
def update_type_options():
    category = st.session_state.category_select
    # Update the type options based on the selected category
    if category in st.session_state.custom_types:
        st.session_state.type_options = st.session_state.custom_types[category]
    else:
        st.session_state.type_options = []


# Helper function to check if a string contains multiple items
def split_string_to_list(s):
    if isinstance(s, str):
        return [item.strip() for item in s.split(',')]
    elif isinstance(s, list):
        return s
    else:
        return [s] if s else []


# Process dataframe to handle multi-value fields
def process_dataframe(df):
    if df.empty:
        return df

    # Process Style and Season columns
    for column in ['Style', 'Season']:
        if column in df.columns:
            df[column] = df[column].apply(split_string_to_list)

    return df


# Load data
wardrobe_df, combinations_df = load_data()
wardrobe_df = process_dataframe(wardrobe_df)


# Extract unique values for Style and Season accounting for list values
def get_unique_values(df, column):
    if df.empty or column not in df.columns:
        return []

    unique_values = set()
    for item in df[column]:
        if isinstance(item, list):
            for subitem in item:
                unique_values.add(subitem)
        elif isinstance(item, str):
            for subitem in split_string_to_list(item):
                unique_values.add(subitem)
        elif item is not None:
            unique_values.add(item)

    return sorted(list(unique_values))


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
            # First handle category selection (without the callback in the form)
            category = st.selectbox(
                "Category",
                ["Upper body", "Lower body", "Footwear"],
                key="category_select"
            )

            # Type selection based on the current category's options
            cloth_type = st.selectbox("Type", st.session_state.type_options)

            # Option to add a new type inline
            add_new_type = st.checkbox("Add a new type?")

            if add_new_type:
                # Get the next type number based on existing types
                if category in st.session_state.custom_types and st.session_state.custom_types[category]:
                    # Extract existing prefixes
                    prefixes = []
                    for typ in st.session_state.custom_types[category]:
                        if "-" in typ:
                            prefix = typ.split("-")[0]
                            if prefix.isdigit():
                                prefixes.append(int(prefix))

                    next_prefix = max(prefixes) + 1 if prefixes else 1
                else:
                    # Default prefixes based on category
                    if category == "Upper body":
                        next_prefix = 1
                    elif category == "Lower body":
                        next_prefix = 20
                    else:  # Footwear
                        next_prefix = 30

                # Form inputs for new type
                new_type_name = st.text_input("New Type Name (e.g., Jacket, Hoodie)", key="new_type_name")
                new_type_prefix = st.number_input("Type Prefix", min_value=1, max_value=99, value=next_prefix,
                                                  key="new_type_prefix")

                # Preview the new type format
                if new_type_name:
                    new_type = f"{new_type_prefix:02d}-{new_type_name}"
                    st.write(f"New type will be: **{new_type}**")

            # Use multiselect for Style
            style_options = ["Casual", "Formal", "Trendy", "Universal"]
            style = st.multiselect("Style (select one or more)", style_options)

            color = st.text_input("Color")

            # Use multiselect for Season
            season_options = ["Winter", "Vernal", "Summer", "Autumn", "Universal"]
            season = st.multiselect("Season (select one or more)", season_options)

            # Get the number of items of this type
            existing_items = wardrobe_df[(wardrobe_df['Category'] == category)]
            if not existing_items.empty and 'Type' in existing_items.columns:
                existing_items = existing_items[existing_items['Type'] == cloth_type]
            next_number = len(existing_items) + 1 if not existing_items.empty else 1

            # Auto-generate model name
            style_code = ''.join([s[0].lower() for s in style]) if style else 'u'
            season_code = ''.join([s[0] for s in season]) if season else 'U'
            category_code = category.split()[0][0]

            # If we're adding a new type, use that prefix
            if add_new_type and new_type_name:
                type_prefix = f"{new_type_prefix:02d}"
            else:
                type_prefix = cloth_type.split("-")[0] if "-" in cloth_type else "00"

            model = f"{category_code}{type_prefix}{next_number:02d}{style_code}{season_code}"

            st.write(f"Generated Model ID: {model}")

            submitted = st.form_submit_button("Add to Wardrobe")

            if submitted:
                # Update type options based on the selected category
                update_type_options()

                # Add the new type if requested
                if add_new_type and new_type_name:
                    new_type = f"{new_type_prefix:02d}-{new_type_name}"
                    if category in st.session_state.custom_types:
                        if new_type not in st.session_state.custom_types[category]:
                            st.session_state.custom_types[category].append(new_type)
                            st.session_state.custom_types[category].sort()
                            cloth_type = new_type  # Use the new type
                    else:
                        st.session_state.custom_types[category] = [new_type]
                        cloth_type = new_type

                # Create new item
                new_item = {
                    'Model': model,
                    'Category': category,
                    'Type': cloth_type,
                    'Style': style,
                    'Color': color,
                    'Season': season
                }

                # Add to dataframe and save
                new_item_df = pd.DataFrame([new_item])
                wardrobe_df = pd.concat([wardrobe_df, new_item_df], ignore_index=True)
                st.session_state.new_item = new_item
                save_data(wardrobe_df, combinations_df)

    with col2:
        st.subheader("Generate Outfit Combination")

        if st.button("Generate New Combination"):
            # Check if we have enough items
            categories = ["Upper body", "Lower body", "Footwear"]
            has_all_categories = True

            for cat in categories:
                if wardrobe_df.empty or 'Category' not in wardrobe_df.columns:
                    has_all_categories = False
                    break
                cat_items = wardrobe_df[wardrobe_df['Category'] == cat]
                if cat_items.empty:
                    has_all_categories = False
                    break

            if has_all_categories:
                try:
                    # Get one item from each category
                    upper = wardrobe_df[wardrobe_df['Category'] == 'Upper body'].sample(1)
                    lower = wardrobe_df[wardrobe_df['Category'] == 'Lower body'].sample(1)
                    footwear = wardrobe_df[wardrobe_df['Category'] == 'Footwear'].sample(1)

                    # Determine season compatibility
                    seasons = []
                    for item in [upper, lower, footwear]:
                        if 'Season' in item.columns:
                            item_seasons = item['Season'].iloc[0]
                            if isinstance(item_seasons, list):
                                # For lists, check if not 'Universal'
                                for s in item_seasons:
                                    if s != 'Universal':
                                        seasons.append(s[0])  # First letter of season
                            elif isinstance(item_seasons, str) and item_seasons != 'Universal':
                                seasons.append(item_seasons[0])  # First letter of season

                    # Create combined season code
                    if not seasons:
                        combined_season = 'U'  # Universal
                    else:
                        combined_season = ''.join(sorted(set(seasons)))

                    # Determine combined style
                    styles = []
                    for item in [upper, lower, footwear]:
                        if 'Style' in item.columns:
                            item_styles = item['Style'].iloc[0]
                            if isinstance(item_styles, list):
                                # For lists, check if not 'Universal'
                                for s in item_styles:
                                    if s != 'Universal':
                                        styles.append(s[0].lower())  # First letter of style
                            elif isinstance(item_styles, str) and item_styles != 'Universal':
                                styles.append(item_styles[0].lower())  # First letter of style

                    if not styles:
                        combined_style = 'u'  # Universal
                    else:
                        combined_style = ''.join(sorted(set(styles)))

                    # Create combination ID
                    combination_id = f"{upper['Model'].iloc[0]}_{lower['Model'].iloc[0]}_{footwear['Model'].iloc[0]}"

                    # Store current combination in session state
                    st.session_state.current_combination = {
                        'Combination_ID': combination_id,
                        'Upper_Body': upper['Model'].iloc[0],
                        'Lower_Body': lower['Model'].iloc[0],
                        'Footwear': footwear['Model'].iloc[0],
                        'Season_Match': combined_season,
                        'Style_Match': combined_style
                    }

                    # Set flag to show rating UI
                    st.session_state.show_rating = True
                except Exception as e:
                    st.error(f"Error generating combination: {str(e)}")
            else:
                st.warning(
                    "You need at least one item in each category (Upper body, Lower body, Footwear) to generate a combination.")

        # Display the combination if available
        if st.session_state.show_rating and st.session_state.current_combination:

            combination = st.session_state.current_combination

            # Get item details
            upper_details = wardrobe_df[
                wardrobe_df['Model'] == combination['Upper_Body']] if not wardrobe_df.empty else pd.DataFrame()
            lower_details = wardrobe_df[
                wardrobe_df['Model'] == combination['Lower_Body']] if not wardrobe_df.empty else pd.DataFrame()
            footwear_details = wardrobe_df[
                wardrobe_df['Model'] == combination['Footwear']] if not wardrobe_df.empty else pd.DataFrame()

            # Display the combination
            st.subheader("Your Outfit Combination:")

            if not upper_details.empty and 'Model' in upper_details.columns:
                st.write(
                    f"**Upper Body:** {upper_details['Model'].iloc[0]} - {upper_details['Type'].iloc[0]} ({upper_details['Color'].iloc[0]})")
            else:
                st.write(f"**Upper Body:** {combination['Upper_Body']}")

            if not lower_details.empty and 'Model' in lower_details.columns:
                st.write(
                    f"**Lower Body:** {lower_details['Model'].iloc[0]} - {lower_details['Type'].iloc[0]} ({lower_details['Color'].iloc[0]})")
            else:
                st.write(f"**Lower Body:** {combination['Lower_Body']}")

            if not footwear_details.empty and 'Model' in footwear_details.columns:
                st.write(
                    f"**Footwear:** {footwear_details['Model'].iloc[0]} - {footwear_details['Type'].iloc[0]} ({footwear_details['Color'].iloc[0]})")
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

    # Safe filtering to handle empty or invalid dataframes
    category_options = wardrobe_df[
        'Category'].unique().tolist() if not wardrobe_df.empty and 'Category' in wardrobe_df.columns else []
    filter_category = st.sidebar.multiselect("Category", category_options)

    # Get unique style values accounting for list values in the column
    style_options = get_unique_values(wardrobe_df, 'Style')
    filter_style = st.sidebar.multiselect("Style", style_options)

    # Get unique season values accounting for list values in the column
    season_options = get_unique_values(wardrobe_df, 'Season')
    filter_season = st.sidebar.multiselect("Season", season_options)

    # Apply filters
    filtered_df = wardrobe_df.copy() if not wardrobe_df.empty else pd.DataFrame()

    if not filtered_df.empty:
        if filter_category and 'Category' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]

        if filter_style and 'Style' in filtered_df.columns:
            # For list values, check if any item in the list matches the filter
            style_mask = filtered_df['Style'].apply(
                lambda x: any(style in x for style in filter_style) if isinstance(x, list) else
                (x in filter_style if isinstance(x, str) else False)
            )
            filtered_df = filtered_df[style_mask]

        if filter_season and 'Season' in filtered_df.columns:
            # For list values, check if any item in the list matches the filter
            season_mask = filtered_df['Season'].apply(
                lambda x: any(season in x for season in filter_season) if isinstance(x, list) else
                (x in filter_season if isinstance(x, str) else False)
            )
            filtered_df = filtered_df[season_mask]

    # Display wardrobe items
    if not filtered_df.empty:
        # Convert list columns to strings for display
        display_df = filtered_df.copy()
        for col in ['Style', 'Season']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

        st.dataframe(display_df)
        st.write(f"Showing {len(filtered_df)} of {len(wardrobe_df)} items")
    else:
        st.info("No items in your wardrobe yet. Add some from the Main page!")

elif page == "Analysis":
    st.title("Wardrobe Analysis")

    if wardrobe_df.empty:
        st.info("Add some items to your wardrobe to see analysis!")
    else:
        try:
            # Select visualization type
            viz_type = st.selectbox("Select Visualization Type",
                                    ["Pie Chart", "Bar Chart", "Line Chart", "Scatter Plot"])

            if viz_type in ["Pie Chart", "Bar Chart", "Line Chart"]:
                # Select data dimension
                dimension = st.selectbox("Select Data Dimension",
                                         ["Category", "Type", "Style", "Color", "Season"])

                # For multi-value columns, need special handling
                if dimension in ['Style', 'Season']:
                    # Explode the multi-value column
                    analysis_df = pd.DataFrame()
                    for _, row in wardrobe_df.iterrows():
                        if dimension in row and isinstance(row[dimension], list):
                            for value in row[dimension]:
                                analysis_df = pd.concat([analysis_df, pd.DataFrame({dimension: [value]})],
                                                        ignore_index=True)
                        elif dimension in row and pd.notna(row[dimension]):
                            analysis_df = pd.concat([analysis_df, pd.DataFrame({dimension: [row[dimension]]})],
                                                    ignore_index=True)

                    # Count values
                    counts = analysis_df[dimension].value_counts()
                else:
                    # Regular counting for single-value columns
                    counts = wardrobe_df[dimension].value_counts() if dimension in wardrobe_df.columns else pd.Series()

                # Create figure
                fig, ax = plt.subplots(figsize=(10, 6))

                if not counts.empty:
                    if viz_type == "Pie Chart":
                        ax.pie(counts, labels=counts.index, autopct='%1.1f%%')
                        ax.set_title(f'Distribution of {dimension}')

                    elif viz_type == "Bar Chart":
                        counts.plot(kind='bar', ax=ax)
                        ax.set_title(f'{dimension} Counts')
                        ax.set_xlabel(dimension)
                        ax.set_ylabel('Count')

                    elif viz_type == "Line Chart":
                        # For line chart, use chronological ordering if possible
                        if dimension == "Type":
                            # Extract type number for ordering
                            type_counts = counts.sort_index()
                            type_counts.plot(kind='line', marker='o', ax=ax)
                        else:
                            counts.plot(kind='line', marker='o', ax=ax)
                        ax.set_title(f'Trend of {dimension}')
                        ax.set_xlabel(dimension)
                        ax.set_ylabel('Count')

                    st.pyplot(fig)
                else:
                    st.info(f"No data available for {dimension}")

            elif viz_type == "Scatter Plot":
                # For scatter plot, need two dimensions
                col1, col2 = st.columns(2)

                with col1:
                    x_dimension = st.selectbox("X-Axis", ["Category", "Type", "Style", "Color", "Season"])

                with col2:
                    y_dimension = st.selectbox("Y-Axis", ["Category", "Type", "Style", "Color", "Season"], index=1)

                # Handle multi-value columns
                if x_dimension in ['Style', 'Season'] or y_dimension in ['Style', 'Season']:
                    st.warning(
                        "Scatter plots for multi-value columns like Style and Season may not display accurately.")

                # Need to encode categorical variables numerically for scatter plot
                fig, ax = plt.subplots(figsize=(10, 6))

                # Create encoded versions for plotting
                wardrobe_encoded = wardrobe_df.copy()


                # Function to get first value for multi-value fields
                def get_first_value(x):
                    if isinstance(x, list) and x:
                        return x[0]
                    return x


                for dim in [x_dimension, y_dimension]:
                    if dim in wardrobe_encoded.columns:
                        # For multi-value columns, use the first value
                        if dim in ['Style', 'Season']:
                            wardrobe_encoded[dim] = wardrobe_encoded[dim].apply(get_first_value)

                        categories = wardrobe_encoded[dim].dropna().unique()
                        category_map = {cat: i for i, cat in enumerate(categories)}
                        wardrobe_encoded[f"{dim}_encoded"] = wardrobe_encoded[dim].map(category_map)
                    else:
                        wardrobe_encoded[f"{dim}_encoded"] = 0  # Default value if column is missing

                # Create scatter plot with categorical encoding
                scatter = ax.scatter(
                    wardrobe_encoded[f"{x_dimension}_encoded"],
                    wardrobe_encoded[f"{y_dimension}_encoded"],
                    c=wardrobe_encoded[f"{x_dimension}_encoded"],
                    alpha=0.6
                )

                # Set tick labels to original categories
                if x_dimension in wardrobe_df.columns:
                    x_categories = sorted(set([get_first_value(x) for x in wardrobe_df[x_dimension].dropna()]))
                    ax.set_xticks(range(len(x_categories)))
                    ax.set_xticklabels(x_categories, rotation=45)

                if y_dimension in wardrobe_df.columns:
                    y_categories = sorted(set([get_first_value(y) for y in wardrobe_df[y_dimension].dropna()]))
                    ax.set_yticks(range(len(y_categories)))
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
        except Exception as e:
            st.error(f"Error in analysis: {str(e)}")
            st.info("Try adding more items to your wardrobe for better analysis.")

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
    3. Manage your clothing types directly when adding new items
    4. View your entire wardrobe on the Wardrobe page
    5. See analytics and insights on the Analysis page

    ### Future Features (Coming Soon)

    - Machine learning recommendations based on your ratings
    - Image upload for clothing items
    - Seasonal wardrobe planning
    - Outfit calendar
    """)
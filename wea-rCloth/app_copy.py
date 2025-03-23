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

# Initialize Airtable tables
wardrobe_table = Table('patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea', 'appdgbGbEz1Dtynvg', 'wardrobe_data')
combinations_table = Table('patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea', 'appdgbGbEz1Dtynvg', 'combinations_data')

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
    if 'new_item' in st.session_state:
        new_item = st.session_state.new_item

        # Remove any fields that don't exist in Airtable
        # Ensure field names match exactly what's in Airtable
        row_dict = {}
        for k, v in new_item.items():
            if k != 'TypeNumber' and pd.notna(v):  # Skip TypeNumber field
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

    # Similar approach for combinations
    if 'new_combination' in st.session_state:
        # Update field names to match your combinations_data.csv
        new_combination = st.session_state.new_combination

        # Map field names to match Airtable schema for combinations
        field_mapping = {
            'CombinationID': 'Combination_ID',
            'UpperBody': 'Upper_Body',
            'LowerBody': 'Lower_Body',
            'Season': 'Season_Match',
            'Style': 'Style_Match'
        }

        row_dict = {}
        for k, v in new_combination.items():
            if pd.notna(v):
                # Use the mapped field name if it exists, otherwise use the original
                airtable_field_name = field_mapping.get(k, k)
                row_dict[airtable_field_name] = v

        try:
            combinations_table.create(row_dict)
            st.success(f"Saved rating for this combination!")
            del st.session_state.new_combination
        except Exception as e:
            st.error(f"Error saving to Airtable: {str(e)}")

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
        # Form for adding new clothing
        with st.form("new_cloth_form"):
            # Initialize session state for category if not exists
            if 'previous_category' not in st.session_state:
                st.session_state.previous_category = "Upper body"

            category = st.selectbox("Category", ["Upper body", "Lower body", "Footwear"], key="category_select")

            # Type selection based on category
            type_options = {
                "Upper body": ["01-Shirt", "02-TShirt", "03-Sweater", "04-Jacket", "05-Coat"],
                "Lower body": ["20-Jeans", "21-Trousers", "22-Shorts", "23-Skirt"],
                "Footwear": ["30-Sneakers", "31-Formal", "32-Boots", "33-Sandals"]
            }

            # Check if category has changed
            if 'previous_category' in st.session_state and st.session_state.previous_category != category:
                # If category changed, reset the type selection by using a new key
                st.session_state.type_key = f"type_select_{category}_{random.randint(0, 1000)}"
                st.session_state.previous_category = category
            elif 'type_key' not in st.session_state:
                # Initialize the type key if it doesn't exist
                st.session_state.type_key = "type_select_initial"

            # Use the dynamic key for the type selectbox
            cloth_type = st.selectbox("Type", type_options[category], key=st.session_state.type_key)

            # Rest of your form code remains the same
            style = st.selectbox("Style", ["Casual", "Formal", "Trendy", "Universal"])
            color = st.text_input("Color")
            season = st.selectbox("Season", ["Winter", "Vernal", "Summer", "Autumn", "Universal"])

            # Get the number of items of this type
            existing_items = wardrobe_df[(wardrobe_df['Category'] == category) &
                                         (wardrobe_df['Type'] == cloth_type)]
            next_number = len(existing_items) + 1

            # Auto-generate model name
            style_code = ''.join([s[0] for s in style.split()])
            season_code = ''.join([s[0] for s in season.split()])
            category_code = category.split()[0][0]
            type_prefix = cloth_type.split("-")[0]
            model = f"{category_code}{type_prefix}{next_number:02d}{style_code.lower()}{season_code}"

            st.write(f"Generated Model ID: {model}")

            submitted = st.form_submit_button("Add to Wardrobe")

            if submitted:
                new_item = {
                    'Model': model,
                    'Category': category,
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

        if st.button("Generate New Combination"):
            # Check if we have enough items - handle error safely
            try:
                # Check if we have at least one item in each category
                categories = ["Upper body", "Lower body", "Footwear"]
                category_counts = {cat: len(wardrobe_df[wardrobe_df['Category'] == cat])
                                   for cat in categories if 'Category' in wardrobe_df.columns}

                has_all_categories = all(category_counts.get(cat, 0) > 0 for cat in categories)

                if has_all_categories:
                    # Get one item from each category
                    upper = wardrobe_df[wardrobe_df['Category'] == 'Upper body'].sample(1)
                    lower = wardrobe_df[wardrobe_df['Category'] == 'Lower body'].sample(1)
                    footwear = wardrobe_df[wardrobe_df['Category'] == 'Footwear'].sample(1)

                    # Determine season compatibility - handle potential missing columns safely
                    seasons = []
                    for item_df in [upper, lower, footwear]:
                        if 'Season' in item_df.columns and len(item_df) > 0:
                            season_val = item_df['Season'].values[0]
                            if isinstance(season_val, str) and season_val != 'Universal':
                                # Handle comma-separated values
                                if ',' in season_val:
                                    for s in season_val.split(','):
                                        seasons.append(s.strip()[0])  # First letter of each season
                                else:
                                    seasons.append(season_val[0])  # First letter of season

                    # Create combined season code
                    if not seasons:
                        combined_season = 'U'  # Universal
                    else:
                        combined_season = ''.join(sorted(set(seasons)))

                    # Determine combined style - safely handle potential missing columns
                    styles = []
                    for item_df in [upper, lower, footwear]:
                        if 'Style' in item_df.columns and len(item_df) > 0 and not pd.isna(item_df['Style'].values[0]):
                            style_val = item_df['Style'].values[0]
                            if isinstance(style_val, str) and style_val != 'Universal':
                                # Handle comma-separated values
                                if ',' in style_val:
                                    for s in style_val.split(','):
                                        styles.append(s.strip()[0].lower())  # First letter of each style
                                else:
                                    styles.append(style_val[0].lower())  # First letter of style

                    if not styles:
                        combined_style = 'u'  # Universal
                    else:
                        combined_style = ''.join(sorted(set(styles)))

                    # Create combination ID - safely access values
                    upper_model = upper['Model'].values[0] if 'Model' in upper.columns else "unknown"
                    lower_model = lower['Model'].values[0] if 'Model' in lower.columns else "unknown"
                    footwear_model = footwear['Model'].values[0] if 'Model' in footwear.columns else "unknown"

                    combination_id = f"{upper_model}_{lower_model}_{footwear_model}"

                    # Store current combination in session state
                    st.session_state.current_combination = {
                        'Combination_ID': combination_id,
                        'Upper_Body': upper_model,
                        'Lower_Body': lower_model,
                        'Footwear': footwear_model,
                        'Season_Match': combined_season,
                        'Style_Match': combined_style
                    }

                    # Display the combination - safely access values
                    st.subheader("Your Outfit Combination:")

                    # Safe display for upper body
                    upper_type = upper['Type'].values[0] if 'Type' in upper.columns else "unknown type"
                    upper_color = upper['Color'].values[0] if 'Color' in upper.columns else "unknown color"
                    st.write(f"**Upper Body:** {upper_model} - {upper_type} ({upper_color})")

                    # Safe display for lower body
                    lower_type = lower['Type'].values[0] if 'Type' in lower.columns else "unknown type"
                    lower_color = lower['Color'].values[0] if 'Color' in lower.columns else "unknown color"
                    st.write(f"**Lower Body:** {lower_model} - {lower_type} ({lower_color})")

                    # Safe display for footwear
                    footwear_type = footwear['Type'].values[0] if 'Type' in footwear.columns else "unknown type"
                    footwear_color = footwear['Color'].values[0] if 'Color' in footwear.columns else "unknown color"
                    st.write(f"**Footwear:** {footwear_model} - {footwear_type} ({footwear_color})")

                    st.write(f"**Season Compatibility:** {combined_season}")
                    st.write(f"**Style Compatibility:** {combined_style}")

                    # Rating slider
                    rating = st.slider("Rate this combination (0-10)", 0, 10, 5)

                    if st.button("Save Rating"):
                        # Check if combination already exists - safely handle potentially missing columns
                        exists = False
                        if 'Combination_ID' in combinations_df.columns:
                            exists = combination_id in combinations_df['Combination_ID'].values

                        if exists:
                            # Update existing combination
                            combinations_df.loc[combinations_df['Combination_ID'] == combination_id, 'Rating'] = rating
                        else:
                            # Add new combination
                            new_combination = st.session_state.current_combination.copy()
                            new_combination['Rating'] = rating
                            combinations_df = pd.concat([combinations_df, pd.DataFrame([new_combination])],
                                                        ignore_index=True)

                        st.session_state.new_combination = new_combination  # Store for saving to Airtable
                        save_data(wardrobe_df, combinations_df)
                else:
                    st.error("You need at least one item in each category to generate a combination!")
            except Exception as e:
                st.error(f"Error generating combination: {str(e)}")
                st.info("Check that your wardrobe has data in the expected format.")

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

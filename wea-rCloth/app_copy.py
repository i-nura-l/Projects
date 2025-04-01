import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from db import get_connection
from user_auth import login_user, create_user

# Set page config
st.set_page_config(page_title="wea-rCloth", layout="wide")


# ------------------------- LOGIN / SIGN UP -------------------------
def login_signup_page():
    st.title("👕 wea-rCloth Login")
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None

    option = st.radio("Choose:", ["Login", "Sign Up"])

    if option == "Login":
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state.user_info = user
                st.success(f"Welcome, {user['name']}!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
    else:  # Sign Up
        name = st.text_input("Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign Up"):
            if create_user(name, email, password):
                st.success("Account created! Please log in.")
            else:
                st.error("User already exists or sign up failed.")


login_signup_page()
if not st.session_state.get("user_info"):
    st.stop()

# ------------------------- SESSION STATE SETUP -------------------------
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


# ------------------------- DATABASE FUNCTIONS -------------------------
def load_data(user_id, role):
    conn = get_connection()
    wardrobe_query = """
        SELECT model, category, type, style, color, season FROM wardrobe
        WHERE %s = 'admin' OR user_id = %s
    """
    combinations_query = """
        SELECT combination_id, upper_body, lower_body, footwear, season_match, style_match, rating FROM combinations
        WHERE %s = 'admin' OR user_id = %s
    """
    wardrobe_df = pd.read_sql(wardrobe_query, conn, params=(role, user_id))
    combos_df = pd.read_sql(combinations_query, conn, params=(role, user_id))
    conn.close()

    # Format multi-value fields as strings
    for col in ['style', 'season']:
        if col in wardrobe_df.columns:
            wardrobe_df[col] = wardrobe_df[col].fillna('').astype(str)
    for col in ['season_match', 'style_match']:
        if col in combos_df.columns:
            combos_df[col] = combos_df[col].fillna('').astype(str)

    return wardrobe_df, combos_df


def save_data():
    conn = get_connection()
    cur = conn.cursor()

    # Save new clothing item
    if 'new_item' in st.session_state:
        item = st.session_state.new_item
        user_id = st.session_state.user_info["id"]
        cur.execute("""
            INSERT INTO wardrobe (user_id, model, category, type, style, color, season)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            item['Model'],
            item['Category'],
            item['Type'],
            ', '.join(item['Style']),
            item['Color'],
            ', '.join(item['Season'])
        ))
        st.success(f"Added {item['Model']} to your wardrobe!")
        del st.session_state.new_item

    # Save new outfit combination (rating)
    if 'new_combination' in st.session_state:
        combo = st.session_state.new_combination
        user_id = st.session_state.user_info["id"]
        cur.execute("""
            INSERT INTO combinations (user_id, combination_id, upper_body, lower_body, footwear,
                                      season_match, style_match, rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            combo['Combination_ID'],
            combo['Upper_Body'],
            combo['Lower_Body'],
            combo['Footwear'],
            ', '.join(combo['Season_Match']),
            ', '.join(combo['Style_Match']),
            combo['Rating']
        ))
        st.success("Saved rating for this combination!")
        del st.session_state.new_combination
        st.session_state.show_rating = False

    conn.commit()
    cur.close()
    conn.close()


def get_unique_values(df, column):
    """Get unique values from a column that may contain comma-separated values."""
    if df is None or df.empty or column not in df.columns:
        return []
    all_values = set()
    for value in df[column].dropna():
        if isinstance(value, str):
            for item in value.split(','):
                all_values.add(item.strip())
        else:
            all_values.add(value)
    return sorted(list(all_values))


def update_type_options():
    """Update the type options based on the selected category."""
    category = st.session_state.category_select
    st.session_state.form_category = category
    if category in st.session_state.custom_types:
        st.session_state.type_options = st.session_state.custom_types[category]
    else:
        st.session_state.type_options = []


# ------------------------- LOAD DATA -------------------------
user = st.session_state.user_info
wardrobe_df, combinations_df = load_data(user["id"], user["role"])

# ------------------------- SIDEBAR NAVIGATION -------------------------
st.sidebar.title("wea-rCloth")
pages = ["Main", "Wardrobe", "Combinations", "Analysis", "About"]
if user["role"] == "admin":
    pages.append("Admin Panel")
page = st.sidebar.selectbox("Navigation", pages)

# ------------------------- PAGE: MAIN -------------------------
if page == "Main":
    st.title("wea-rCloth - Your Smart Wardrobe Assistant")
    col1, col2 = st.columns(2)

    # Column 1: Add New Clothing
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
            selected_style = st.multiselect("Style", ["Casual", "Formal", "Trendy", "Universal"], default=["Casual"])
            color = st.text_input("Color")
            selected_season = st.multiselect("Season", ["Winter", "Vernal", "Summer", "Autumn", "Universal"],
                                             default=["Universal"])

            existing_items = wardrobe_df[
                (wardrobe_df['category'] == st.session_state.form_category) &
                (wardrobe_df['type'] == cloth_type)
                ]
            next_number = len(existing_items) + 1 if not existing_items.empty else 1

            # Auto-generate model name
            style_code = ''.join([s[0] for s in selected_style]) if selected_style else ''
            season_code = ''.join([s[0] for s in selected_season]) if selected_season else ''
            category_code = st.session_state.form_category[0]
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
                wardrobe_df = pd.concat([wardrobe_df, pd.DataFrame([new_item])], ignore_index=True)
                st.session_state.new_item = new_item
                save_data()

    # Column 2: Generate Outfit Combination
    with col2:
        st.subheader("Generate Outfit Combination")
        with st.form("generate_outfit_form"):
            chosen_season = st.selectbox("Choose Season", ["Winter", "Vernal", "Summer", "Autumn", "Universal"],
                                         index=4)
            chosen_style = st.selectbox("Choose Style", ["Casual", "Formal", "Trendy", "Universal"], index=3)
            generate_button = st.form_submit_button("Generate Outfit")

        if generate_button:
            try:
                def matches_season(item_season_str, season_choice):
                    if season_choice == "Universal":
                        return True
                    if not isinstance(item_season_str, str):
                        return False
                    item_season_list = [s.strip() for s in item_season_str.split(',')]
                    return ("Universal" in item_season_list) or (season_choice in item_season_list)


                def matches_style(item_style_str, style_choice):
                    if style_choice == "Universal":
                        return True
                    if not isinstance(item_style_str, str):
                        return False
                    item_style_list = [s.strip() for s in item_style_str.split(',')]
                    return ("Universal" in item_style_list) or (style_choice in item_style_list)


                valid_items = wardrobe_df[
                    wardrobe_df['season'].apply(lambda x: matches_season(x, chosen_season)) &
                    wardrobe_df['style'].apply(lambda x: matches_style(x, chosen_style))
                    ]

                if valid_items.empty:
                    st.error("No items match your chosen Season/Style. Please add more clothes or change filters.")
                else:
                    upper_df = valid_items[valid_items['category'] == 'Upper body']
                    lower_df = valid_items[valid_items['category'] == 'Lower body']
                    foot_df = valid_items[valid_items['category'] == 'Footwear']

                    if upper_df.empty or lower_df.empty or foot_df.empty:
                        st.error("Not enough items in all categories to build a complete outfit!")
                    else:
                        upper_item = upper_df.sample(1).iloc[0]
                        lower_item = lower_df.sample(1).iloc[0]
                        shoe_item = foot_df.sample(1).iloc[0]

                        if not combinations_df.empty and 'combination_id' in combinations_df.columns:
                            existing_codes = [
                                code for code in combinations_df['combination_id']
                                if isinstance(code, str) and code.startswith('C')
                            ]
                            new_num = max([int(code[1:]) for code in existing_codes]) + 1 if existing_codes else 1
                        else:
                            new_num = 1
                        combination_id = f"C{new_num:03d}"

                        st.session_state.current_combination = {
                            'Combination_ID': combination_id,
                            'Upper_Body': upper_item['model'],
                            'Lower_Body': lower_item['model'],
                            'Footwear': shoe_item['model'],
                            'Season_Match': [chosen_season],
                            'Style_Match': [chosen_style]
                        }
                        st.session_state.show_rating = True

            except Exception as e:
                st.error("Error generating outfit combination: " + str(e))

        if st.session_state.show_rating and st.session_state.current_combination:
            combo = st.session_state.current_combination
            upper_details = wardrobe_df[wardrobe_df['model'] == combo['Upper_Body']]
            lower_details = wardrobe_df[wardrobe_df['model'] == combo['Lower_Body']]
            foot_details = wardrobe_df[wardrobe_df['model'] == combo['Footwear']]

            st.subheader("Your Outfit Combination:")
            if not upper_details.empty:
                st.write(
                    f"**Upper Body:** {upper_details['model'].values[0]} - {upper_details['type'].values[0]} ({upper_details['color'].values[0]})")
            if not lower_details.empty:
                st.write(
                    f"**Lower Body:** {lower_details['model'].values[0]} - {lower_details['type'].values[0]} ({lower_details['color'].values[0]})")
            if not foot_details.empty:
                st.write(
                    f"**Footwear:** {foot_details['model'].values[0]} - {foot_details['type'].values[0]} ({foot_details['color'].values[0]})")

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

# ------------------------- PAGE: WARDROBE -------------------------
elif page == "Wardrobe":
    st.title("Your Wardrobe")
    st.sidebar.subheader("Filter Options")
    filter_category = st.sidebar.multiselect("Category",
                                             wardrobe_df['category'].unique().tolist() if not wardrobe_df.empty else [])
    filter_style = st.sidebar.multiselect("Style", get_unique_values(wardrobe_df, 'style'))
    filter_season = st.sidebar.multiselect("Season", get_unique_values(wardrobe_df, 'season'))

    filtered_df = wardrobe_df.copy()
    if filter_category:
        filtered_df = filtered_df[filtered_df['category'].isin(filter_category)]
    if filter_style:
        filtered_df = filtered_df[
            filtered_df['style'].apply(lambda x: any(s in str(x) for s in filter_style) if pd.notna(x) else False)]
    if filter_season:
        filtered_df = filtered_df[
            filtered_df['season'].apply(lambda x: any(s in str(x) for s in filter_season) if pd.notna(x) else False)]

    if not filtered_df.empty:
        st.dataframe(filtered_df)
        st.write(f"Showing {len(filtered_df)} of {len(wardrobe_df)} items")
    else:
        st.info("No items in your wardrobe yet. Add some from the Main page!")

# ------------------------- PAGE: COMBINATIONS -------------------------
elif page == "Combinations":
    st.title("Combination Records")
    st.sidebar.subheader("Filter Options for Combinations")
    unique_seasons = get_unique_values(combinations_df, "season_match")
    unique_styles = get_unique_values(combinations_df, "style_match")
    filter_season = st.sidebar.multiselect("Season", unique_seasons)
    filter_style = st.sidebar.multiselect("Style", unique_styles)
    rating_range = st.sidebar.slider("Rating Range", 0, 10, (0, 10))
    combo_filtered_df = combinations_df.copy()


    def filter_list_field(cell, selected_options):
        if isinstance(cell, str):
            items = [i.strip() for i in cell.split(',')]
            return any(item in items for item in selected_options)
        return False


    if filter_season:
        combo_filtered_df = combo_filtered_df[
            combo_filtered_df["season_match"].apply(lambda x: filter_list_field(x, filter_season))]
    if filter_style:
        combo_filtered_df = combo_filtered_df[
            combo_filtered_df["style_match"].apply(lambda x: filter_list_field(x, filter_style))]
    if "rating" in combo_filtered_df.columns:
        combo_filtered_df = combo_filtered_df[
            combo_filtered_df["rating"].apply(lambda x: x is not None and rating_range[0] <= x <= rating_range[1])]

    st.dataframe(combo_filtered_df)
    st.write(f"Showing {len(combo_filtered_df)} of {len(combinations_df)} combination records.")
    if not combinations_df.empty:
        st.subheader("Combination Ratings Analysis")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(combinations_df['rating'], bins=11, kde=True, ax=ax)
        ax.set_title('Distribution of Outfit Ratings')
        ax.set_xlabel('Rating')
        ax.set_ylabel('Count')
        st.pyplot(fig)
        st.subheader("Top Rated Combinations")
        top_combinations = combinations_df.sort_values('rating', ascending=False).head(5)
        st.dataframe(top_combinations)

# ------------------------- PAGE: ANALYSIS -------------------------
elif page == "Analysis":
    st.title("Wardrobe Analysis")
    if wardrobe_df.empty:
        st.info("Add some items to your wardrobe to see analysis!")
    else:
        viz_type = st.selectbox("Select Visualization Type", ["Pie Chart", "Bar Chart", "Line Chart", "Scatter Plot"])
        if viz_type in ["Pie Chart", "Bar Chart", "Line Chart"]:
            dimension = st.selectbox("Select Data Dimension", ["category", "type", "style", "color", "season"])
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
                counts = wardrobe_df[dimension].value_counts().sort_index()
                counts.plot(kind='line', marker='o', ax=ax)
                ax.set_title(f'Trend of {dimension}')
                ax.set_xlabel(dimension)
                ax.set_ylabel('Count')
            st.pyplot(fig)
        elif viz_type == "Scatter Plot":
            colA, colB = st.columns(2)
            with colA:
                x_dimension = st.selectbox("X-Axis", ["category", "type", "style", "color", "season"])
            with colB:
                y_dimension = st.selectbox("Y-Axis", ["category", "type", "style", "color", "season"])
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
        if not combinations_df.empty:
            st.subheader("Combination Ratings Analysis")
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(combinations_df['rating'], bins=11, kde=True, ax=ax)
            ax.set_title('Distribution of Outfit Ratings')
            ax.set_xlabel('Rating')
            ax.set_ylabel('Count')
            st.pyplot(fig)
            st.subheader("Top Rated Combinations")
            top_combinations = combinations_df.sort_values('rating', ascending=False).head(5)
            st.dataframe(top_combinations)

# ------------------------- PAGE: ABOUT -------------------------
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

# ------------------------- PAGE: ADMIN PANEL (For Admin Users) -------------------------
elif page == "Admin Panel" and user["role"] == "admin":
    st.title("Admin Dashboard")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    st.metric("Total Registered Users", total_users)
    cur.execute("""
        SELECT u.name, COUNT(c.id) FROM users u
        LEFT JOIN combinations c ON u.id = c.user_id
        GROUP BY u.name ORDER BY COUNT(c.id) DESC LIMIT 5
    """)
    rows = cur.fetchall()
    st.subheader("Top 5 Active Users")
    for name, count in rows:
        st.write(f"{name}: {count} combinations")
    cur.close()
    conn.close()

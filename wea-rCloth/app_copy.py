import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import bcrypt
from supabase import create_client, Client

# Set page config
st.set_page_config(page_title="wea-rCloth", layout="wide")

# Initialize Supabase client using secrets
SUPABASE_URL = "https://tnrzphomntjzwwgvsvvk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRucnpwaG9tbnRqend3Z3ZzdnZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM2NTcxNTAsImV4cCI6MjA1OTIzMzE1MH0.GEMCVRhxmw_MHAD4rmaEHoCTOGKhVuYGJo5IyGFte8k"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------- AUTHENTICATION FUNCTIONS -------------------------
def sign_up(name, email, password):
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        data = {"name": name, "email": email, "password": hashed, "role": "user"}
        result = supabase.table("user_data").insert(data).execute()
        result_dict = result.dict()
        if result_dict.get("error"):
            st.error(result_dict["error"]["message"])
            return None
        else:
            st.success("Account created successfully! Please sign in.")
            return result_dict.get("data")
    except Exception as e:
        st.error(f"Sign up failed: {e}")
        return None

def sign_in(email, password):
    result = supabase.table("user_data").select("*").eq("email", email).execute()
    result_dict = result.dict()
    if result_dict.get("error") or not result_dict.get("data"):
        st.error("User not found")
        return None
    user = result_dict.get("data")[0]
    if bcrypt.checkpw(password.encode(), user["password"].encode()):
        return user
    else:
        st.error("Invalid credentials")
        return None

def login_signup_page():
    # Skip this page if the user is already logged in
    if st.session_state.get("user_info"):
        return

    st.title("👕 wea-rCloth Login")
    option = st.radio("Choose:", ["Login", "Sign Up"])

    if option == "Login":
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")
            if submitted:
                user = sign_in(email, password)
                if user:
                    st.session_state.user_info = user
                    st.success(f"Welcome, {user['name']}!")
    else:  # Sign Up
        with st.form("signup_form"):
            name = st.text_input("Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                if sign_up(name, email, password):
                    st.success("Account created! Please sign in.")

# Call login/signup page and stop if not signed in
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

# ------------------------- DATABASE FUNCTIONS USING SUPABASE -------------------------
def load_data(user_id, role):
    if role == "admin":
        wardrobe_response = supabase.table("wardrobe_data").select("*").execute()
        combo_response = supabase.table("combination_data").select("*").execute()
    else:
        wardrobe_response = supabase.table("wardrobe_data").select("*").eq("user_id", user_id).execute()
        combo_response = supabase.table("combination_data").select("*").eq("user_id", user_id).execute()

    wardrobe_dict = wardrobe_response.dict()
    combo_dict = combo_response.dict()

    if wardrobe_dict.get("error"):
        st.error(wardrobe_dict["error"]["message"])
        wardrobe_df = pd.DataFrame()
    else:
        wardrobe_df = pd.DataFrame(wardrobe_dict.get("data"))
    if combo_dict.get("error"):
        st.error(combo_dict["error"]["message"])
        combos_df = pd.DataFrame()
    else:
        combos_df = pd.DataFrame(combo_dict.get("data"))

    # Convert array fields to comma-separated strings for display
    for col in ['style', 'season']:
        if col in wardrobe_df.columns:
            wardrobe_df[col] = wardrobe_df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    for col in ['season_match', 'style_match']:
        if col in combos_df.columns:
            combos_df[col] = combos_df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    return wardrobe_df, combos_df

def save_data():
    # Save new clothing item using capitalized keys
    if 'new_item' in st.session_state:
        item = st.session_state.new_item
        user_id = st.session_state.user_info["id"]
        data = {
            "user_id": user_id,
            "Model": item['Model'],
            "Category": item['Category'],
            "Type": item['Type'],
            "Style": item['Style'],    # stored as an array
            "Color": item['Color'],
            "Season": item['Season']   # stored as an array
        }
        response = supabase.table("wardrobe_data").insert(data).execute()
        response_dict = response.dict()
        if response_dict.get("error"):
            st.error(f"Error saving wardrobe item: {response_dict['error']['message']}")
        else:
            st.success(f"Added {item['Model']} to your wardrobe!")
        del st.session_state.new_item

    # Save new outfit combination using capitalized keys
    if 'new_combination' in st.session_state:
        combo = st.session_state.new_combination
        user_id = st.session_state.user_info["id"]
        data = {
            "user_id": user_id,
            "Combination_ID": combo['Combination_ID'],
            "Upper_Body": combo['Upper_Body'],
            "Lower_Body": combo['Lower_Body'],
            "Footwear": combo['Footwear'],
            "Season_Match": combo['Season_Match'],  # stored as an array
            "Style_Match": combo['Style_Match'],     # stored as an array
            "Rating": combo['Rating']
        }
        response = supabase.table("combination_data").insert(data).execute()
        response_dict = response.dict()
        if response_dict.get("error"):
            st.error(f"Error saving combination: {response_dict['error']['message']}")
        else:
            st.success("Saved rating for this combination!")
        del st.session_state.new_combination
        st.session_state.show_rating = False

def get_unique_values(df, column):
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
    category = st.session_state.category_select
    st.session_state.form_category = category
    if category in st.session_state.custom_types:
        st.session_state.type_options = st.session_state.custom_types[category]
    else:
        st.session_state.type_options = []

# Load data for the signed-in user
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
                wardrobe_df = pd.concat([wardrobe_df, pd.DataFrame([new_item])], ignore_index=True)
                st.session_state.new_item = new_item
                save_data()

    # ============== COLUMN 2: Generate Outfit by Season/Style ==============
    with col2:
        st.subheader("Generate Outfit Combination")

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

            except Exception as e:
                st.error("Error generating outfit combination: " + str(e))

        if st.session_state.show_rating and st.session_state.current_combination:
            combo = st.session_state.current_combination

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
            filtered_df['Style'].apply(lambda x: any(s in str(x) for s in filter_style) if pd.notna(x) else False)
        ]
    if filter_season and 'Season' in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df['Season'].apply(lambda x: any(s in str(x) for s in filter_season) if pd.notna(x) else False)
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
            combo_filtered_df["Rating"].apply(lambda x: x is not None and rating_range[0] <= x <= rating_range[1])
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
                counts = wardrobe_df[dimension].value_counts().sort_index()
                counts.plot(kind='line', marker='o', ax=ax)
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
elif page == "Admin Panel" and user["role"] == "admin":
    st.title("Admin Dashboard")
    admin_response = supabase.table("user_data").select("*").execute()
    if admin_response.error:
        st.error(admin_response.error.message)
    else:
        users = pd.DataFrame(admin_response.data)
        total_users = len(users)
        st.metric("Total Registered Users", total_users)
        combo_response = supabase.table("combination_data").select("*").execute()
        if combo_response.error:
            st.error(combo_response.error.message)
        else:
            combos = pd.DataFrame(combo_response.data)
            top_users = combos.groupby("user_id").size().reset_index(name="count").sort_values("count", ascending=False).head(5)
            st.subheader("Top 5 Active Users")
            for _, row in top_users.iterrows():
                user_id = row["user_id"]
                count = row["count"]
                user_name = users[users["id"] == user_id]["name"].values[0] if not users[users["id"] == user_id].empty else "Unknown"
                st.write(f"{user_name}: {count} combinations")

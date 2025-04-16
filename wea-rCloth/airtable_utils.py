def load_data():
    """Fetch data from Airtable instead of local CSVs."""
    wardrobe_records = wardrobe_table.all()
    combinations_records = combinations_table.all()

    loaded_wardrobe_df = pd.DataFrame(
        [rec['fields'] for rec in wardrobe_records if 'fields' in rec and rec['fields']]
    ) if wardrobe_records else pd.DataFrame()

    loaded_combinations_df = pd.DataFrame(
        [{'id': rec['id'], **rec['fields']} for rec in combinations_records if 'fields' in rec and rec['fields']]
    ) if combinations_records else pd.DataFrame()

    if not loaded_wardrobe_df.empty:
        loaded_wardrobe_df = loaded_wardrobe_df.reset_index(drop=True)
        loaded_wardrobe_df.index = loaded_wardrobe_df.index + 1

    if not loaded_combinations_df.empty:
        loaded_combinations_df = loaded_combinations_df.reset_index(drop=True)
        loaded_combinations_df.index = loaded_combinations_df.index + 1
        # Remove the 'id' column so it is not displayed in the app
        if 'id' in loaded_combinations_df.columns:
            loaded_combinations_df = loaded_combinations_df.drop(columns=['id'])

    expected_columns = ['Model', 'Category', 'Type', 'Style', 'Color', 'Season']
    for col in expected_columns:
        if col not in loaded_wardrobe_df.columns:
            loaded_wardrobe_df[col] = None

    multi_select_columns = ['Style', 'Season']
    for col in multi_select_columns:
        if col in loaded_wardrobe_df.columns:
            loaded_wardrobe_df[col] = loaded_wardrobe_df[col].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )

    return loaded_wardrobe_df, loaded_combinations_df

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

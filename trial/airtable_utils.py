# airtable_utils.py

import pandas as pd
from pyairtable import Table
import streamlit as st

WARDROBE_TABLE = Table(
    'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
    'appdgbGbEz1Dtynvg',
    'wardrobe_data'
)
COMBINATIONS_TABLE = Table(
    'patO49KbikvJl3JCT.bcc975992a1f9821a40d6341ffc296bbef4eb9f19c0fb1811e4e159f7de223ea',
    'appdgbGbEz1Dtynvg',
    'combinations_data'
)

def load_data():
    wardrobe_records = WARDROBE_TABLE.all()
    combinations_records = COMBINATIONS_TABLE.all()

    wardrobe_df = pd.DataFrame(
        [rec['fields'] for rec in wardrobe_records if 'fields' in rec and rec['fields']]
    ) if wardrobe_records else pd.DataFrame()

    combinations_df = pd.DataFrame(
        [{'id': rec['id'], **rec['fields']} for rec in combinations_records if 'fields' in rec and rec['fields']]
    ) if combinations_records else pd.DataFrame()

    if not wardrobe_df.empty:
        wardrobe_df = wardrobe_df.reset_index(drop=True)
        wardrobe_df.index = wardrobe_df.index + 1

    if not combinations_df.empty:
        combinations_df = combinations_df.reset_index(drop=True)
        combinations_df.index = combinations_df.index + 1
        if 'id' in combinations_df.columns:
            combinations_df = combinations_df.drop(columns=['id'])

    expected_columns = ['Model', 'Category', 'Type', 'Style', 'Color', 'Season']
    for col in expected_columns:
        if col not in wardrobe_df.columns:
            wardrobe_df[col] = None

    multi_select_columns = ['Style', 'Season']
    for col in multi_select_columns:
        if col in wardrobe_df.columns:
            wardrobe_df[col] = wardrobe_df[col].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )

    return wardrobe_df, combinations_df

def save_data(session_state):
    # Save new clothing item if available
    if 'new_item' in session_state:
        new_item_data = session_state.new_item
        row_dict = {}
        for key, value in new_item_data.items():
            if isinstance(value, list) and value:
                row_dict[key] = value
            elif pd.notna(value):
                row_dict[key] = value
        try:
            WARDROBE_TABLE.create(row_dict)
            st.success(f"Added {row_dict.get('Model', 'item')} to your wardrobe!")
            del session_state.new_item
        except Exception as e:
            st.error(f"Error saving to Airtable: {str(e)}")
            st.error("Check if all field names match your Airtable schema")

    # Save new outfit combination if available
    if 'new_combination' in session_state:
        new_combination_data = session_state.new_combination
        row_dict = {}
        for key, value in new_combination_data.items():
            if isinstance(value, list) and value:
                row_dict[key] = value
            elif pd.notna(value):
                row_dict[key] = value

        try:
            COMBINATIONS_TABLE.create(row_dict)
            st.success("Saved rating for this combination!")
            del session_state.new_combination
            session_state.show_rating = False  # Reset rating UI state
        except Exception as e:
            st.error(f"Error saving combination to Airtable: {str(e)}")
            st.error(f"Data being sent: {row_dict}")

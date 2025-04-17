# wardrobe_helpers.py

import pandas as pd

def get_unique_values(df, column):
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

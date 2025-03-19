# !pip install streamlit pandas matplotlib seaborn


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Create or load wardrobe data
try:
    wardrobe_df = pd.read_csv('/content/drive/MyDrive/Data Sets/wardrobe_data.csv')
except:
    wardrobe_df = pd.DataFrame(columns=[
        'Model', 'Category', 'Type', 'TypeNumber', 'Style', 'Color', 'Season'
    ])

# Create or load combinations data
try:
    combinations_df = pd.read_csv('/content/drive/MyDrive/Data Sets/combinations_data.csv')
except:
    combinations_df = pd.DataFrame(columns=[
        'CombinationID', 'UpperBody', 'LowerBody', 'Footwear', 'Season', 'Style', 'Rating'
    ])

# ! pip install streamlit -q
#
# !wget -q -O - ipv4.icanhazip.com
#
# ! streamlit run '/content/drive/MyDrive/Data Sets/apps_streamlit/app.py'.py & npx localtunnel --port 8501
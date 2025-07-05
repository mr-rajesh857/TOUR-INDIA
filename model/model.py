# ml_model/model.py
import pandas as pd
import re

file_path = "ml_model/tourism1_cleaned.csv"
df = pd.read_csv(file_path)

# Clean Data
df['Place'] = df['Place'].apply(lambda x: re.sub(r'^[\d\.\s]+', '', str(x)).strip())
df_clean = df.dropna(subset=['State', 'City', 'Place', 'Place_desc'])

def predict_places(state, city):
    location_df = df_clean[(df_clean['State'] == state) & (df_clean['City'] == city)]
    if location_df.empty:
        return []
    return location_df[['Place', 'Place_desc']].head(10).values.tolist()

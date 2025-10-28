import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib

# Load both datasets
crop_df = pd.read_csv("data/combined_crop_stage_dataset.csv")
fert_df = pd.read_csv("data/Fertilizer Prediction.csv")

# Combine crop names
all_crops = pd.concat([crop_df['crop'], fert_df['Crop Type']]).unique()

# Retrain encoder
encoder = LabelEncoder()
encoder.fit(all_crops)

# Save it again
joblib.dump(encoder, "backend/models/pkl/modelA/crop_encoder.pkl")

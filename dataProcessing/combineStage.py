import pandas as pd
import glob

dfs = []
for f in glob.glob("data/stages/*.csv"):
    df = pd.read_csv(f)
    dfs.append(df)

data = pd.concat(dfs, ignore_index=True)
print("Combined shape:", data.shape)
data.to_csv("data/combined_crop_stage_dataset.csv", index=False)
print("✅ Combined dataset saved as combined_crop_stage_dataset.csv")
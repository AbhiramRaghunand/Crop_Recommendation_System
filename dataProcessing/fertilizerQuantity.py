import pandas as pd

df=pd.read_csv(r"C:\ABHIRAM\Mini Project\crop_system\data\Fertilizer Prediction.csv")

optimal_npk = {
    "Paddy": {"N": 150, "P": 75, "K": 75},     # alias of rice
    "Wheat": {"N": 120, "P": 60, "K": 40},
    "Maize": {"N": 140, "P": 70, "K": 70},
    "Cotton": {"N": 100, "P": 50, "K": 50},
    "Sugarcane": {"N": 250, "P": 115, "K": 120},
    "Ground Nuts": {"N": 40, "P": 60, "K": 70},
    "Tobacco": {"N": 90, "P": 60, "K": 90},
    "Barley": {"N": 80, "P": 40, "K": 40},
    "Millets": {"N": 80, "P": 40, "K": 40},
    "Oil seeds": {"N": 60, "P": 40, "K": 40},
    "Pulses": {"N": 25, "P": 50, "K": 30}
}

def compute_deficiency(row):
    crop=row["Crop Type"]
    if crop not in optimal_npk:
        return row["Nitrogen"],row["Phosphorous"],row["Potassium"]
    opt=optimal_npk[crop]
    N_need=max(opt["N"]-row["Nitrogen"],0)
    P_need=max(opt["P"]-row["Phosphorous"],0)
    K_need=max(opt["K"]-row["Potassium"],0)
    return N_need,P_need,K_need

df[["N_need", "P_need", "K_need"]]= df.apply(lambda r: pd.Series(compute_deficiency(r)), axis=1)

fertilizer_content = {
    "Urea": {"N": 46, "P": 0, "K": 0},
    "DAP": {"N": 18, "P": 46, "K": 0},
    "MOP": {"N": 0, "P": 0, "K": 60},
    "NPK": {"N": 15, "P": 15, "K": 15},
    "10-26-26": {"N": 10, "P": 26, "K": 26},
    "14-35-14": {"N": 14, "P": 35, "K": 14},
    "17-17-17": {"N": 17, "P": 17, "K": 17},
    "20-20": {"N": 20, "P": 20, "K": 0},
    "28-28": {"N": 28, "P": 28, "K": 0}
}

def calculate_fert_amount(row):
    fert = row["Fertilizer Name"]
    if fert not in fertilizer_content:
        return None
    comp = fertilizer_content[fert]
    total = 0
    count = 0

    if comp["N"] > 0:
        total += (row["N_need"] / comp["N"]) * 100
        count += 1
    if comp["P"] > 0:
        total += (row["P_need"] / comp["P"]) * 100
        count += 1
    if comp["K"] > 0:
        total += (row["K_need"] / comp["K"]) * 100
        count += 1

    return round(total / count, 2) if count > 0 else None

df["Fertilizer Quantity"] = df.apply(calculate_fert_amount, axis=1)

df["Fertilizer Quantity (kg/acre)"] = (df["Fertilizer Quantity"] / 2.47).round(2)

output_path = r"C:\ABHIRAM\Mini Project\crop_system\data\Fertilizer Prediction.csv"
df.to_csv(output_path, index=False)
print("✅ Fertilizer quantities calculated and saved to:", output_path)
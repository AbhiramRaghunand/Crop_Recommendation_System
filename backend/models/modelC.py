import pandas as pd
from sklearn.preprocessing import LabelEncoder,StandardScaler
from sklearn.metrics import r2_score,mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib

#load data
df=pd.read_csv(r"C:\ABHIRAM\Mini Project\crop_system\data\irrigation_synthetic_medium_v2.csv")

#select features and targets
target="Water_Requirement"
X=df.drop(columns=["Water_Requirement","Irrigation_Level","Date","State","District"])
y=df[target]

#Encode categorical columns
cat_cols = X.select_dtypes(include="object").columns
encoders = {}

for col in cat_cols:
    le = LabelEncoder()
    le.fit(X[col])  # learns all categories, including new soils
    X[col] = le.transform(X[col])
    encoders[col] = le

#Scaling
scaler=StandardScaler()
X_scaled=scaler.fit_transform(X)

#Train test split
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42)
print("Train and test split done")

#train model
model=RandomForestRegressor(n_estimators=200,random_state=42)
model.fit(X_train,y_train)
print("Model training done")

#Evaluate
preds=model.predict(X_test)
print("R2 score:",round(r2_score(y_test,preds),3))
print("RMSE:",round((mean_squared_error(y_test, preds) ** 0.5),3))

#retrain on full data
model.fit(X,y)
print("Final model retrained on full data")

#Save model and encoders
joblib.dump(model,"backend/models/pkl/irrigation_model.pkl")
joblib.dump(model,"backend/models/pkl/season_encoder.pkl")
print("Model and encoders saved")
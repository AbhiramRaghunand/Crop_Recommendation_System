import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split,StratifiedKFold,cross_val_score
import joblib
from sklearn.preprocessing import LabelEncoder,StandardScaler
from sklearn.metrics import classification_report,accuracy_score,r2_score,mean_squared_error
from xgboost import XGBClassifier,XGBRegressor

df=pd.read_csv(r'C:\\ABHIRAM\Mini Project\\crop_system\\data\\Fertilizer Prediction.csv')


#Encode categorical features
soilType_enc=LabelEncoder()
crop_encoder=joblib.load('backend/models/pkl/modelA/crop_encoder.pkl')
fert_enc=LabelEncoder()

df["soil_encoded"]=soilType_enc.fit_transform(df["Soil Type"])
df["crop_encoded"]=crop_encoder.transform(df["Crop Type"])
df["fert_encoded"]=fert_enc.fit_transform(df["Fertilizer Name"])

#Fill missing values
# df = df.fillna(df.median())



#Features and Targets
features=["Temparature","Humidity ","Moisture","soil_encoded","crop_encoded","Nitrogen","Potassium","Phosphorous","N_need","P_need","K_need"]
X=df[features]
y_class=df["fert_encoded"]
y_reg=df["Fertilizer Quantity (kg/acre)"]

#Scaleing
scaler=StandardScaler()
X_scaled=scaler.fit_transform(X)

#training test split
# Split once only!
X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
    X_scaled, y_class, y_reg,
    test_size=0.2,
    random_state=42,
    stratify=y_class
)
print("Data split into training and test")

#Training XGBoost classifier
clf=XGBClassifier(
    objective='multi:softmax',
    eval_metric='mlogloss',
    num_class=len(fert_enc.classes_),
    n_estimators=300,
    learning_rate=0.1,
    max_depth=5,
    random_state=42
)
clf.fit(X_train,y_class_train)

reg=XGBRegressor(
    objective='reg:squarederror',
    n_estimators=400,
    learning_rate=0.1,
    max_depth=5,
    random_state=42
)
reg.fit(X_train,y_reg_train)
print("Model trained")

#Predict
y_pred_class=clf.predict(X_test)
print("\nFertilizer Type classifier")
print("Acuuracy Score:",accuracy_score(y_class_test,y_pred_class))
print("Classification Report:\n",
      classification_report(
          y_class_test, 
          y_pred_class, 
          labels=range(len(fert_enc.classes_)), 
          target_names=fert_enc.classes_,
          zero_division=0
      )
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(clf, X_scaled, y_class, cv=cv, scoring='accuracy')
print(f"Cross-validation accuracies: {scores}")
print(f"Mean accuracy: {np.mean(scores):.4f} ± {np.std(scores):.4f}")

#Regression
y_pred_reg=reg.predict(X_test)
print("\nFertilizer Quantity Regressor")
print("R2 Score:", round(r2_score(y_reg_test,y_pred_reg),3))
print("RMSE:",round((mean_squared_error(y_reg_test, y_pred_reg) ** 0.5),3))

#Retrain on full data
clf.fit(X_scaled, y_class)
reg.fit(X_scaled, y_reg)
print("Final model retrained on full data")

#save model and encoders
joblib.dump(clf,"backend/models/pkl/fertilizer_type_model.pkl")
joblib.dump(reg,"backend/models/pkl/fertilizer_quantity_model.pkl")
joblib.dump(soilType_enc,"backend/models/pkl/soilType_encoder.pkl")  
joblib.dump(fert_enc,"backend/models/pkl/fertilizer_encoder.pkl")
joblib.dump(scaler,"backend/models/pkl/fertilizer_scaler.pkl")
print("Models and encoders saved")
  



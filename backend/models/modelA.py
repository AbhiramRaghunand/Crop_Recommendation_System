from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report,confusion_matrix,accuracy_score
import pandas as pd
import joblib

data = pd.read_csv("data/combined_crop_stage_dataset.csv")
print("Loaded dataset with shape:", data.shape)

data=data.dropna(subset=['NDVI','temp','PRECTOTCORR','humidity','stage_label'])

crop_encoder=LabelEncoder()
data['crop_encoded']=crop_encoder.fit_transform(data['crop'])

stage_encoder=LabelEncoder()
data['stage_encoded']=stage_encoder.fit_transform(data['stage_label'])


features=['NDVI','temp','PRECTOTCORR','humidity','days_since_sowing','crop_encoded']
X=data[features]
print (X.columns)
y=data['stage_encoded']
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
print("Spliting Done")
#=======================================================================
# model=RandomForestClassifier(n_estimators=150,random_state=42)
# model.fit(X_train,y_train)

# preds=model.predict(X_test)
# print(classification_report(y_test, preds, target_names=stage_encoder.classes_))
#======================================================================================
# xgb = XGBClassifier(
#     n_estimators=300,
#     learning_rate=0.05,
#     max_depth=6,
#     subsample=0.8,
#     colsample_bytree=0.8,
#     eval_metric='mlogloss',
#     random_state=42
# )

# xgb.fit(X_train, y_train)

# y_pred = xgb.predict(X_test)

# print("Accuracy:", accuracy_score(y_test, y_pred))
# print(classification_report(y_test, y_pred, target_names=stage_encoder.classes_))

# scores = cross_val_score(xgb, X, y, cv=5)
# print(scores.mean(), scores.std())

#==================================================================================================
param_grid = {
    'n_estimators': [200, 300, 400],
    'max_depth': [4, 6, 8],               # Controls tree depth (higher = more complex)
    'learning_rate': [0.05, 0.1],         # Controls step size (lower = more careful)
    'subsample': [0.8, 1],                # Fraction of samples for each tree (regularization)
    'colsample_bytree': [0.8, 1],         # Fraction of features to use in each tree
    'gamma': [0, 1, 5],                   # Minimum loss reduction to make a further partition
    'objective': ['multi:softmax'],       # Multi-class classification
    'eval_metric': ['mlogloss'],          # Log-loss for multi-class
    'num_class': [4]                      # Adjust according to the number of stages in your problem
}

xgb_model = XGBClassifier(random_state=42)

grid_search = GridSearchCV(
    estimator=xgb_model,
    param_grid=param_grid,
    cv=5,                                  # 5-fold cross-validation
    n_jobs=-1,                             # Use all available CPUs
    scoring='accuracy',                    # Metric to optimize (accuracy)
    verbose=1                              # Shows progress
)

grid_search.fit(X_train, y_train)

# Display the best parameters
print("Best Parameters:", grid_search.best_params_)
print("Best CV Score:", grid_search.best_score_)

# Predict using the best model
y_pred = grid_search.best_estimator_.predict(X_test)

# Evaluate the model
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=stage_encoder.classes_))

# Accuracy score
print("Accuracy:", accuracy_score(y_test, y_pred))

#==========================================================================================
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.utils import shuffle

# 1️⃣ Shuffle test
y_shuffled = shuffle(y, random_state=42)
score_shuffled = cross_val_score(grid_search.best_estimator_, X, y_shuffled, cv=5).mean()
print(f"🔍 Shuffle test accuracy: {score_shuffled:.3f}")
if score_shuffled > 0.35:
    print("⚠️ Possible leakage — model still predicts well on random labels.")
else:
    print("✅ Passed shuffle test — no leakage detected.")

# 2️⃣ Feature–label correlation
print("\n🔍 Feature–label correlation check:")
label_factorized = pd.factorize(data['stage_label'])[0]
for col in X.columns:
    corr = np.corrcoef(X[col], label_factorized)[0,1]
    print(f"{col:15}: {corr:.3f}")

# 3️⃣ NDVI/time separability visual (optional)
import seaborn as sns
import matplotlib.pyplot as plt
sns.scatterplot(data=data, x='days_since_sowing', y='NDVI', hue='stage_label')
plt.title("NDVI vs Days Since Sowing by Stage")
plt.show()
#==============================================================================================



# joblib.dump(model, "crop_stage_model.pkl")
joblib.dump(xgb_model, "backend/models/pkl/modelA/crop_stage_model.pkl")
joblib.dump(crop_encoder, "backend/models/pkl/modelA/crop_encoder.pkl")
joblib.dump(stage_encoder, "backend/models/pkl/modelA/stage_encoder.pkl")









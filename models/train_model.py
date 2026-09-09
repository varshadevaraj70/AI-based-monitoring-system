import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix

DATA_PATH = "../data/landslide_data.csv"
FEATURES = ["rainfall_mm", "soil_moisture", "slope_deg", "ground_movement_mm", "elevation_m"]
TARGET = "landslide"

data = pd.read_csv(DATA_PATH)
required = FEATURES + [TARGET]
missing = [c for c in required if c not in data.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

data = data.dropna(subset=required)
data = data[
    (data["rainfall_mm"] >= 0) &
    (data["soil_moisture"].between(0, 100)) &
    (data["slope_deg"].between(0, 90)) &
    (data["ground_movement_mm"] >= 0) &
    (data["elevation_m"] >= 0)
]

X = data[FEATURES]
y = data[TARGET].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=14,
    min_samples_split=4,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

print(f"Accuracy : {accuracy_score(y_test, predictions) * 100:.2f}%")
print(f"Precision: {precision_score(y_test, predictions, zero_division=0) * 100:.2f}%")
print(f"Recall   : {recall_score(y_test, predictions, zero_division=0) * 100:.2f}%")
print(f"F1 Score : {f1_score(y_test, predictions, zero_division=0) * 100:.2f}%")
print("\nConfusion Matrix:\n", confusion_matrix(y_test, predictions))
print("\nClassification Report:\n", classification_report(y_test, predictions, zero_division=0))

importance = pd.DataFrame({
    "Feature": FEATURES,
    "Importance": model.feature_importances_
}).sort_values("Importance", ascending=False)

print("\nFeature Importance:\n", importance.to_string(index=False))

joblib.dump(model, "landslide_model.pkl")
importance.to_csv("../data/feature_importance.csv", index=False)
print("\nModel saved: models/landslide_model.pkl")

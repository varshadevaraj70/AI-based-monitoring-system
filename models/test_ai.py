import joblib
import pandas as pd

model = joblib.load("landslide_model.pkl")

data = pd.DataFrame([{
    "rainfall_mm": 180,
    "soil_moisture": 88,
    "slope_deg": 38,
    "ground_movement_mm": 15,
    "elevation_m": 2500
}])

prediction = model.predict(data)[0]
probability = model.predict_proba(data)[0][1] * 100

print("Landslide Prediction:", prediction)
print("Landslide Probability:", round(probability, 2), "%")

if probability >= 80:
    level = "CRITICAL"
elif probability >= 60:
    level = "HIGH"
elif probability >= 40:
    level = "MODERATE"
else:
    level = "LOW"

print("Risk Level:", level)
from alert_engine import generate_alert


alert = generate_alert(
    location="Tawang, Arunachal Pradesh",
    probability=86.5,
    rainfall=180,
    soil_moisture=88,
    slope=38,
    ground_movement=15
)


print("==============================")
print("LANDSLIDE EARLY WARNING")
print("==============================")

print("Location:", alert["location"])
print("Risk Level:", alert["risk_level"])
print("Probability:", alert["probability"], "%")

print("\nEnvironmental Conditions")
print("------------------------------")

print("Rainfall:", alert["rainfall"], "mm")
print("Soil Moisture:", alert["soil_moisture"], "%")
print("Slope:", alert["slope"], "degrees")
print("Ground Movement:", alert["ground_movement"], "mm")

print("\nWARNING")
print("------------------------------")
print(alert["message"])

print("\nRecommended Action")
print("------------------------------")
print(alert["action"])

print("\nTime:", alert["timestamp"])
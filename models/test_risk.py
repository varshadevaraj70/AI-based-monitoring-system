from risk_engine import calculate_risk


risk, level = calculate_risk(
    rainfall=164,
    soil_moisture=89,
    slope=38,
    ground_movement=12,
    elevation=2400
)

print("Risk Score:", risk)
print("Risk Level:", level)
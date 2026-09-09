def calculate_risk(
    rainfall,
    soil_moisture,
    slope,
    ground_movement,
    elevation
):

    rainfall_score = min(
        (rainfall / 200) * 100,
        100
    )

    moisture_score = min(
        soil_moisture,
        100
    )

    slope_score = min(
        (slope / 45) * 100,
        100
    )

    movement_score = min(
        (ground_movement / 20) * 100,
        100
    )

    elevation_score = min(
        (elevation / 3000) * 100,
        100
    )

    risk_score = (
        rainfall_score * 0.30
        + moisture_score * 0.20
        + slope_score * 0.20
        + movement_score * 0.20
        + elevation_score * 0.10
    )

    risk_score = round(
        risk_score,
        2
    )

    if risk_score >= 80:

        risk_level = "CRITICAL"

    elif risk_score >= 60:

        risk_level = "HIGH"

    elif risk_score >= 40:

        risk_level = "MODERATE"

    else:

        risk_level = "LOW"

    return risk_score, risk_level
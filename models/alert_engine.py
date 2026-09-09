from datetime import datetime


def generate_alert(
    location,
    probability,
    rainfall,
    soil_moisture,
    slope,
    ground_movement
):

    if probability >= 80:

        level = "CRITICAL"

        message = (
            f"Immediate landslide danger detected at {location}. "
            "Emergency monitoring and response recommended."
        )

        action = (
            "Inspect vulnerable roads, restrict unsafe routes "
            "and prepare community warning."
        )

    elif probability >= 60:

        level = "HIGH"

        message = (
            f"High landslide risk detected at {location}. "
            "Increased monitoring is required."
        )

        action = (
            "Inspect slopes and roads and keep emergency "
            "response teams prepared."
        )

    elif probability >= 40:

        level = "MODERATE"

        message = (
            f"Moderate landslide risk detected at {location}. "
            "Continue environmental monitoring."
        )

        action = (
            "Monitor rainfall, soil moisture and ground movement."
        )

    else:

        level = "LOW"

        message = (
            f"Low landslide risk detected at {location}. "
            "No immediate high-risk condition detected."
        )

        action = (
            "Continue routine monitoring."
        )


    return {
        "location": location,
        "risk_level": level,
        "probability": round(probability, 2),
        "rainfall": rainfall,
        "soil_moisture": soil_moisture,
        "slope": slope,
        "ground_movement": ground_movement,
        "message": message,
        "action": action,
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }
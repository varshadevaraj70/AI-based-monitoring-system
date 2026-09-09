import requests


def get_weather(latitude, longitude):

    """
    Get current weather information.
    """

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation,rain",
        "timezone": "auto"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        current = data.get(
            "current",
            {}
        )

        return {
            "temperature": current.get(
                "temperature_2m"
            ),

            "precipitation": current.get(
                "precipitation"
            ),

            "rain": current.get(
                "rain"
            )
        }

    except requests.RequestException as error:

        print(
            "Weather API error:",
            error
        )

        return None
from weather import get_weather


# Tawang
latitude = 27.586
longitude = 91.859


weather = get_weather(
    latitude,
    longitude
)


if weather:

    print(
        "Weather Data"
    )

    print(
        "------------------"
    )

    print(
        "Temperature:",
        weather["temperature"],
        "°C"
    )

    print(
        "Precipitation:",
        weather["precipitation"],
        "mm"
    )

    print(
        "Rain:",
        weather["rain"],
        "mm"
    )

else:

    print(
        "Unable to retrieve weather data."
    )
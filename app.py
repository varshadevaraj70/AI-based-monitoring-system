import base64
import math
import sqlite3
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
import folium
from streamlit_folium import st_folium

from models.risk_engine import calculate_risk


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

IMAGE_PATH = BASE_DIR / "assets" / "background.jpg"
MODEL_PATH = BASE_DIR / "models" / "landslide_model.pkl"
DB_PATH = BASE_DIR / "data" / "incidents.db"

RISK_DATA_PATH = BASE_DIR / "data" / "risk_locations.csv"
ROAD_DATA_PATH = BASE_DIR / "data" / "road_risk.csv"
INFRA_DATA_PATH = BASE_DIR / "data" / "infrastructure_risk.csv"
VILLAGE_DATA_PATH = BASE_DIR / "data" / "village_risk.csv"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NER Landslide Early Warning System",
    page_icon="⛰️",
    layout="wide"
)


# ============================================================
# BACKGROUND
# ============================================================

def set_background(image_path):

    if image_path.exists():

        with open(image_path, "rb") as image_file:

            encoded = base64.b64encode(
                image_file.read()
            ).decode()

        st.markdown(
            f"""
            <style>

            .stApp {{
                background-image:
                    linear-gradient(
                        rgba(0, 0, 0, 0.72),
                        rgba(0, 0, 0, 0.72)
                    ),
                    url("data:image/jpeg;base64,{encoded}");

                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}

            .block-container {{
                padding-top: 1.5rem;
            }}

            </style>
            """,
            unsafe_allow_html=True
        )


set_background(IMAGE_PATH)


# ============================================================
# INCIDENT DATABASE
# ============================================================

def init_incident_db():
    """Create the local SQLite database used for geo-tagged reports."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reported_at TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                severity TEXT NOT NULL,
                road_blocked TEXT NOT NULL,
                village TEXT,
                description TEXT,
                photo_name TEXT,
                photo_data BLOB
            )
            """
        )
        conn.commit()


def save_incident(latitude, longitude, severity, road_blocked,
                  village, description, photo_name, photo_data):
    """Store a geo-tagged incident report in SQLite."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO incidents
            (reported_at, latitude, longitude, severity, road_blocked,
             village, description, photo_name, photo_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                float(latitude),
                float(longitude),
                severity,
                road_blocked,
                village,
                description,
                photo_name,
                photo_data,
            ),
        )
        conn.commit()


def load_incidents(include_photo=False):
    """Load incident reports from SQLite."""
    columns = "id, reported_at, latitude, longitude, severity, road_blocked, village, description, photo_name"
    if include_photo:
        columns += ", photo_data"
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            f"SELECT {columns} FROM incidents ORDER BY id DESC",
            conn,
        )


init_incident_db()


# ============================================================
# LOAD MODEL
# ============================================================

@st.cache_resource
def load_model():

    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)

    return None


model = load_model()


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_csv(path):

    if path.exists():

        try:
            return pd.read_csv(path)

        except Exception:
            return pd.DataFrame()

    return pd.DataFrame()


risk_df = load_csv(RISK_DATA_PATH)
road_df = load_csv(ROAD_DATA_PATH)
infra_df = load_csv(INFRA_DATA_PATH)
village_df = load_csv(VILLAGE_DATA_PATH)


# ============================================================
# AI PROBABILITY
# ============================================================

def get_ai_probability(row):

    rainfall = float(
        row.get("rainfall_mm", 100)
    )

    moisture = float(
        row.get("soil_moisture", 60)
    )

    slope = float(
        row.get("slope_deg", 30)
    )

    movement = float(
        row.get("ground_movement_mm", 5)
    )

    elevation = float(
        row.get("elevation_m", 1500)
    )

    # Use trained model when available

    if model is not None:

        try:

            input_data = pd.DataFrame(
                [[
                    rainfall,
                    moisture,
                    slope,
                    movement,
                    elevation
                ]],
                columns=[
                    "rainfall_mm",
                    "soil_moisture",
                    "slope_deg",
                    "ground_movement_mm",
                    "elevation_m"
                ]
            )

            probability = (
                model.predict_proba(
                    input_data
                )[0][1] * 100
            )

            return round(
                float(probability),
                2
            )

        except Exception:
            pass

    # Fallback transparent risk engine

    score, _ = calculate_risk(
        rainfall,
        moisture,
        slope,
        movement,
        elevation
    )

    return score


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = lat2 - lat1

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(probability):

    if probability >= 80:
        return "CRITICAL"

    elif probability >= 60:
        return "HIGH"

    elif probability >= 40:
        return "MODERATE"

    return "LOW"


# ============================================================
# VILLAGE PRIORITY CALCULATION
# ============================================================

def calculate_village_priorities():

    if village_df.empty:
        return pd.DataFrame()

    risk_points = []

    # --------------------------------------------
    # CREATE AI RISK POINTS
    # --------------------------------------------

    if not risk_df.empty:

        for _, row in risk_df.iterrows():

            probability = get_ai_probability(
                row
            )

            risk_points.append(
                {
                    "latitude":
                        float(row["latitude"]),

                    "longitude":
                        float(row["longitude"]),

                    "probability":
                        probability,

                    "risk_level":
                        get_risk_level(
                            probability
                        )
                }
            )


    results = []

    # --------------------------------------------
    # PROCESS EVERY VILLAGE
    # --------------------------------------------

    for _, row in village_df.iterrows():

        village_lat = float(
            row["latitude"]
        )

        village_lon = float(
            row["longitude"]
        )

        # ----------------------------------------
        # FIND NEAREST RISK LOCATION
        # ----------------------------------------

        nearest_probability = 0
        nearest_risk_level = "LOW"
        nearest_distance = None

        for point in risk_points:

            distance = calculate_distance(
                village_lat,
                village_lon,
                point["latitude"],
                point["longitude"]
            )

            if (
                nearest_distance is None
                or distance < nearest_distance
            ):

                nearest_distance = distance

                nearest_probability = (
                    point["probability"]
                )

                nearest_risk_level = (
                    point["risk_level"]
                )


        # ----------------------------------------
        # POPULATION SCORE — 20%
        # ----------------------------------------

        population = float(
            row.get(
                "population",
                0
            )
        )

        population_score = min(
            population / 20000 * 100,
            100
        )


        # ----------------------------------------
        # ROAD CONNECTIVITY — 20%
        #
        # Lower connectivity = higher priority
        # ----------------------------------------

        connectivity = str(
            row.get(
                "road_connectivity",
                "Medium"
            )
        ).lower()

        if connectivity == "low":

            connectivity_score = 100

        elif connectivity == "medium":

            connectivity_score = 60

        else:

            connectivity_score = 30


        # ----------------------------------------
        # IMPORTANCE — 20%
        # ----------------------------------------

        importance = str(
            row.get(
                "importance",
                "Medium"
            )
        ).lower()

        if importance == "critical":

            importance_score = 100

        elif importance == "high":

            importance_score = 70

        else:

            importance_score = 40


        # ----------------------------------------
        # AI RISK — 40%
        # ----------------------------------------

        ai_score = nearest_probability


        # ----------------------------------------
        # FINAL BALANCED SCORE
        # ----------------------------------------

        priority_score = (

            ai_score * 0.40

            + population_score * 0.20

            + connectivity_score * 0.20

            + importance_score * 0.20
        )

        priority_score = round(
            priority_score,
            2
        )


        # ----------------------------------------
        # PRIORITY LEVEL
        # ----------------------------------------

        if priority_score >= 75:

            priority = "PRIORITY 1"

        elif priority_score >= 50:

            priority = "PRIORITY 2"

        else:

            priority = "PRIORITY 3"


        # ----------------------------------------
        # AUTOMATIC ALERT LEVEL
        # ----------------------------------------

        if (
            nearest_probability >= 80
            or priority_score >= 85
        ):

            alert_level = "CRITICAL"

        elif (
            nearest_probability >= 60
            or priority_score >= 70
        ):

            alert_level = "HIGH"

        elif (
            nearest_probability >= 40
            or priority_score >= 50
        ):

            alert_level = "MODERATE"

        else:

            alert_level = "LOW"


        # ----------------------------------------
        # AUTOMATIC RESPONSE
        # ----------------------------------------

        if alert_level == "CRITICAL":

            action = (
                "Immediate field assessment recommended. "
                "Prepare community warning and inspect "
                "vulnerable roads."
            )

        elif alert_level == "HIGH":

            action = (
                "Increase monitoring, inspect slopes and "
                "keep emergency response teams prepared."
            )

        elif alert_level == "MODERATE":

            action = (
                "Continue monitoring rainfall, soil moisture "
                "and ground movement."
            )

        else:

            action = (
                "Continue routine environmental monitoring."
            )


        # ----------------------------------------
        # STORE RESULT
        # ----------------------------------------

        results.append(
            {
                "Village":
                    row.get(
                        "village",
                        "Unknown"
                    ),

                "State":
                    row.get(
                        "state",
                        "Unknown"
                    ),

                "Population":
                    int(population),

                "AI Risk (%)":
                    round(
                        nearest_probability,
                        2
                    ),

                "Risk Level":
                    nearest_risk_level,

                "Distance to Risk Zone (km)":
                    round(
                        nearest_distance,
                        2
                    )
                    if nearest_distance is not None
                    else None,

                "Road Connectivity":
                    row.get(
                        "road_connectivity",
                        "Unknown"
                    ),

                "Importance":
                    row.get(
                        "importance",
                        "Unknown"
                    ),

                "Priority":
                    priority,

                "Priority Score":
                    priority_score,

                "Alert":
                    alert_level,

                "Recommended Action":
                    action,

                "Nearest Hospital":
                    row.get(
                        "nearest_hospital",
                        "Unknown"
                    )
            }
        )


    return pd.DataFrame(results)


# ============================================================
# GENERATE VILLAGE RESULTS
# ============================================================

village_results_df = calculate_village_priorities()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "⛰️ NER Landslide AI"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Risk Map",
        "Alerts",
        "Sensors",
        "Analytics",
        "Incident Reporting",
        "Reports",
        "Settings"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    """
    **AI-Based Early Warning System**

    Monitor → Predict → Prioritize → Alert
    """
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title(
        "⛰️ NER Landslide Early Warning System"
    )

    st.markdown(
        """
        ### AI-Based Risk Monitoring & Early Warning Platform

        Monitor rainfall, soil moisture, slope, ground movement,
        vulnerable communities, roads and infrastructure.
        """
    )

    # --------------------------------------------
    # METRICS
    # --------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    critical_count = 0
    high_count = 0

    if not village_results_df.empty:

        critical_count = len(
            village_results_df[
                village_results_df["Alert"]
                == "CRITICAL"
            ]
        )

        high_count = len(
            village_results_df[
                village_results_df["Alert"]
                == "HIGH"
            ]
        )

    with col1:

        st.metric(
            "🚨 Critical Alerts",
            critical_count
        )

    with col2:

        st.metric(
            "⚠️ High Alerts",
            high_count
        )

    with col3:

        st.metric(
            "🏘️ Villages Monitored",
            len(village_df)
        )

    with col4:

        st.metric(
            "🛣️ Roads Monitored",
            len(road_df)
        )


    st.markdown("---")


    # --------------------------------------------
    # LIVE WEATHER
    # --------------------------------------------

    st.subheader(
        "🌧️ Live Weather — Tawang"
    )

    w1, w2, w3 = st.columns(3)

    try:

        from services.weather import get_weather

        weather = get_weather(
            latitude=27.586,
            longitude=91.859
        )

        if weather:

            with w1:

                st.metric(
                    "Temperature",
                    f"{weather['temperature']} °C"
                )

            with w2:

                st.metric(
                    "Precipitation",
                    f"{weather['precipitation']} mm"
                )

            with w3:

                st.metric(
                    "Rain",
                    f"{weather['rain']} mm"
                )

        else:

            st.warning(
                "Weather data unavailable."
            )

    except Exception:

        st.warning(
            "Unable to retrieve weather data."
        )


    st.markdown("---")


    # --------------------------------------------
    # AI DEMO
    # --------------------------------------------

    st.subheader(
        "🤖 AI Landslide Risk Prediction"
    )

    c1, c2 = st.columns(2)

    with c1:

        rainfall = st.slider(
            "Rainfall (mm)",
            0,
            300,
            160
        )

        soil_moisture = st.slider(
            "Soil Moisture (%)",
            0,
            100,
            85
        )

        slope = st.slider(
            "Slope (degrees)",
            0,
            60,
            35
        )

    with c2:

        ground_movement = st.slider(
            "Ground Movement (mm)",
            0,
            30,
            12
        )

        elevation = st.slider(
            "Elevation (m)",
            0,
            5000,
            2400
        )

        if st.button(
            "🔍 Analyze Landslide Risk",
            use_container_width=True
        ):

            risk_score, risk_level = calculate_risk(
                rainfall,
                soil_moisture,
                slope,
                ground_movement,
                elevation
            )

            st.metric(
                "Risk Score",
                f"{risk_score}%"
            )

            if risk_level == "CRITICAL":

                st.error(
                    "🚨 CRITICAL RISK"
                )

            elif risk_level == "HIGH":

                st.warning(
                    "⚠️ HIGH RISK"
                )

            elif risk_level == "MODERATE":

                st.info(
                    "🟡 MODERATE RISK"
                )

            else:

                st.success(
                    "🟢 LOW RISK"
                )

            if model is not None:

                input_data = pd.DataFrame(
                    [[
                        rainfall,
                        soil_moisture,
                        slope,
                        ground_movement,
                        elevation
                    ]],
                    columns=[
                        "rainfall_mm",
                        "soil_moisture",
                        "slope_deg",
                        "ground_movement_mm",
                        "elevation_m"
                    ]
                )

                probability = (
                    model.predict_proba(
                        input_data
                    )[0][1] * 100
                )

                st.metric(
                    "AI Landslide Probability",
                    f"{probability:.2f}%"
                )


# ============================================================
# RISK MAP
# ============================================================

elif page == "Risk Map":

    st.title(
        "🗺️ AI Risk & Community Monitoring Map"
    )

    st.markdown(
        """
        The map combines AI landslide risk with community
        vulnerability to support response prioritization.
        """
    )

    st.sidebar.markdown(
        "### Map Layers"
    )

    show_risk = st.sidebar.checkbox(
        "Landslide Risk",
        True
    )

    show_roads = st.sidebar.checkbox(
        "Roads",
        True
    )

    show_infrastructure = st.sidebar.checkbox(
        "Infrastructure",
        True
    )

    show_villages = st.sidebar.checkbox(
        "Villages",
        True
    )

    high_risk_only = st.sidebar.checkbox(
        "High Risk Only",
        False
    )


    # --------------------------------------------
    # MAP
    # --------------------------------------------

    m = folium.Map(
        location=[
            25.8,
            92.0
        ],
        zoom_start=6,
        tiles="OpenStreetMap"
    )


    # --------------------------------------------
    # RISK LAYER
    # --------------------------------------------

    risk_layer = folium.FeatureGroup(
        name="AI Landslide Risk"
    )

    if show_risk and not risk_df.empty:

        for _, row in risk_df.iterrows():

            probability = get_ai_probability(
                row
            )

            level = get_risk_level(
                probability
            )

            if (
                high_risk_only
                and level not in [
                    "HIGH",
                    "CRITICAL"
                ]
            ):
                continue

            if level == "CRITICAL":

                icon_color = "red"

            elif level == "HIGH":

                icon_color = "orange"

            elif level == "MODERATE":

                icon_color = "beige"

            else:

                icon_color = "green"


            popup = f"""
            <b>📍 Location:</b>
            {row.get('location', 'Unknown')}<br><br>

            <b>🤖 AI Probability:</b>
            {probability:.2f}%<br>

            <b>Risk Level:</b>
            {level}<br>

            <b>Rainfall:</b>
            {row.get('rainfall_mm', 'N/A')} mm<br>

            <b>Soil Moisture:</b>
            {row.get('soil_moisture', 'N/A')}%<br>

            <b>Slope:</b>
            {row.get('slope_deg', 'N/A')}°<br>

            <b>Ground Movement:</b>
            {row.get('ground_movement_mm', 'N/A')} mm
            """

            folium.Marker(
                location=[
                    row["latitude"],
                    row["longitude"]
                ],
                popup=folium.Popup(
                    popup,
                    max_width=350
                ),
                icon=folium.Icon(
                    color=icon_color,
                    icon="warning-sign"
                )
            ).add_to(risk_layer)

    risk_layer.add_to(m)


    # --------------------------------------------
    # ROAD LAYER
    # --------------------------------------------

    road_layer = folium.FeatureGroup(
        name="Road Risk"
    )

    if show_roads and not road_df.empty:

        for _, row in road_df.iterrows():

            risk = str(
                row.get(
                    "risk_level",
                    "Moderate"
                )
            ).lower()

            if "critical" in risk:

                marker_color = "red"

            elif "high" in risk:

                marker_color = "orange"

            else:

                marker_color = "blue"


            popup = f"""
            <b>🛣️ Road:</b>
            {row.get('road_name', 'Unknown')}<br><br>

            <b>Risk:</b>
            {row.get('risk_level', 'Unknown')}<br>

            <b>Connectivity:</b>
            {row.get('connectivity', 'Unknown')}
            """

            folium.CircleMarker(
                location=[
                    row["latitude"],
                    row["longitude"]
                ],
                radius=8,
                color=marker_color,
                fill=True,
                popup=folium.Popup(
                    popup,
                    max_width=300
                )
            ).add_to(road_layer)

    road_layer.add_to(m)


    # --------------------------------------------
    # INFRASTRUCTURE
    # --------------------------------------------

    infrastructure_layer = folium.FeatureGroup(
        name="Critical Infrastructure"
    )

    if (
        show_infrastructure
        and not infra_df.empty
    ):

        for _, row in infra_df.iterrows():

            popup = f"""
            <b>🏥 Infrastructure:</b>
            {row.get('name', 'Unknown')}<br><br>

            <b>Type:</b>
            {row.get('type', 'Unknown')}<br>

            <b>Importance:</b>
            {row.get('importance', 'Unknown')}
            """

            folium.Marker(
                location=[
                    row["latitude"],
                    row["longitude"]
                ],
                popup=folium.Popup(
                    popup,
                    max_width=300
                ),
                icon=folium.Icon(
                    color="blue",
                    icon="plus"
                )
            ).add_to(
                infrastructure_layer
            )

    infrastructure_layer.add_to(m)


    # --------------------------------------------
    # VILLAGE LAYER
    # --------------------------------------------

    village_layer = folium.FeatureGroup(
        name="Community / Villages"
    )

    if (
        show_villages
        and not village_results_df.empty
    ):

        for _, row in village_results_df.iterrows():

            priority = row["Priority"]

            if priority == "PRIORITY 1":

                marker_color = "red"

            elif priority == "PRIORITY 2":

                marker_color = "orange"

            else:

                marker_color = "green"


            popup = f"""
            <div style="width:330px">

            <h4>🏘️ {row['Village']}</h4>

            <b>State:</b>
            {row['State']}<br>

            <b>Population:</b>
            {row['Population']:,}<br><br>

            <b>🤖 AI Landslide Risk:</b>
            {row['AI Risk (%)']}%<br>

            <b>Risk Level:</b>
            {row['Risk Level']}<br>

            <b>📍 Distance to Risk Zone:</b>
            {row['Distance to Risk Zone (km)']} km<br><br>

            <b>🛣️ Road Connectivity:</b>
            {row['Road Connectivity']}<br>

            <b>Importance:</b>
            {row['Importance']}<br>

            <b>🏥 Nearest Hospital:</b>
            {row['Nearest Hospital']}<br><br>

            <b>🚨 Priority:</b>
            {priority}<br>

            <b>Priority Score:</b>
            {row['Priority Score']}/100<br><br>

            <b>Alert:</b>
            {row['Alert']}

            </div>
            """

            folium.Marker(
                location=[
                    village_df.loc[
                        village_df["village"]
                        == row["Village"],
                        "latitude"
                    ].iloc[0],

                    village_df.loc[
                        village_df["village"]
                        == row["Village"],
                        "longitude"
                    ].iloc[0]
                ],
                popup=folium.Popup(
                    popup,
                    max_width=350
                ),
                icon=folium.Icon(
                    color=marker_color,
                    icon="home"
                )
            ).add_to(village_layer)

    village_layer.add_to(m)


    # --------------------------------------------
    # GEO-TAGGED INCIDENT REPORTS
    # --------------------------------------------

    incident_layer = folium.FeatureGroup(
        name="📸 Reported Landslide Incidents"
    )

    incidents_for_map = load_incidents(include_photo=False)

    severity_colors = {
        "Critical": "red",
        "High": "orange",
        "Moderate": "beige",
        "Low": "green",
    }

    for _, incident in incidents_for_map.iterrows():
        severity = str(incident["severity"])
        color = severity_colors.get(severity, "blue")
        photo_text = (
            f"<b>📷 Photo:</b> {incident['photo_name']}<br>"
            if incident.get("photo_name")
            else ""
        )
        popup = f"""
        <div style="width:330px">
            <h4>📸 Reported Landslide Incident</h4>
            <b>Severity:</b> {severity}<br>
            <b>Village:</b> {incident.get('village') or 'Not specified'}<br>
            <b>Road Blocked:</b> {incident['road_blocked']}<br>
            <b>Coordinates:</b> {float(incident['latitude']):.5f}, {float(incident['longitude']):.5f}<br>
            <b>Reported:</b> {incident['reported_at']}<br>
            {photo_text}<br>
            <b>Description:</b><br>{incident.get('description') or 'No description'}
        </div>
        """
        folium.Marker(
            location=[float(incident["latitude"]), float(incident["longitude"])],
            popup=folium.Popup(popup, max_width=360),
            icon=folium.Icon(color=color, icon="camera"),
        ).add_to(incident_layer)

    incident_layer.add_to(m)


    folium.LayerControl(
        collapsed=False
    ).add_to(m)


    st_folium(
        m,
        width=None,
        height=650
    )


    # --------------------------------------------
    # PRIORITY TABLE
    # --------------------------------------------

    if not village_results_df.empty:

        st.markdown("---")

        st.subheader(
            "🚨 AI-Assisted Community Response Priority"
        )

        display_df = village_results_df[
            [
                "Village",
                "State",
                "Population",
                "AI Risk (%)",
                "Risk Level",
                "Distance to Risk Zone (km)",
                "Priority",
                "Priority Score",
                "Alert"
            ]
        ]

        display_df = display_df.sort_values(
            "Priority Score",
            ascending=False
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# ALERTS
# ============================================================

elif page == "Alerts":

    st.title(
        "🚨 Automated Early Warning Center"
    )

    st.markdown(
        """
        Alerts are automatically generated from the AI risk
        probability and community response-priority score.
        """
    )


    if village_results_df.empty:

        st.warning(
            "No village data available."
        )

    else:

        # ----------------------------------------
        # ALERT COUNTS
        # ----------------------------------------

        critical = len(
            village_results_df[
                village_results_df["Alert"]
                == "CRITICAL"
            ]
        )

        high = len(
            village_results_df[
                village_results_df["Alert"]
                == "HIGH"
            ]
        )

        moderate = len(
            village_results_df[
                village_results_df["Alert"]
                == "MODERATE"
            ]
        )

        low = len(
            village_results_df[
                village_results_df["Alert"]
                == "LOW"
            ]
        )


        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.metric(
                "🚨 Critical",
                critical
            )

        with c2:

            st.metric(
                "🔴 High",
                high
            )

        with c3:

            st.metric(
                "🟠 Moderate",
                moderate
            )

        with c4:

            st.metric(
                "🟢 Low",
                low
            )


        st.markdown("---")


        # ----------------------------------------
        # CRITICAL ALERTS
        # ----------------------------------------

        critical_df = village_results_df[
            village_results_df["Alert"]
            == "CRITICAL"
        ]

        if not critical_df.empty:

            st.error(
                "🚨 CRITICAL EARLY WARNINGS"
            )

            for _, alert in critical_df.iterrows():

                st.error(
                    f"""
                    **{alert['Village']} — {alert['State']}**

                    🤖 AI Landslide Probability:
                    **{alert['AI Risk (%)']}%**

                    🚨 Response Priority:
                    **{alert['Priority']}**

                    📊 Priority Score:
                    **{alert['Priority Score']}/100**

                    🏥 Nearest Hospital:
                    **{alert['Nearest Hospital']}**

                    **Recommended Action:**
                    {alert['Recommended Action']}
                    """
                )


        # ----------------------------------------
        # HIGH ALERTS
        # ----------------------------------------

        high_df = village_results_df[
            village_results_df["Alert"]
            == "HIGH"
        ]

        if not high_df.empty:

            st.warning(
                "⚠️ HIGH RISK WARNINGS"
            )

            st.dataframe(
                high_df[
                    [
                        "Village",
                        "AI Risk (%)",
                        "Priority",
                        "Priority Score",
                        "Recommended Action"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )


        # ----------------------------------------
        # ALL ALERTS
        # ----------------------------------------

        st.markdown("---")

        st.subheader(
            "📋 Complete Alert Register"
        )

        all_alerts = village_results_df[
            [
                "Village",
                "State",
                "AI Risk (%)",
                "Risk Level",
                "Priority",
                "Priority Score",
                "Alert",
                "Recommended Action"
            ]
        ].sort_values(
            "Priority Score",
            ascending=False
        )

        st.dataframe(
            all_alerts,
            use_container_width=True,
            hide_index=True
        )


        st.caption(
            """
            Prototype warning system: AI probabilities and
            priority scores are decision-support indicators,
            not official evacuation orders. Real deployment
            requires validated models, authoritative data and
            approval from disaster-management authorities.
            """
        )


# ============================================================
# SENSORS
# ============================================================

elif page == "Sensors":

    st.title(
        "📡 Sensor Monitoring"
    )

    sensor_data = pd.DataFrame(
        {
            "Sensor": [
                "Soil Sensor 01",
                "Rain Gauge 01",
                "Movement Sensor 01",
                "Soil Sensor 02",
                "Rain Gauge 02"
            ],

            "Location": [
                "Tawang",
                "Sela",
                "Dirang",
                "Bomdila",
                "Tawang"
            ],

            "Value": [
                89,
                164,
                12,
                71,
                145
            ],

            "Unit": [
                "%",
                "mm",
                "mm",
                "%",
                "mm"
            ],

            "Status": [
                "Warning",
                "Critical",
                "Warning",
                "Normal",
                "Warning"
            ]
        }
    )

    st.dataframe(
        sensor_data,
        use_container_width=True,
        hide_index=True
    )

    st.info(
        """
        Prototype sensor values are simulated.
        The production version can connect IoT sensors
        through an API or MQTT gateway.
        """
    )


# ============================================================
# ANALYTICS
# ============================================================

elif page == "Analytics":

    st.title(
        "📊 Risk Analytics"
    )


    if not village_results_df.empty:

        chart_data = village_results_df[
            [
                "Village",
                "AI Risk (%)"
            ]
        ].sort_values(
            "AI Risk (%)",
            ascending=False
        )

        fig = px.bar(
            chart_data,
            x="Village",
            y="AI Risk (%)",
            title="AI Landslide Probability by Village"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


        priority_chart = village_results_df[
            [
                "Village",
                "Priority Score"
            ]
        ].sort_values(
            "Priority Score",
            ascending=False
        )

        fig2 = px.bar(
            priority_chart,
            x="Village",
            y="Priority Score",
            title="Community Response Priority"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )


        alert_distribution = (
            village_results_df["Alert"]
            .value_counts()
            .reset_index()
        )

        alert_distribution.columns = [
            "Alert Level",
            "Villages"
        ]

        fig3 = px.pie(
            alert_distribution,
            names="Alert Level",
            values="Villages",
            title="Current Alert Distribution"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )


# ============================================================
# GEO-TAGGED INCIDENT REPORTING
# ============================================================

elif page == "Incident Reporting":

    st.title("📸 Geo-Tagged Landslide Incident Reporting")

    st.markdown(
        """
        Report a landslide observed in the field. Each report is stored locally
        with coordinates, severity, road status, description and an optional photo.
        Reports automatically appear as markers on the **Risk Map**.
        """
    )

    st.info(
        "Workflow: **Report → Geo-tag → Store → Map → Alert**. "
        "For the prototype, SQLite provides free local storage."
    )

    left, right = st.columns([1.15, 0.85])

    with left:
        st.subheader("📝 New Incident Report")

        uploaded_photo = st.file_uploader(
            "📷 Upload landslide photo (optional)",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a field photo. The image is stored in the local prototype database."
        )

        if uploaded_photo is not None:
            st.image(uploaded_photo, caption="Incident photo preview", use_container_width=True)

        r1, r2 = st.columns(2)
        with r1:
            latitude = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=27.58600,
                format="%.6f",
                help="Enter the GPS latitude of the incident."
            )
        with r2:
            longitude = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=91.85900,
                format="%.6f",
                help="Enter the GPS longitude of the incident."
            )

        r3, r4 = st.columns(2)
        with r3:
            severity = st.selectbox(
                "⚠️ Severity",
                ["Low", "Moderate", "High", "Critical"],
                index=2
            )
        with r4:
            road_blocked = st.selectbox(
                "🛣️ Road blocked?",
                ["No", "Yes"]
            )

        village_options = ["Not specified"]
        if not village_df.empty and "village" in village_df.columns:
            village_options += village_df["village"].dropna().astype(str).tolist()

        village = st.selectbox(
            "🏘️ Affected village / area",
            village_options
        )

        description = st.text_area(
            "📝 Incident description",
            placeholder="Describe visible cracks, debris flow, damaged houses, road condition, etc.",
            height=120
        )

        submit_incident = st.button(
            "🚨 Submit Incident Report",
            type="primary",
            use_container_width=True
        )

        if submit_incident:
            if not description.strip():
                st.warning("Please add a short incident description.")
            else:
                photo_name = uploaded_photo.name if uploaded_photo is not None else ""
                photo_data = uploaded_photo.getvalue() if uploaded_photo is not None else None
                save_incident(
                    latitude,
                    longitude,
                    severity,
                    road_blocked,
                    village,
                    description.strip(),
                    photo_name,
                    photo_data,
                )
                st.success("✅ Incident report stored successfully and added to the Risk Map.")
                st.rerun()

    with right:
        st.subheader("📊 Incident Summary")
        incidents = load_incidents(include_photo=False)

        if incidents.empty:
            st.info("No field incidents have been reported yet.")
        else:
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                st.metric("Total Reports", len(incidents))
            with ic2:
                st.metric("High / Critical", len(incidents[incidents["severity"].isin(["High", "Critical"])]))
            with ic3:
                st.metric("Road Blocked", len(incidents[incidents["road_blocked"] == "Yes"]))

            st.markdown("---")
            st.subheader("🚨 Recent Critical / High Reports")
            urgent = incidents[incidents["severity"].isin(["Critical", "High"])]
            if urgent.empty:
                st.success("No High or Critical field reports.")
            else:
                for _, incident in urgent.head(5).iterrows():
                    box = st.error if incident["severity"] == "Critical" else st.warning
                    box(
                        f"**{incident['severity']} — {incident.get('village') or 'Unknown area'}**\\n\\n"
                        f"{incident.get('description') or 'No description'}\\n\\n"
                        f"📍 {float(incident['latitude']):.5f}, {float(incident['longitude']):.5f}  |  "
                        f"🛣️ Road blocked: {incident['road_blocked']}"
                    )

    st.markdown("---")
    st.subheader("📋 Incident Register")

    incidents = load_incidents(include_photo=False)
    if incidents.empty:
        st.caption("Submitted reports will appear here.")
    else:
        display_incidents = incidents.rename(
            columns={
                "id": "ID",
                "reported_at": "Reported At",
                "latitude": "Latitude",
                "longitude": "Longitude",
                "severity": "Severity",
                "road_blocked": "Road Blocked",
                "village": "Village / Area",
                "description": "Description",
                "photo_name": "Photo",
            }
        )
        st.dataframe(
            display_incidents,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download Incident Register",
            data=display_incidents.to_csv(index=False),
            file_name="NER_landslide_incident_register.csv",
            mime="text/csv"
        )

    st.caption(
        "Prototype note: manually entered coordinates are used in this version. "
        "A production mobile app can capture GPS coordinates automatically and sync reports offline."
    )


# ============================================================
# REPORTS
# ============================================================

elif page == "Reports":

    st.title(
        "📄 Monitoring Reports"
    )


    if not village_results_df.empty:

        report = village_results_df[
            [
                "Village",
                "State",
                "Population",
                "AI Risk (%)",
                "Risk Level",
                "Priority",
                "Priority Score",
                "Alert",
                "Recommended Action"
            ]
        ]

        st.dataframe(
            report,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download Early Warning Report",
            data=report.to_csv(
                index=False
            ),
            file_name=(
                "NER_landslide_early_warning_report.csv"
            ),
            mime="text/csv"
        )


# ============================================================
# SETTINGS
# ============================================================

elif page == "Settings":

    st.title(
        "⚙️ System Settings"
    )


    st.subheader(
        "Notification Channels"
    )

    st.checkbox(
        "SMS Alerts",
        value=True
    )

    st.checkbox(
        "Mobile App Notifications",
        value=True
    )

    st.checkbox(
        "Dashboard Alerts",
        value=True
    )


    st.markdown("---")


    st.subheader(
        "AI-Assisted Priority Weights"
    )

    weights = pd.DataFrame(
        {
            "Factor": [
                "AI Landslide Risk",
                "Population Exposure",
                "Road Connectivity",
                "Community Importance"
            ],

            "Weight": [
                "40%",
                "20%",
                "20%",
                "20%"
            ]
        }
    )

    st.table(weights)


    st.success(
        "Balanced AI-assisted prioritization enabled."
    )
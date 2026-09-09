import base64
import math
import sqlite3
from datetime import datetime
from pathlib import Path

import folium
import joblib
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from models.risk_engine import calculate_risk


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

IMAGE_PATH = BASE_DIR / "assets" / "background.jpg"
MODEL_PATH = BASE_DIR / "models" / "landslide_model.pkl"
DB_PATH = BASE_DIR / "data" / "incidents.db"

RISK_DATA_PATH = BASE_DIR / "data" / "risk_locations.csv"
ROAD_DATA_PATH = BASE_DIR / "data" / "road_risk.csv"
INFRA_DATA_PATH = BASE_DIR / "data" / "infrastructure_risk.csv"
VILLAGE_DATA_PATH = BASE_DIR / "data" / "village_risk.csv"


st.set_page_config(
    page_title="NER Landslide Early Warning System",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# UI / BACKGROUND
# ============================================================

def set_background(image_path: Path):
    if not image_path.exists():
        return

    try:
        encoded = base64.b64encode(image_path.read_bytes()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image:
                    linear-gradient(
                        rgba(0,0,0,0.72),
                        rgba(0,0,0,0.72)
                    ),
                    url("data:image/jpeg;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}

            .block-container {{
                padding-top: 1.5rem;
                padding-bottom: 3rem;
            }}

            [data-testid="stMetric"] {{
                background: rgba(255,255,255,0.07);
                padding: 12px;
                border-radius: 12px;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass


set_background(IMAGE_PATH)


# ============================================================
# DATABASE
# ============================================================

def init_incident_db():
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


def save_incident(
    latitude,
    longitude,
    severity,
    road_blocked,
    village,
    description,
    photo_name,
    photo_data,
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO incidents
            (
                reported_at,
                latitude,
                longitude,
                severity,
                road_blocked,
                village,
                description,
                photo_name,
                photo_data
            )
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
    columns = (
        "id, reported_at, latitude, longitude, severity, "
        "road_blocked, village, description, photo_name"
    )

    if include_photo:
        columns += ", photo_data"

    try:
        with sqlite3.connect(DB_PATH) as conn:
            return pd.read_sql_query(
                f"SELECT {columns} FROM incidents ORDER BY id DESC",
                conn,
            )
    except Exception:
        return pd.DataFrame()


init_incident_db()


# ============================================================
# DATA / MODEL
# ============================================================

@st.cache_resource
def load_model():
    if not MODEL_PATH.exists():
        return None

    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


@st.cache_data
def load_csv(path: Path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


model = load_model()

risk_df = load_csv(RISK_DATA_PATH)
road_df = load_csv(ROAD_DATA_PATH)
infra_df = load_csv(INFRA_DATA_PATH)
village_df = load_csv(VILLAGE_DATA_PATH)


# ============================================================
# AI RISK ENGINE
# ============================================================

FEATURE_COLUMNS = [
    "rainfall_mm",
    "soil_moisture",
    "slope_deg",
    "ground_movement_mm",
    "elevation_m",
]


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def get_ai_probability(row):
    rainfall = safe_float(row.get("rainfall_mm", 100), 100)
    moisture = safe_float(row.get("soil_moisture", 60), 60)
    slope = safe_float(row.get("slope_deg", 30), 30)
    movement = safe_float(row.get("ground_movement_mm", 5), 5)
    elevation = safe_float(row.get("elevation_m", 1500), 1500)

    if model is not None:
        try:
            input_data = pd.DataFrame(
                [[rainfall, moisture, slope, movement, elevation]],
                columns=FEATURE_COLUMNS,
            )

            probability = (
                model.predict_proba(input_data)[0][1] * 100
            )

            return round(max(0.0, min(100.0, float(probability))), 2)

        except Exception:
            pass

    try:
        score, _ = calculate_risk(
            rainfall,
            moisture,
            slope,
            movement,
            elevation,
        )
        return round(max(0.0, min(100.0, float(score))), 2)
    except Exception:
        return 0.0


def get_risk_level(probability):
    probability = safe_float(probability)

    if probability >= 80:
        return "CRITICAL"
    if probability >= 60:
        return "HIGH"
    if probability >= 40:
        return "MODERATE"
    return "LOW"


def risk_color(level):
    return {
        "CRITICAL": "red",
        "HIGH": "orange",
        "MODERATE": "beige",
        "LOW": "green",
    }.get(level, "blue")


def risk_message(level):
    return {
        "CRITICAL": (
            "🚨 VERY HIGH PROBABILITY — Immediate field assessment "
            "and emergency preparedness are recommended."
        ),
        "HIGH": (
            "⚠️ HIGH PROBABILITY — Increase monitoring and keep "
            "response teams prepared."
        ),
        "MODERATE": (
            "🟡 MODERATE PROBABILITY — Continue close monitoring "
            "of rainfall, soil moisture and ground movement."
        ),
        "LOW": (
            "🟢 LOW PROBABILITY — Continue routine environmental monitoring."
        ),
    }.get(level, "Continue monitoring.")


def get_recommended_action(level):
    return {
        "CRITICAL": (
            "Immediate field assessment recommended. Prepare community "
            "warning and inspect vulnerable roads."
        ),
        "HIGH": (
            "Increase monitoring, inspect slopes and keep emergency "
            "response teams prepared."
        ),
        "MODERATE": (
            "Continue monitoring rainfall, soil moisture and ground movement."
        ),
        "LOW": "Continue routine environmental monitoring.",
    }.get(level, "Continue monitoring.")


# ============================================================
# GEOGRAPHIC HELPERS
# ============================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371.0

    lat1 = math.radians(safe_float(lat1))
    lat2 = math.radians(safe_float(lat2))
    delta_lat = lat2 - lat1
    delta_lon = math.radians(
        safe_float(lon2) - safe_float(lon1)
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(max(0.0, 1 - a)),
    )

    return radius * c


# ============================================================
# VILLAGE PRIORITY ENGINE
# ============================================================

@st.cache_data
def calculate_village_priorities(risk_data, village_data):
    if village_data.empty:
        return pd.DataFrame()

    risk_points = []

    if not risk_data.empty:
        for _, row in risk_data.iterrows():
            try:
                probability = get_ai_probability(row)

                risk_points.append(
                    {
                        "latitude": safe_float(row.get("latitude")),
                        "longitude": safe_float(row.get("longitude")),
                        "probability": probability,
                        "risk_level": get_risk_level(probability),
                    }
                )
            except Exception:
                continue

    results = []

    for _, row in village_data.iterrows():
        village_lat = safe_float(row.get("latitude"))
        village_lon = safe_float(row.get("longitude"))

        nearest_probability = 0.0
        nearest_risk_level = "LOW"
        nearest_distance = None

        for point in risk_points:
            distance = calculate_distance(
                village_lat,
                village_lon,
                point["latitude"],
                point["longitude"],
            )

            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_probability = point["probability"]
                nearest_risk_level = point["risk_level"]

        population = safe_float(row.get("population", 0))

        population_score = min(
            population / 20000 * 100,
            100,
        )

        connectivity = str(
            row.get("road_connectivity", "Medium")
        ).lower()

        connectivity_score = {
            "low": 100,
            "medium": 60,
            "high": 30,
        }.get(connectivity, 60)

        importance = str(
            row.get("importance", "Medium")
        ).lower()

        importance_score = {
            "critical": 100,
            "high": 70,
            "medium": 40,
        }.get(importance, 40)

        ai_score = nearest_probability

        priority_score = (
            ai_score * 0.40
            + population_score * 0.20
            + connectivity_score * 0.20
            + importance_score * 0.20
        )

        priority_score = round(
            max(0.0, min(100.0, priority_score)),
            2,
        )

        if priority_score >= 75:
            priority = "PRIORITY 1"
        elif priority_score >= 50:
            priority = "PRIORITY 2"
        else:
            priority = "PRIORITY 3"

        if nearest_probability >= 80 or priority_score >= 85:
            alert_level = "CRITICAL"
        elif nearest_probability >= 60 or priority_score >= 70:
            alert_level = "HIGH"
        elif nearest_probability >= 40 or priority_score >= 50:
            alert_level = "MODERATE"
        else:
            alert_level = "LOW"

        results.append(
            {
                "Village": row.get("village", "Unknown"),
                "State": row.get("state", "Unknown"),
                "Latitude": village_lat,
                "Longitude": village_lon,
                "Population": int(population),
                "AI Risk (%)": round(nearest_probability, 2),
                "Risk Level": nearest_risk_level,
                "Distance to Risk Zone (km)": (
                    round(nearest_distance, 2)
                    if nearest_distance is not None
                    else None
                ),
                "Road Connectivity": row.get(
                    "road_connectivity", "Unknown"
                ),
                "Importance": row.get(
                    "importance", "Unknown"
                ),
                "Priority": priority,
                "Priority Score": priority_score,
                "Alert": alert_level,
                "Recommended Action": get_recommended_action(
                    alert_level
                ),
                "Nearest Hospital": row.get(
                    "nearest_hospital", "Unknown"
                ),
            }
        )

    return pd.DataFrame(results)


village_results_df = calculate_village_priorities(
    risk_df,
    village_df,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⛰️ NER Landslide AI")

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
        "Settings",
    ],
)

st.sidebar.markdown("---")

st.sidebar.info(
    """
    **AI-Based Early Warning System**

    Monitor → Predict → Prioritize → Alert

    Prototype for SIH demonstration.
    """
)

st.sidebar.markdown("---")

st.sidebar.caption(
    f"Model: {'🟢 Loaded' if model is not None else '🟡 Fallback risk engine'}"
)

st.sidebar.caption(
    f"Risk locations: {len(risk_df)}"
)

st.sidebar.caption(
    f"Villages: {len(village_df)}"
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.title("⛰️ NER Landslide Early Warning System")

    st.markdown(
        """
        ### AI-Based Risk Monitoring & Early Warning Platform

        Monitor rainfall, soil moisture, slope, ground movement,
        vulnerable communities, roads and critical infrastructure.
        """
    )

    st.markdown(
        """
        <div style="
            padding:18px;
            border-radius:14px;
            background:linear-gradient(
                90deg,
                rgba(127,29,29,0.92),
                rgba(153,27,27,0.82)
            );
            color:white;
            margin:10px 0 22px 0;
        ">
            <h3 style="margin:0;">🚨 AI-Powered Landslide Early Warning</h3>
            <p style="margin:8px 0 0 0;">
                Continuous monitoring of environmental indicators
                and community vulnerability.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    critical_count = 0
    high_count = 0
    moderate_count = 0

    if not village_results_df.empty:
        critical_count = int(
            (village_results_df["Alert"] == "CRITICAL").sum()
        )
        high_count = int(
            (village_results_df["Alert"] == "HIGH").sum()
        )
        moderate_count = int(
            (village_results_df["Alert"] == "MODERATE").sum()
        )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("🚨 Critical Alerts", critical_count)

    with c2:
        st.metric("⚠️ High Alerts", high_count)

    with c3:
        st.metric("🏘️ Villages Monitored", len(village_df))

    with c4:
        st.metric("🛣️ Roads Monitored", len(road_df))

    st.markdown("---")

    st.subheader("🟢 System Status")

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.success("🟢 AI Model Online" if model is not None
                   else "🟡 Fallback Risk Engine")

    with s2:
        st.success("🟢 Weather Service Ready")

    with s3:
        st.success("🟢 Risk Engine Online")

    with s4:
        st.success("🟢 Monitoring Active")

    if critical_count > 0:
        st.error(
            f"🚨 CRITICAL WARNING: {critical_count} location(s) "
            "require immediate attention."
        )
    elif high_count > 0:
        st.warning(
            f"⚠️ HIGH RISK: {high_count} location(s) "
            "require increased monitoring."
        )
    else:
        st.success(
            "🟢 No critical or high-risk village alerts detected."
        )

    st.markdown("---")

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    st.subheader("🌧️ Live Weather — Tawang")

    w1, w2, w3 = st.columns(3)

    try:
        from services.weather import get_weather

        weather = get_weather(
            latitude=27.586,
            longitude=91.859,
        )

        if weather:
            with w1:
                st.metric(
                    "Temperature",
                    f"{weather.get('temperature', 'N/A')} °C",
                )

            with w2:
                st.metric(
                    "Precipitation",
                    f"{weather.get('precipitation', 'N/A')} mm",
                )

            with w3:
                st.metric(
                    "Rain",
                    f"{weather.get('rain', 'N/A')} mm",
                )
        else:
            st.warning("Weather data unavailable.")

    except Exception:
        st.warning(
            "Weather service is unavailable. "
            "The rest of the monitoring system remains available."
        )

    st.markdown("---")

    # --------------------------------------------------------
    # AI DEMO
    # --------------------------------------------------------

    st.subheader("🤖 AI Landslide Risk Prediction")

    left, right = st.columns(2)

    with left:
        rainfall = st.slider(
            "Rainfall (mm)",
            0,
            300,
            160,
            help="Estimated or observed rainfall.",
        )

        soil_moisture = st.slider(
            "Soil Moisture (%)",
            0,
            100,
            85,
            help="Soil moisture percentage.",
        )

        slope = st.slider(
            "Slope (degrees)",
            0,
            60,
            35,
            help="Terrain slope.",
        )

    with right:
        ground_movement = st.slider(
            "Ground Movement (mm)",
            0,
            30,
            12,
            help="Detected ground displacement.",
        )

        elevation = st.slider(
            "Elevation (m)",
            0,
            5000,
            2400,
            help="Terrain elevation.",
        )

        analyze = st.button(
            "🔍 Analyze Landslide Risk",
            use_container_width=True,
            type="primary",
        )

    if analyze:
        fallback_score, fallback_level = calculate_risk(
            rainfall,
            soil_moisture,
            slope,
            ground_movement,
            elevation,
        )

        probability = get_ai_probability(
            {
                "rainfall_mm": rainfall,
                "soil_moisture": soil_moisture,
                "slope_deg": slope,
                "ground_movement_mm": ground_movement,
                "elevation_m": elevation,
            }
        )

        level = get_risk_level(probability)

        r1, r2 = st.columns(2)

        with r1:
            st.metric(
                "Risk Score",
                f"{fallback_score:.2f}%",
            )

        with r2:
            st.metric(
                "AI Landslide Probability",
                f"{probability:.2f}%",
            )

        st.progress(
            int(max(0, min(100, round(probability)))),
            text=f"AI Risk Probability: {probability:.2f}%",
        )

        if level == "CRITICAL":
            st.error("🚨 CRITICAL RISK")
        elif level == "HIGH":
            st.warning("⚠️ HIGH RISK")
        elif level == "MODERATE":
            st.info("🟡 MODERATE RISK")
        else:
            st.success("🟢 LOW RISK")

        st.markdown(f"**Assessment:** {risk_message(level)}")

        st.info(
            f"**Recommended action:** "
            f"{get_recommended_action(level)}"
        )

    st.markdown("---")

    st.caption(
        "Prototype decision-support system. AI probabilities are "
        "not official evacuation orders."
    )


# ============================================================
# RISK MAP
# ============================================================

elif page == "Risk Map":

    st.title("🗺️ AI Risk & Community Monitoring Map")

    st.markdown(
        """
        The map combines AI landslide probability, community
        vulnerability, roads, infrastructure and field incidents.
        """
    )

    st.sidebar.markdown("### Map Filters")

    show_risk = st.sidebar.checkbox(
        "Landslide Risk",
        True,
    )

    show_roads = st.sidebar.checkbox(
        "Roads",
        True,
    )

    show_infrastructure = st.sidebar.checkbox(
        "Infrastructure",
        True,
    )

    show_villages = st.sidebar.checkbox(
        "Villages",
        True,
    )

    show_incidents = st.sidebar.checkbox(
        "Field Incidents",
        True,
    )

    high_risk_only = st.sidebar.checkbox(
        "High Risk Only",
        False,
    )

    map_center = [25.8, 92.0]

    if not village_df.empty:
        try:
            map_center = [
                village_df["latitude"].astype(float).mean(),
                village_df["longitude"].astype(float).mean(),
            ]
        except Exception:
            pass

    m = folium.Map(
        location=map_center,
        zoom_start=6,
        tiles="OpenStreetMap",
    )

    # --------------------------------------------------------
    # AI RISK LAYER
    # --------------------------------------------------------

    if show_risk:
        risk_layer = folium.FeatureGroup(
            name="AI Landslide Risk",
        )

        for _, row in risk_df.iterrows():
            try:
                probability = get_ai_probability(row)
                level = get_risk_level(probability)

                if (
                    high_risk_only
                    and level not in ["HIGH", "CRITICAL"]
                ):
                    continue

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

                folium.CircleMarker(
                    location=[
                        safe_float(row.get("latitude")),
                        safe_float(row.get("longitude")),
                    ],
                    radius=10 if level in ["HIGH", "CRITICAL"] else 7,
                    color=risk_color(level),
                    fill=True,
                    fill_color=risk_color(level),
                    fill_opacity=0.75,
                    popup=folium.Popup(
                        popup,
                        max_width=350,
                    ),
                ).add_to(risk_layer)

            except Exception:
                continue

        risk_layer.add_to(m)

    # --------------------------------------------------------
    # ROAD LAYER
    # --------------------------------------------------------

    if show_roads:
        road_layer = folium.FeatureGroup(
            name="Road Risk",
        )

        for _, row in road_df.iterrows():
            risk = str(
                row.get("risk_level", "Moderate")
            ).lower()

            if "critical" in risk:
                color = "red"
            elif "high" in risk:
                color = "orange"
            elif "moderate" in risk:
                color = "beige"
            else:
                color = "blue"

            popup = f"""
            <b>🛣️ Road:</b>
            {row.get('road_name', 'Unknown')}<br><br>

            <b>Risk:</b>
            {row.get('risk_level', 'Unknown')}<br>

            <b>Connectivity:</b>
            {row.get('connectivity', 'Unknown')}
            """

            try:
                folium.CircleMarker(
                    location=[
                        safe_float(row.get("latitude")),
                        safe_float(row.get("longitude")),
                    ],
                    radius=8,
                    color=color,
                    fill=True,
                    fill_opacity=0.75,
                    popup=folium.Popup(
                        popup,
                        max_width=300,
                    ),
                ).add_to(road_layer)
            except Exception:
                continue

        road_layer.add_to(m)

    # --------------------------------------------------------
    # INFRASTRUCTURE
    # --------------------------------------------------------

    if show_infrastructure:
        infrastructure_layer = folium.FeatureGroup(
            name="Critical Infrastructure",
        )

        for _, row in infra_df.iterrows():
            popup = f"""
            <b>🏥 Infrastructure:</b>
            {row.get('name', 'Unknown')}<br><br>

            <b>Type:</b>
            {row.get('type', 'Unknown')}<br>

            <b>Importance:</b>
            {row.get('importance', 'Unknown')}
            """

            try:
                folium.Marker(
                    location=[
                        safe_float(row.get("latitude")),
                        safe_float(row.get("longitude")),
                    ],
                    popup=folium.Popup(
                        popup,
                        max_width=300,
                    ),
                    icon=folium.Icon(
                        color="blue",
                        icon="plus",
                    ),
                ).add_to(infrastructure_layer)
            except Exception:
                continue

        infrastructure_layer.add_to(m)

    # --------------------------------------------------------
    # VILLAGE LAYER
    # --------------------------------------------------------

    if show_villages and not village_results_df.empty:
        village_layer = folium.FeatureGroup(
            name="Community / Villages",
        )

        for _, row in village_results_df.iterrows():
            level = row["Alert"]

            if high_risk_only and level not in ["HIGH", "CRITICAL"]:
                continue

            popup = f"""
            <b>🏘️ Village:</b>
            {row['Village']}<br>

            <b>State:</b>
            {row['State']}<br>

            <b>AI Risk:</b>
            {row['AI Risk (%)']}%<br>

            <b>Alert:</b>
            {row['Alert']}<br>

            <b>Priority:</b>
            {row['Priority']}<br>

            <b>Priority Score:</b>
            {row['Priority Score']}/100<br>

            <b>Population:</b>
            {row['Population']}<br>

            <b>Nearest Hospital:</b>
            {row['Nearest Hospital']}<br><br>

            <b>Recommended Action:</b>
            {row['Recommended Action']}
            """

            try:
                folium.CircleMarker(
                    location=[
                        safe_float(row["Latitude"]),
                        safe_float(row["Longitude"]),
                    ],
                    radius=8,
                    color=risk_color(level),
                    fill=True,
                    fill_color=risk_color(level),
                    fill_opacity=0.55,
                    popup=folium.Popup(
                        popup,
                        max_width=350,
                    ),
                ).add_to(village_layer)
            except Exception:
                continue

        village_layer.add_to(m)

    # --------------------------------------------------------
    # FIELD INCIDENTS
    # --------------------------------------------------------

    if show_incidents:
        incidents = load_incidents()

        if not incidents.empty:
            incident_layer = folium.FeatureGroup(
                name="Field Incidents",
            )

            for _, incident in incidents.iterrows():
                severity = str(
                    incident.get("severity", "Low")
                )

                if severity == "Critical":
                    color = "red"
                elif severity == "High":
                    color = "orange"
                elif severity == "Moderate":
                    color = "beige"
                else:
                    color = "green"

                popup = f"""
                <b>🚨 Field Incident</b><br><br>

                <b>Severity:</b>
                {severity}<br>

                <b>Village / Area:</b>
                {incident.get('village', 'Unknown')}<br>

                <b>Road Blocked:</b>
                {incident.get('road_blocked', 'Unknown')}<br>

                <b>Reported:</b>
                {incident.get('reported_at', 'Unknown')}<br><br>

                <b>Description:</b>
                {incident.get('description', 'No description')}
                """

                try:
                    folium.Marker(
                        location=[
                            safe_float(incident["latitude"]),
                            safe_float(incident["longitude"]),
                        ],
                        popup=folium.Popup(
                            popup,
                            max_width=350,
                        ),
                        icon=folium.Icon(
                            color=color,
                            icon="exclamation-sign",
                        ),
                    ).add_to(incident_layer)
                except Exception:
                    continue

            incident_layer.add_to(m)

    folium.LayerControl().add_to(m)

    st_folium(
        m,
        use_container_width=True,
        height=650,
    )

    st.info(
        "Map legend: 🟢 Low | 🟡 Moderate | 🟠 High | 🔴 Critical. "
        "Use the sidebar to turn layers on/off."
    )


# ============================================================
# ALERTS
# ============================================================

elif page == "Alerts":

    st.title("🚨 Automated Early Warning Center")

    st.markdown(
        """
        Alerts are generated from AI risk probability and
        community response-priority scoring.
        """
    )

    if village_results_df.empty:
        st.warning("No village data available.")
    else:
        counts = {
            level: int(
                (village_results_df["Alert"] == level).sum()
            )
            for level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]
        }

        a1, a2, a3, a4 = st.columns(4)

        with a1:
            st.metric("🚨 Critical", counts["CRITICAL"])

        with a2:
            st.metric("🔴 High", counts["HIGH"])

        with a3:
            st.metric("🟠 Moderate", counts["MODERATE"])

        with a4:
            st.metric("🟢 Low", counts["LOW"])

        st.markdown("---")

        critical_df = village_results_df[
            village_results_df["Alert"] == "CRITICAL"
        ]

        if not critical_df.empty:
            st.error("🚨 CRITICAL EARLY WARNINGS")

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

        high_df = village_results_df[
            village_results_df["Alert"] == "HIGH"
        ]

        if not high_df.empty:
            st.warning("⚠️ HIGH RISK WARNINGS")

            st.dataframe(
                high_df[
                    [
                        "Village",
                        "AI Risk (%)",
                        "Priority",
                        "Priority Score",
                        "Recommended Action",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("---")

        st.subheader("📋 Complete Alert Register")

        all_alerts = village_results_df[
            [
                "Village",
                "State",
                "AI Risk (%)",
                "Risk Level",
                "Priority",
                "Priority Score",
                "Alert",
                "Recommended Action",
            ]
        ].sort_values(
            "Priority Score",
            ascending=False,
        )

        st.dataframe(
            all_alerts,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download Alert Register",
            data=all_alerts.to_csv(index=False),
            file_name="NER_alert_register.csv",
            mime="text/csv",
        )

        st.caption(
            "Prototype warning system: AI probabilities and priority "
            "scores are decision-support indicators, not official "
            "evacuation orders."
        )


# ============================================================
# SENSOR MONITORING
# ============================================================

elif page == "Sensors":

    st.title("📡 Sensor Monitoring")

    sensor_data = pd.DataFrame(
        {
            "Sensor": [
                "Soil Sensor 01",
                "Rain Gauge 01",
                "Movement Sensor 01",
                "Soil Sensor 02",
                "Rain Gauge 02",
            ],
            "Location": [
                "Tawang",
                "Sela",
                "Dirang",
                "Bomdila",
                "Tawang",
            ],
            "Value": [89, 164, 12, 71, 145],
            "Unit": ["%", "mm", "mm", "%", "mm"],
            "Status": [
                "Warning",
                "Critical",
                "Warning",
                "Normal",
                "Warning",
            ],
        }
    )

    st.dataframe(
        sensor_data,
        use_container_width=True,
        hide_index=True,
    )

    critical_sensors = int(
        (sensor_data["Status"] == "Critical").sum()
    )

    warning_sensors = int(
        (sensor_data["Status"] == "Warning").sum()
    )

    s1, s2, s3 = st.columns(3)

    with s1:
        st.metric("Total Sensors", len(sensor_data))

    with s2:
        st.metric("Critical Sensors", critical_sensors)

    with s3:
        st.metric("Warning Sensors", warning_sensors)

    st.markdown("---")

    st.subheader("📈 Sensor Simulation")

    st.info(
        """
        These values are simulated for the prototype.
        A production version can connect IoT sensors through
        an API, MQTT gateway or edge device.
        """
    )

    if st.button("🔄 Refresh Sensor Data"):
        st.rerun()


# ============================================================
# ANALYTICS
# ============================================================

elif page == "Analytics":

    st.title("📊 Risk Analytics")

    if village_results_df.empty:
        st.warning("No village data available for analytics.")
    else:
        chart_data = village_results_df[
            ["Village", "AI Risk (%)"]
        ].sort_values(
            "AI Risk (%)",
            ascending=False,
        )

        fig = px.bar(
            chart_data,
            x="Village",
            y="AI Risk (%)",
            title="AI Landslide Probability by Village",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        priority_chart = village_results_df[
            ["Village", "Priority Score"]
        ].sort_values(
            "Priority Score",
            ascending=False,
        )

        fig2 = px.bar(
            priority_chart,
            x="Village",
            y="Priority Score",
            title="Community Response Priority",
        )

        st.plotly_chart(
            fig2,
            use_container_width=True,
        )

        alert_distribution = (
            village_results_df["Alert"]
            .value_counts()
            .reset_index()
        )

        alert_distribution.columns = [
            "Alert Level",
            "Villages",
        ]

        fig3 = px.pie(
            alert_distribution,
            names="Alert Level",
            values="Villages",
            title="Current Alert Distribution",
        )

        st.plotly_chart(
            fig3,
            use_container_width=True,
        )

        st.subheader("📋 Highest Priority Communities")

        top = village_results_df.sort_values(
            "Priority Score",
            ascending=False,
        ).head(10)

        st.dataframe(
            top[
                [
                    "Village",
                    "State",
                    "AI Risk (%)",
                    "Alert",
                    "Priority",
                    "Priority Score",
                    "Population",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# INCIDENT REPORTING
# ============================================================

elif page == "Incident Reporting":

    st.title("📸 Geo-Tagged Landslide Incident Reporting")

    st.markdown(
        """
        Report a landslide observed in the field.
        Each report is stored with coordinates, severity,
        road status, description and an optional photo.
        """
    )

    st.info(
        "Workflow: Report → Geo-tag → Store → Map → Alert"
    )

    left, right = st.columns([1.15, 0.85])

    with left:
        st.subheader("📝 New Incident Report")

        uploaded_photo = st.file_uploader(
            "📷 Upload landslide photo (optional)",
            type=["jpg", "jpeg", "png", "webp"],
        )

        if uploaded_photo is not None:
            st.image(
                uploaded_photo,
                caption="Incident photo preview",
                use_container_width=True,
            )

        r1, r2 = st.columns(2)

        with r1:
            latitude = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=27.58600,
                format="%.6f",
            )

        with r2:
            longitude = st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=91.85900,
                format="%.6f",
            )

        r3, r4 = st.columns(2)

        with r3:
            severity = st.selectbox(
                "⚠️ Severity",
                ["Low", "Moderate", "High", "Critical"],
                index=2,
            )

        with r4:
            road_blocked = st.selectbox(
                "🛣️ Road blocked?",
                ["No", "Yes"],
            )

        village_options = ["Not specified"]

        if (
            not village_df.empty
            and "village" in village_df.columns
        ):
            village_options += (
                village_df["village"]
                .dropna()
                .astype(str)
                .tolist()
            )

        village = st.selectbox(
            "🏘️ Affected village / area",
            village_options,
        )

        description = st.text_area(
            "📝 Incident description",
            placeholder=(
                "Describe visible cracks, debris flow, "
                "damaged houses, road condition, etc."
            ),
            height=120,
        )

        submit = st.button(
            "🚨 Submit Incident Report",
            type="primary",
            use_container_width=True,
        )

        if submit:
            if not description.strip():
                st.warning(
                    "Please add a short incident description."
                )
            else:
                photo_name = (
                    uploaded_photo.name
                    if uploaded_photo is not None
                    else ""
                )

                photo_data = (
                    uploaded_photo.getvalue()
                    if uploaded_photo is not None
                    else None
                )

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

                st.success(
                    "✅ Incident report stored successfully."
                )

                st.rerun()

    with right:
        st.subheader("📊 Incident Summary")

        incidents = load_incidents()

        if incidents.empty:
            st.info("No field incidents have been reported yet.")
        else:
            ic1, ic2, ic3 = st.columns(3)

            with ic1:
                st.metric(
                    "Total Reports",
                    len(incidents),
                )

            with ic2:
                st.metric(
                    "High / Critical",
                    len(
                        incidents[
                            incidents["severity"].isin(
                                ["High", "Critical"]
                            )
                        ]
                    ),
                )

            with ic3:
                st.metric(
                    "Road Blocked",
                    len(
                        incidents[
                            incidents["road_blocked"] == "Yes"
                        ]
                    ),
                )

            st.markdown("---")

            urgent = incidents[
                incidents["severity"].isin(
                    ["Critical", "High"]
                )
            ]

            if urgent.empty:
                st.success(
                    "No High or Critical field reports."
                )
            else:
                st.subheader(
                    "🚨 Recent Critical / High Reports"
                )

                for _, incident in urgent.head(5).iterrows():
                    box = (
                        st.error
                        if incident["severity"] == "Critical"
                        else st.warning
                    )

                    box(
                        f"""
                        **{incident['severity']} — {incident.get('village') or 'Unknown area'}**

                        {incident.get('description') or 'No description'}

                        📍 {float(incident['latitude']):.5f},
                        {float(incident['longitude']):.5f}

                        🛣️ Road blocked:
                        {incident['road_blocked']}
                        """
                    )

    st.markdown("---")

    st.subheader("📋 Incident Register")

    incidents = load_incidents()

    if incidents.empty:
        st.caption(
            "Submitted reports will appear here."
        )
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
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download Incident Register",
            data=display_incidents.to_csv(index=False),
            file_name="NER_landslide_incident_register.csv",
            mime="text/csv",
        )


# ============================================================
# REPORTS
# ============================================================

elif page == "Reports":

    st.title("📄 Monitoring Reports")

    if village_results_df.empty:
        st.warning("No village data available.")
    else:
        report_columns = [
            "Village",
            "State",
            "Population",
            "AI Risk (%)",
            "Risk Level",
            "Priority",
            "Priority Score",
            "Alert",
            "Recommended Action",
        ]

        report = village_results_df[
            report_columns
        ].sort_values(
            "Priority Score",
            ascending=False,
        )

        st.dataframe(
            report,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "⬇️ Download Early Warning Report",
            data=report.to_csv(index=False),
            file_name="NER_landslide_early_warning_report.csv",
            mime="text/csv",
        )

        st.markdown("---")

        st.subheader("📌 Executive Summary")

        total = len(report)
        critical = int(
            (report["Alert"] == "CRITICAL").sum()
        )
        high = int(
            (report["Alert"] == "HIGH").sum()
        )

        st.write(
            f"""
            The current monitoring dataset contains **{total}**
            monitored communities. The system currently identifies
            **{critical} critical** and **{high} high-risk** alerts.
            AI risk scores should be treated as decision-support
            indicators during this prototype stage.
            """
        )


# ============================================================
# SETTINGS
# ============================================================

elif page == "Settings":

    st.title("⚙️ System Settings")

    st.subheader("Notification Channels")

    st.checkbox(
        "SMS Alerts",
        value=True,
    )

    st.checkbox(
        "Mobile App Notifications",
        value=True,
    )

    st.checkbox(
        "Dashboard Alerts",
        value=True,
    )

    st.markdown("---")

    st.subheader("AI-Assisted Priority Weights")

    weights = pd.DataFrame(
        {
            "Factor": [
                "AI Landslide Risk",
                "Population Exposure",
                "Road Connectivity",
                "Community Importance",
            ],
            "Weight": [
                "40%",
                "20%",
                "20%",
                "20%",
            ],
        }
    )

    st.table(weights)

    st.success(
        "Balanced AI-assisted prioritization enabled."
    )

    st.markdown("---")

    st.subheader("System Information")

    info = {
        "Application": "NER Landslide Early Warning System",
        "Mode": "SIH Prototype",
        "AI Model": "Loaded" if model is not None else "Fallback risk engine",
        "Risk Locations": len(risk_df),
        "Villages": len(village_df),
        "Roads": len(road_df),
        "Infrastructure Points": len(infra_df),
    }

    st.json(info)

    st.warning(
        "This is a prototype decision-support system. "
        "Production deployment requires validated models, "
        "authoritative sensor/weather data, security controls "
        "and approval from relevant disaster-management authorities."
    )

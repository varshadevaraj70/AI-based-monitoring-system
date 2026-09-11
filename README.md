# AI-based-monitoring-system
An AI-based early warning and landslide risk monitoring system for the North Eastern Region (NER) is an intelligent platform that uses sensors and machine learning to predict slope failures and protect vulnerable mountain communities
🏔️ AI-Based Early Warning & Landslide Risk Monitoring System

Smart India Hackathon 2026 • SIH26001 • Disaster Management

«Predict risk. Prioritize action. Protect communities.»

An intelligent AI-assisted landslide early-warning and risk-monitoring platform designed for the North Eastern Region (NER) of India, combining environmental signals, risk scoring, GIS visualization, community-level prioritization, incident reporting, analytics and early-warning workflows into one decision-support system.

---

<p align="center">🌧️ Monitor → 🤖 Predict → 🗺️ Visualize → 🚨 Alert → 🛟 Respond

</p>---

🏆 Smart India Hackathon

| Details
🎯 Problem Statement| SIH26001
🏛️ Theme| Disaster Management
🌏 Target Region| North Eastern Region (NER), India
💡 Solution Type| AI-assisted Early Warning & Risk Monitoring
🖥️ Prototype| Interactive Web-Based Decision Support Platform
⚙️ Framework| Streamlit

Problem

The North Eastern Region faces recurring landslide hazards due to combinations of intense rainfall, steep slopes, soil saturation, ground movement and vulnerable terrain.

Traditional monitoring can become reactive, especially when information is fragmented between field observations, environmental measurements and administrative response.

Our goal is to create a unified platform that helps answer:

«“Where is the risk increasing, how severe is it, and which community should receive attention first?”»

The official SIH problem statement calls for an AI-powered platform capable of analysing rainfall, soil moisture, satellite/terrain information and historical landslide data to identify high-risk areas and support early warnings.

---

🚨 Our Solution

The platform converts environmental and community-level information into an actionable monitoring workflow:

        ENVIRONMENTAL INPUTS
                 │
                 ▼
      ┌─────────────────────┐
      │  Risk / AI Engine   │
      └──────────┬──────────┘
                 │
                 ▼
        LANDSLIDE RISK SCORE
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
   🗺️ GIS     🚨 Alerts   📊 Analytics
       │         │         │
       └─────────┼─────────┘
                 ▼
       COMMUNITY PRIORITIZATION
                 │
                 ▼
        🛟 RESPONSE SUPPORT

The current prototype is designed as a decision-support system, not as an autonomous replacement for disaster-management authorities.

---

✨ Key Features

🧠 1. AI-Assisted Landslide Risk Prediction

The prediction pipeline works with five core environmental features:

- 🌧️ Rainfall
- 💧 Soil moisture
- ⛰️ Slope
- 🌍 Ground movement
- 📍 Elevation

When a trained model is available, the application can load it using "joblib" and use "predict_proba()" to generate a risk probability.

The application also contains a deterministic risk-engine fallback so the prototype remains functional when a trained model is unavailable.

Risk Levels

Risk Score| Level| Interpretation
"< 40"| 🟢 LOW| Routine monitoring
"40–59.99"| 🟡 MODERATE| Increased monitoring
"60–79.99"| 🟠 HIGH| Field attention recommended
"≥ 80"| 🔴 CRITICAL| Immediate assessment recommended

---

📡 2. Environmental Sensor Monitoring

The prototype provides a dedicated Sensor Command Center for monitoring:

- Rainfall
- Soil moisture
- Ground movement
- Slope
- Elevation

It also includes an interactive sensor simulator that allows judges and developers to change environmental conditions and immediately observe how the risk output changes.

«⚠️ Prototype note: The current interactive sensor values are simulated/test values. Production deployment would connect these inputs to physical IoT sensor gateways and validated environmental data sources.»

---

🗺️ 3. GIS Risk Map

The system uses Fo

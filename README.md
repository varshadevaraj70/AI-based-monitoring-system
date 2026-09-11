# AI-based-monitoring-system
An AI-based early warning and landslide risk monitoring system for the North Eastern Region (NER) is an intelligent platform that uses sensors and machine learning to predict slope failures and protect vulnerable mountain communities
# 🏔️ AI-Based Early Warning & Landslide Risk Monitoring System

### Smart India Hackathon 2026 • SIH26001 • Disaster Management

> **Predict risk. Prioritize action. Protect communities.**

An intelligent **AI-assisted landslide early-warning and risk-monitoring platform** designed for the **North Eastern Region (NER) of India**, combining environmental signals, risk scoring, GIS visualization, community-level prioritization, incident reporting, analytics and early-warning workflows into one decision-support system.

---

<p align="center">

### 🌧️ Monitor → 🤖 Predict → 🗺️ Visualize → 🚨 Alert → 🛟 Respond

</p>

---

## 🏆 Smart India Hackathon

|                          | Details                                         |
| ------------------------ | ----------------------------------------------- |
| 🎯 **Problem Statement** | **SIH26001**                                    |
| 🏛️ **Theme**            | Disaster Management                             |
| 🌏 **Target Region**     | North Eastern Region (NER), India               |
| 💡 **Solution Type**     | AI-assisted Early Warning & Risk Monitoring     |
| 🖥️ **Prototype**        | Interactive Web-Based Decision Support Platform |
| ⚙️ **Framework**         | Streamlit                                       |

### Problem

The North Eastern Region faces recurring landslide hazards due to combinations of **intense rainfall, steep slopes, soil saturation, ground movement and vulnerable terrain**.

Traditional monitoring can become reactive, especially when information is fragmented between field observations, environmental measurements and administrative response.

Our goal is to create a unified platform that helps answer:

> **“Where is the risk increasing, how severe is it, and which community should receive attention first?”**

The official SIH problem statement calls for an AI-powered platform capable of analysing rainfall, soil moisture, satellite/terrain information and historical landslide data to identify high-risk areas and support early warnings.

---

# 🚨 Our Solution

The platform converts environmental and community-level information into an actionable monitoring workflow:

```text
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
```

The current prototype is designed as a **decision-support system**, not as an autonomous replacement for disaster-management authorities.

---

# ✨ Key Features

## 🧠 1. AI-Assisted Landslide Risk Prediction

The prediction pipeline works with five core environmental features:

* 🌧️ Rainfall
* 💧 Soil moisture
* ⛰️ Slope
* 🌍 Ground movement
* 📍 Elevation

When a trained model is available, the application can load it using `joblib` and use `predict_proba()` to generate a risk probability.

The application also contains a deterministic risk-engine fallback so the prototype remains functional when a trained model is unavailable.

### Risk Levels

| Risk Score | Level       | Interpretation                   |
| ---------: | ----------- | -------------------------------- |
|     `< 40` | 🟢 LOW      | Routine monitoring               |
| `40–59.99` | 🟡 MODERATE | Increased monitoring             |
| `60–79.99` | 🟠 HIGH     | Field attention recommended      |
|     `≥ 80` | 🔴 CRITICAL | Immediate assessment recommended |

---

# 📡 2. Environmental Sensor Monitoring

The prototype provides a dedicated **Sensor Command Center** for monitoring:

* Rainfall
* Soil moisture
* Ground movement
* Slope
* Elevation

It also includes an **interactive sensor simulator** that allows judges and developers to change environmental conditions and immediately observe how the risk output changes.

> ⚠️ **Prototype note:** The current interactive sensor values are simulated/test values. Production deployment would connect these inputs to physical IoT sensor gateways and validated environmental data sources.

---

# 🗺️ 3. GIS Risk Map

The system uses **Folium + Streamlit-Folium** to visualize geographically distributed risk.

The map can display:

* 📍 Village/community locations
* 🚨 Risk levels
* 🛣️ Field incidents
* 📊 AI risk values
* 🎯 Response priority
* 📌 Geographic coordinates

This transforms numerical predictions into an interface that can be understood geographically.

---

# 🚨 4. Early Warning System

Risk predictions are converted into four warning levels:

```text
🟢 LOW
   ↓
🟡 MODERATE
   ↓
🟠 HIGH
   ↓
🔴 CRITICAL
```

Each level is associated with recommended response actions.

### Example

**CRITICAL**

> Immediate field assessment recommended. Prepare community warning and inspect vulnerable roads.

**HIGH**

> Increase monitoring, inspect slopes and keep emergency response teams prepared.

The application explicitly treats these outputs as **decision-support warnings**, not guaranteed landslide occurrence times or automatic evacuation orders.

---

# 🏘️ 5. Community Risk Prioritization

A major focus of the prototype is:

> **Risk is not the only thing that matters — who is exposed matters too.**

The system associates risk with community-level information such as:

* Population
* Geographic location
* Road connectivity
* Importance
* Nearby infrastructure
* Nearest hospital
* Response priority

This produces a **Priority Score** that can help authorities determine which communities deserve attention first.

```text
             AI RISK
                │
                ▼
       ┌────────────────┐
       │ Priority Engine│
       └───────┬────────┘
               │
     ┌─────────┼─────────┐
     ▼         ▼         ▼
 Population  Location  Infrastructure
     │         │         │
     └─────────┼─────────┘
               ▼
       RESPONSE PRIORITY
```

---

# 📸 6. Incident Reporting

The platform allows field users to submit incident information including:

* 📷 Landslide photographs
* 📹 Camera evidence
* 📍 Latitude & longitude
* ⚠️ Severity
* 🛣️ Road blockage status
* 🏘️ Affected village/area
* 📝 Incident description

Incident records are stored locally using **SQLite** and can contain verification and notification metadata.

### Incident Workflow

```text
FIELD REPORT
     ↓
📷 Evidence
     ↓
📍 Geo-location
     ↓
🤖 AI-assisted verification
     ↓
🚨 Response queue
     ↓
🛟 Field / Emergency teams
```

> The current camera verification workflow is an evidence-assisted prototype. A production implementation would connect authenticated camera sources and a dedicated trained computer-vision model.

---

# 📊 7. Risk Analytics

The Analytics module provides decision-oriented visualizations including:

* AI risk distribution
* Alert-level distribution
* Population exposure
* Risk vs response priority
* Community comparison
* State/community filtering
* Top-risk communities
* Priority rankings
* Searchable data explorer
* CSV export

The system specifically highlights communities that combine **high predicted risk with high response priority**, helping move from raw prediction to operational decision-making.

---

# 📑 8. Decision-Ready Reports

The reporting module converts monitoring information into structured reports.

### Available outputs

* 📊 CSV reports
* 📄 Summary reports
* 📈 Full monitoring data
* 🚨 Recommended response queue
* 🎯 Priority-ranked communities
* 👥 Population exposure summaries

The response queue can rank communities using **Priority Score + AI Risk** and display recommended actions.

---

# 🌐 9. Multilingual Interface

The application is designed with the linguistic diversity of NER in mind.

Current interface language options include:

🇬🇧 English
🇮🇳 Hindi
ಕನ್ನಡ Kannada
தமிழ் Tamil
অসমীয়া Assamese
বাংলা Bengali
মৈতৈলোন্ / Manipuri
Mizo
Khasi
Garo
Bodo
नेपाली Nepali

This is intended to make the platform more accessible to different regional stakeholders.

---

# 🧩 System Architecture

```text
                    ┌───────────────────────┐
                    │  Environmental Data   │
                    │                       │
                    │ Rainfall              │
                    │ Soil Moisture         │
                    │ Slope                 │
                    │ Ground Movement       │
                    │ Elevation             │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    AI / Risk Engine   │
                    │                       │
                    │ ML model if available │
                    │ + risk-engine fallback│
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Risk Classification │
                    │                       │
                    │ LOW / MODERATE        │
                    │ HIGH / CRITICAL       │
                    └───────────┬───────────┘
                                │
             ┌──────────────────┼──────────────────┐
             ▼                  ▼                  ▼
       🗺️ GIS MAP         🚨 ALERTS          📊 ANALYTICS
             │                  │                  │
             └──────────────────┼──────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │ Community Prioritizer │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Response Support      │
                    │ Reports / Incidents   │
                    └───────────────────────┘
```

---

# 🛠️ Technology Stack

| Technology              | Purpose                     |
| ----------------------- | --------------------------- |
| 🐍 **Python**           | Core application logic      |
| 🎈 **Streamlit**        | Interactive web application |
| 🧠 **Scikit-learn**     | ML model support            |
| 💾 **Joblib**           | Model loading               |
| 🐼 **Pandas**           | Data processing             |
| 📊 **Plotly**           | Interactive analytics       |
| 🗺️ **Folium**          | GIS mapping                 |
| 🌐 **Streamlit-Folium** | Map integration             |
| 🗄️ **SQLite**          | Incident storage            |
| 🎨 **HTML/CSS**         | Custom dashboard interface  |

The project's Python dependencies are defined in `requirements.txt`.

---

# 📂 Project Structure

```text
AI-based-monitoring-system/
│
├── 📁 assets/
│   └── Application assets
│
├── 📁 data/
│   └── Risk, road, infrastructure & village datasets
│
├── 📁 models/
│   └── Risk engine / ML model components
│
├── 📁 services/
│   └── Supporting application services
│
├── 📄 app.py
│   └── Main Streamlit application
│
├── 📄 requirements.txt
│   └── Python dependencies
│
├── 📄 package-lock.json
│   └── Package dependency lock file
│
└── 📄 README.md
    └── Project documentation
```

---

# 🚀 Run Locally

## 1️⃣ Clone the repository

```bash
git clone https://github.com/varshadevaraj70/AI-based-monitoring-system.git
cd AI-based-monitoring-system
```

## 2️⃣ Create a virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

## 4️⃣ Start the application

```bash
streamlit run app.py
```

The application will normally become available at:

```text
http://localhost:8501
```

---

# 🌐 Live Prototype

### 🚀 Try the deployed prototype

**[Open AI-Based Landslide Monitoring System](https://ai-based-monitoring-system-9nfn8r3kavkpxn6nuwaom2.streamlit.app/)**

---

# 🎬 Suggested SIH Demonstration Flow

For a short college-level SIH demonstration:

### 01 — Dashboard

Show the overall monitoring situation.

↓

### 02 — Risk Map

Select a high-risk community and show its geographic position.

↓

### 03 — Sensor Command Center

Change:

```text
Rainfall ↑
Soil Moisture ↑
Ground Movement ↑
```

↓

### 04 — AI Risk

Show the change in predicted risk.

↓

### 05 — Early Alert

Show how the risk level changes:

```text
LOW → MODERATE → HIGH → CRITICAL
```

↓

### 06 — Community Priority

Show why a high-risk populated community receives higher response priority.

↓

### 07 — Incident Reporting

Submit a sample geo-tagged incident with photo evidence.

↓

### 08 — Reports

Generate/export a decision-ready response report.

> **The strongest demo story is not “look at our dashboard.”**
>
> **It is “watch an environmental change propagate from sensor input → risk prediction → map → warning → community priority → response.”**

---

# 🧪 Prototype vs Production

This project is currently an **SIH prototype / proof of concept**.

### ✅ Demonstrated in the prototype

* Interactive dashboard
* Risk calculation
* ML-model loading support
* Environmental feature processing
* Sensor simulation
* GIS risk visualization
* Risk classification
* Early-warning workflow
* Community prioritization
* Analytics
* Incident reporting
* Camera/photo evidence capture
* SQLite incident storage
* CSV/report export
* Multilingual interface
* Decision-support workflow

### 🚀 Planned for production deployment

* Real IoT sensor networks
* Validated regional sensor calibration
* Operational weather/API feeds
* Satellite-derived terrain and vegetation features
* Larger historical landslide datasets
* Dedicated computer-vision model
* Model calibration and uncertainty estimation
* SMS / push notification infrastructure
* Offline-first mobile functionality
* Secure role-based access
* Government-authority integration
* Continuous model monitoring and retraining

---

# 🔬 AI / Risk Methodology

The system accepts the following core environmental variables:

```text
Rainfall
    +
Soil Moisture
    +
Slope
    +
Ground Movement
    +
Elevation
    ↓
Risk Estimation
    ↓
0–100 Risk Score
    ↓
Risk Level
```

The fallback prototype risk engine uses weighted environmental contributions:

```text
Risk =
    30% Rainfall
  + 20% Soil Moisture
  + 20% Slope
  + 20% Ground Movement
  + 10% Elevation
```

This fallback provides a transparent baseline while the application can use a trained probabilistic model when a compatible model artifact is available.

### Why this approach?

Landslide risk is influenced by multiple interacting environmental factors. A single rainfall threshold is therefore insufficient as a complete decision-support mechanism.

The platform is designed so that the risk engine can evolve as better regional datasets and validated ML models become available.

---

# 🎯 What Makes This Different?

### ❌ Traditional approach

```text
Incident occurs
      ↓
Manual report
      ↓
Investigation
      ↓
Response
```

### ✅ Proposed approach

```text
Environmental signals
        ↓
Risk estimation
        ↓
Early warning
        ↓
GIS visualization
        ↓
Community prioritization
        ↓
Field verification
        ↓
Response
```

### Core philosophy

> **Move from reactive disaster response toward predictive, prioritized and data-assisted preparedness.**

---

# 🛡️ Safety & Responsible AI

This system is designed as a **decision-support tool**.

AI predictions should **not** be treated as guaranteed landslide events.

Critical operational decisions such as:

* evacuation,
* road closure,
* emergency dispatch,
* public warnings,

should be validated using authoritative field observations and disaster-management protocols.

The prototype itself distinguishes between predictive outputs and official emergency decisions.

---

# 🌱 Future Roadmap

```text
                 CURRENT
                    │
                    ▼
          🖥️ SIH PROTOTYPE
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     IoT Sensors        Better Datasets
          │                   │
          └─────────┬─────────┘
                    ▼
             🤖 Better AI
                    │
                    ▼
             🛰️ Satellite Data
                    │
                    ▼
          📱 Offline Mobile App
                    │
                    ▼
          🚨 Operational Alerts
                    │
                    ▼
       🏛️ Government Integration
                    │
                    ▼
       🌏 NER-Wide Deployment
```

### Phase 1 — Prototype

* Risk engine
* Dashboard
* GIS
* Alerts
* Analytics
* Incident reporting

### Phase 2 — Real Data

* IoT sensors
* Weather APIs
* Historical event databases
* Satellite-derived features

### Phase 3 — Intelligence

* Advanced ML models
* Computer vision
* Model calibration
* Uncertainty estimation
* Continuous learning

### Phase 4 — Deployment

* Offline mobile application
* SMS/push alerts
* Authority dashboards
* Field-worker applications
* NER-wide infrastructure

---

# 💡 Expected Impact

### 👨‍👩‍👧 Communities

Earlier awareness of potentially dangerous conditions.

### 🏛️ Authorities

A centralized view of risk and response priorities.

### 🚑 Emergency Teams

Better prioritization of locations requiring field attention.

### 🛣️ Infrastructure Teams

Early identification of potentially vulnerable roads and corridors.

### 🌏 NER

A scalable foundation for data-driven landslide preparedness.

---

# 🧭 Project Vision

> ### **“Don't wait for the mountain to move. Detect the risk before it becomes a disaster.”**

The long-term vision is to build a continuously learning regional disaster-intelligence platform that combines **AI + IoT + GIS + satellite data + community reporting** to help protect vulnerable communities across the North Eastern Region.

---

# 👥 Team

### Smart India Hackathon 2026

**Project:** AI-Based Early Warning & Landslide Risk Monitoring System in NER
**Problem Statement:** SIH26001
**Theme:** Disaster Management

---

# 📜 Disclaimer

This repository contains an **SIH 2026 prototype** intended for demonstration, experimentation and further development.

It is **not a certified disaster-warning or evacuation system**.

Predictions, risk scores and simulated sensor values must be validated against authoritative environmental measurements and field observations before any real-world emergency use.

---

<p align="center">

### 🏔️ AI + Data + GIS + Community = Safer Mountains

**Built for Smart India Hackathon 2026**

⭐ If you find this project interesting, consider starring the repository.

</p>


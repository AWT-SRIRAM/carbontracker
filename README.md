# 🌱 EcoTrace — Carbon Footprint Analytics & Dashboard

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org)

**EcoTrace** is a carbon footprint analytics microservice and interactive web dashboard. It enables users to complete an onboarding assessment, log daily eco-friendly activities (like commuting by public transit, eating vegan meals, or hang-drying laundry), track their net carbon reduction in real-time, and unlock gamified achievements. 

Powered by **FastAPI** on the backend, **Pandas** & **NumPy** for heavy data calculations, and a high-performance vanilla **HTML5/CSS3/JS** dashboard, EcoTrace makes sustainable living intuitive and rewarding.

---

## 🗺️ System Overview & Architecture

```
                 +--------------------------------------------+
                 |             Web UI Dashboard               |
                 |  (index.html, styles.css, app.js in /static) |
                 +----------------------+---------------------+
                                        |
                             API Calls  | (JSON / CSV Export)
                                        v
                 +----------------------+---------------------+
                 |           FastAPI Web Server               |
                 |      (main.py, routes.py, schemas.py)      |
                 +----------+----------------------+----------+
                            |                      |
             Read/Write SQL |                      | Calculate Stats
                            v                      v
                 +----------+-----------+  +-------+----------+
                 |  SQLite DB / Models  |  | Analytics Engine |
                 | (database.py,        |  | (analytics.py using|
                 |  models.py)          |  |  Pandas/NumPy)   |
                 +----------------------+  +------------------+
```

---

## ✨ Key Features

*   **📊 Personalized Baseline Profile**: Calculate your initial monthly carbon footprint across **Energy**, **Transport**, **Food**, and **Consumption** based on your lifestyle choices (car fuel type, monthly electricity/gas usage, dietary habits, etc.).
*   **🌿 Real-Time Reduction Analytics**: Log daily green activities. The dashboard automatically computes total CO2 saved in kilograms and displays how close you are to your custom footprint reduction goal.
*   **📈 Dynamic Insights Engine**: Automated recommendations based on your highest emission categories (e.g. suggesting meatless alternatives if your food footprint is high, or carpool solutions if transport dominates).
*   **🏆 Gamified Badges**: Unlock credentials as you perform eco-friendly tasks:
    *   `Transit Hero` (30+ km green transit logged)
    *   `Plant-Powered` (10+ vegetarian or vegan meals logged)
    *   `Energy Saver` (5+ electricity/heating/appliance saving activities logged)
    *   `Eco Champion` (Achieved or exceeded your custom monthly reduction goal)
*   **📥 CSV Export**: Seamlessly download your full logging history as a structured CSV spreadsheet.
*   **🐳 Containerized & Cloud-Ready**: Fully dockerized with multi-stage build compatibility.

---

## 📐 How Carbon Footprint is Calculated

The system evaluates emissions using scientifically backed base factors:

| Category | Input Metric | Emission Factor |
| :--- | :--- | :--- |
| **Energy** | Electricity (kWh) | `0.40 kg CO2 / kWh` |
| **Energy** | Natural Gas (kWh) | `0.18 kg CO2 / kWh` |
| **Transport**| Gasoline Car | `0.19 kg CO2 / km` |
| **Transport**| Diesel Car | `0.17 kg CO2 / km` |
| **Transport**| Hybrid Car | `0.10 kg CO2 / km` |
| **Transport**| Electric Car | `0.05 kg CO2 / km` |
| **Transport**| Public Transit | `1.20 kg CO2 / hour` (~0.04 kg CO2 / km) |
| **Food** | Diet Type | Vegan: `80 kg/month` \| Vegetarian: `120 kg/month` \| Moderate Meat: `200 kg/month` \| High Meat: `300 kg/month` |
| **Consumption**| Shopping Level | Low: `100 kg/month` \| Moderate: `220 kg/month` \| High: `400 kg/month` |

> [!NOTE]
> Daily carbon savings subtraction is computed using Pandas vector sums on action quantities times the action's specific mitigation weight (e.g. `-1.50 kg CO2` for a Vegan meal, `-0.19 kg CO2` per km of biking).

---

## 🛠️ Tech Stack & Directory Structure

*   **Backend Framework**: FastAPI (Asynchronous Python Web framework)
*   **Database**: SQLite (SQLAlchemy 2.0 ORM)
*   **Data Processing**: Pandas & NumPy
*   **Frontend**: Native HTML5, modern vanilla CSS3 (including custom properties and animations), and asynchronous Vanilla JS.

Here are the key files inside the project:
*   [main.py](file:///s:/prompt%20war/main.py) - FastAPI application entry point, database seeding, and static assets mounting.
*   [routes.py](file:///s:/prompt%20war/routes.py) - REST API routes for users, profiles, action logs, and dashboard.
*   [models.py](file:///s:/prompt%20war/models.py) - SQLAlchemy database tables mapping users, profiles, actions, and logs.
*   [schemas.py](file:///s:/prompt%20war/schemas.py) - Pydantic schemas validating API inputs/outputs.
*   [analytics.py](file:///s:/prompt%20war/analytics.py) - Pandas-powered calculation module for baselines, savings, badges, and insights.
*   [database.py](file:///s:/prompt%20war/database.py) - Database engine creation and session providers.
*   [Dockerfile](file:///s:/prompt%20war/Dockerfile) - Docker build script optimized for containerized environments.
*   [static/](file:///s:/prompt%20war/static) - Frontend web assets.

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.11+ and Git installed on your system.

### 2. Local Setup
1. **Clone the repository and enter the directory**:
   ```bash
   git clone https://github.com/AWT-SRIRAM/carbontracker.git
   cd carbontracker
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```
   The backend will seed default data and host the application at: `http://127.0.0.1:8000`

### 3. Docker Deployment
You can run the application containerized:
```bash
# Build the image
docker build -t ecotrace .

# Run the container
docker run -p 8080:8080 ecotrace
```
Access the application at `http://localhost:8080`.

---

## 📡 API Reference

All requests must be prefixed with `/api`.

### Users & Profiles
*   `GET /users` — Retrieve all active users (useful for switches).
*   `POST /users` — Create a user.
*   `POST /profile/baseline?user_id={id}` — Save/Update onboarding baseline.
*   `GET /profile/baseline?user_id={id}` — Fetch onboarding baseline settings.

### Action Items & Logs
*   `GET /actions` — List all standard carbon-reducing actions (seeded automatically).
*   `POST /logs?user_id={id}` — Log a carbon-saving activity.
*   `GET /logs?user_id={id}` — Retrieve a history of user-logged actions.
*   `DELETE /logs/{log_id}?user_id={id}` — Remove a daily log entry.
*   `GET /logs/export?user_id={id}` — Export entire activity logs as a `.csv` download.

### Analytics
*   `GET /analytics/dashboard?user_id={id}` — Calculate baseline emissions, total logged savings, goal progression status, list badges, and yield dynamic insights.

---

## 💡 Developer Customization

To add customized actions for seeding the database, edit the `DEFAULT_ACTIONS` array in [main.py](file:///s:/prompt%20war/main.py#L19-L68):
```python
DEFAULT_ACTIONS = [
    {
        "title": "Use Solar Panels",
        "description": "Utilized home-generated solar electricity.",
        "category": "Energy",
        "co2_savings_kg": 2.50
    },
    # ...
]
```

To modify default carbon conversion metrics, update `CO2_FACTORS` in [analytics.py](file:///s:/prompt%20war/analytics.py#L11-L32).

---

## 🤝 Contributing
Contributions are welcome! Please feel free to open a Pull Request or report bugs via issues.

*Made with 💚 to support sustainable lifestyles.*

# 🖥️ EcoTrace Frontend Dashboard

This directory contains the user interface assets for the **EcoTrace** application. It functions as a single-page application (SPA) that interacts with the FastAPI backend to log activities, visualize carbon footprint metrics, and track progress.

---

## 🎨 Design System & Aesthetics

The interface is styled using modern **Vanilla CSS** with a premium, sleek glassmorphism theme designed for visual appeal and accessibility:
*   **Color Palette**: Harmonious forest greens, subtle emerald gradients, slate greys, and vibrant status colors for gamification badges.
*   **Typography**: Uses `Outfit` and `Inter` via Google Fonts for clean, modern legibility.
*   **Glassmorphism**: Visual depth created through thin semi-transparent backgrounds (`backdrop-filter: blur(12px)`), subtle borders, and soft drop shadows.
*   **Micro-interactions**: Hover transitions on interactive inputs, active scaling on buttons, fade-in animations on onboarding cards, and animated progress bars for carbon goal tracking.

---

## 📁 File Structure

*   [index.html](file:///s:/prompt%20war/static/index.html) — Holds the structure of the dashboard, containing:
    *   **User switcher** (top navigation bar)
    *   **Onboarding screen** (multi-step form to calculate baseline carbon footprints)
    *   **Dashboard view** (real-time metrics, goals, insights, and interactive graphs)
    *   **Activity logs** (form to log tasks, table of recent logs, and CSV download trigger)
*   [styles.css](file:///s:/prompt%20war/static/styles.css) — Custom stylesheet defining the design system tokens, responsive grid layouts, glassmorphic cards, custom utility classes, and keyframe animations.
*   [app.js](file:///s:/prompt%20war/static/app.js) — Interactive frontend controller containing the application state, API wrappers, DOM binding, rendering logic, and Chart.js visualizations.

---

## 🛠️ Key UI Components & Flows

```
  +-------------------------------------------------------------+
  |                        1. USER SWITCHER                     |
  |  Select user profile to instantly load personalized state   |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  |                 2. ONBOARDING & CALCULATOR                  |
  |  Collect Energy, Transport, Food & Shopping baselines       |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  |                   3. DASHBOARD METRICS                      |
  |  Baseline Total | Net Savings | Actual Monthly CO2 | Goal % |
  +------------------------------+------------------------------+
                                 |
                                 v
  +------------------------------+------------------------------+
  |                  4. DATA VISUALIZATION                      |
  |  Interactive Doughnut Chart (Chart.js) showing footprint %   |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  |              5. ENGAGEMENT, LOGGING & EXPORTS               |
  |  Earn Badges | Log Daily Actions | View History | Export CSV|
  +-------------------------------------------------------------+
```

---

## 📊 Data Visualization (Chart.js Integration)

To showcase the baseline emissions, the frontend integrates with **Chart.js** via CDN.
*   **Canvas Element**: `<canvas id="emissionsDoughnutChart"></canvas>`
*   **Render Function**: `renderEmissionsChart(categoryBaselines)` in [app.js](file:///s:/prompt%20war/static/app.js#L522) automatically instantiates or updates a custom Doughnut chart.
*   **Fallbacks**: Automatically toggles between a chart rendering state and a user-friendly empty state if no profile baseline data has been calculated.

---

## 🔌 API Integration Interface

The frontend connects to the backend through a standard set of async fetch helper functions in `app.js`:

```javascript
const API_BASE = '/api';

// Example fetching dashboard analytics
async function fetchDashboardData(userId) {
    const res = await fetch(`${API_BASE}/analytics/dashboard?user_id=${userId}`);
    return await res.json();
}
```

---

## 💅 Styling Customs & Custom Properties

We maintain a consistent theme using global CSS variables defined in [styles.css](file:///s:/prompt%20war/static/styles.css):
```css
:root {
    --primary-color: #10b981;     /* Emerald green main theme */
    --primary-hover: #059669;
    --bg-dark: #0f172a;           /* Deep dark slate background */
    --card-bg: rgba(30, 41, 59, 0.7);
    --border-color: rgba(255, 255, 255, 0.08);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
}
```

---

## 🚀 Local Development

To make changes to the layout or script:
1. Since static files are served by FastAPI, make sure to start the server:
   ```bash
   python main.py
   ```
2. Navigate to `http://127.0.0.1:8000` in your browser.
3. FastAPI is configured with hot reloading (`reload=True`), so modifications in these files will reflect immediately in the browser.

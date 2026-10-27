# 💧 WaterAid Smart Monitor

AI-based Smart Water Infrastructure Monitoring System
**Case Study:** WaterAid Rwanda

A full-stack web application that continuously monitors water pipeline infrastructure using IoT telemetry, machine learning anomaly detection, and real-time dashboards.

---

## 🎯 Features

- **Real-time telemetry ingestion** (5-second background simulator)
- **AI leak detection** (Isolation Forest + rule-based thresholds)
- **Automated alerts** with confidence scores and estimated water loss
- **Interactive dashboards** with live charts and health breakdowns
- **Role-based access control** (Admin / Manager / Technician)
- **Maintenance task logging** from field technicians
- **Live WebSocket updates** (with polling fallback)
- **Continuous sensor simulator** runs forever while backend is up

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  React Frontend │  ←WS→   │  Django Backend │  ←SQL→  │   PostgreSQL    │
│   (Vite + v4)   │  ←HTTP→ │  (DRF + Chnl)   │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                    ↑
                                    │ Thread
                            ┌─────────────────┐
                            │ Sensor Simulator│
                            │  (Daemon Thread)│
                            └─────────────────┘
                                    ↓
                            ┌─────────────────┐
                            │   AI Engine     │
                            │ (LeakDetector)  │
                            └─────────────────┘
```

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS v4, Chart.js, React Router |
| Backend | Django 4.2, Django REST Framework, Channels, SimpleJWT |
| Database | PostgreSQL 15 |
| AI/ML | scikit-learn (Isolation Forest), pandas, numpy |
| Real-time | WebSockets (Django Channels), polling fallback |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/wateraid-smart-monitor.git
cd wateraid-smart-monitor
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Create database
# In psql: CREATE DATABASE wateraid_monitor;

python manage.py migrate
python manage.py seed_data --logs 500
python manage.py runserver
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
cp .env.example .env
npm run dev
```

### 4. Access the App

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000/api/
- **Swagger Docs:** http://localhost:8000/swagger/
- **Django Admin:** http://localhost:8000/admin/

### Demo Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Manager | `manager` | `manager123` |
| Technician | `tech1` | `tech123` |

---

## 📸 Screenshots

### Login
![Login](docs/screenshots/login.png)

### Manager Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### AI Predictive Alerts
![Alerts](docs/screenshots/alerts.png)

### IoT Telemetry
![Telemetry](docs/screenshots/telemetry.png)

---

## 🔐 Role-Based Access Control

| Feature | Admin | Manager | Technician |
|---|---|---|---|
| View Dashboard | ✅ | ✅ | ✅ |
| View Telemetry | ✅ | ✅ | ✅ |
| Log Maintenance Task | ✅ | ✅ | ✅ |
| View AI Alerts | ✅ | ✅ | ❌ |
| Deploy Technician | ✅ | ✅ | ❌ |
| Register New Sector | ✅ | ✅ | ❌ |
| Manage Users | ✅ | ❌ | ❌ |
| Control Simulator | ✅ | ✅ | ❌ |

---

## 🧪 Testing

### Manual Sensor Trigger

```bash
curl -X POST http://localhost:8000/api/simulate/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sector_id": "SEC-NYA-01", "scenario": "leak"}'
```

### Simulator Control

```bash
# Status
curl http://localhost:8000/api/simulator/status/ -H "Authorization: Bearer YOUR_TOKEN"

# Stop
curl -X POST http://localhost:8000/api/simulator/stop/ -H "Authorization: Bearer YOUR_TOKEN"

# Start
curl -X POST http://localhost:8000/api/simulator/start/ -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📖 API Documentation

Once the backend is running, visit:

- **Swagger UI:** http://localhost:8000/swagger/
- **ReDoc:** http://localhost:8000/redoc/

Key endpoints:

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login/` | Get JWT token |
| GET | `/api/dashboard/stats/` | Aggregated stats |
| GET | `/api/sectors/` | List pipeline sectors |
| POST | `/api/sensor-logs/` | Ingest new telemetry |
| GET | `/api/sensor-logs/trend/` | Time-series data |
| GET | `/api/alerts/active/` | Unresolved alerts |
| POST | `/api/tasks/` | Log maintenance task |
| POST | `/api/simulate/` | Trigger one-off anomaly |

---

## 🌐 WebSocket Channels

| URL | Payload | Purpose |
|---|---|---|
| `ws://localhost:8000/ws/telemetry/` | Sensor log JSON | Live flow/pressure updates |
| `ws://localhost:8000/ws/alerts/` | AI alert JSON | Instant anomaly notifications |

---

## 🧠 AI Engine

The leak detector combines:

1. **Rule-based thresholds** (instant, deterministic)
   - Pressure drop >15% + flow anomaly >20% → Critical leak
   - Pressure drop >10% → Warning
   - Flow deviation >25% → Flow anomaly

2. **Isolation Forest** (unsupervised ML, pattern-based)
   - Trained on 5,500 synthetic samples
   - Detection based on multi-dimensional outliers
   - Auto-retrains on first launch if model missing

Model file: `backend/ai_engine/models/leak_detector_model.pkl`
Generated automatically on first startup (excluded from git).

---

## 📁 Project Structure

```
wateraid-smart-monitor/
├── backend/
│   ├── wateraid_project/       # Django settings + URLs
│   ├── core/                    # Main app
│   │   ├── models.py            # 6 database models
│   │   ├── views.py             # API endpoints + RBAC
│   │   ├── serializers.py       # DRF serializers
│   │   ├── permissions.py       # Role permission classes
│   │   ├── simulator.py         # Background sensor simulator
│   │   ├── consumers.py         # WebSocket consumers
│   │   ├── routing.py           # WS URL routes
│   │   └── management/
│   │       └── commands/
│   │           ├── seed_data.py
│   │           └── run_simulation.py
│   ├── ai_engine/
│   │   ├── leak_detector.py     # Hybrid AI model
│   │   └── models/              # .pkl files (gitignored)
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx
│   │   │   └── RoleGate.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── hooks/
│   │   │   └── useLiveTelemetry.js
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── ManagerDashboard.jsx
│   │   │   ├── AIAlerts.jsx
│   │   │   ├── IoTTelmetry.jsx
│   │   │   ├── TaskEntry.jsx
│   │   │   └── Infrastructure.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── .env.example
│
├── docs/
│   └── screenshots/
├── .gitignore
└── README.md
```

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `401 Unauthorized` on login | Run `python manage.py seed_data` to create users |
| WebSocket not connecting | Ensure you're using `daphne` (not `runserver`) |
| Charts show no data | The simulator should auto-start; check terminal for `[Simulator] ▶ Started` |
| `psycopg2` build fails | Install PostgreSQL first (`pip install psycopg2-binary`) |
| Tailwind classes not applying | Hard refresh `Ctrl+Shift+R` after `npm run dev` |

---

## 📝 License

This project is a final-year academic submission for Mount Kigali University.

**Developer:** Ruberwa Toussaint (BBICTR/2024/44697)
**Supervisor:** Mr. Rafiki Ndayitegye
**Institution:** Mount Kigali University

---

## 🙏 Acknowledgments

- **WaterAid Rwanda** — Case study partner
- **Mount Kigali University** — Academic support
- **Django, React, and Tailwind communities** — Open-source foundations
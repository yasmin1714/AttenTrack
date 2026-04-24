# AttenTrack 🎯
### AI-Driven Attention Span Monitoring & Notification System

> Real-time student attention monitoring using computer vision — with instant parental alerts, role-based dashboards, and a privacy-first design.

---

### Live Demo: https://www.youtube.com/watch?v=vai5OrEoKxE

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Environment Variables](#environment-variables)
- [How It Works](#-how-it-works)
- [AI Models](#-ai-models)
- [User Roles & Dashboards](#-user-roles--dashboards)
- [API Endpoints](#-api-endpoints)
- [Deployment](#-deployment)
- [Known Limitations](#-known-limitations)
- [Future Scope](#-future-scope)
- [Contributing](#-contributing)

---

## 🧠 Overview

AttenTrack is a full-stack, AI-powered web application that monitors student attention in real time through a webcam. It detects distraction signals — closed eyes, phone usage, and abnormal head pose — fuses them into a single **Attention Score (0–100)**, and automatically notifies parents when a sustained violation is detected.

The system is built around **three user roles**: Student, Parent, and Admin — each with a dedicated dashboard. All video processing happens on the backend; only derived numerical metrics are stored, ensuring student privacy.

---

## ✨ Key Features

- 🎥 **Live Webcam Monitoring** — Captures and analyses frames every 500 ms directly from the browser
- 👁️ **Eye Tracking** — Detects closed eyes and sleeping using Eye Aspect Ratio (EAR)
- 🧭 **Head Pose Estimation** — Detects looking away via 3D PnP landmark projection
- 📱 **Phone Detection** — Identifies mobile phone usage using YOLOv8 (COCO class 67)
- 📊 **Real-time Attention Score** — Fused 0–100 score streamed live via WebSocket
- 🔔 **Instant Parental Alerts** — Email with screenshot when 3 consecutive violations are detected
- 👨‍👩‍👧 **Parent-Child Account Linking** — Student registers with parent's email; auto-linked on signup
- 🟢 **Online/Offline Status** — Parent dashboard shows whether student is actively in session
- 📈 **Live Charts** — Rolling 40-point attention trend graph with Chart.js
- 🛡️ **Role-Based Auth** — Separate login/signup for Student, Parent, and Admin
- 📥 **PDF Export** — Admin can export alert reports as formatted PDFs via jsPDF
- 🔒 **Privacy-First** — No raw video is ever stored or transmitted; only scores and timestamps

---

## 🛠 Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 + Vite | UI framework and build tool |
| React Router DOM v6 | Client-side routing |
| Chart.js + react-chartjs-2 | Real-time attention charts |
| jsPDF | PDF export for admin alert reports |
| Scoped CSS | Component-isolated styling |

### Backend
| Technology | Purpose |
|---|---|
| FastAPI | REST API + WebSocket server |
| Uvicorn | ASGI server |
| PyMongo | MongoDB driver |
| python-dotenv | Environment variable management |
| smtplib / Gmail SMTP | Email alert delivery |

### AI / Computer Vision
| Technology | Purpose |
|---|---|
| MediaPipe Face Mesh | 468-point facial landmark detection |
| MediaPipe BlazeFace | Fast face presence detection |
| OpenCV (cv2) | Image processing and head pose (solvePnP) |
| Ultralytics YOLOv8n | Phone object detection (COCO) |
| NumPy | Numerical array operations |

### Database & Infrastructure
| Technology | Purpose |
|---|---|
| MongoDB | Document store (Atlas or local) |
| WebSocket (FastAPI) | Real-time score streaming |
| Gmail SMTP SSL (port 465) | Email notifications |

---

## 🏗 System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      BROWSER (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │   Student   │  │   Parent    │  │     Admin       │    │
│  │  Dashboard  │  │  Dashboard  │  │   Dashboard     │    │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘    │
│         │ webcam         │ poll              │ REST        │
│         │ frames         │                   │             │
└─────────┼────────────────┼───────────────────┼─────────────┘
          │                │                   │
          ▼                ▼                   ▼
┌────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                             │
│  frame_processor.py      REST Routes       WebSocket Mgr   │
│  ┌─────────────────┐    ┌────────────┐    ┌─────────────┐  │
│  │ FaceDetector    │    │ /auth      │    │ push() per  │  │
│  │ EyeTracker      │    │ /student   │    │ student_id  │  │
│  │ PhoneDetector   │    │ /parent    │    └─────────────┘  │
│  │ AttentionScorer │    │ /admin     │                     │
│  └────────┬────────┘    └────────────┘                     │
│           │                                                 │
│           └──► AlertService ──► Gmail SMTP ──► Parent      │
└───────────┬────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────────────┐
│                        MongoDB                              │
│   students | parents | admins | attention_logs | alerts    │
└────────────────────────────────────────────────────────────┘
```

**Data flow:**
1. Browser captures webcam frame every 500 ms
2. Frame is encoded as base64 JPEG and POSTed to `/api/process-frame`
3. AI pipeline runs: face → eye → head pose → phone → score
4. Result stored in `attention_logs`; alerts triggered after 3 consecutive violations
5. Result pushed via WebSocket to all connected dashboards for that `student_id`

---

## 📁 Project Structure

```
attentrack/
│
├── backend/
│   ├── main.py                  # FastAPI app entry point, CORS, WebSocket route
│   ├── auth.py                  # Signup, login, logout endpoints
│   ├── database.py              # MongoDB connection and collection handles
│   ├── schemas.py               # Pydantic request/response models
│   ├── frame_processor.py       # Core AI pipeline endpoint (POST /api/process-frame)
│   ├── alert_service.py         # Email alert with dynamic parent email lookup
│   ├── websocket_manager.py     # ConnectionManager — multi-client WebSocket hub
│   ├── screenshot_capture.py    # Saves violation screenshots to disk
│   ├── realtime_monitor.py      # Optional standalone local monitor script
│   ├── requirements.txt
│   ├── .env.example
│   └── routes/
│       ├── attention.py         # POST /api/attention (manual ingestion)
│       ├── student.py           # GET /api/student/:id/...
│       ├── parent.py            # GET /api/parent/:id/...
│       └── admin.py             # GET /api/admin/...
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── pages/
    │   │   ├── HomePage.jsx
    │   │   ├── AttenTrack.jsx       # Login page
    │   │   ├── SignUp.jsx           # Signup page (Student / Parent)
    │   │   ├── StudentDashboard.jsx
    │   │   ├── ParentDashboard.jsx
    │   │   └── AdminDashboard.jsx
    │   ├── components/
    │   │   └── AttentionChart.jsx   # Chart.js line chart (forwardRef)
    │   └── hooks/
    │       └── useAttenTrack.js     # useStudentLive | useParentReport | useAdminMetrics
    ├── .env.example
    └── package.json
```

---

## 🚀 Getting Started

### Prerequisites

- Python **3.11+**
- Node.js **20 LTS** + npm
- MongoDB **7.x** — [local](https://www.mongodb.com/docs/manual/installation/) or [Atlas free tier](https://www.mongodb.com/cloud/atlas)
- A **Gmail App Password** — [how to generate one](https://support.google.com/accounts/answer/185833)
- A device with a webcam

---

### Backend Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/attentrack.git
cd attentrack/backend

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI, Gmail credentials, and admin password

# 5. Start the server
uvicorn main:app --reload --port 8000
```

API live at: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

---

### Frontend Setup

```bash
cd attentrack/frontend

# 1. Install dependencies
npm install

# 2. Install jsPDF (required for Admin PDF export)
npm install jspdf

# 3. Configure backend URL
echo "VITE_BACKEND_URL=http://localhost:8000" > .env

# 4. Start dev server
npm run dev
```

App live at: `http://localhost:5173`

---

### Environment Variables

**`backend/.env`**

```env
# MongoDB
MONGO_URI=mongodb://localhost:27017

# Email alerts  (use Gmail App Password, NOT your Gmail account password)
SENDER_EMAIL=your.alerts@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
RECEIVER_EMAIL=fallback@example.com   # fallback if no parent email found in DB

# Admin login credentials
ADMIN_EMAIL=admin@attentrack.com
ADMIN_PASSWORD=YourStrongPassword123

# Optional tuning
SEND_INTERVAL=2.0           # seconds between backend posts (standalone monitor)
ALERT_COOLDOWN=10.0         # minimum seconds between two alert emails
VIOLATION_THRESHOLD=3       # consecutive violations before alert fires
STUDENT_ID=101              # student ID for standalone realtime_monitor.py
```

**`frontend/.env`**

```env
VITE_BACKEND_URL=http://localhost:8000
```

---

## ⚙️ How It Works

### Attention Scoring

Every frame is analysed through four detection stages. A base score of **100** has the following deductions applied:

| Condition | Deduction |
|---|---|
| Face not detected | −40 |
| Phone detected | −35 |
| Eyes closed / sleeping | −30 |
| Looking away (head pose) | −20 |
| Multiple flags simultaneously | −10 extra |

Scores are clamped to **[0, 100]** and mapped to statuses:

| Score | Status | UI Colour |
|---|---|---|
| 70 – 100 | ✅ ATTENTIVE | 🟢 Green |
| 40 – 69 | ⚠️ DISTRACTED | 🟠 Orange |
| 0 – 39 | 🚫 NOT PAYING ATTENTION | 🔴 Red |

### Alert Trigger Logic

An alert fires only after **3 consecutive violations** — preventing single-frame false positives. On trigger:

1. Screenshot saved to `backend/screenshots/{student_id}_{timestamp}.jpg`
2. Alert document written to MongoDB `alerts` collection
3. Email with screenshot sent to the student's linked parent
4. WebSocket event pushed to all connected dashboards for that student
5. Violation counter resets to 0

### Parent Email Lookup (alert_service.py)

Resolution order for the recipient email:
1. `student.parent_email` field (set at signup)
2. `students.parent_id → parents collection → email` (set when parent registers)
3. `RECEIVER_EMAIL` env variable (global fallback)

---

## 🤖 AI Models

### 1. MediaPipe BlazeFace — Face Detection
Short-range mode (`model_selection=0`), optimised for < 2 m distances. Min confidence: **0.5**.

### 2. MediaPipe Face Mesh — Eye Tracking + Head Pose

**Eye Aspect Ratio (EAR):**
```
EAR = (‖p2−p6‖ + ‖p3−p5‖) / (2 × ‖p1−p4‖)
```
- EAR < 0.25 for 20+ frames → `eyes_closed = True`
- EAR < 0.20 for 60+ frames → `sleeping = True`

**Head Pose via OpenCV solvePnP:**
- Projects 6 landmarks (nose, chin, eye corners, mouth corners) onto a 3D face model
- Yaw > ±15° or Pitch < −10° → `looking_away = True`

### 3. YOLOv8n — Phone Detection
Pre-trained on COCO. Target class: **67 (cell phone)**. Confidence threshold: **0.5**.  
Runs on CPU — no GPU required.

---

## 👥 User Roles & Dashboards

### 🎓 Student Dashboard
- Live webcam feed with colour-coded status overlay
- Real-time attention score (updates every ~500 ms)
- 4 mini stat cards: Eye Status, Phone, Avg Score, Alert Count
- Rolling 40-point trend chart
- Alert history with scores and timestamps
- Session stats panel

### 👨‍👩‍👧 Parent Dashboard
- Displays data for the **linked student only** (resolved from login session)
- **Online/Offline status** — live data only shown when student is logged in
- 5 stat cards: Current Score, Session Avg, Peak, Lowest, Alert Count
- Attention performance chart with date pickers and PNG download
- Alert history with screenshot indicators
- Weekly performance progress bars
- AI-generated recommendations

### 🛡️ Admin Dashboard
- System-wide metrics: total students, estimated active, avg attention, alerts today
- Class-wide attention trend chart (per-minute averages across all students)
- Searchable user table — shows real `student_id`, email, parent email, online status
- Alert log with keyword search and **Export to PDF** (jsPDF)
- Add new users (student/parent) directly from the dashboard modal

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/signup/student` | Register student (with optional `parent_email`) |
| `POST` | `/api/auth/signup/parent` | Register parent |
| `POST` | `/api/auth/login` | Login — returns role, IDs, and linked children |
| `POST` | `/api/auth/logout/{student_id}` | Mark student offline |

### Student
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/student/{id}/live` | Latest attention log entry |
| `GET` | `/api/student/{id}/trend` | Last 20 attention logs |
| `GET` | `/api/student/{id}/alerts` | All alerts for this student |
| `GET` | `/api/student/{id}/status` | Online / offline flag |

### Parent
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/parent/{pid}/children` | List of linked student records |
| `GET` | `/api/parent/{pid}/student/{sid}/report` | Avg, peak, and lowest scores |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/metrics` | Total students, avg attention, alert count |
| `GET` | `/api/admin/alerts` | 10 most recent alerts (all students) |
| `GET` | `/api/admin/students` | All student records |
| `GET` | `/api/admin/attention-trend` | Per-minute class-wide average scores |

### Core Processing
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/process-frame` | Receive base64 JPEG, run full AI pipeline |
| `POST` | `/api/attention` | Manual attention data ingestion |
| `WS` | `/ws/{student_id}` | WebSocket stream — live score updates |

---

## 🌐 Deployment

### Frontend → [Vercel](https://vercel.com) *(Free)*

```bash
cd frontend
npm run build
npx vercel --prod
```

Set in Vercel dashboard → Environment Variables:
```
VITE_BACKEND_URL = https://your-backend.onrender.com
```

### Backend → [Render](https://render.com) *(Free tier)*

| Setting | Value |
|---|---|
| Root Directory | `backend/` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

Add all variables from `backend/.env` in the Render environment settings.

### Database → [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) *(Free 512 MB)*

1. Create a free M0 cluster
2. Add a database user and set IP access to `0.0.0.0/0`
3. Copy the connection string → set as `MONGO_URI` on Render

> ⚠️ **AI inference note:** MediaPipe + YOLOv8 require ~500 MB RAM. Render's free tier (512 MB) may be tight for multiple concurrent students. Consider Render Starter ($7/mo) or run the Python backend locally and expose it with [ngrok](https://ngrok.com) while using Atlas for the database — a practical setup since the monitor needs a webcam anyway.

---

## ⚠️ Known Limitations

- **Lighting:** Accuracy drops below ~100 lux. Good desk lighting is recommended.
- **Camera evasion:** Students who angle the webcam away can avoid detection.
- **Flat phone angle:** Phones held horizontally or placed flat may not be detected.
- **Password security:** Currently uses SHA-256 (unsalted). Migrate to **bcrypt** or **Argon2** before production deployment.
- **Single child view:** Parent dashboard shows only the first linked child. Multi-child selector is planned.
- **HTTPS required for webcam:** Browsers block `getUserMedia` on non-HTTPS origins. Use `localhost` in dev; cloud deployments (Vercel/Render) provide HTTPS automatically.

---

## 🔭 Future Scope

- [ ] ML-based attention classifier (replace rule-based scoring with a trained model)
- [ ] Emotion recognition using MediaPipe FaceBlendshapes (52 expression coefficients)
- [ ] Multi-child selector UI in parent dashboard
- [ ] Teacher dashboard with class-wide student grid (colour-coded tiles)
- [ ] Client-side AI inference via WebNN / MediaPipe.js (true edge processing)
- [ ] Mobile push notifications (React Native or Flutter app)
- [ ] LMS integration via LTI (Moodle, Canvas, Google Classroom)
- [ ] Session scheduling tied to class timetable (auto-activate/deactivate monitoring)
- [ ] Salted password hashing (bcrypt / Argon2)
- [ ] Configurable per-student EAR thresholds (e.g., adjusted for glasses wearers)

---

## 🤝 Contributing

Contributions are welcome! To get started:

```bash
# 1. Fork the repository and clone your fork
git clone https://github.com/your-username/attentrack.git

# 2. Create a feature branch
git checkout -b feature/your-feature-name

# 3. Make your changes and commit
git commit -m "Add: description of your change"

# 4. Push and open a Pull Request
git push origin feature/your-feature-name
```

Please test backend changes via the Swagger UI at `/docs` before submitting. Keep frontend CSS changes scoped to the relevant component file.

---

<div align="center">
  <p>Built with FastAPI · React · MediaPipe · YOLOv8 · MongoDB</p>
  <strong>AttenTrack — Because attention matters.</strong>
</div>

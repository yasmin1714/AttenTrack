# AttenTrack — Integrated Setup Guide

## Architecture Overview

```
realtime_monitor.py  ──POST /api/attention──►  FastAPI Backend
                                                     │
                                               WebSocket push
                                                     │
                                          React Dashboards ◄──ws://
```

---

## 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Copy env template
cp .env.example .env
# Edit .env with your MongoDB URI, email credentials, etc.

# Start server
uvicorn main:app --reload --port 8000
```

The backend runs on `http://localhost:8000`.

---

## 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev   # or: npm start
```

React dev server runs on `http://localhost:5173` (Vite) or `http://localhost:3000` (CRA).

Make sure `BASE` / `WS_BASE` in `src/hooks/useAttenTrack.js` point to your backend URL.

---

## 3. Realtime Monitor

```bash
cd backend
python realtime_monitor.py
```

The monitor reads `STUDENT_ID` from `.env` — make sure it matches a student in your DB.

---

## 4. Key Files Changed

| File | Change |
|------|--------|
| `main.py` | Added CORS + WebSocket endpoint |
| `websocket_manager.py` | **NEW** — manages WS connections |
| `routes/attention.py` | Threshold-based alerts, WS push |
| `routes/admin.py` | Aggregation pipeline (efficient) |
| `routes/parent.py` | Fixed route param bug |
| `routes/student.py` | ObjectId serialisation fix |
| `realtime_monitor.py` | Batching, retry, env secrets, violation threshold |
| `frontend/src/hooks/useAttenTrack.js` | **NEW** — unified data hook |
| `frontend/src/StudentDashboard.jsx` | Live WS data |
| `frontend/src/AdminDashboard.jsx` | Live API metrics |
| `frontend/src/ParentDashboard.jsx` | Live WS + report data |

---

## 5. WebSocket Flow

1. Student opens dashboard → connects to `ws://localhost:8000/ws/101`
2. `realtime_monitor.py` POSTs every 2 seconds to `/api/attention`
3. `attention.py` route calls `manager.push(student_id, data)`
4. Dashboard receives update instantly, updates score + chart + alerts

If WebSocket fails (network issue), the hook automatically falls back to REST polling every 2 seconds — zero code change needed.

---

## 6. Environment Variables (.env)

```
MONGO_URI=mongodb://localhost:27017
BACKEND_URL=http://127.0.0.1:8000/api/attention
STUDENT_ID=101
SEND_INTERVAL=2.0           # seconds between monitor→backend posts
ALERT_COOLDOWN=10.0         # seconds between email alerts
VIOLATION_THRESHOLD=3       # consecutive bad frames before alert

SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=app_password
RECEIVER_EMAIL=parent@email.com
```

---

## 7. What's Still TODO (next steps)

- [ ] JWT authentication (protect all routes)
- [ ] Login page wired to real auth endpoint
- [ ] Admin "Add User" form posting to backend
- [ ] Date-range filtering on reports
- [ ] Screenshot viewer in alerts table

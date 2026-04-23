print("✅ frame_processor loaded")

from dotenv import load_dotenv
load_dotenv()

import base64
import time
import numpy as np
import cv2
import os
from fastapi import APIRouter, Request
from pydantic import BaseModel

from database import attention_collection, alerts_collection
from alert_service import AlertService

from face_detection import FaceDetector
from eye_tracking import EyeTracker
from phone_detection import PhoneDetector
from attention_scoring import AttentionScorer

router = APIRouter()

# AI modules
face_detector  = FaceDetector()
eye_tracker    = EyeTracker()
phone_detector = PhoneDetector()
scorer         = AttentionScorer()

_violation_counters = {}
VIOLATION_THRESHOLD = 3

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Single shared alert_service instance (reads creds from .env)
alert_service = AlertService()


class FramePayload(BaseModel):
    student_id: str
    frame: str


def decode_frame(b64):
    header, data = b64.split(",", 1)
    arr = np.frombuffer(base64.b64decode(data), np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def save_screenshot(frame, student_id, timestamp):
    filename = f"{student_id}_{timestamp}.jpg"
    path     = os.path.join(SCREENSHOT_DIR, filename)
    success  = cv2.imwrite(path, frame)
    print("✅ Screenshot saved:" if success else "❌ Screenshot failed:", path)
    return path


@router.post("/api/process-frame")
async def process_frame(payload: FramePayload, request: Request):

    frame      = decode_frame(payload.frame)
    student_id = payload.student_id
    timestamp  = int(time.time() * 1000)

    # ── Detection ────────────────────────────────────────────────
    face_detector.detect_async(frame, timestamp)
    face_detected = bool(
        face_detector.latest_result and
        face_detector.latest_result.detections
    )

    eye_result   = eye_tracker.process(frame, timestamp)
    eyes_closed  = False
    sleeping     = False
    looking_away = False

    if eye_result and face_detected:
        eyes_closed  = bool(eye_result["eyes_closed"])
        sleeping     = bool(eye_result["sleeping"])

    phone_detected = bool(phone_detector.detect_phone(frame)["phone_detected"])

    # ── Scoring ───────────────────────────────────────────────────
    score, status, _ = scorer.calculate(
        face_detected, eyes_closed, sleeping, looking_away, phone_detected
    )

    # ── Save log ──────────────────────────────────────────────────
    doc = {
        "student_id":     str(student_id),
        "attention_score": float(score),
        "status":          str(status),
        "eyes_closed":     bool(eyes_closed),
        "sleeping":        bool(sleeping),
        "looking_away":    bool(looking_away),
        "phone_detected":  bool(phone_detected),
        "timestamp":       int(timestamp),
        "screenshot":      None,
    }
    attention_collection.insert_one(doc)

    # ── WebSocket push ────────────────────────────────────────────
    manager = getattr(request.app.state, "manager", None)
    if manager:
        await manager.push(student_id, {"type": "attention_update", **doc})

    # ── Violation counter + alert ─────────────────────────────────
    sid          = student_id
    is_violation = phone_detected or status == "NOT PAYING ATTENTION"

    if is_violation:
        _violation_counters[sid] = _violation_counters.get(sid, 0) + 1
    else:
        _violation_counters[sid] = 0

    if _violation_counters.get(sid, 0) >= VIOLATION_THRESHOLD:
        print("🚨 ALERT TRIGGERED for", sid)

        screenshot_path = save_screenshot(frame, sid, timestamp)

        alert = {
            "student_id": sid,
            "type":       "Phone Detected" if phone_detected else "Low Attention",
            "score":      float(score),
            "timestamp":  int(timestamp),
            "screenshot": screenshot_path,
            "resolved":   False,
        }
        alerts_collection.insert_one(alert)

        # ✅ Pass student_id so alert_service finds the correct parent email
        alert_service.send_email_alert(
            image_path=screenshot_path,
            subject="🚨 AttenTrack Attention Alert",
            student_id=sid,
        )

        if manager:
            await manager.push(sid, {
                "type":       "alert",
                "alert_type": alert["type"],
                "score":      alert["score"],
                "timestamp":  alert["timestamp"],
            })

        _violation_counters[sid] = 0

    return {
        "type":            "attention_update",
        "student_id":      str(student_id),
        "attention_score": float(score),
        "status":          str(status),
        "eyes_closed":     bool(eyes_closed),
        "sleeping":        bool(sleeping),
        "looking_away":    bool(looking_away),
        "phone_detected":  bool(phone_detected),
        "timestamp":       int(timestamp),
    }

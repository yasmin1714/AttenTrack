"""
AttenTrack — Production Realtime Monitor
-----------------------------------------
Improvements over original:
  ✅ Secrets via .env (no hardcoded credentials)
  ✅ Batching: sends data every SEND_INTERVAL seconds (not every frame)
  ✅ Retry logic with exponential back-off
  ✅ Violation counter — no alert spam
  ✅ Backend URL from env
  ✅ Graceful camera error handling
"""

import cv2
import time
import threading
import numpy as np
import requests
import os
from dotenv import load_dotenv

from face_detection import FaceDetector
from eye_tracking import EyeTracker
from phone_detection import PhoneDetector
from attention_scoring import AttentionScorer
from screenshot_capture import ScreenshotCapture
from alert_service import AlertService

load_dotenv()

# ──────────────────────────────────────────
# CONFIG  (all from .env)
# ──────────────────────────────────────────
BACKEND_URL  = os.getenv("BACKEND_URL",    "http://127.0.0.1:8000/api/attention")
STUDENT_ID   = os.getenv("STUDENT_ID",     "101")
SEND_INTERVAL = float(os.getenv("SEND_INTERVAL", "2.0"))   # seconds between API posts
ALERT_COOLDOWN = float(os.getenv("ALERT_COOLDOWN", "10.0"))
VIOLATION_THRESHOLD = int(os.getenv("VIOLATION_THRESHOLD", "3"))

SENDER_EMAIL    = os.getenv("SENDER_EMAIL",    "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
RECEIVER_EMAIL  = os.getenv("RECEIVER_EMAIL",  "")


# ──────────────────────────────────────────
# MODULES
# ──────────────────────────────────────────
face_detector   = FaceDetector()
eye_tracker     = EyeTracker()
phone_detector  = PhoneDetector()
scorer          = AttentionScorer()
screenshot_tool = ScreenshotCapture()
alert_service   = AlertService(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL)


# ──────────────────────────────────────────
# RETRY POST
# ──────────────────────────────────────────
def post_with_retry(payload: dict, retries: int = 3, delay: float = 0.5):
    for attempt in range(retries):
        try:
            requests.post(BACKEND_URL, json=payload, timeout=2)
            return
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))   # exponential back-off
            else:
                print(f"[WARN] Failed to send after {retries} attempts: {e}")


def send_async(payload: dict):
    threading.Thread(target=post_with_retry, args=(payload,), daemon=True).start()


# ──────────────────────────────────────────
# CAMERA MATRIX
# ──────────────────────────────────────────
def get_camera_matrices(img_w: int, img_h: int):
    f = img_w
    cam = np.array([[f, 0, img_w/2], [0, f, img_h/2], [0, 0, 1]], dtype=np.float64)
    dist = np.zeros((4, 1), dtype=np.float64)
    return cam, dist


# ──────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────
def run_monitor():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Webcam not accessible")
        return

    last_send_time  = 0.0
    last_alert_time = 0.0
    violation_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Empty frame — retrying...")
            time.sleep(0.1)
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        timestamp = int(time.time() * 1000)
        cam_matrix, dist_matrix = get_camera_matrices(w, h)

        # ── 1. Face detection ─────────────────────────────────────────
        face_detector.detect_async(frame, timestamp)
        face_detected = bool(
            face_detector.latest_result and
            face_detector.latest_result.detections
        )

        # ── 2. Eye tracking + head pose ───────────────────────────────
        eye_result   = eye_tracker.process(frame, timestamp)
        eyes_closed  = False
        sleeping     = False
        looking_away = False
        pose_text    = "Forward"

        if eye_result and face_detected:
            eyes_closed = eye_result["eyes_closed"]
            sleeping    = eye_result["sleeping"]

            landmarks = eye_tracker.latest_result.face_landmarks[0]
            face_2d, face_3d = [], []
            for idx in [1, 33, 263, 61, 291, 199]:
                lm = landmarks[idx]
                face_2d.append([int(lm.x * w), int(lm.y * h)])
                face_3d.append([int(lm.x * w), int(lm.y * h), lm.z])

            face_2d = np.array(face_2d, dtype=np.float64)
            face_3d = np.array(face_3d, dtype=np.float64)

            ok, rot_vec, _ = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
            if ok:
                rmat, _ = cv2.Rodrigues(rot_vec)
                angles, *_ = cv2.RQDecomp3x3(rmat)
                rx, ry = angles[0] * 360, angles[1] * 360
                if rx < -10:
                    pose_text, looking_away = "Looking Down", True
                elif abs(ry) > 15:
                    pose_text, looking_away = "Looking Sideways", True

            for pt in eye_result["left_coords"] + eye_result["right_coords"]:
                cv2.circle(frame, pt, 2, (0, 255, 255), -1)

        # ── 3. Phone detection ────────────────────────────────────────
        phone_detected = phone_detector.detect_phone(frame)["phone_detected"]

        # ── 4. Attention score ────────────────────────────────────────
        score, status, color = scorer.calculate(
            face_detected, eyes_closed, sleeping, looking_away, phone_detected
        )

        # ── 5. Batched send (every SEND_INTERVAL seconds) ─────────────
        now = time.time()
        if now - last_send_time >= SEND_INTERVAL:
            send_async({
                "student_id":    STUDENT_ID,
                "attention_score": float(score),
                "status":        status,
                "eyes_closed":   bool(eyes_closed),
                "sleeping":      bool(sleeping),
                "looking_away":  bool(looking_away),
                "phone_detected": bool(phone_detected),
                "timestamp":     timestamp,
                "screenshot":    None,
            })
            last_send_time = now

        # ── 6. Threshold alert (no spam) ──────────────────────────────
        is_violation = phone_detected or status == "NOT PAYING ATTENTION"
        if is_violation:
            violation_count += 1
        else:
            violation_count = 0

        if violation_count >= VIOLATION_THRESHOLD and (now - last_alert_time > ALERT_COOLDOWN):
            path = screenshot_tool.capture(frame)
            print("📸 Violation captured:", path)
            alert_service.send_email_alert(path)

            send_async({
                "student_id":    STUDENT_ID,
                "attention_score": float(score),
                "status":        status,
                "eyes_closed":   bool(eyes_closed),
                "sleeping":      bool(sleeping),
                "looking_away":  bool(looking_away),
                "phone_detected": bool(phone_detected),
                "timestamp":     timestamp,
                "screenshot":    path,
            })
            last_alert_time = now
            violation_count = 0   # reset after alert sent

        # ── 7. Display ────────────────────────────────────────────────
        cv2.putText(frame, f"Score: {score} | {status}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"Pose: {pose_text}",
                    (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if phone_detected:
            cv2.putText(frame, "PHONE DETECTED!",
                        (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("AttenTrack Monitor", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_monitor()

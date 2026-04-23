import cv2
import time
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class EyeTracker:
    def __init__(self,
                 model_path="face_landmarker.task",
                 ear_threshold=0.21,
                 consecutive_frames=15):

        self.ear_threshold = ear_threshold
        self.consecutive_frames = consecutive_frames
        self.frame_counter = 0
        self.sleeping = False
        self.latest_result = None

        base_options = python.BaseOptions(model_asset_path=model_path)

        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            num_faces=1,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            result_callback=self._process_result
        )

        self.detector = vision.FaceLandmarker.create_from_options(options)

        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    def _process_result(self, result, output_image, timestamp_ms):
        self.latest_result = result

    def _calculate_ear(self, eye_points, landmarks, w, h):
        coords = []

        for idx in eye_points:
            x = int(landmarks[idx].x * w)
            y = int(landmarks[idx].y * h)
            coords.append((x, y))

        vertical1 = np.linalg.norm(np.array(coords[1]) - np.array(coords[5]))
        vertical2 = np.linalg.norm(np.array(coords[2]) - np.array(coords[4]))
        horizontal = np.linalg.norm(np.array(coords[0]) - np.array(coords[3]))

        ear = (vertical1 + vertical2) / (2.0 * horizontal)
        return ear, coords

    def process(self, frame, timestamp):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self.detector.detect_async(mp_image, timestamp)

        if not self.latest_result or not self.latest_result.face_landmarks:
            return None

        landmarks = self.latest_result.face_landmarks[0]
        h, w, _ = frame.shape

        left_ear, left_coords = self._calculate_ear(self.LEFT_EYE, landmarks, w, h)
        right_ear, right_coords = self._calculate_ear(self.RIGHT_EYE, landmarks, w, h)

        avg_ear = (left_ear + right_ear) / 2.0
        eyes_closed = avg_ear < self.ear_threshold

        if eyes_closed:
            self.frame_counter += 1
        else:
            self.frame_counter = 0
            self.sleeping = False

        if self.frame_counter >= self.consecutive_frames:
            self.sleeping = True

        return {
            "avg_ear": round(avg_ear, 3),
            "eyes_closed": eyes_closed,
            "sleeping": self.sleeping,
            "left_coords": left_coords,
            "right_coords": right_coords
        }


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    tracker = EyeTracker()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = int(time.time() * 1000)
        result = tracker.process(frame, timestamp)

        if result:
            for pt in result["left_coords"] + result["right_coords"]:
                cv2.circle(frame, pt, 2, (0, 255, 255), -1)

            status = "Eyes Closed" if result["eyes_closed"] else "Eyes Open"

            if result["sleeping"]:
                status = "SLEEPING DETECTED"

            cv2.putText(frame, status, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255) if result["eyes_closed"] else (0, 255, 0), 2)

            cv2.putText(frame,
                        f"EAR: {result['avg_ear']}",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 0), 2)

        else:
            cv2.putText(frame, "No Face Detected",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255), 2)

        cv2.imshow("AttenTrack - Eye Tracking", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
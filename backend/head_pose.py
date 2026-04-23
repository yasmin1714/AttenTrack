import cv2
import mediapipe as mp
import numpy as np
import time
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ----------------------------
# Setup MediaPipe FaceLandmarker (Tasks API)
# ----------------------------

base_options = python.BaseOptions(model_asset_path="face_landmarker.task")

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1
)

detector = vision.FaceLandmarker.create_from_options(options)

# ----------------------------
# Open webcam
# ----------------------------

cap = cv2.VideoCapture(0)

while True:

    success, frame = cap.read()
    if not success:
        break

    # flip for selfie view
    frame = cv2.flip(frame, 1)

    img_h, img_w, _ = frame.shape

    # Convert to RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    timestamp = int(time.time() * 1000)

    result = detector.detect_for_video(mp_image, timestamp)

    face_3d = []
    face_2d = []

    if result.face_landmarks:

        landmarks = result.face_landmarks[0]

        for idx, lm in enumerate(landmarks):

            if idx in [1, 33, 263, 61, 291, 199]:

                x, y = int(lm.x * img_w), int(lm.y * img_h)

                face_2d.append([x, y])
                face_3d.append([x, y, lm.z])

                if idx == 1:
                    nose_2d = (x, y)
                    nose_3d = (x, y, lm.z * 3000)

        face_2d = np.array(face_2d, dtype=np.float64)
        face_3d = np.array(face_3d, dtype=np.float64)

        # ----------------------------
        # Camera matrix
        # ----------------------------

        focal_length = img_w
        cam_matrix = np.array([
            [focal_length, 0, img_w / 2],
            [0, focal_length, img_h / 2],
            [0, 0, 1]
        ])

        dist_matrix = np.zeros((4, 1))

        # ----------------------------
        # SolvePnP
        # ----------------------------

        success, rot_vec, trans_vec = cv2.solvePnP(
            face_3d,
            face_2d,
            cam_matrix,
            dist_matrix
        )

        rmat, _ = cv2.Rodrigues(rot_vec)

        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

        x = angles[0] * 360
        y = angles[1] * 360
        z = angles[2] * 360

        # ----------------------------
        # Direction Logic
        # ----------------------------

        if y < -10:
            text = "Looking Left"

        elif y > 10:
            text = "Looking Right"

        elif x < -10:
            text = "Looking Down"

        elif x > 10:
            text = "Looking Up"

        else:
            text = "Forward"

        # ----------------------------
        # Draw direction line
        # ----------------------------

        p1 = (int(nose_2d[0]), int(nose_2d[1]))
        p2 = (
            int(nose_2d[0] + y * 10),
            int(nose_2d[1] - x * 10)
        )

        cv2.line(frame, p1, p2, (255, 0, 0), 3)

        cv2.putText(
            frame,
            text,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    else:
        cv2.putText(
            frame,
            "No Face",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    cv2.imshow("Head Pose Estimation", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
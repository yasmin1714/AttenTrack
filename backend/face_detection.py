import cv2
import time
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class FaceDetector:
    def __init__(self, model_path="blaze_face_short_range.tflite"):

        self.latest_result = None

        base_options = python.BaseOptions(model_asset_path=model_path)

        options = vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            min_detection_confidence=0.6,
            result_callback=self._process_result
        )

        self.detector = vision.FaceDetector.create_from_options(options)

    def _process_result(self, result, output_image, timestamp_ms):
        self.latest_result = result

    def detect_async(self, frame, timestamp):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        self.detector.detect_async(mp_image, timestamp)

    def draw(self, frame):
        if self.latest_result and self.latest_result.detections:
            for detection in self.latest_result.detections:
                bbox = detection.bounding_box
                x, y, w, h = bbox.origin_x, bbox.origin_y, bbox.width, bbox.height

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                score = round(detection.categories[0].score, 2)
                cv2.putText(frame, f"{int(score*100)}%",
                            (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0,255,0), 2)

        return frame


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    detector = FaceDetector()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = int(time.time() * 1000)
        detector.detect_async(frame, timestamp)

        frame = detector.draw(frame)

        cv2.imshow("AttenTrack - Face Detection", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
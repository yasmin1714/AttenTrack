import cv2
from ultralytics import YOLO


class PhoneDetector:

    def __init__(self, model_path="yolov8n.pt", confidence_threshold=0.4):
        """
        model_path: YOLOv8 model file
        confidence_threshold: Minimum detection confidence
        """
        self.model = YOLO(model_path)
        self.conf_threshold = confidence_threshold

        # COCO class ID for cell phone = 67
        self.PHONE_CLASS_ID = 67

    def detect_phone(self, frame):
        """
        Detect phone in frame.

        Returns:
        {
            "phone_detected": bool,
            "confidence": float,
            "bbox": (x1, y1, x2, y2)
        }
        """

        results = self.model(frame, verbose=False)

        phone_detected = False
        best_conf = 0
        best_bbox = None

        for result in results:
            boxes = result.boxes

            for box in boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])

                if cls_id == self.PHONE_CLASS_ID and confidence > self.conf_threshold:

                    phone_detected = True

                    if confidence > best_conf:
                        best_conf = confidence
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        best_bbox = (x1, y1, x2, y2)

        return {
            "phone_detected": phone_detected,
            "confidence": round(best_conf, 2),
            "bbox": best_bbox
        }

    def draw_detection(self, frame, detection_result):
        """
        Draw bounding box if phone detected
        """

        if detection_result["phone_detected"]:
            x1, y1, x2, y2 = detection_result["bbox"]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            cv2.putText(
                frame,
                f"Phone Detected {detection_result['confidence']}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        return frame


# ----------------------------------------
# Test Script
# ----------------------------------------

if __name__ == "__main__":

    cap = cv2.VideoCapture(0)

    detector = PhoneDetector()

    while True:
        success, frame = cap.read()
        if not success:
            break

        result = detector.detect_phone(frame)

        if result["phone_detected"]:
            print("Phone Detected!", result["confidence"])

        frame = detector.draw_detection(frame, result)

        cv2.imshow("AttenTrack - Phone Detection", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
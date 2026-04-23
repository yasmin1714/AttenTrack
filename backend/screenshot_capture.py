import cv2
import os
from datetime import datetime
class ScreenshotCapture:
    def __init__(self, save_dir="screenshots"):
        """
        save_dir: folder where screenshots will be stored
        """
        self.save_dir = save_dir
        # Create folder if not exists
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    def capture(self, frame, prefix="alert"):
        """
        Save screenshot with timestamp
        Returns:
            file_path (str)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.jpg"
        file_path = os.path.join(self.save_dir, filename)
        cv2.imwrite(file_path, frame)

        return file_path
    def capture_with_overlay(self, frame, text="ALERT"):
        """
        Capture screenshot with alert text overlay
        """
        frame_copy = frame.copy()
        cv2.putText(frame_copy,
                    text,
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 0, 255),
                    3)
        return self.capture(frame_copy)
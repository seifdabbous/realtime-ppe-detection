from ultralytics import YOLO

from app.config.settings import MODEL_PATH


class PPEDetector:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)

    def detect(self, frame):
        results = self.model(
            frame,
            verbose=False
        )

        return results[0]
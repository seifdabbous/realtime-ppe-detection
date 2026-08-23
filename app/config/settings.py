import os
from dotenv import load_dotenv


load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.environ[
    "KAFKA_BOOTSTRAP_SERVERS"
]

VIDEO_FRAMES_TOPIC = os.getenv(
    "VIDEO_FRAMES_TOPIC",
    "video-frames"
)

DETECTION_EVENTS_TOPIC = os.getenv(
    "DETECTION_EVENTS_TOPIC",
    "detection-events"
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    "runs/detect/runs/ppe_yolo11n-2/weights/best.pt"
)

VIDEO_SOURCE = os.getenv(
    "VIDEO_SOURCE",
    "videos/13753913_3840_2160_50fps.mp4"
)

FRAME_WIDTH = int(
    os.getenv("FRAME_WIDTH", "640")
)

FRAME_HEIGHT = int(
    os.getenv("FRAME_HEIGHT", "360")
)

JPEG_QUALITY = int(
    os.getenv("JPEG_QUALITY", "80")
)

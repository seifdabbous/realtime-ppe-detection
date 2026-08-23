import time

import cv2
from kafka import KafkaProducer

from app.config.settings import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    JPEG_QUALITY,
    KAFKA_BOOTSTRAP_SERVERS,
    VIDEO_FRAMES_TOPIC,
    VIDEO_SOURCE,
)


producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
)


video = cv2.VideoCapture(VIDEO_SOURCE)


if not video.isOpened():
    raise RuntimeError(
        f"Could not open video source: {VIDEO_SOURCE}"
    )


while True:
    success, frame = video.read()

    if not success:
        break

    frame = cv2.resize(
        frame,
        (FRAME_WIDTH, FRAME_HEIGHT)
    )

    success_encode, buffer = cv2.imencode(
        ".jpg",
        frame,
        [
            cv2.IMWRITE_JPEG_QUALITY,
            JPEG_QUALITY
        ]
    )

    if not success_encode:
        continue

    producer.send(
        VIDEO_FRAMES_TOPIC,
        buffer.tobytes()
    )

    time.sleep(0.02)


producer.flush()
producer.close()
video.release()

print("Video streaming finished")
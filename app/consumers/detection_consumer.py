import json
from datetime import datetime, timezone

import cv2
import numpy as np
from kafka import KafkaConsumer, KafkaProducer

from app.config.settings import (
    DETECTION_EVENTS_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
    VIDEO_FRAMES_TOPIC,
)

from app.services.detector import PPEDetector
from app.services.safety_rules import build_safety_events


detector = PPEDetector()


consumer = KafkaConsumer(
    VIDEO_FRAMES_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    auto_offset_reset="latest",
    group_id="ppe-detection-group"
)


event_producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda value: json.dumps(value).encode("utf-8")
)


print("Detection consumer started...")


frame_id = 0


for message in consumer:
    image_bytes = message.value

    numpy_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    frame = cv2.imdecode(
        numpy_array,
        cv2.IMREAD_COLOR
    )

    if frame is None:
        continue

    result = detector.detect(frame)

    detections = []

    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        class_name = result.names[class_id]

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        detections.append(
            {
                "class_id": class_id,
                "class_name": class_name,
                "confidence": round(confidence, 4),
                "bbox": {
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2),
                },
            }
        )

    safety_events = build_safety_events(detections)

    frame_id += 1

    event = {
        "camera_id": "CAM_01",
        "frame_id": frame_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detections_count": len(detections),
        "detections": detections,
        "safety_events_count": len(safety_events),
        "safety_events": safety_events,
    }

    event_producer.send(
        DETECTION_EVENTS_TOPIC,
        value=event
    )

    print(event)
import cv2
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers="localhost:9092"
)

video = cv2.VideoCapture(
    "videos/13753913_3840_2160_50fps.mp4"
)

success, frame = video.read()

if success:
    frame = cv2.resize(
        frame,
        (640, 360)
    )

    success_encode, buffer = cv2.imencode(".jpg", frame)

    if success_encode:
        producer.send(
            "video-frames",
            buffer.tobytes()
        )

        producer.flush()

        print("one frame sent to Kafka")

video.release()
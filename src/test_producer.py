from kafka import KafkaProducer


producer = KafkaProducer(
    bootstrap_servers="localhost:9092"
)



producer.send(
    "video-frames",
    b"hello from producer"
)

producer.flush()

print("message sent")
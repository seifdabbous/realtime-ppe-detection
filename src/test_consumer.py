from kafka import KafkaConsumer


consumer = KafkaConsumer(
    "video-frames",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    group_id="test-group"
)


print("waiting for messages...")


for message in consumer:
    print(message.value.decode("utf-8"))
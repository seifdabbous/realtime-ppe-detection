import json

from kafka import KafkaConsumer

from app.config.database import detections_collection
from app.config.settings import (
    DETECTION_EVENTS_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
)


consumer = KafkaConsumer(
    DETECTION_EVENTS_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    auto_offset_reset="latest",
    group_id="ppe-persistence-group",
    value_deserializer=lambda value: json.loads(
        value.decode("utf-8")
    ),
)


print("Persistence consumer started...")


for message in consumer:
    event = message.value

    result = detections_collection.insert_one(event)

    print(
        f"Event saved to MongoDB with id: {result.inserted_id}"
    )
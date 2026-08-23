import cv2
import numpy as np
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    "video-frames",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="latest",
    group_id="frame-consumer-group"
    
)


print("waitting for frame...")


for message in consumer:
    image_bytes = message.value

    numpy_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )
    
    
    frame = cv2.imencode(
        numpy_array,
        cv2.IMREAD_COLOR
    )
    
    
    cv2.imwrite(
        "received_frame.jpg",
        frame
    )
    
    print("frame received and saved")
    
    break


def build_safety_events(detections):
    events = []

    for detection in detections:
        class_name = detection["class_name"]
        confidence = detection["confidence"]

        if class_name == "no-helmet":
            events.append(
                {
                    "event_type": "PPE_VIOLATION",
                    "violation": "NO_HELMET",
                    "severity": "high",
                    "confidence": confidence,
                    "bbox": detection["bbox"],
                }
            )

        elif class_name == "no-vest":
            events.append(
                {
                    "event_type": "PPE_VIOLATION",
                    "violation": "NO_VEST",
                    "severity": "medium",
                    "confidence": confidence,
                    "bbox": detection["bbox"],
                }
            )

    return events
import os
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import cv2

from app.services.detector import PPEDetector
from app.services.safety_rules import build_safety_events


PREDICTION_DIR = Path(
    os.getenv("PREDICTION_DIR", "runtime/predictions")
).resolve()
PREDICTION_DIR.mkdir(parents=True, exist_ok=True)

RESULT_TTL_SECONDS = int(os.getenv("PREDICTION_TTL_SECONDS", "86400"))
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
VIDEO_ANALYSIS_FPS = float(os.getenv("VIDEO_ANALYSIS_FPS", "10"))
MAX_VIDEO_WIDTH = int(os.getenv("MAX_VIDEO_WIDTH", "1280"))
MAX_VIDEO_HEIGHT = int(os.getenv("MAX_VIDEO_HEIGHT", "720"))

_detector = None
_detector_lock = threading.Lock()
_jobs_lock = threading.Lock()
_jobs = {}
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ppe-upload")


def _get_detector():
    global _detector
    if _detector is None:
        _detector = PPEDetector()
    return _detector


def cleanup_expired_results():
    cutoff = time.time() - RESULT_TTL_SECONDS
    for path in PREDICTION_DIR.iterdir():
        if path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)


def extract_detections(result):
    detections = []
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        detections.append(
            {
                "class_id": class_id,
                "class_name": result.names[class_id],
                "confidence": round(confidence, 4),
                "bbox": {
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2),
                },
            }
        )
    return detections


def _detect(frame):
    # Ultralytics model inference is serialized because a shared model instance
    # is not guaranteed to be thread-safe across concurrent requests.
    with _detector_lock:
        result = _get_detector().detect(frame)
        annotated = result.plot()
    detections = extract_detections(result)
    return annotated, detections, build_safety_events(detections)


def process_image(source_path: Path, result_id: str):
    frame = cv2.imread(str(source_path))
    if frame is None:
        raise ValueError("The uploaded image could not be decoded.")

    annotated, detections, safety_events = _detect(frame)
    output_path = PREDICTION_DIR / f"{result_id}.jpg"
    if not cv2.imwrite(str(output_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 90]):
        raise RuntimeError("The annotated image could not be created.")

    return {
        "result_id": result_id,
        "kind": "image",
        "media_type": "image/jpeg",
        "result_url": f"/predictions/{result_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "frames_processed": 1,
        "detections_count": len(detections),
        "safety_events_count": len(safety_events),
        "detections": detections,
        "safety_events": safety_events,
    }


def process_video(source_path: Path, result_id: str, progress_callback=None):
    capture = cv2.VideoCapture(str(source_path))
    if not capture.isOpened():
        raise ValueError("The uploaded video could not be decoded.")

    fps = capture.get(cv2.CAP_PROP_FPS)
    source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if not fps or fps <= 0:
        fps = 25.0
    if source_width <= 0 or source_height <= 0:
        capture.release()
        raise ValueError("The uploaded video has invalid dimensions.")

    sample_step = max(1, round(fps / VIDEO_ANALYSIS_FPS))
    output_fps = fps / sample_step
    expected_frames = max(1, source_frame_count // sample_step)
    scale = min(1.0, MAX_VIDEO_WIDTH / source_width, MAX_VIDEO_HEIGHT / source_height)
    width = max(2, int(source_width * scale) // 2 * 2)
    height = max(2, int(source_height * scale) // 2 * 2)

    output_path = PREDICTION_DIR / f"{result_id}.webm"
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"VP80"),
        output_fps,
        (width, height),
    )
    if not writer.isOpened():
        capture.release()
        raise RuntimeError("The annotated video could not be created.")

    frames_processed = 0
    detections_count = 0
    safety_events_count = 0
    class_counts = Counter()
    violation_counts = Counter()
    source_frame_index = 0
    thumbnail_written = False

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break
            source_frame_index += 1
            if (source_frame_index - 1) % sample_step:
                continue
            if scale < 1.0:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
            annotated, detections, safety_events = _detect(frame)
            writer.write(annotated)
            if not thumbnail_written:
                thumbnail_path = PREDICTION_DIR / f"{result_id}.thumb.jpg"
                thumbnail_written = cv2.imwrite(
                    str(thumbnail_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 88]
                )
            frames_processed += 1
            detections_count += len(detections)
            safety_events_count += len(safety_events)
            class_counts.update(item["class_name"] for item in detections)
            violation_counts.update(item["violation"] for item in safety_events)
            if progress_callback and (frames_processed == 1 or frames_processed % 5 == 0):
                progress_callback(frames_processed, expected_frames)
    finally:
        capture.release()
        writer.release()

    if frames_processed == 0:
        output_path.unlink(missing_ok=True)
        raise ValueError("The uploaded video contains no readable frames.")

    return {
        "result_id": result_id,
        "kind": "video",
        "media_type": "video/webm",
        "result_url": f"/predictions/{result_id}",
        "thumbnail_url": f"/predictions/{result_id}?thumbnail=true",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "frames_processed": frames_processed,
        "detections_count": detections_count,
        "safety_events_count": safety_events_count,
        "class_counts": dict(class_counts),
        "violation_counts": dict(violation_counts),
        "source_fps": round(fps, 2),
        "analysis_fps": round(output_fps, 2),
    }


def get_prediction_file(result_id: str, thumbnail: bool = False):
    if len(result_id) != 32 or any(char not in "0123456789abcdef" for char in result_id):
        return None
    suffixes = (".thumb.jpg",) if thumbnail else (".jpg", ".webm")
    for suffix in suffixes:
        candidate = PREDICTION_DIR / f"{result_id}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def _public_job(job):
    public = {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job.get("progress", 0),
    }
    if job.get("error"):
        public["error"] = job["error"]
    if job.get("result"):
        public.update(job["result"])
    return public


def register_completed_job(result, owner_id: str):
    with _jobs_lock:
        _jobs[result["result_id"]] = {
            "job_id": result["result_id"],
            "owner_id": owner_id,
            "status": "completed",
            "progress": 100,
            "result": result,
        }


def submit_video_job(source_path: Path, result_id: str, owner_id: str):
    job = {
        "job_id": result_id,
        "owner_id": owner_id,
        "status": "queued",
        "progress": 0,
        "result": None,
        "error": None,
    }
    with _jobs_lock:
        _jobs[result_id] = job

    def update_progress(processed, total):
        with _jobs_lock:
            job["progress"] = min(99, round(processed / max(total, 1) * 100))

    def run():
        with _jobs_lock:
            job["status"] = "processing"
            job["progress"] = 1
        try:
            result = process_video(source_path, result_id, update_progress)
            with _jobs_lock:
                job["result"] = result
                job["status"] = "completed"
                job["progress"] = 100
        except Exception as error:
            with _jobs_lock:
                job["status"] = "failed"
                job["error"] = str(error)
        finally:
            source_path.unlink(missing_ok=True)

    _executor.submit(run)
    return _public_job(job)


def get_prediction_job(job_id: str, owner_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None or job["owner_id"] != owner_id:
            return None
        return _public_job(job)

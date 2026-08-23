from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status, Depends
from app.schemas.auth import UserRegister,UserLogin
from app.config.database import detections_collection,users_collection
import asyncio
import json
from app.security import hash_password,verify_password,create_access_token
from fastapi import WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer
from app.dependencies import get_current_user
from bson import ObjectId
import jwt
from app.config.database import users_collection
from app.security import SECRET_KEY, ALGORITHM
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from app.config.settings import (
    DETECTION_EVENTS_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
)
from fastapi import status
from app.services.upload_inference import (
    IMAGE_EXTENSIONS,
    PREDICTION_DIR,
    VIDEO_EXTENSIONS,
    cleanup_expired_results,
    get_prediction_job,
    get_prediction_file,
    process_image,
    register_completed_job,
    submit_video_job,
)



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connected_clients = set()
MAX_UPLOAD_BYTES = 100 * 1024 * 1024

async def broadcast_event(event: dict):
    disconnected_clients = []

    for websocket in connected_clients:
        try:
            await websocket.send_json(event)
        except Exception:
            disconnected_clients.append(websocket)

    for websocket in disconnected_clients:
        connected_clients.discard(websocket)
        
        
async def consume_detection_events():
    consumer = KafkaConsumer(
        DETECTION_EVENTS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="latest",
        group_id="ppe-fastapi-live-group",
        value_deserializer=lambda value: json.loads(
            value.decode("utf-8")
        ),
    )

    while True:
        records = await asyncio.to_thread(
            consumer.poll,
            timeout_ms=1000
        )

        for messages in records.values():
            for message in messages:
                await broadcast_event(message.value)
        
        
        
@app.on_event("startup")
async def start_kafka_consumer():
    asyncio.create_task(
        consume_detection_events()
    )
        
@app.get("/events/latest")
def get_latest_event(current_user=Depends(get_current_user)):
    event = detections_collection.find_one(
        sort=[("_id", -1)]
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="No detection events found"
        )

    event["_id"] = str(event["_id"])

    return event


@app.get("/events")
def get_events(limit: int = Query(default=20,ge=1,le=100),current_user=Depends(get_current_user)):
    events = list(
        detections_collection
        .find()
        .sort("_id", -1)
        .limit(limit)
    )

    for event in events:
        event["_id"] = str(event["_id"])

    return events


@app.get("/violations")
def get_violations(
    limit: int = Query(default=20,ge=1,le=100),current_user=Depends(get_current_user)):
    events = detections_collection.find(
        {
            "safety_events_count": {
                "$gt": 0
            }
        }
    ).sort(
        "_id",
        -1
    ).limit(limit)

    violations = []

    for event in events:
        for safety_event in event.get(
            "safety_events",
            []
        ):
            violations.append(
                {
                    "event_id": str(event["_id"]),
                    "camera_id": event.get("camera_id"),
                    "frame_id": event.get("frame_id"),
                    "timestamp": event.get("timestamp"),
                    "event_type": safety_event.get(
                        "event_type"
                    ),
                    "violation": safety_event.get(
                        "violation"
                    ),
                    "severity": safety_event.get(
                        "severity"
                    ),
                    "confidence": safety_event.get(
                        "confidence"
                    ),
                    "bbox": safety_event.get(
                        "bbox"
                    ),
                }
            )

    return violations



@app.get("/stats")
def get_stats(urrent_user=Depends(get_current_user)):
    total_events = detections_collection.count_documents({})

    total_violations = detections_collection.count_documents(
        {
            "safety_events_count": {
                "$gt": 0
            }
        }
    )

    no_helmet = detections_collection.count_documents(
        {
            "safety_events.violation": "NO_HELMET"
        }
    )

    no_vest = detections_collection.count_documents(
        {
            "safety_events.violation": "NO_VEST"
        }
    )

    return {
        "total_events": total_events,
        "total_violations": total_violations,
        "no_helmet": no_helmet,
        "no_vest": no_vest,
    }


@app.post("/predict/upload")
async def predict_upload(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Supported files: JPG, PNG, WEBP, MP4, AVI, MOV, MKV, and WEBM.",
        )

    cleanup_expired_results()
    result_id = uuid.uuid4().hex
    source_path = PREDICTION_DIR / f"{result_id}.source{suffix}"
    size = 0

    keep_source = False
    try:
        with source_path.open("wb") as destination:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="The maximum upload size is 100 MB.",
                    )
                destination.write(chunk)

        owner_id = str(current_user["_id"])
        if suffix in VIDEO_EXTENSIONS:
            keep_source = True
            return submit_video_job(source_path, result_id, owner_id)

        try:
            result = await asyncio.to_thread(process_image, source_path, result_id)
            register_completed_job(result, owner_id)
            return {**result, "status": "completed", "progress": 100}
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        await file.close()
        if not keep_source:
            source_path.unlink(missing_ok=True)


@app.get("/predict/jobs/{job_id}")
def prediction_job_status(
    job_id: str,
    current_user=Depends(get_current_user),
):
    job = get_prediction_job(job_id, str(current_user["_id"]))
    if job is None:
        raise HTTPException(status_code=404, detail="Prediction job not found or expired.")
    return job


@app.get("/predictions/{result_id}")
def download_prediction(
    result_id: str,
    thumbnail: bool = Query(default=False),
    current_user=Depends(get_current_user),
):
    job = get_prediction_job(result_id, str(current_user["_id"]))
    if job is None or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Prediction result not found or expired.")
    result_path = get_prediction_file(result_id, thumbnail=thumbnail)
    if result_path is None:
        raise HTTPException(status_code=404, detail="Prediction result not found or expired.")
    media_type = "image/jpeg" if result_path.name.endswith(".jpg") else "video/webm"
    return FileResponse(result_path, media_type=media_type, filename=result_path.name)
    
    
    
    
@app.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    token: str
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            await websocket.close(code=1008)
            return

        user = users_collection.find_one(
            {
                "_id": ObjectId(user_id)
            }
        )

        if user is None:
            await websocket.close(code=1008)
            return

    except (jwt.InvalidTokenError, Exception):
        await websocket.close(code=1008)
        return

    await websocket.accept()

    connected_clients.add(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        
@app.post("/register",status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
    existing_user = users_collection.find_one(
        {
            "$or": [
                {"email": user.email},
                {"username": user.username},
            ]
        }
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    new_user = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hash_password(
            user.password
        ),
    }

    result = users_collection.insert_one(
        new_user
    )

    return {
        "id": str(result.inserted_id),
        "username": user.username,
        "email": user.email,
    }
    
    
    
    
@app.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one(
        {
            "email": user.email
        }
    )

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(
        user.password,
        db_user["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": str(db_user["_id"])
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

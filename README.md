# Real-Time PPE Detection

An end-to-end safety monitoring system that detects personal protective equipment (PPE) violations from video frames and uploaded media. The project combines YOLO inference, Kafka event streaming, MongoDB persistence, a FastAPI API, WebSocket updates, and a React dashboard.

## What it does

- Detects PPE classes with a custom Ultralytics YOLO model.
- Converts `no-helmet` and `no-vest` detections into structured safety violations.
- Streams video frames and detection events through Kafka.
- Stores detection events in MongoDB.
- Broadcasts live events to authenticated WebSocket clients.
- Provides JWT-based registration and login.
- Supports authenticated image and video uploads for on-demand inference.
- Displays statistics, recent events, violations, and annotated upload results in a React dashboard.

## Architecture

```mermaid
flowchart LR
    VS[Video source] --> VP[Video producer]
    VP -->|video-frames| K[Kafka]
    K --> DC[Detection consumer]
    DC --> Y[YOLO model]
    DC -->|detection-events| K
    K --> PC[Persistence consumer]
    PC --> M[(MongoDB)]
    K --> API[FastAPI]
    M --> API
    API -->|REST + WebSocket| UI[React dashboard]
    UP[Uploaded image/video] --> API
    API --> Y
    API --> PR[Annotated result]
```

The live pipeline uses two Kafka topics:

| Topic | Producer | Consumer | Payload |
| --- | --- | --- | --- |
| `video-frames` | Video producer | Detection consumer | JPEG-encoded frames |
| `detection-events` | Detection consumer | FastAPI and persistence consumer | JSON detections and safety events |

## Technology stack

- Python 3.14, FastAPI, Uvicorn
- Ultralytics YOLO, PyTorch, OpenCV
- Apache Kafka
- MongoDB
- React 19 and Vite
- JWT authentication with Argon2 password hashing
- Docker and Docker Compose

## Repository structure

```text
.
├── app/
│   ├── api/
│   │   └── main.py                 # REST API, authentication, and WebSocket endpoint
│   ├── config/
│   │   ├── database.py             # MongoDB connection and collections
│   │   └── settings.py             # Kafka, model, video, and frame settings
│   ├── consumers/
│   │   ├── detection_consumer.py   # Runs YOLO on Kafka video frames
│   │   └── persistence_consumer.py # Persists detection events to MongoDB
│   ├── producers/
│   │   └── video_producer.py       # Reads a video and publishes JPEG frames
│   ├── schemas/
│   │   └── auth.py                 # Registration and login request models
│   ├── services/
│   │   ├── detector.py             # YOLO model wrapper
│   │   ├── safety_rules.py         # Maps detections to PPE violations
│   │   └── upload_inference.py     # Image/video upload processing and result jobs
│   ├── dependencies.py             # Bearer-token authentication dependency
│   └── security.py                 # Password hashing and JWT creation
├── frontend/
│   ├── src/                        # React dashboard source
│   ├── .env.example                # Browser API and WebSocket URLs
│   └── package.json
├── src/                            # Small producer/consumer/WebSocket test scripts
├── .env.example                    # Backend environment template
├── docker-compose.yml              # Kafka, MongoDB, and backend services
├── Dockerfile                      # Backend image
└── requirements.txt                # Python dependencies
```

## Prerequisites

Choose either Docker for the infrastructure/backend or install the services locally.

- Docker Engine with Docker Compose, or local Kafka and MongoDB installations
- Node.js 22+ and npm for the dashboard
- A trained YOLO `.pt` weights file for detection
- A video file or camera source for the streaming pipeline
- Optional: a CUDA-capable GPU and compatible PyTorch installation for faster inference

> Model weights, training data, and sample videos are intentionally not committed to this repository. The `.gitignore` excludes `*.pt`, `videos/`, `runs/`, and `data/raw/`.

## Quick start: API and infrastructure with Docker

1. Clone the repository and enter it:

   ```bash
   git clone https://github.com/seifdabbous/realtime-ppe-detection.git
   cd realtime-ppe-detection
   ```

2. Create the backend environment file:

   ```bash
   cp .env.example .env
   ```

3. Replace `SECRET_KEY` in `.env` with a strong random value. For example:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

4. Start Kafka, MongoDB, and the API:

   ```bash
   docker compose up --build -d
   docker compose ps
   ```

5. Open the API documentation at <http://127.0.0.1:8000/docs>.

This Compose file starts the infrastructure and backend only. Run the frontend and live-pipeline processes using the sections below. A YOLO model is loaded only when inference begins, so the API can start before weights are supplied. To use upload inference inside the backend container, place the weights at the path configured by `MODEL_PATH` before building the image, then rebuild the backend.

To stop the services:

```bash
docker compose down
```

Add `-v` only when you also want to delete the MongoDB volume and all stored application data:

```bash
docker compose down -v
```

## Run the frontend

In a separate terminal:

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

Open <http://127.0.0.1:5173>. Create an account on the login screen, then sign in. The frontend stores the access token in browser session storage.

For a production bundle:

```bash
npm run build
npm run preview
```

## Run the complete live-detection pipeline locally

The following mode is the simplest way to run the model and video workers because the Compose file does not define worker services and the default `videos/` directory is excluded from the Docker build context.

1. Make sure Kafka is reachable at `localhost:9092` and MongoDB is reachable at `localhost:27017`.

2. Put your assets in the repository, for example:

   ```text
   models/best.pt
   videos/input.mp4
   ```

3. Create a local `.env`:

   ```dotenv
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   MONGO_URL=mongodb://admin:admin@localhost:27017/
   MONGO_DB_NAME=ppe_safety
   SECRET_KEY=replace-with-a-long-random-secret
   MODEL_PATH=models/best.pt
   VIDEO_SOURCE=videos/input.mp4
   ```

4. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Start each long-running process in its own terminal, from the repository root and with the virtual environment activated:

   ```bash
   uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   ```bash
   python -m app.consumers.persistence_consumer
   ```

   ```bash
   python -m app.consumers.detection_consumer
   ```

6. Start the finite video producer last:

   ```bash
   python -m app.producers.video_producer
   ```

The producer stops at the end of the file. The consumers and API continue running until interrupted.

## On-demand image and video inference

After signing in, use the dashboard upload panel or call `POST /predict/upload` with an authenticated multipart request. Supported formats are:

- Images: JPG, JPEG, PNG, WEBP
- Videos: MP4, AVI, MOV, MKV, WEBM
- Maximum upload size: 100 MB

Images are processed synchronously. Videos return a job ID and are processed by a single background worker; poll `GET /predict/jobs/{job_id}` until the status is `completed` or `failed`. Completed results are downloaded from `GET /predictions/{result_id}`.

Generated files default to `runtime/predictions/` and expire after 24 hours. Job metadata is held in application memory, so restarting the API clears job lookup state.

## Environment variables

### Backend and workers

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | Yes | None | Kafka broker address; use `kafka:9092` in Compose or `localhost:9092` locally |
| `MONGO_URL` | Yes | None | MongoDB connection URI |
| `MONGO_DB_NAME` | Yes | None | MongoDB database name |
| `SECRET_KEY` | Yes | None | Secret used to sign JWT access tokens |
| `VIDEO_FRAMES_TOPIC` | No | `video-frames` | Kafka input topic for encoded frames |
| `DETECTION_EVENTS_TOPIC` | No | `detection-events` | Kafka topic for detection results |
| `MODEL_PATH` | No | `runs/detect/runs/ppe_yolo11n-2/weights/best.pt` | YOLO weights path |
| `VIDEO_SOURCE` | No | `videos/13753913_3840_2160_50fps.mp4` | Video file path or OpenCV-compatible source |
| `FRAME_WIDTH` | No | `640` | Width published by the video producer |
| `FRAME_HEIGHT` | No | `360` | Height published by the video producer |
| `JPEG_QUALITY` | No | `80` | Kafka frame JPEG quality |
| `PREDICTION_DIR` | No | `runtime/predictions` | Upload result directory |
| `PREDICTION_TTL_SECONDS` | No | `86400` | Retention time for generated results |
| `VIDEO_ANALYSIS_FPS` | No | `10` | Target video sampling rate for uploads |
| `MAX_VIDEO_WIDTH` | No | `1280` | Maximum annotated upload-video width |
| `MAX_VIDEO_HEIGHT` | No | `720` | Maximum annotated upload-video height |

`MONGO_ROOT_USERNAME` and `MONGO_ROOT_PASSWORD` configure the MongoDB container and both default to `admin` in Compose.

### Frontend

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | REST API base URL |
| `VITE_WS_BASE_URL` | `ws://127.0.0.1:8000` | WebSocket base URL |

## API overview

| Method | Endpoint | Authentication | Description |
| --- | --- | --- | --- |
| `POST` | `/register` | No | Create a user account |
| `POST` | `/login` | No | Return a bearer access token |
| `GET` | `/events/latest` | Bearer token | Return the newest detection event |
| `GET` | `/events?limit=20` | Bearer token | Return recent detection events |
| `GET` | `/violations?limit=20` | Bearer token | Flatten recent safety violations |
| `GET` | `/stats` | Bearer token | Return event and violation totals |
| `POST` | `/predict/upload` | Bearer token | Analyze an uploaded image or video |
| `GET` | `/predict/jobs/{job_id}` | Bearer token | Check an upload job |
| `GET` | `/predictions/{result_id}` | Bearer token | Download an annotated result |
| `WS` | `/ws/events?token=...` | Token query parameter | Receive live detection events |

Access tokens expire after 30 minutes.

## Basic API example

Register and log in:

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"operator","email":"operator@example.com","password":"change-me-123"}'

curl -X POST http://127.0.0.1:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"operator@example.com","password":"change-me-123"}'
```

Copy the returned `access_token`, then call an authenticated endpoint:

```bash
curl http://127.0.0.1:8000/stats \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

## Verification

Backend syntax check:

```bash
python -m compileall app src
```

Frontend build:

```bash
cd frontend
npm ci
npm run build
```

The files in `src/` are standalone integration helpers rather than a formal automated test suite. They require the corresponding local services to be running.

## Troubleshooting

- **`KeyError: KAFKA_BOOTSTRAP_SERVERS`**: create `.env` and define the variable; unlike several other settings, it has no default.
- **YOLO weights not found**: set `MODEL_PATH` to an existing `.pt` file. Weights are not stored in Git; if inference runs in Docker, make sure the file is present before the image is built and rebuild the backend.
- **Video source cannot be opened**: verify `VIDEO_SOURCE` and confirm that OpenCV supports the file or camera source.
- **No events in the dashboard**: start both consumers, then start the video producer. Kafka consumers use `auto_offset_reset="latest"`, so start them before publishing frames.
- **Kafka connection errors**: use `kafka:9092` from Compose containers and `localhost:9092` only for a broker configured for host access.
- **MongoDB authentication errors**: keep `MONGO_URL`, `MONGO_ROOT_USERNAME`, and `MONGO_ROOT_PASSWORD` consistent. Existing Docker volumes preserve the credentials used when they were first initialized.
- **WebSocket disconnects immediately**: log in again and use a current token in the `token` query parameter.
- **Uploaded video is queued forever after restart**: upload jobs are in memory and do not survive API restarts; submit the file again.

## Security and production notes

- Never commit `.env`, model weights, videos, or production credentials.
- Replace the example `SECRET_KEY` and MongoDB credentials before deployment.
- Restrict CORS origins to the deployed frontend URL.
- Put the API behind TLS and use `wss://` for WebSocket traffic.
- Add durable job storage and an external task queue if upload jobs must survive restarts or scale across API replicas.
- Add authentication to Kafka and MongoDB for non-local environments.

## License

No license file is currently included. Unless a license is added, the repository's code is not automatically granted an open-source license.

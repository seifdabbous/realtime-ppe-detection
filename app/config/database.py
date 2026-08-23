import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()

MONGO_URL = os.getenv(
    "MONGO_URL"
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME"
)

client = MongoClient(MONGO_URL)

database = client[MONGO_DB_NAME]

detections_collection = database["detections"]


users_collection = database["users"]
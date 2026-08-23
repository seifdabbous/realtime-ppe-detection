import asyncio
import json

import requests
import websockets


BASE_URL = "http://127.0.0.1:8000"

EMAIL = "your_email@example.com"
PASSWORD = "your_password"


def login():
    response = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": EMAIL,
            "password": PASSWORD
        }
    )

    response.raise_for_status()

    data = response.json()

    return data["access_token"]


async def websocket_client():

    token = login()

    print("Login successful")
    print("Connecting to websocket...")

    websocket_url = (
        f"ws://127.0.0.1:8000/ws/events"
        f"?token={token}"
    )

    async with websockets.connect(
        websocket_url
    ) as websocket:

        print("WebSocket connected")

        while True:
            message = await websocket.recv()

            event = json.loads(message)

            print(event)


asyncio.run(websocket_client())
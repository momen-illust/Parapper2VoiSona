
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request

from voisona_client import VoiSonaClient


voisona = VoiSonaClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await voisona.initialize()
    try:
        yield
    finally:
        await voisona.close()


app = FastAPI(
    title="Parapper2VoiSona",
    lifespan=lifespan,
)


@app.post("/api/events")
async def receive_event(request: Request):
    event = await request.json()

    if event.get("type") != "turn.final":
        return {"status": "ignored"}

    text = event.get("text", "")

    if not isinstance(text, str) or not text.strip():
        return {"status": "ignored"}

    text = text.strip()
    print(f"[Parapper] {text}", flush=True)

    try:
        uuid = await voisona.speak(text)
    except httpx.HTTPStatusError as error:
        print(
            "[VoiSona] HTTPエラー:",
            error.response.status_code,
            error.response.text,
            flush=True,
        )
        return {"status": "error"}
    except httpx.RequestError as error:
        print(f"[VoiSona] 通信エラー: {error}", flush=True)
        return {"status": "error"}

    return {
        "status": "accepted",
        "uuid": uuid,
    }

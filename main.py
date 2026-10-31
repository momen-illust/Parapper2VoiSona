
import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request

from voisona_client import VoiSonaClient

from config import get_int


voisona = VoiSonaClient()

text_queue = asyncio.Queue(
    maxsize=get_int("QUEUE_MAX_SIZE", 100)
)


async def speech_worker():
    """キュー内のテキストを順番にVoiSonaへ送信する"""

    while True:
        text = await text_queue.get()

        try:
            print(f"[Queue] 送信開始: {text}", flush=True)

            uuid = await voisona.speak(text)

            print(
                f"[VoiSona] 受付完了: {uuid}",
                flush=True,
            )

        except httpx.HTTPStatusError as error:
            print(
                f"[VoiSona] HTTPエラー: "
                f"{error.response.status_code} "
                f"{error.response.text}",
                flush=True,
            )

        except httpx.RequestError as error:
            print(
                f"[VoiSona] 通信エラー: {error}",
                flush=True,
            )

        except Exception as error:
            print(
                f"[Worker] エラー: {error}",
                flush=True,
            )

        finally:
            text_queue.task_done()


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker = None

    try:
        await voisona.initialize()

        # バックグラウンドでWorkerを1つ起動
        worker = asyncio.create_task(speech_worker())

        yield

    finally:
        if worker is not None:
            worker.cancel()

            try:
                await worker
            except asyncio.CancelledError:
                pass

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

    try:
        # キューに追加。VoiSonaの処理完了は待たない
        text_queue.put_nowait(text)

    except asyncio.QueueFull:
        print(
            f"[Queue] 満杯のため破棄: {text}",
            flush=True,
        )

        return {
            "status": "dropped",
            "reason": "queue_full",
        }

    print(
        f"[Queue] 追加: {text} "
        f"(待機数: {text_queue.qsize()})",
        flush=True,
    )

    return {
        "status": "queued",
        "queue_size": text_queue.qsize(),
    }

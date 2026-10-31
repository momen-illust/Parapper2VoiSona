import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from config import get_int, get_str
from voisona_client import VoiSonaClient, VoiSonaHTTPError


voisona = VoiSonaClient()
text_queue = asyncio.Queue(
    maxsize=get_int("QUEUE_MAX_SIZE", 100)
)


async def speech_worker():
    while True:
        text = await text_queue.get()

        try:
            print(f"[Queue] 送信開始: {text}", flush=True)

            uuid = await voisona.speak(text)

            print(
                f"[VoiSona] 受付完了: {uuid}",
                flush=True,
            )

        except VoiSonaHTTPError as error:
            print(
                f"[VoiSona] HTTPエラー: "
                f"{error.status_code} {error}",
                flush=True,
            )

        except OSError as error:
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


class EventHandler(BaseHTTPRequestHandler):
    loop = None
    queue = None

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/events":
            self.send_json(404, {"status": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > 1024 * 1024:
                self.send_json(400, {"status": "invalid_length"})
                return

            body = self.rfile.read(length)
            event = json.loads(body)

            if not isinstance(event, dict):
                self.send_json(400, {"status": "invalid_event"})
                return

        except (ValueError, UnicodeDecodeError):
            self.send_json(400, {"status": "invalid_json"})
            return

        if event.get("type") != "turn.final":
            self.send_json(200, {"status": "ignored"})
            return

        text = event.get("text", "")

        if not isinstance(text, str) or not text.strip():
            self.send_json(200, {"status": "ignored"})
            return

        text = text.strip()

        # HTTPスレッドからasyncioイベントループへ渡す
        future = asyncio.run_coroutine_threadsafe(
            self.enqueue(text),
            self.loop,
        )

        try:
            result = future.result(timeout=1.0)
            self.send_json(200, result)

        except Exception as error:
            future.cancel()
            print(f"[HTTP] キュー登録エラー: {error}", flush=True)
            self.send_json(503, {"status": "error"})

    async def enqueue(self, text):
        try:
            self.queue.put_nowait(text)

        except asyncio.QueueFull:
            print(f"[Queue] 満杯のため破棄: {text}", flush=True)
            return {
                "status": "dropped",
                "reason": "queue_full",
            }

        print(
            f"[Queue] 追加: {text} "
            f"(待機数: {self.queue.qsize()})",
            flush=True,
        )

        return {
            "status": "queued",
            "queue_size": self.queue.qsize(),
        }


async def main():
    await voisona.initialize()

    worker = None
    server = None
    server_task = None

    try:
        worker = asyncio.create_task(speech_worker())

        host = get_str("SERVER_HOST", "127.0.0.1")
        port = get_int("SERVER_PORT", 15522)

        EventHandler.loop = asyncio.get_running_loop()
        EventHandler.queue = text_queue

        server = ThreadingHTTPServer(
            (host, port),
            EventHandler,
        )
        server.daemon_threads = True

        print(
            f"[Server] 起動しました: http://{host}:{port}",
            flush=True,
        )
        print(
            "[Server] 終了するには Ctrl+C を押してください",
            flush=True,
        )

        server_task = asyncio.create_task(
            asyncio.to_thread(server.serve_forever)
        )

        await asyncio.shield(server_task)

    finally:
        if server is not None:
            await asyncio.to_thread(server.shutdown)
            server.server_close()

        if server_task is not None:
            await server_task

        if worker is not None:
            worker.cancel()

            try:
                await worker
            except asyncio.CancelledError:
                pass

        await voisona.close()

        print("[Server] 終了しました", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Server] 停止しました", flush=True)

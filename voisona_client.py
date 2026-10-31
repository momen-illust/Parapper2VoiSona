
import asyncio
import base64
import json
import urllib.error
import urllib.request

from config import get_int, get_str


class VoiSonaHTTPError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(message)


class VoiSonaClient:
    def __init__(self):
        host = get_str("VOISONA_HOST", "127.0.0.1")
        port = get_int("VOISONA_PORT", 32766)

        self.base_url = (
            f"http://{host}:{port}/api/talk/v1"
        )

        user = get_str("VOISONA_USER")
        password = get_str("VOISONA_API_PASSWORD")

        credentials = f"{user}:{password}".encode("utf-8")
        encoded = base64.b64encode(credentials).decode("ascii")

        self.headers = {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
        }

        self.voice = None

        # localhostへの通信でプロキシを使わない
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({})
        )

    def _request(self, method, endpoint, payload=None):
        url = f"{self.base_url}/{endpoint}"

        data = None
        headers = self.headers.copy()

        if payload is not None:
            data = json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8")

            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with self.opener.open(
                request,
                timeout=15,
            ) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)

        except urllib.error.HTTPError as error:
            body = error.read().decode(
                "utf-8",
                errors="replace",
            )

            raise VoiSonaHTTPError(
                error.code,
                body,
            ) from error

    async def initialize(self):
        result = await asyncio.to_thread(
            self._request,
            "GET",
            "voices",
        )

        voices = result["items"]

        self.voice = next(
            (
                voice
                for voice in voices
                if "ja_JP" in voice["languages"]
            ),
            None,
        )

        if self.voice is None:
            raise RuntimeError(
                "日本語ボイスが見つかりません"
            )

        print(
            "[VoiSona] 使用ボイス:",
            self.voice["voice_name"],
            self.voice["voice_version"],
            flush=True,
        )

    async def speak(self, text: str):
        if self.voice is None:
            raise RuntimeError(
                "VoiSonaClientが初期化されていません"
            )

        payload = {
            "text": text,
            "language": "ja_JP",
            "voice_name": self.voice["voice_name"],
            "voice_version": self.voice["voice_version"],
            "force_enqueue": True,
        }

        result = await asyncio.to_thread(
            self._request,
            "POST",
            "speech-syntheses",
            payload,
        )

        return result["uuid"]

    async def close(self):
        pass

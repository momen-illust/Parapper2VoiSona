
import httpx
from config import get_str, get_int


class VoiSonaClient:
    def __init__(self):
        host = get_str("VOISONA_HOST", "127.0.0.1")
        port = get_int("VOISONA_PORT", 32766)

        self.base_url = (
            f"http://{host}:{port}/api/talk/v1"
        )

        self.client = httpx.AsyncClient(
            auth=httpx.BasicAuth(
                get_str("VOISONA_USER"),
                get_str("VOISONA_API_PASSWORD"),
            ),
            timeout=15.0,
            trust_env=False,
        )

        self.voice = None

    async def initialize(self):
        response = await self.client.get(
            f"{self.base_url}/voices"
        )
        response.raise_for_status()

        voices = response.json()["items"]

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

        response = await self.client.post(
            f"{self.base_url}/speech-syntheses",
            json=payload,
        )
        response.raise_for_status()

        return response.json()["uuid"]

    async def close(self):
        await self.client.aclose()

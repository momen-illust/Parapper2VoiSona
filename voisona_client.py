
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class VoiSonaClient:
    def __init__(self):
        user = os.getenv("VOISONA_USER")
        password = os.getenv("VOISONA_API_PASSWORD")
        port = os.getenv("VOISONA_PORT", "32766")

        if not user or not password:
            raise ValueError(
                "VOISONA_USERとVOISONA_API_PASSWORDを"
                ".envに設定してください"
            )

        self.base_url = f"http://127.0.0.1:{port}/api/talk/v1"
        self.client = httpx.AsyncClient(
            auth=httpx.BasicAuth(user, password),
            timeout=10.0,
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
                "日本語のボイスライブラリが見つかりません"
            )

        print(
            "[VoiSona] 使用ボイス:",
            self.voice["voice_name"],
            self.voice["voice_version"],
        )

    async def speak(self, text: str):
        if self.voice is None:
            raise RuntimeError("VoiSonaClientが初期化されていません")

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

        uuid = response.json()["uuid"]
        print(f"[VoiSona] 合成リクエスト受付: {uuid}")
        return uuid

    async def close(self):
        await self.client.aclose()


import os
import sys
from pathlib import Path

from dotenv import dotenv_values


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


CONFIG_PATH = get_app_dir() / "config.env"

if not CONFIG_PATH.is_file():
    raise FileNotFoundError(
        f"設定ファイルが見つかりません: {CONFIG_PATH}"
    )

settings = dotenv_values(CONFIG_PATH)


def get_str(key: str, default: str | None = None) -> str:
    value = settings.get(key)

    if value is None or not value.strip():
        if default is not None:
            return default
        raise ValueError(f"設定項目がありません: {key}")

    return value


def get_int(key: str, default: int) -> int:
    return int(get_str(key, str(default)))


import sys
from pathlib import Path


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


CONFIG_PATH = get_app_dir() / "config.env"


def load_config() -> dict[str, str]:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(
            f"設定ファイルが見つかりません: {CONFIG_PATH}"
        )

    result = {}

    with CONFIG_PATH.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, 1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                raise ValueError(
                    f"設定ファイルの{line_number}行目が不正です"
                )

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if not key:
                raise ValueError(
                    f"設定ファイルの{line_number}行目にキーがありません"
                )

            if (
                len(value) >= 2
                and value[0] == value[-1]
                and value[0] in ('"', "'")
            ):
                value = value[1:-1]

            result[key] = value

    return result


settings = load_config()


def get_str(key: str, default: str | None = None) -> str:
    value = settings.get(key)

    if value is None or not value.strip():
        if default is not None:
            return default

        raise ValueError(f"設定項目がありません: {key}")

    return value


def get_int(key: str, default: int) -> int:
    return int(get_str(key, str(default)))


import asyncio

from main import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Server] 停止しました", flush=True)

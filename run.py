import uvicorn

from config import get_str, get_int
from main import app


def main():
    uvicorn.run(
        app,
        host=get_str("SERVER_HOST", "127.0.0.1"),
        port=get_int("SERVER_PORT", 15522),
        reload=False,
        workers=1,
    )


if __name__ == "__main__":
    main()
from pathlib import Path
import os
import threading
import time
import webbrowser

import uvicorn


BASE_DIR = Path(__file__).resolve().parent
APP_URL = "http://127.0.0.1:8000/login"


def open_browser() -> None:
    time.sleep(1.5)
    webbrowser.open(APP_URL)


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

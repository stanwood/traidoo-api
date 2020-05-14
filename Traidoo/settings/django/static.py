from pathlib import Path

import environ

env = environ.Env(GAE_APPLICATION=(str, ""))

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_BUCKET = env("STATIC_BUCKET")
if env("GAE_APPLICATION"):
    STATIC_URL = f"https://storage.googleapis.com/{STATIC_BUCKET}/"
else:
    STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR.joinpath("static")

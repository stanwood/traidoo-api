from pathlib import Path

import environ

from Traidoo.settings.project.google import DEFAULT_BUCKET

env = environ.Env(GAE_APPLICATION=(str, ""))

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if env("GAE_APPLICATION"):
    STATIC_URL = f"https://storage.googleapis.com/{DEFAULT_BUCKET}/static/"
else:
    STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR.joinpath("static")

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
ROUTERAI_BASE_URL = "https://routerai.ru/api/v1"


def _load_env_file() -> None:
    if not ENV_PATH.exists():
        return

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_file()

ROUTERAI_API_KEY = os.getenv("ROUTERAI_API_KEY")

if not ROUTERAI_API_KEY:
    raise RuntimeError("ROUTERAI_API_KEY is missing. Add it to .env.")

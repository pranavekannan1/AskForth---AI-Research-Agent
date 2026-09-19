import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()


def require_groq_api_key() -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "The backend is missing GROQ_API_KEY. Configure a new key in the "
            "deployment environment and retry the report."
        )
    return GROQ_API_KEY


class Settings:
    APP_NAME = os.getenv("APP_NAME", "Askforth AI Research Agent")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


settings = Settings()
import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()


def _comma_separated_values(value: str) -> list[str]:
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


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
    CORS_ORIGINS = _comma_separated_values(
        os.getenv(
            "CORS_ORIGINS",
            ",".join(
                (
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "https://ask-forth-ai-research-agent.vercel.app",
                    "https://askforth-ai-research-agent.onrender.com",
                )
            ),
        )
    )
    # Vercel creates a distinct origin for preview and branch deployments.
    # The expression also supports the historical AskForth project spelling
    # and local development servers running on a non-default port.
    CORS_ORIGIN_REGEX = os.getenv(
        "CORS_ORIGIN_REGEX",
        (
            r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?"
            r"|https://ask-?forth-ai-research-agent(?:-[a-z0-9-]+)?\.vercel\.app"
        ),
    )


settings = Settings()

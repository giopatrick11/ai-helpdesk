import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(f"{name} is not configured")

    return value


def parse_cors_origins(value: str) -> list[str]:
    origins = [
        origin.strip()
        for origin in value.split(",")
        if origin.strip()
    ]

    if not origins:
        raise ValueError("CORS_ORIGINS must include at least one origin")

    return origins


DATABASE_URL = get_required_env("DATABASE_URL")
SECRET_KEY = get_required_env("SECRET_KEY")
GEMINI_API_KEY = get_required_env("GEMINI_API_KEY")
GEMINI_MODEL = get_required_env("GEMINI_MODEL")
GEMINI_EMBEDDING_MODEL = get_required_env("GEMINI_EMBEDDING_MODEL")
REDIS_URL = get_required_env("REDIS_URL")

MAX_PDF_UPLOAD_BYTES = int(
    os.getenv("MAX_PDF_UPLOAD_BYTES", str(10 * 1024 * 1024))
)

if MAX_PDF_UPLOAD_BYTES <= 0:
    raise ValueError("MAX_PDF_UPLOAD_BYTES must be greater than zero")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)
CORS_ORIGINS = parse_cors_origins(
    get_required_env("CORS_ORIGINS")
)

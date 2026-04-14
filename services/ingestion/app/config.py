from pathlib import Path

from pydantic_settings import BaseSettings

def _find_env() -> str:
    p = Path(__file__).resolve()
    for parent in p.parents:
        candidate = parent / ".env"
        if candidate.is_file():
            return str(candidate)
    return ".env"

_ENV_FILE = _find_env()


class Settings(BaseSettings):
    SERVICE_NAME: str = "ingestion-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 100

    LOG_LEVEL: str = "INFO"

    DEEPGRAM_API_KEY: str = ""
    DEEPGRAM_MODEL: str = "nova-2"

    ALLOWED_EXTENSIONS: list[str] = [
        ".pdf", ".docx", ".txt", ".html", ".htm",
        ".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm",
    ]

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}

    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


settings = Settings()

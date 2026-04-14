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
    SERVICE_NAME: str = "preprocessing-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


settings = Settings()

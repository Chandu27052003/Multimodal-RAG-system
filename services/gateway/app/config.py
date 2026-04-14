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
    SERVICE_NAME: str = "api-gateway"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    INGESTION_SERVICE_URL: str = "http://localhost:8001"
    PREPROCESSING_SERVICE_URL: str = "http://localhost:8002"
    EMBEDDING_SERVICE_URL: str = "http://localhost:8003"
    VECTOR_STORE_SERVICE_URL: str = "http://localhost:8004"
    RETRIEVAL_SERVICE_URL: str = "http://localhost:8005"
    GENERATION_SERVICE_URL: str = "http://localhost:8006"

    DEFAULT_COLLECTION: str = "default"

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


settings = Settings()

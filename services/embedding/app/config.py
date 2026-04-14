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
    SERVICE_NAME: str = "embedding-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8003

    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    EMBEDDING_MODEL: str = "nvidia/llama-3.2-nv-embedqa-1b-v2"

    EMBEDDING_DIM: int = 2048
    BATCH_SIZE: int = 32

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


settings = Settings()

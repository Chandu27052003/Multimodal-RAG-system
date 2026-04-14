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
    SERVICE_NAME: str = "retrieval-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8005

    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    RERANKING_MODEL: str = "nv-rerank-qa-mistral-4b:1"

    EMBEDDING_SERVICE_URL: str = "http://localhost:8003"
    VECTOR_STORE_SERVICE_URL: str = "http://localhost:8004"

    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANK: int = 5
    CONTEXT_TOKEN_LIMIT: int = 4000

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


settings = Settings()

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
    SERVICE_NAME: str = "generation-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8006

    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    GENERATION_MODEL: str = "qwen/qwen2-7b-instruct"

    TEMPERATURE: float = 0.7
    TOP_P: float = 0.7
    MAX_TOKENS: int = 10000

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


settings = Settings()

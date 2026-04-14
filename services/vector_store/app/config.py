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
    SERVICE_NAME: str = "vector-store-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8004

    VECTOR_DB_PATH: str = "./data/vector_db"
    VECTOR_DB_DISTANCE: str = "cosine"
    DEFAULT_COLLECTION: str = "default"

    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}

    @property
    def db_path(self) -> Path:
        path = Path(self.VECTOR_DB_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Chunky"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 64

    max_upload_bytes: int = 10 * 1024 * 1024
    max_pdf_pages: int = 200
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 5
    frontend_origin: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("FRONTEND_ORIGIN", "CORS_ORIGINS"),
    )
    allowed_hosts: str = "localhost,127.0.0.1,testserver"

    data_dir: Path = Field(default_factory=lambda: BACKEND_DIR / "data")

    @field_validator("frontend_origin")
    @classmethod
    def validate_frontend_origin(cls, value: str) -> str:
        origin = value.strip().rstrip("/")
        if "," in origin:
            raise ValueError("FRONTEND_ORIGIN must be a single origin")
        if "*" in origin:
            raise ValueError("FRONTEND_ORIGIN cannot contain wildcards")
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("FRONTEND_ORIGIN must be like http://localhost:3000")
        if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
            raise ValueError("FRONTEND_ORIGIN must not include a path or query")
        if parsed.hostname in {"localhost", "127.0.0.1"} and parsed.port is None:
            raise ValueError("FRONTEND_ORIGIN must include a port, e.g. http://localhost:3000")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise ValueError("Non-local FRONTEND_ORIGIN must use https")
        return origin

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [self.frontend_origin]

    @property
    def allowed_host_list(self) -> list[str]:
        hosts = [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]
        if "*" in hosts:
            raise ValueError("ALLOWED_HOSTS cannot contain wildcards")
        return hosts

    @property
    def max_request_bytes(self) -> int:
        return self.max_upload_bytes + (1024 * 1024)

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "chunky.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.sqlite_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def ensure_data_directories(settings: Settings | None = None) -> None:
    config = settings or get_settings()
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.uploads_dir.mkdir(parents=True, exist_ok=True)
    config.chroma_dir.mkdir(parents=True, exist_ok=True)

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import Settings, ensure_data_directories, get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.core.security import register_security_middleware
from app.db.init_db import init_db
from app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    ensure_data_directories()
    init_db()
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    configure_logging(config)

    application = FastAPI(
        title=config.app_name,
        version="1.0.0",
        docs_url=None if config.is_production else "/docs",
        redoc_url=None if config.is_production else "/redoc",
        lifespan=lifespan,
    )
    register_security_middleware(application, config)
    application.include_router(api_router, prefix=config.api_v1_prefix)

    @application.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @application.get("/health", response_model=HealthResponse, tags=["health"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", environment=config.app_env)

    return application


app = create_app()

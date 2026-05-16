from fastapi import FastAPI

from app.api.router import router
from app.core.config import get_config
from app.exceptions import register_exception_handlers
from app.lifecycle import lifespan
from app.logging_config import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    config = get_config()
    api = FastAPI(title=config.app_name, version=config.version, lifespan=lifespan)
    register_exception_handlers(api)
    api.include_router(router)
    return api

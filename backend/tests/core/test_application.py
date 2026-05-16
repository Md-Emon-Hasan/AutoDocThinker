"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application import create_app
from app.cli.commands import command_names
from app.cli.interactive import help_text, interactive_loop
from app.cli.printing import (
    _print_help,
    _print_result,
    print_help_payload,
    print_result_payload,
)
from app.core.config import get_config
from app.core.constants import (
    APP_TITLE,
    DEFAULT_DOMAIN,
    DEFAULT_RAG_MODE,
    SUPPORTED_FILE_TYPES,
)
from app.core.environment import env_bool
from app.core.errors import AppError, NotFoundError, ValidationAppError
from app.core.paths import project_path
from app.dependencies import container
from app.exceptions import register_exception_handlers
from app.lifecycle import lifespan
from app.logging_config import configure_logging


class TestApplication:
    def test_create_app(self):
        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title == "AutoDocThinker"

    def test_container_returns_all_keys(self):
        box = container()
        for key in (
            "config",
            "index",
            "domains",
            "retrieval",
            "ingestion",
            "rag",
            "chat",
        ):
            assert key in box

    def test_container_is_cached(self):
        assert container() is container()

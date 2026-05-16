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


class TestCLI:
    def test_command_names(self):
        names = command_names()
        assert "ask" in names and "quit" in names

    def test_help_text(self):
        assert "status" in help_text()

    def test_print_help_payload(self):
        assert "ask" in print_help_payload()

    def test_print_result_payload(self):
        payload = {"mode": "advanced", "answer": "ok", "sources": [{"label": "s"}]}
        result = print_result_payload(payload)
        assert "Answer" in result and "[Mode: advanced]" in result

    def test_print_does_not_crash(self):
        _print_help()
        _print_result({"mode": "a", "answer": "b", "sources": [{"label": "c"}]})
        interactive_loop()

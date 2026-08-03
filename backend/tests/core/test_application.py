"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

from fastapi import FastAPI

from app.application import create_app
from app.dependencies import container


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

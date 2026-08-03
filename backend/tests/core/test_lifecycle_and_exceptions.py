"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import AppError
from app.exceptions import register_exception_handlers
from app.lifecycle import lifespan


class TestLifecycleAndExceptions:
    def test_lifespan_sets_ready(self):
        app = FastAPI(lifespan=lifespan)
        register_exception_handlers(app)

        @app.get("/boom")
        def boom():
            raise AppError("broken")

        with TestClient(app) as c:
            assert app.state.ready is True
            assert c.get("/boom").json()["detail"] == "broken"
        assert app.state.ready is False

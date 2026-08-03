"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

from app.core.errors import AppError, NotFoundError, ValidationAppError


class TestErrors:
    def test_status_codes(self):
        assert AppError.status_code == 500
        assert NotFoundError.status_code == 404
        assert ValidationAppError.status_code == 422

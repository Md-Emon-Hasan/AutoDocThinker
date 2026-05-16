class AppError(Exception):
    status_code = 500


class NotFoundError(AppError):
    status_code = 404


class ValidationAppError(AppError):
    status_code = 422

import os

from fastapi import Header, HTTPException


def require_admin_token(
    x_admin_token: str | None = Header(default=None),  # noqa: B008
) -> None:
    """Shared admin-token dependency for destructive/admin endpoints.

    If ADMIN_TOKEN is unset, these endpoints must refuse outright (503),
    not silently allow -- an unset token is a misconfiguration, not an
    open door.
    """
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="ADMIN_TOKEN is not configured; admin/destructive endpoints "
            "are disabled",
        )
    if x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")

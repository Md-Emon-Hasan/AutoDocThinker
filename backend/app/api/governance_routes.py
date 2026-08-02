from fastapi import APIRouter, Depends

from app.api.security import require_admin_token
from app.dependencies import container

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/audit", dependencies=[Depends(require_admin_token)])
def audit_log(limit: int = 50, offset: int = 0):
    return container()["audit_log"].list(limit=limit, offset=offset)

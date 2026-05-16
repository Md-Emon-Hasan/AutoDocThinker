from fastapi import APIRouter, HTTPException

from app.dependencies import container
from app.schemas.domain import DomainOut

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("", response_model=list[DomainOut])
def list_domains():
    return [
        DomainOut(name=item.name, label=item.label, description=item.description)
        for item in container()["domains"].list()
    ]


@router.get("/{name}", response_model=DomainOut)
def get_domain(name: str):
    try:
        item = container()["domains"].get(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Domain not found") from exc
    return DomainOut(name=item.name, label=item.label, description=item.description)

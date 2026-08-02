from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.dependencies import container
from app.schemas.ingestion import IngestRequest, IngestResponse, IngestTextRequest

router = APIRouter(prefix="/ingest", tags=["ingestion"])

_UPLOAD_TYPES = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}


@router.post("/source", response_model=IngestResponse)
def ingest_source(payload: IngestRequest):
    try:
        return container()["ingestion"].ingest(
            payload.source, payload.file_type, scope=payload.scope
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/upload", response_model=IngestResponse)
async def ingest_upload(
    file: UploadFile = File(...), scope: str | None = Form(None)  # noqa: B008
):
    # Use only the basename to prevent path traversal
    original_name = Path(file.filename or "upload").name
    suffix = Path(original_name).suffix.lower()
    file_type = _UPLOAD_TYPES.get(suffix)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: .pdf, .docx, .txt",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    box = container()
    save_path = box["config"].upload_dir / original_name
    try:
        save_path.write_bytes(content)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Could not save file: {exc}"
        ) from exc

    if not save_path.exists():
        raise HTTPException(status_code=500, detail="File was not persisted to disk")

    try:
        return box["ingestion"].ingest(
            str(save_path), file_type, display_name=original_name, scope=scope
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/text", response_model=IngestResponse)
def ingest_text(payload: IngestTextRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty")
    try:
        return container()["ingestion"].ingest(
            payload.text,
            "text",
            display_name=payload.title or "pasted_text",
            scope=payload.scope,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auto")
def auto_ingest():
    box = container()
    return box["ingestion"].auto_ingest(
        box["config"].data_dir, box["config"].supported_extensions
    )

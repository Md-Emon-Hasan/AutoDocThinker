from datetime import UTC, datetime


def enrich_metadata(
    metadata: dict, source: str, source_id: str, file_type: str
) -> dict:
    return {
        **metadata,
        "source": source,
        "source_id": source_id,
        "file_type": file_type,
        "ingested_at": datetime.now(UTC).isoformat(),
    }

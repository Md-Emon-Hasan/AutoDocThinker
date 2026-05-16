from pathlib import Path


def upload_path(root: Path, filename: str) -> Path:
    return root / filename

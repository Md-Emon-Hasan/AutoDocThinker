from pathlib import Path


def ensure_supported_path(path: str, extensions: tuple[str, ...]) -> Path:
    file_path = Path(path)
    if file_path.suffix.lower() not in extensions:
        raise ValueError(f"Unsupported extension: {file_path.suffix}")
    return file_path

from pathlib import Path


def save_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path

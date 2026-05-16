from pathlib import Path


def removable(path: Path) -> bool:
    return path.exists() and path.is_file()

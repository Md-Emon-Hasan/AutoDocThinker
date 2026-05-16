from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def project_path(*parts: str) -> Path:
    return ROOT_DIR.joinpath(*parts)

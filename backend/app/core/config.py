import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RAGConfig:
    data_dir: Path = field(default_factory=lambda: ROOT_DIR / "data")
    upload_dir: Path = field(default_factory=lambda: ROOT_DIR / "uploads")
    vector_store_dir: Path = field(
        default_factory=lambda: ROOT_DIR / "data" / "vector_store"
    )
    supported_extensions: tuple[str, ...] = (".pdf", ".docx", ".txt")
    default_domain: str = "general"
    default_mode: str = "advanced"
    initial_k: int = 20
    rerank_top_k: int = 5
    crag_high_confidence: float = 0.6
    crag_low_confidence: float = 0.3
    crag_max_retries: int = 2
    app_name: str = "AutoDocThinker"
    version: str = "3.0.0"


def get_config() -> RAGConfig:
    config = RAGConfig()
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.upload_dir.mkdir(parents=True, exist_ok=True)
    config.vector_store_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("USER_AGENT", "AutoDocThinker/3.0")
    return config

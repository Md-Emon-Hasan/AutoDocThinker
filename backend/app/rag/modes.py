RAG_MODES = ("naive", "advanced", "crag", "self_rag")


def ensure_mode(mode: str) -> str:
    clean = mode.strip().lower()
    if clean not in RAG_MODES:
        raise ValueError(f"Unknown RAG mode: {mode}")
    return clean

import hashlib


def make_source_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]

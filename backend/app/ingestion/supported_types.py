EXTENSION_TO_TYPE = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}


def extension_to_type(ext: str) -> str | None:
    return EXTENSION_TO_TYPE.get(ext.lower())

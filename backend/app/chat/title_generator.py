def generate_title(message: str) -> str:
    return message.strip()[:40] or "Untitled chat"

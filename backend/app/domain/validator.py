from app.rag.modes import ensure_mode


def validate_profile(domain_registry, domain: str, rag_mode: str):
    profile = domain_registry.get(domain)
    return profile, ensure_mode(rag_mode)

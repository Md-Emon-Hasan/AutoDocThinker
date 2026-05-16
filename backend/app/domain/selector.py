from app.domain.validator import validate_profile


def select_profile(domain_registry, domain: str, rag_mode: str) -> dict:
    profile, mode = validate_profile(domain_registry, domain, rag_mode)
    return {"domain": profile.name, "rag_mode": mode, "prompt": profile.system_prompt}

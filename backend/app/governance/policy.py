"""Per-domain governance policy, reusing app/domain/registry.py's names.

Medical, Legal, and Finance are higher-risk than General: they require
hedging/a disclaimer on advice-shaped output and a higher groundedness
threshold. Fail mode is explicit per policy: high-risk domains fail
closed (a blocked output stays blocked), General fails open with a
warning.
"""

HIGH_RISK_DOMAINS = {"legal", "medical", "finance"}

_DEFAULT_POLICY = {
    "min_groundedness": 0.5,
    "require_disclaimer": False,
    "fail_closed": False,
}

DOMAIN_POLICIES: dict[str, dict] = {
    "legal": {
        "min_groundedness": 0.75,
        "require_disclaimer": True,
        "fail_closed": True,
    },
    "medical": {
        "min_groundedness": 0.75,
        "require_disclaimer": True,
        "fail_closed": True,
    },
    "finance": {
        "min_groundedness": 0.7,
        "require_disclaimer": True,
        "fail_closed": True,
    },
    "general": dict(_DEFAULT_POLICY),
}


def get_policy(domain: str) -> dict:
    return DOMAIN_POLICIES.get(domain, _DEFAULT_POLICY)


def is_high_risk(domain: str) -> bool:
    return domain in HIGH_RISK_DOMAINS

from app.domain.models import DomainProfile
from app.domain.presets.customer_support import CUSTOMER_SUPPORT
from app.domain.presets.education import EDUCATION
from app.domain.presets.finance import FINANCE
from app.domain.presets.general import GENERAL
from app.domain.presets.legal import LEGAL
from app.domain.presets.medical import MEDICAL
from app.domain.presets.technical import TECHNICAL


def build_domain_presets() -> dict[str, DomainProfile]:
    profiles = [
        GENERAL,
        LEGAL,
        MEDICAL,
        FINANCE,
        EDUCATION,
        TECHNICAL,
        CUSTOMER_SUPPORT,
    ]
    return {profile.name: profile for profile in profiles}

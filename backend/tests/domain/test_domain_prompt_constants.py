"""Consolidated tests for the domain module: models, presets, defaults,
registry, selector, validator, and all domain prompt constants."""

import pytest

from app.domain.defaults import build_domain_presets
from app.domain.models import DomainProfile
from app.domain.registry import DomainRegistry
from app.domain.selector import select_profile
from app.domain.validator import validate_profile
from app.prompts.domain.customer_support import CUSTOMER_SUPPORT_PROMPT
from app.prompts.domain.education import EDUCATION_PROMPT
from app.prompts.domain.finance import FINANCE_PROMPT
from app.prompts.domain.general import GENERAL_PROMPT
from app.prompts.domain.legal import LEGAL_PROMPT
from app.prompts.domain.medical import MEDICAL_PROMPT
from app.prompts.domain.technical import TECHNICAL_PROMPT


class TestDomainPromptConstants:
    def test_all_prompts_are_non_empty(self):
        for prompt in (
            GENERAL_PROMPT,
            LEGAL_PROMPT,
            MEDICAL_PROMPT,
            FINANCE_PROMPT,
            EDUCATION_PROMPT,
            TECHNICAL_PROMPT,
            CUSTOMER_SUPPORT_PROMPT,
        ):
            assert isinstance(prompt, str) and len(prompt) > 0

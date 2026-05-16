from __future__ import annotations

from typing import List

from app.domain.defaults import build_domain_presets
from app.domain.models import DomainProfile


class DomainRegistry:
    def __init__(self) -> None:
        self._profiles = build_domain_presets()

    def list(self) -> List[DomainProfile]:
        return list(self._profiles.values())

    def get(self, name: str) -> DomainProfile:
        key = name.strip().lower()
        if key not in self._profiles:
            raise KeyError(key)
        return self._profiles[key]

    def names(self) -> List[str]:
        return list(self._profiles)

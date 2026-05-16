from dataclasses import dataclass


@dataclass(frozen=True)
class DomainProfile:
    name: str
    label: str
    description: str
    system_prompt: str
    metadata_filter: dict[str, str]

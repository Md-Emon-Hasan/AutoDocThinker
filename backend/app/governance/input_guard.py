"""Input guard: mostly deterministic pattern/heuristic checks.

Kept regex/heuristic-first rather than LLM-first per the spec: cheaper,
faster, testable, and not itself vulnerable to prompt injection (an LLM
asked "is this an injection attempt?" can itself be steered by the very
injection it's judging).
"""

import ipaddress
import re
import socket
from dataclasses import dataclass, field
from urllib.parse import urlparse

DEFAULT_MAX_INPUT_CHARS = 20_000

ALLOWED_URL_SCHEMES = {"http", "https"}
MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 10 * 1024 * 1024

_INJECTION_PATTERNS = [
    re.compile(r"ignore (all|any|the) (previous|prior|above) instructions", re.I),
    re.compile(r"disregard (all|any|the) (previous|prior|above)", re.I),
    re.compile(r"you are now (in )?(developer|admin|jailbreak|dan) mode", re.I),
    re.compile(r"reveal (your|the) (system prompt|instructions)", re.I),
    re.compile(r"what (is|are) your (system prompt|instructions)", re.I),
    re.compile(r"<\|.*?\|>"),  # delimiter escape attempts
    re.compile(r"```\s*system"),
    re.compile(r"\[system\]", re.I),
]

_PII_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "phone": re.compile(r"\b(?:\+?\d{1,2}[ -]?)?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4}\b"),
    "card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "national_id": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


class URLSafetyError(ValueError):
    """Raised by validate_url when a URL is unsafe to fetch (SSRF guard)."""


@dataclass
class InputGuardResult:
    allowed: bool
    rules_fired: list[str] = field(default_factory=list)
    redacted_text: str | None = None


def check_injection(text: str) -> list[str]:
    return [p.pattern for p in _INJECTION_PATTERNS if p.search(text)]


def detect_pii(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for label, pattern in _PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            found[label] = matches
    return found


def redact_pii(text: str) -> str:
    redacted = text
    for label, pattern in _PII_PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)
    return redacted


def check_size(text: str, max_chars: int = DEFAULT_MAX_INPUT_CHARS) -> bool:
    return len(text) <= max_chars


def validate_url(url: str) -> None:
    """SSRF guard: allows only http/https, resolves the hostname, and
    rejects private/loopback/link-local/reserved/multicast addresses.
    Raises URLSafetyError on rejection."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise URLSafetyError(
            f"URL scheme '{parsed.scheme}' is not allowed; only http/https"
        )
    if not parsed.hostname:
        raise URLSafetyError("URL has no hostname")
    try:
        addr_infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise URLSafetyError(f"could not resolve hostname: {parsed.hostname}") from exc
    for info in addr_infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise URLSafetyError(f"URL resolves to a disallowed address: {ip}")


class InputGuard:
    """Fails closed: a guard error rejects the request."""

    def __init__(
        self, max_input_chars: int = DEFAULT_MAX_INPUT_CHARS, redact: bool = True
    ) -> None:
        self.max_input_chars = max_input_chars
        self.redact = redact

    def check(self, text: str) -> InputGuardResult:
        try:
            if not check_size(text, self.max_input_chars):
                return InputGuardResult(allowed=False, rules_fired=["oversized_input"])
            if check_injection(text):
                return InputGuardResult(allowed=False, rules_fired=["prompt_injection"])
            pii = detect_pii(text)
            if pii:
                redacted = redact_pii(text) if self.redact else None
                return InputGuardResult(
                    allowed=True, rules_fired=["pii_detected"], redacted_text=redacted
                )
            return InputGuardResult(allowed=True)
        except Exception:
            return InputGuardResult(allowed=False, rules_fired=["guard_error"])

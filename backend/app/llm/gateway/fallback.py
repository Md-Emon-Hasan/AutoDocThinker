import logging
import time

from app.llm.fallback import fallback_answer
from app.llm.gateway.models import GatewayRequest, GatewayResponse, Provider
from app.utils.retry import backoff_seconds, should_retry

logger = logging.getLogger(__name__)

_RETRYABLE_MARKERS = (
    "timeout",
    "rate limit",
    "429",
    "connection",
    "500",
    "502",
    "503",
    "504",
)
_NON_RETRYABLE_MARKERS = (
    "400",
    "401",
    "403",
    "422",
    "unauthorized",
    "invalid api key",
    "auth",
)


def is_retryable(exc: Exception) -> bool:
    """Retryable: timeout, 429, 5xx, connection error. Not retryable:
    400/422/auth -- those fail fast rather than cascade down the chain.
    Anything unrecognized defaults to non-retryable."""
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    if isinstance(exc, (ValueError, KeyError)):
        return False
    message = str(exc).lower()
    if any(marker in message for marker in _NON_RETRYABLE_MARKERS):
        return False
    return any(marker in message for marker in _RETRYABLE_MARKERS)


def with_fallback(
    providers: list[Provider],
    request: GatewayRequest,
    max_attempts: int = 3,
) -> GatewayResponse:
    """Try providers in order, retrying retryable failures with backoff.
    A non-retryable failure advances to the next provider immediately.
    On full chain exhaustion, falls back to fallback_answer()."""
    attempts_log: list[tuple[str, str]] = []
    total_attempts = 0
    for provider in providers:
        provider_name = type(provider).__name__
        attempt = 0
        while should_retry(attempt, max_attempts):
            total_attempts += 1
            try:
                text = provider.answer(
                    request.question, request.context, request.domain_prompt
                )
                return GatewayResponse(
                    text=text, provider=provider_name, attempts=total_attempts
                )
            except Exception as exc:  # noqa: BLE001 - must classify any failure
                attempts_log.append((provider_name, str(exc)))
                if not is_retryable(exc):
                    logger.warning(
                        "Non-retryable failure from %s, advancing to next "
                        "provider: %s",
                        provider_name,
                        exc,
                    )
                    break
                attempt += 1
                logger.warning(
                    "Retryable failure from %s (attempt %d/%d): %s",
                    provider_name,
                    attempt,
                    max_attempts,
                    exc,
                )
                if should_retry(attempt, max_attempts):
                    time.sleep(backoff_seconds(attempt))

    logger.error(
        "LLM gateway fallback chain exhausted after %d attempts across %d "
        "provider(s): %s",
        total_attempts,
        len(providers),
        attempts_log,
    )
    return GatewayResponse(
        text=fallback_answer(request.question),
        provider="fallback",
        attempts=total_attempts,
    )

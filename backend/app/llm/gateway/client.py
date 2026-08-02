from app.core.config import RAGConfig
from app.llm.gateway.fallback import with_fallback
from app.llm.gateway.models import GatewayRequest, Provider, TaskCategory


class LLMGateway:
    """Provider abstraction, task-based routing, and ordered fallback.

    ``providers_by_task`` maps a TaskCategory to its ordered fallback
    chain (primary -> secondary -> tertiary). A missing/unconfigured
    provider for a task simply isn't in that chain -- it never breaks
    startup, it's just unavailable for routing.
    """

    def __init__(
        self,
        providers_by_task: dict[TaskCategory, list[Provider]],
        config: RAGConfig,
        max_attempts: int = 3,
    ) -> None:
        self._providers_by_task = providers_by_task
        self._config = config
        self._max_attempts = max_attempts

    def answer(
        self,
        question: str,
        context: str,
        domain_prompt: str,
        task: TaskCategory,
        complexity_hint: float | None = None,
    ) -> str:
        providers = self._providers_by_task.get(task, [])
        request = GatewayRequest(
            question=question,
            context=context,
            domain_prompt=domain_prompt,
            task=task,
            complexity_hint=complexity_hint,
        )
        response = with_fallback(providers, request, self._max_attempts)
        return response.text


class TaskBoundClient:
    """Adapter binding a gateway call to one fixed task category.

    Exposes the exact 3-arg ``.answer(question, context, domain_prompt)``
    signature GroqClient already has, so it's a drop-in replacement
    wherever a raw GroqClient is injected today (nodes.py, chain_factory)
    with zero changes to those call sites.
    """

    def __init__(self, gateway: LLMGateway, task: TaskCategory) -> None:
        self._gateway = gateway
        self._task = task

    def answer(self, question: str, context: str, domain_prompt: str) -> str:
        return self._gateway.answer(question, context, domain_prompt, self._task)

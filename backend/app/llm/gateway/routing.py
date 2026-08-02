from app.core.config import RAGConfig
from app.llm.gateway.models import TaskCategory


def resolve_model(
    task: TaskCategory,
    config: RAGConfig,
    complexity_hint: float | None = None,
) -> str:
    """Resolve the model configured for ``task``, escalating if warranted.

    Escalation is a no-op unless the caller has explicitly configured an
    entry in ``escalated_model_map`` for this task -- absent that, this
    always returns the base task_model_map entry, preserving today's
    single-model behavior for every task until someone opts in.
    """
    base_model = config.task_model_map.get(task.value)
    if base_model is None:
        raise KeyError(f"No model configured for task category: {task.value}")
    if (
        complexity_hint is not None
        and complexity_hint >= config.complexity_escalation_threshold
    ):
        return config.escalated_model_map.get(task.value, base_model)
    return base_model

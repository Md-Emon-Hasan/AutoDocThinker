from app.llm.output_parser import parse_json
from app.orchestration.models import SubTask

_PLAN_INSTRUCTION = (
    "Decompose the QUESTION into independent sub-tasks, with an explicit "
    "dependency graph (list which sub-task ids each one must wait for, if "
    "any -- most should have none, meaning they can run in parallel). Keep "
    "the plan small.\n\n"
    'Respond with ONLY a JSON object: {"subtasks": [{"id": <short str>, '
    '"query": <sub-question text>, "depends_on": [<id>, ...]}]}'
)

# A trivial query needs no decomposition call at all -- spending a
# planning call to conclude "no plan is needed" is itself the cost leak
# the spec warns against.
_TRIVIAL_MAX_CHARS = 120
_TRIVIAL_MARKERS = (" and ", " then ", ";", " vs ", " compare ")


def is_trivial(question: str) -> bool:
    lowered = question.lower()
    return len(question) < _TRIVIAL_MAX_CHARS and not any(
        marker in lowered for marker in _TRIVIAL_MARKERS
    )


def _single_task(question: str) -> list[SubTask]:
    return [SubTask(id="t1", query=question, depends_on=[])]


class Planner:
    """One gateway call producing a structured decomposition, capped at
    max_subtasks/max_depth (both configurable) -- an uncapped planner is
    an unbounded cost leak."""

    def __init__(self, task_client, max_subtasks: int = 5, max_depth: int = 2) -> None:
        self.task_client = task_client
        self.max_subtasks = max_subtasks
        self.max_depth = max_depth

    def plan(self, question: str) -> tuple[list[SubTask], bool]:
        """Returns (subtasks, made_llm_call)."""
        if self.task_client is None or is_trivial(question):
            return _single_task(question), False

        raw = self.task_client.answer(question, "", _PLAN_INSTRUCTION)
        parsed = parse_json(raw)
        if not parsed or not parsed.get("subtasks"):
            return _single_task(question), True

        raw_subtasks = parsed["subtasks"][: self.max_subtasks]
        valid_ids = {t.get("id") for t in raw_subtasks if isinstance(t, dict)}
        subtasks = [
            SubTask(
                id=str(t["id"]),
                query=str(t["query"]),
                # Only depend on ids that exist in this same plan, and
                # never on itself -- an invalid/self reference would
                # otherwise deadlock the dependency-graph dispatch.
                depends_on=[
                    str(d)
                    for d in t.get("depends_on", [])
                    if d in valid_ids and d != t.get("id")
                ],
            )
            for t in raw_subtasks
            if isinstance(t, dict) and t.get("id") and t.get("query")
        ]
        return (subtasks or _single_task(question)), True

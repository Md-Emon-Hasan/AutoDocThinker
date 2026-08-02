import time
from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


@dataclass
class Budget:
    """Enforces the four hard caps per deep query: max LLM calls, max
    tokens, max wall-clock time, max recursion depth. On exhaustion the
    caller stops and synthesizes from partial results -- never
    continues, never truncates silently. This is the difference between
    an impressive architecture and a runaway bill.
    """

    max_llm_calls: int
    max_tokens: int
    max_wall_clock_seconds: float
    max_recursion_depth: int
    calls_used: int = 0
    tokens_used: int = 0

    def __post_init__(self) -> None:
        self._start_time = time.time()

    def record_call(self, tokens: int = 0) -> None:
        self.calls_used += 1
        self.tokens_used += tokens

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self._start_time

    def exhausted(self, depth: int = 0) -> bool:
        # depth is 1-indexed (depth=1 is the first/only level sub-agents
        # run at today), so max_recursion_depth=1 must permit depth=1 --
        # only depth exceeding the cap trips this.
        return (
            self.calls_used >= self.max_llm_calls
            or self.tokens_used >= self.max_tokens
            or self.elapsed_seconds >= self.max_wall_clock_seconds
            or depth > self.max_recursion_depth
        )

    def consumed(self) -> dict:
        return {
            "llm_calls": self.calls_used,
            "tokens": self.tokens_used,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "max_llm_calls": self.max_llm_calls,
            "max_tokens": self.max_tokens,
            "max_wall_clock_seconds": self.max_wall_clock_seconds,
            "max_recursion_depth": self.max_recursion_depth,
        }

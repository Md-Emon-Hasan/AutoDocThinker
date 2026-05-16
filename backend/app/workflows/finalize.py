from app.rag.history import append_turn


def finalize(state: dict) -> dict:
    state["history"] = append_turn(
        state.get("history", []), state["input"], state["answer"]
    )
    return state

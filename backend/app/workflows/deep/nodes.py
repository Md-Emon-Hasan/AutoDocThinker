def orchestrate_node(state: dict, orchestrator, domain_profile) -> dict:
    result = orchestrator.run(
        state["input"], domain_profile, state.get("metadata_filter")
    )
    return {
        **state,
        "answer": result["answer"],
        "sources": result["sources"],
        # "orchestration" must be declared on DeepState -- LangGraph
        # silently drops any state key its schema doesn't declare.
        "orchestration": {
            "succeeded": result.get("succeeded", []),
            "failed": result.get("failed", []),
            "skipped": result.get("skipped", []),
            "budget": result.get("budget", {}),
            "query_id": result.get("query_id"),
        },
    }

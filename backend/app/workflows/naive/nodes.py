def retrieve_node(state: dict, retrieval) -> dict:
    docs = retrieval.retrieve(state["input"], 6, state.get("metadata_filter"))
    return {**state, "context_docs": docs}


def answer_node(state: dict, llm, domain_profile) -> dict:
    context, sources = state["formatter"](state.get("context_docs", []))
    answer = llm.answer(state["input"], context, domain_profile.system_prompt)
    return {**state, "sources": sources, "answer": answer}

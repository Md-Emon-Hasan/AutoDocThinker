def decide_node(state: dict, retrieval) -> dict:
    docs = retrieval.retrieve(state["input"], 6, state.get("metadata_filter"))
    return {**state, "context_docs": docs, "need_retrieval": bool(docs)}


def generate_node(state: dict, llm, domain_profile) -> dict:
    context, sources = state["formatter"](state.get("context_docs", []))
    answer = llm.answer(state["input"], context, domain_profile.system_prompt)
    docs = state.get("context_docs", [])
    avg_len = sum(len(d.page_content) for d in docs) / max(len(docs), 1)
    confidence = min(0.9, 0.5 + 0.4 * (avg_len / 1500)) if docs else 0.35
    return {
        **state,
        "sources": sources,
        "answer": answer,
        "confidence": round(confidence, 3),
    }

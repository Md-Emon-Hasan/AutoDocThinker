def retrieve_node(state: dict, retrieval) -> dict:
    return {
        **state,
        "context_docs": retrieval.retrieve(
            state["input"], 6, state.get("metadata_filter")
        ),
    }


def evaluate_node(state: dict) -> dict:
    docs = state.get("context_docs", [])
    if not docs:
        confidence = 0.0
    else:
        # Score based on content length and count — longer, more chunks = more confident
        avg_len = sum(len(d.page_content) for d in docs) / len(docs)
        count_score = min(len(docs) / 6, 1.0)
        len_score = min(avg_len / 1500, 1.0)
        confidence = 0.5 * count_score + 0.5 * len_score
    return {**state, "confidence": round(confidence, 3)}


def web_search_node(state: dict, wiki) -> dict:
    wiki_doc = wiki.search(state["input"])
    docs = [*state.get("context_docs", []), wiki_doc]
    return {
        **state,
        "context_docs": docs,
        "confidence": max(state.get("confidence", 0.0), 0.6),
    }


def answer_node(state: dict, llm, domain_profile) -> dict:
    docs = state.get("context_docs", [])[:8]
    context, sources = state["formatter"](docs)
    return {
        **state,
        "context_docs": docs,
        "sources": sources,
        "answer": llm.answer(state["input"], context, domain_profile.system_prompt),
    }

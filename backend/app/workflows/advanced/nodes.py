def rewrite_node(state: dict, domain_profile) -> dict:
    question = state["input"]
    domain_label = domain_profile.label
    # Generate multiple query angles for better retrieval coverage
    queries = [
        question,
        f"{domain_label} context: {question}",
        f"What are the key facts about: {question}",
        f"Explain in detail: {question}",
    ]
    return {**state, "rewritten_queries": queries}


def retrieve_node(state: dict, retrieval) -> dict:
    docs = []
    seen_ids = set()
    for query in state["rewritten_queries"]:
        for doc in retrieval.retrieve(query, 6, state.get("metadata_filter")):
            cid = doc.metadata.get("chunk_id", doc.page_content[:50])
            if cid not in seen_ids:
                seen_ids.add(cid)
                docs.append(doc)
    # Return top 8 unique docs to give the LLM rich context
    return {**state, "context_docs": docs[:8]}


def answer_node(state: dict, llm, domain_profile) -> dict:
    context, sources = state["formatter"](state.get("context_docs", []))
    return {
        **state,
        "sources": sources,
        "answer": llm.answer(state["input"], context, domain_profile.system_prompt),
    }

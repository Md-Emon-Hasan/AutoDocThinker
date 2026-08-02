_SYNTHESIS_PREFIX = (
    "Synthesize a single, coherent, well-structured answer from the sub-task "
    "results below. Merge overlapping information, resolve any redundancy, and "
    "cite sources as [1], [2], etc. Note any gaps if a sub-task failed.\n\n"
)


def _merge_sources(successful: list) -> list[dict]:
    """Dedup by chunk_id/source, renumber ids sequentially so citations
    stay traceable to real chunks after the merge."""
    merged: list[dict] = []
    seen: set = set()
    for result in successful:
        for source in result.sources:
            key = source.get("chunk_id") or source.get("source")
            if key in seen:
                continue
            seen.add(key)
            merged.append(dict(source))
    for idx, source in enumerate(merged, start=1):
        source["id"] = idx
    return merged


def synthesize(
    question: str, sub_results: list, llm, domain_profile, skipped: list
) -> dict:
    """Combine sub-agent results into one answer with merged, deduplicated
    citations. Reports which sub-tasks succeeded, failed, or were
    skipped by budget."""
    successful = [r for r in sub_results if r.success]
    failed = [r.subtask_id for r in sub_results if not r.success]

    if not successful:
        return {
            "answer": (
                "Unable to produce an answer: every sub-task failed or none "
                "completed within budget."
            ),
            "sources": [],
            "succeeded": [],
            "failed": failed,
            "skipped": skipped,
        }

    combined_context = "\n\n".join(
        f"[Sub-task {r.subtask_id}] {r.answer}" for r in successful
    )
    if failed or skipped:
        combined_context += (
            f"\n\n(Note: sub-tasks {failed + skipped} did not complete -- "
            "acknowledge any resulting gap in the answer.)"
        )
    sources = _merge_sources(successful)
    answer = llm.answer(
        question, combined_context, _SYNTHESIS_PREFIX + domain_profile.system_prompt
    )
    return {
        "answer": answer,
        "sources": sources,
        "succeeded": [r.subtask_id for r in successful],
        "failed": failed,
        "skipped": skipped,
    }

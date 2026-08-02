def _matches_one(actual, expected) -> bool:
    if isinstance(expected, (list, tuple, set)):
        return actual in expected
    return actual == expected


def matches_filter(metadata: dict, metadata_filter: dict | None) -> bool:
    return not metadata_filter or all(
        _matches_one(metadata.get(key), value) for key, value in metadata_filter.items()
    )


SHARED_SCOPE = "shared"

# Used whenever a caller supplies no explicit scope, for both ingestion and
# retrieval. This is NOT "shared" (so it can never be reached by a caller
# who *does* supply a distinct explicit scope, e.g. a chat session id --
# real isolation holds for anyone actually using scopes). It exists so the
# ordinary "ingest a document, then immediately ask about it" flow keeps
# working for callers that don't manage scope tokens at all: without this,
# a fresh random scope per unscoped call would make that content
# permanently unreachable by any later unscoped query. Callers that want
# real per-caller isolation must pass an explicit scope (chat sessions do
# this automatically -- see app/chat/service.py).
ANONYMOUS_SCOPE = "session:anonymous"


def resolve_scope(scope: str | None) -> str:
    return scope or ANONYMOUS_SCOPE


def scope_filter(scope: str | None) -> dict:
    """Build the metadata_filter fragment enforcing scope isolation.

    A query only ever reaches the shared corpus plus its own scope --
    never another session's. Merge this into any other metadata_filter
    (it uses list-value "in" matching via matches_filter/_build_where,
    not exact equality).
    """
    resolved = resolve_scope(scope)
    if resolved == SHARED_SCOPE:
        return {"scope": [SHARED_SCOPE]}
    return {"scope": [SHARED_SCOPE, resolved]}

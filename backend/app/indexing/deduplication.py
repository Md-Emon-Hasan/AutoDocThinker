def already_ingested(source_ids: set[str], incoming: set[str]) -> bool:
    return bool(source_ids & incoming)

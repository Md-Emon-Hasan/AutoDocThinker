def matches_filter(metadata: dict, metadata_filter: dict | None) -> bool:
    return not metadata_filter or all(
        metadata.get(key) == value for key, value in metadata_filter.items()
    )

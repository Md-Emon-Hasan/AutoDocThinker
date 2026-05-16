class SourceRegistry:
    def __init__(self) -> None:
        self.sources: set[str] = set()

    def add(self, source_id: str) -> None:
        self.sources.add(source_id)

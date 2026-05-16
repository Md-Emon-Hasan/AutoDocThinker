class ChromaStore:
    def __init__(self) -> None:
        self.persisted = False

    def persist(self) -> bool:
        self.persisted = True
        return self.persisted

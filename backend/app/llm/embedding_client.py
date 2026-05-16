class EmbeddingClient:
    def embed(self, text: str) -> list[float]:
        return [float(len(text))]

from app.indexing.tokenizer import tokenize


class BM25Index:
    def score(self, query: str, text: str) -> float:
        q = set(tokenize(query))
        d = set(tokenize(text))
        return len(q & d) / max(len(q), 1)

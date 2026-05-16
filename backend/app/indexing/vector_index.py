class VectorIndex:
    def similarity(self, left: str, right: str) -> float:
        left_chars = set(left.lower())
        right_chars = set(right.lower())
        return len(left_chars & right_chars) / max(len(left_chars | right_chars), 1)

def combine_scores(
    vector_score: float, bm25_score: float, bm25_weight: float = 0.5
) -> float:
    return (1 - bm25_weight) * vector_score + bm25_weight * bm25_score

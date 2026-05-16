def rewrite_queries(question: str, domain_label: str) -> list[str]:
    return [question, f"{domain_label}: {question}"]

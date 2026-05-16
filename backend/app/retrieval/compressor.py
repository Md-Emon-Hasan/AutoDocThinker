def compress_documents(docs: list, max_chars: int = 3000) -> list:
    for doc in docs:
        if len(doc.page_content) > max_chars:
            doc.page_content = doc.page_content[:max_chars].rstrip()
    return docs

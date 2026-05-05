from langchain_core.documents import Document

from services.kb_vector_service import load_kb_vector_store


def retrieve_kb_documents(query: str, top_k: int = 3) -> list[Document]:
    if not query or not str(query).strip():
        raise ValueError("Query is required")

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    vector_store = load_kb_vector_store()
    results = vector_store.similarity_search(query, k=top_k)
    return results


def format_retrieved_results(results: list[Document]) -> str:
    if not results:
        return "No retrieved results found."

    lines = []

    for index, doc in enumerate(results, start=1):
        metadata = doc.metadata or {}

        lines.append(f"Result #{index}")
        lines.append("Content:")
        lines.append(doc.page_content)
        lines.append("Metadata:")
        lines.append(f"  id: {metadata.get('id', '')}")
        lines.append(f"  regulation: {metadata.get('regulation', '')}")
        lines.append(f"  chapter: {metadata.get('chapter', '')}")
        lines.append(f"  article: {metadata.get('article', '')}")
        lines.append(f"  topic: {metadata.get('topic', '')}")
        lines.append("-" * 60)

    return "\n".join(lines)

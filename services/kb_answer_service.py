from pathlib import Path
import os

from dotenv import load_dotenv
from openai import OpenAI

from knowledge_base.prompts.kb_prompt import build_kb_prompt
from services.kb_retriever_service import retrieve_kb_documents


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_env() -> None:
    env_path = _get_project_root() / ".env"
    load_dotenv(dotenv_path=env_path)


def is_openai_available() -> bool:
    try:
        _load_env()
        api_key = os.getenv("OPENAI_API_KEY")
        return bool(api_key)
    except Exception:
        return False


def _build_context_from_docs(retrieved_docs: list) -> str:
    context_parts = []

    for index, doc in enumerate(retrieved_docs, start=1):
        context_parts.append(f"المصدر {index}:\n{doc.page_content}")

    return "\n\n".join(context_parts)


def generate_openai_answer(query: str, retrieved_docs: list) -> str:
    _load_env()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    if not retrieved_docs:
        return "لم أجد نتائج مسترجعة كافية للإجابة على هذا السؤال."

    client = OpenAI(api_key=api_key)

    context = _build_context_from_docs(retrieved_docs)
    prompt = build_kb_prompt(query=query, context=context)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "أنت مساعد أكاديمي متخصص في اللوائح والأنظمة الجامعية. أجب فقط من السياق المقدم لك."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    answer = response.choices[0].message.content.strip()

    if not answer:
        return "لم أتمكن من توليد إجابة واضحة من السياق المسترجع."

    return answer


def generate_fallback_answer(query: str, retrieved_docs: list) -> str:
    if not retrieved_docs:
        return "لم أجد إجابة واضحة في اللائحة المسترجعة."

    best_doc = retrieved_docs[0]
    content = best_doc.page_content

    answer_prefix = "الإجابة:"
    if answer_prefix in content:
        answer = content.split(answer_prefix, 1)[1].strip()
        if answer:
            return answer

    return "لم أجد إجابة واضحة في اللائحة المسترجعة."


def answer_kb_query(query: str, top_k: int = 3) -> dict:
    if not query or not str(query).strip():
        raise ValueError("Query is required")

    retrieved_docs = retrieve_kb_documents(query=query, top_k=top_k)

    sources = []
    for doc in retrieved_docs:
        metadata = doc.metadata or {}
        sources.append({
            "id": metadata.get("id", ""),
            "regulation": metadata.get("regulation", ""),
            "chapter": metadata.get("chapter", ""),
            "article": metadata.get("article", ""),
            "topic": metadata.get("topic", ""),
            "content": doc.page_content
        })

    if is_openai_available():
        try:
            answer = generate_openai_answer(query=query, retrieved_docs=retrieved_docs)
            mode = "openai"
        except Exception:
            answer = generate_fallback_answer(query=query, retrieved_docs=retrieved_docs)
            mode = "fallback"
    else:
        answer = generate_fallback_answer(query=query, retrieved_docs=retrieved_docs)
        mode = "fallback"

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_count": len(retrieved_docs),
        "mode": mode
    }

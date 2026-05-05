from pathlib import Path
import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from services.kb_documents_service import load_kb_documents


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_env() -> None:
    env_path = _get_project_root() / ".env"
    load_dotenv(dotenv_path=env_path)


def _get_vector_store_path() -> Path:
    return _get_project_root() / "knowledge_base" / "vector_store"


def _get_embeddings():
    _load_env()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=api_key,
    )


def vector_store_exists() -> bool:
    vector_store_path = _get_vector_store_path()

    if not vector_store_path.exists():
        return False

    if not vector_store_path.is_dir():
        return False

    return any(vector_store_path.iterdir())


def build_kb_vector_store():
    documents = load_kb_documents()
    vector_store_path = _get_vector_store_path()
    vector_store_path.mkdir(parents=True, exist_ok=True)

    embeddings = _get_embeddings()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(vector_store_path),
        collection_name="murshid_kb",
    )

    return {
        "vector_store": vector_store,
        "documents_count": len(documents),
        "persist_directory": str(vector_store_path),
    }


def load_kb_vector_store():
    if not vector_store_exists():
        raise FileNotFoundError(
            f"Vector store does not exist yet at: {_get_vector_store_path()}"
        )

    embeddings = _get_embeddings()

    vector_store = Chroma(
        persist_directory=str(_get_vector_store_path()),
        embedding_function=embeddings,
        collection_name="murshid_kb",
    )

    return vector_store

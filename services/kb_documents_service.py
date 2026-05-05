from pathlib import Path
import pandas as pd
from langchain_core.documents import Document


REQUIRED_KB_COLUMNS = [
    "id",
    "اللائحة",
    "الفصل",
    "المادة",
    "topic",
    "السؤال",
    "الإجابة",
]


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_kb_dataset_path() -> Path:
    return _get_project_root() / "knowledge_base" / "data" / "knowledge_base_dataset_ready.xlsx"


def load_kb_dataframe() -> pd.DataFrame:
    dataset_path = _get_kb_dataset_path()

    if not dataset_path.exists():
        raise FileNotFoundError(f"Knowledge Base dataset file not found: {dataset_path}")

    df = pd.read_excel(dataset_path)
    return df


def validate_kb_columns(df: pd.DataFrame) -> bool:
    missing_columns = [col for col in REQUIRED_KB_COLUMNS if col not in df.columns]

    if missing_columns:
        raise ValueError(
            "Missing required Knowledge Base columns: " + ", ".join(missing_columns)
        )

    return True


def clean_kb_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned_df = df.copy()

    cleaned_df = cleaned_df.dropna(how="all")

    for col in REQUIRED_KB_COLUMNS:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].fillna("").astype(str).str.strip()

    cleaned_df = cleaned_df[
        ~(
            (cleaned_df["السؤال"] == "")
            & (cleaned_df["الإجابة"] == "")
        )
    ]

    cleaned_df = cleaned_df.reset_index(drop=True)
    return cleaned_df


def build_kb_documents(df: pd.DataFrame) -> list[Document]:
    documents = []

    for _, row in df.iterrows():
        content = (
            f"اللائحة: {row['اللائحة']}\n"
            f"الفصل: {row['الفصل']}\n"
            f"المادة: {row['المادة']}\n"
            f"الموضوع: {row['topic']}\n"
            f"السؤال: {row['السؤال']}\n"
            f"الإجابة: {row['الإجابة']}"
        )

        metadata = {
            "id": row["id"],
            "regulation": row["اللائحة"],
            "chapter": row["الفصل"],
            "article": row["المادة"],
            "topic": row["topic"],
        }

        documents.append(
            Document(
                page_content=content,
                metadata=metadata,
            )
        )

    return documents


def load_kb_documents() -> list[Document]:
    df = load_kb_dataframe()
    validate_kb_columns(df)
    cleaned_df = clean_kb_dataframe(df)
    documents = build_kb_documents(cleaned_df)
    return documents

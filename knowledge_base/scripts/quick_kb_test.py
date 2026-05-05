from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from services.kb_documents_service import (
    load_kb_dataframe,
    validate_kb_columns,
    clean_kb_dataframe,
    build_kb_documents,
)
from services.kb_retriever_service import (
    retrieve_kb_documents,
    format_retrieved_results,
)


def main():
    try:
        print("=== Stage B Check ===\n")

        df = load_kb_dataframe()
        print("dataset loaded successfully")
        print(f"rows count = {len(df)}")

        validate_kb_columns(df)
        print("columns valid")

        cleaned_df = clean_kb_dataframe(df)
        print(f"cleaned rows count = {len(cleaned_df)}")

        documents = build_kb_documents(cleaned_df)
        print(f"documents count = {len(documents)}")

        if documents:
            print("\nfirst document preview:\n")
            print(documents[0].page_content)
            print("\nfirst document metadata:\n")
            print(documents[0].metadata)
        else:
            print("no documents were created")

        print("\n=== Stage D Retrieval Test ===\n")

        query = "ما هو تعريف العام الدراسي؟"
        top_k = 3

        print(f"query = {query}")
        print(f"top_k = {top_k}\n")

        results = retrieve_kb_documents(query=query, top_k=top_k)
        print(f"retrieved results count = {len(results)}\n")

        formatted_results = format_retrieved_results(results)
        print(formatted_results)

    except Exception as e:
        print("quick kb test failed")
        print(str(e))


if __name__ == "__main__":
    main()

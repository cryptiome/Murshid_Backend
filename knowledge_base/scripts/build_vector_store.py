from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from services.kb_vector_service import build_kb_vector_store


def main():
    try:
        result = build_kb_vector_store()

        print("vector store built successfully")
        print(f"documents count = {result['documents_count']}")
        print(f"saved to = {result['persist_directory']}")

    except Exception as e:
        print("build vector store failed")
        print(str(e))


if __name__ == "__main__":
    main()

from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from services.kb_answer_service import is_openai_available, generate_openai_answer
from services.kb_retriever_service import retrieve_kb_documents


def main():
    try:
        print(f"openai available = {is_openai_available()}")

        query = "ما هو تعريف العام الدراسي؟"
        docs = retrieve_kb_documents(query=query, top_k=3)

        answer = generate_openai_answer(query=query, retrieved_docs=docs)

        print("\nOpenAI response test SUCCESS")
        print(f"query = {query}")
        print("\nanswer:\n")
        print(answer)

    except Exception as e:
        print("OpenAI response test FAILED")
        print(str(e))


if __name__ == "__main__":
    main()

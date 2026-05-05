from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from services.kb_vector_service import _get_embeddings


def main():
    try:
        embeddings = _get_embeddings()
        result = embeddings.embed_query("ما هو تعريف العام الدراسي؟")

        print("OpenAI embeddings test SUCCESS")
        print(f"vector length = {len(result)}")

    except Exception as e:
        print("OpenAI embeddings test FAILED")
        print(str(e))


if __name__ == "__main__":
    main()

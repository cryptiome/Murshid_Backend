from flask import Blueprint, jsonify, request

from services.kb_documents_service import load_kb_dataframe, validate_kb_columns
from services.kb_retriever_service import retrieve_kb_documents
from services.kb_vector_service import vector_store_exists
from services.kb_answer_service import answer_kb_query



knowledge_base_bp = Blueprint("knowledge_base", __name__)


@knowledge_base_bp.route("/api/knowledge-base/health", methods=["GET"])
def knowledge_base_health():
    try:
        return jsonify({
            "status": "success",
            "data": {
                "agent": "knowledge_base",
                "working": True,
                "vector_store_exists": vector_store_exists()
            },
            "error": None
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "data": None,
            "error": str(e)
        }), 500


@knowledge_base_bp.route("/api/knowledge-base/info", methods=["GET"])
def knowledge_base_info():
    try:
        df = load_kb_dataframe()
        validate_kb_columns(df)

        return jsonify({
            "status": "success",
            "data": {
                "dataset_file": "knowledge_base_dataset_ready.xlsx",
                "rows_count": len(df),
                "columns_count": len(df.columns),
                "columns": list(df.columns),
                "vector_store_exists": vector_store_exists()
            },
            "error": None
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "data": None,
            "error": str(e)
        }), 500


@knowledge_base_bp.route("/api/knowledge-base/retrieve", methods=["POST"])
def knowledge_base_retrieve():
    try:
        body = request.get_json(silent=True) or {}

        query = str(body.get("query", "")).strip()
        top_k = body.get("top_k", 3)

        if not query:
            return jsonify({
                "status": "error",
                "data": None,
                "error": "Query is required"
            }), 400

        try:
            top_k = int(top_k)
        except Exception:
            return jsonify({
                "status": "error",
                "data": None,
                "error": "top_k must be an integer"
            }), 400

        if top_k <= 0:
            return jsonify({
                "status": "error",
                "data": None,
                "error": "top_k must be greater than 0"
            }), 400

        results = retrieve_kb_documents(query=query, top_k=top_k)

        formatted_results = []
        for doc in results:
            metadata = doc.metadata or {}

            formatted_results.append({
                "content": doc.page_content,
                "metadata": {
                    "id": metadata.get("id", ""),
                    "regulation": metadata.get("regulation", ""),
                    "chapter": metadata.get("chapter", ""),
                    "article": metadata.get("article", ""),
                    "topic": metadata.get("topic", "")
                }
            })

        return jsonify({
            "status": "success",
            "data": {
                "query": query,
                "count": len(formatted_results),
                "results": formatted_results
            },
            "error": None
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "data": None,
            "error": str(e)
        }), 500


@knowledge_base_bp.route("/api/knowledge-base/ask", methods=["POST"])
def knowledge_base_ask():
    try:
        body = request.get_json(silent=True) or {}

        query = str(body.get("query", "")).strip()
        top_k = body.get("top_k", 3)

        if not query:
            return jsonify({
                "status": "error",
                "data": None,
                "error": "Query is required"
            }), 400

        try:
            top_k = int(top_k)
        except Exception:
            return jsonify({
                "status": "error",
                "data": None,
                "error": "top_k must be an integer"
            }), 400

        if top_k <= 0:
            return jsonify({
                "status": "error",
                "data": None,
                "error": "top_k must be greater than 0"
            }), 400

        result = answer_kb_query(query=query, top_k=top_k)

        return jsonify({
            "status": "success",
            "data": result,
            "error": None
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "data": None,
            "error": str(e)
        }), 500

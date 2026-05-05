import json
import requests
from typing import Dict, Any, List

BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 120

JSON_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json",
}


def execute_api_calls(api_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []

    for call in api_calls:
        method = (call.get("method") or "GET").upper()
        path = call.get("path") or ""
        purpose = call.get("purpose") or ""

        url = BASE_URL.rstrip("/") + path

        try:
            if method == "GET":
                r = requests.get(url, headers=JSON_HEADERS, timeout=TIMEOUT)

            elif method == "POST":
                body = call.get("body")
                if body is None:
                    body = {}

                r = requests.post(
                    url,
                    data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                    headers=JSON_HEADERS,
                    timeout=TIMEOUT
                )

            else:
                results.append({
                    "ok": False,
                    "method": method,
                    "path": path,
                    "purpose": purpose,
                    "error": "UNSUPPORTED_METHOD"
                })
                continue

            try:
                payload = r.json()
            except Exception:
                payload = {"raw_text": r.text}

            results.append({
                "ok": (r.status_code < 400),
                "status_code": r.status_code,
                "method": method,
                "path": path,
                "purpose": purpose,
                "response": payload
            })

        except Exception as e:
            results.append({
                "ok": False,
                "method": method,
                "path": path,
                "purpose": purpose,
                "error": str(e)
            })

    return results


def execute_knowledge_base_query(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    api_calls = [
        {
            "method": "POST",
            "path": "/api/knowledge-base/ask",
            "purpose": "Ask Knowledge Base Agent",
            "body": {
                "query": query,
                "top_k": top_k
            }
        }
    ]
    return execute_api_calls(api_calls)
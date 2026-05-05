from typing import Any, Dict, Optional


SUPPORTED_AGENTS = ["study_plan", "knowledge_base"]


def ok_response(
    reply_text: str,
    *,
    agent: str,
    intent: str = "unresolved",
    api_calls: Optional[list] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "ok": True,
        "reply_text": reply_text,
        "agent": agent,
        "intent": intent,
        "api_calls": api_calls or [],
        "payload": payload or {},
    }


def error_response(
    error_code: str,
    message: str,
    *,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "ok": False,
        "error": error_code,
        "message": message,
        "details": details or {},
    }
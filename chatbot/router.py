from typing import Dict, Any, List

from chatbot.extractors import (
    extract_course_id,
    extract_max_courses,
    extract_simulation_plans,
)
from chatbot.intents import detect_intent
from chatbot.executor import execute_api_calls
from chatbot.formatter import format_reply
from chatbot.input_guard import validate_user_input


def resolve_agent(intent: str) -> str:
    if intent == "knowledge_base_query":
        return "knowledge_base"
    return "study_plan"


def build_api_calls(
    intent: str,
    student_id: int,
    extracted: Dict[str, Any],
    message: str
) -> List[Dict[str, Any]]:
    calls = []

    if intent == "knowledge_base_query":
        calls.append({
            "method": "POST",
            "path": "/api/knowledge-base/ask",
            "purpose": "Ask Knowledge Base Agent",
            "body": {
                "query": message,
                "top_k": 3
            }
        })
        return calls

    if intent == "snapshot":
        calls.append({
            "method": "GET",
            "path": f"/api/student-plan/{student_id}/snapshot",
            "purpose": "Get full student snapshot"
        })

    elif intent == "credits_summary":
        calls.append({
            "method": "GET",
            "path": f"/api/student-plan/{student_id}/credits",
            "purpose": "Compute credits summary"
        })

    elif intent == "gpa_summary":
        calls.append({
            "method": "GET",
            "path": f"/api/student-plan/{student_id}/gpa",
            "purpose": "Get official GPA summary"
        })

    elif intent == "gpa_simulate":
        calls.append({
            "method": "POST",
            "path": f"/api/student-plan/{student_id}/gpa/simulate",
            "purpose": "Simulate expected GPA",
            "body": {
                "planned_courses": extracted.get("plans", [])
            }
        })

    elif intent == "eligibility_check":
        course_id = extracted.get("course_id")
        if course_id:
            calls.append({
                "method": "GET",
                "path": f"/api/student-plan/{student_id}/eligibility/{course_id}",
                "purpose": "Check eligibility for course"
            })

    elif intent == "recommendations":
        max_courses = extracted.get("max_courses") or 6
        calls.append({
            "method": "GET",
            "path": f"/api/student-plan/{student_id}/recommendations?max_courses={max_courses}",
            "purpose": "Get recommended courses for next semester"
        })

    return calls


def route_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    student_id = int(payload.get("student_id") or 0)
    language = payload.get("language") or "ar"
    message = (payload.get("message") or "").strip()

    guard_result = validate_user_input(
        message=message,
        student_id=student_id,
        language=language
    )

    if not guard_result.get("ok"):
        return {
            "agent": "input_guard",
            "student_id": student_id,
            "language": language,
            "intent": "input_error",
            "confidence": 1.0,
            "extracted": {},
            "api_calls": [],
            "api_results": [],
            "reply_text": guard_result.get("message"),
            "debug": {
                "error_code": guard_result.get("error_code"),
                "details": guard_result.get("details", {})
            }
        }

    message = guard_result.get("normalized_message", message)

    extracted = {
        "course_id": extract_course_id(message),
        "max_courses": extract_max_courses(message),
        "plans": extract_simulation_plans(message),
    }

    det = detect_intent(message)
    intent = det["intent"]
    confidence = det["confidence"]

    agent = resolve_agent(intent)

    api_calls = build_api_calls(
        intent=intent,
        student_id=student_id,
        extracted=extracted,
        message=message
    )

    api_results = execute_api_calls(api_calls) if api_calls else []

    reply_text = format_reply(
        language=language,
        agent=agent,
        intent=intent,
        extracted=extracted,
        api_results=api_results
    )

    return {
        "agent": agent,
        "student_id": student_id,
        "language": language,
        "intent": intent,
        "confidence": confidence,
        "extracted": extracted,
        "api_calls": api_calls,
        "api_results": api_results,
        "reply_text": reply_text,
        "debug": {
            "scores": det.get("scores", {}),
            "matches": det.get("matches", {}),
            "signals": det.get("signals", {}),
        }
    }
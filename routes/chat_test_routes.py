from flask import Blueprint, jsonify, request
from chatbot.intents import detect_intent
from chatbot.extractors import (
    extract_course_id,
    extract_all_course_ids,
    extract_max_courses,
    extract_simulation_plans,
)

chat_test_bp = Blueprint("chat_test", __name__)

@chat_test_bp.route("/api/chat/test/extract", methods=["POST"])
def test_extract():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()

    return jsonify({
        "status": "success",
        "data": {
            "text": text,
            "course_id": extract_course_id(text),
            "all_course_ids": extract_all_course_ids(text),
            "max_courses": extract_max_courses(text),
            "plans": extract_simulation_plans(text),
        }
    })


@chat_test_bp.route("/api/chat/test/intent", methods=["POST"])
def test_intent():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()

    out = detect_intent(text)

    return jsonify({
        "status": "success",
        "data": {
            "text": text,
            "intent": out["intent"],
            "confidence": out["confidence"],
            "signals": out["signals"],
            "scores": out["scores"],
            "matches": out["matches"],
        }
    })
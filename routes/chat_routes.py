from flask import Blueprint, jsonify, request

from chatbot.contracts import SUPPORTED_AGENTS, ok_response, error_response
from chatbot.router import route_message




chat_bp = Blueprint("chat", __name__)


# @chat_bp.route("/api/chat/message", methods=["POST"])
# def chat_message():
#     body = request.get_json(silent=True) or {}

#     session = body.get("session") or {}
#     student_id = session.get("student_id")
#     language = (session.get("language") or "ar").lower()

#     selected_agent = (body.get("selected_agent") or "study_plan").lower()
#     message = (body.get("message") or "").strip()

#     # --- Validation 
#     if selected_agent not in SUPPORTED_AGENTS:
#         out = error_response(
#             "AGENT_NOT_SUPPORTED",
#             "الوكيل المختار غير مدعوم حالياً.",
#             details={"supported_agents": SUPPORTED_AGENTS, "selected_agent": selected_agent},
#         )
#         return jsonify({"status": "error", "data": out}), 400

#     if not student_id:
#         out = error_response(
#             "MISSING_STUDENT_ID",
#             "رقم الطالب غير موجود داخل session. أرسله ضمن session.student_id.",
#         )
#         return jsonify({"status": "error", "data": out}), 400

#     if not message:
#         out = error_response(
#             "EMPTY_MESSAGE",
#             "الرسالة فارغة. اكتب سؤالك ثم أرسل.",
#         )
#         return jsonify({"status": "error", "data": out}), 400

#     if language.startswith("en"):
#         reply = (
#             f"Message received \n"
#             f"Agent: {selected_agent}\n"
#             f"Student: {student_id}\n"
#             f"Next: Stage 7.1/7.2 will detect intent and call Study Plan endpoints."
#         )
#     else:
#         reply = (
#             f"تم استلام رسالتك \n"
#             f"الوكيل المختار: {selected_agent}\n"
#             f"رقم الطالب: {student_id}\n"
#             f"سؤالك: {message}\n\n"
#             f"التالي: في 7.1 و 7.2 سنحدد نوع السؤال (Intent) ثم نربطه بخدمات Study Plan."
#         )

#     out = ok_response(
#         reply_text=reply,
#         agent=selected_agent,
#         intent="unresolved",
#         api_calls=[],
#         payload={
#             "echo": {
#                 "student_id": student_id,
#                 "language": language,
#                 "message": message,
#             }
#         },
#     )

#     return jsonify({"status": "success", "data": out})


@chat_bp.route("/api/chat/message", methods=["POST"])
def chat_message():
    body = request.get_json(silent=True) or {}

    out = route_message(body)

    return jsonify({
        "status": "success",
        "data": out
    })
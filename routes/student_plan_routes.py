# routes/student_plan_routes.py

from flask import Blueprint, jsonify, request
from services.snapshot_service import build_student_snapshot
from services.prereq_service import check_course_eligibility
from services.credits_service import compute_credits_summary
from services.gpa_service import get_gpa_summary, simulate_expected_gpa
from services.recommend_service import recommend_courses


student_plan_bp = Blueprint("student_plan", __name__)

@student_plan_bp.route("/api/student-plan/<student_id>/snapshot", methods=["GET"])
def snapshot(student_id):
    data = build_student_snapshot(student_id)
    if not data.get("ok"):
        return jsonify({"status": "error", "data": data}), 404
    return jsonify({"status": "success", "data": data})


@student_plan_bp.route("/api/student-plan/<student_id>/eligibility/<course_id>", methods=["GET"])
def eligibility(student_id, course_id):
    data = check_course_eligibility(student_id, course_id)
    if not data.get("ok"):
        return jsonify({"status": "error", "data": data}), 404
    return jsonify({"status": "success", "data": data})
    


@student_plan_bp.route("/api/student-plan/<student_id>/credits", methods=["GET"])
def credits(student_id):
    data = compute_credits_summary(student_id)
    if not data.get("ok"):
        return jsonify({"status": "error", "data": data}), 404
    return jsonify({"status": "success", "data": data})


@student_plan_bp.route("/api/student-plan/<student_id>/gpa", methods=["GET"])
def gpa(student_id):
    data = get_gpa_summary(student_id)
    if not data.get("ok"):
        return jsonify({"status": "error", "data": data}), 404
    return jsonify({"status": "success", "data": data})

# @student_plan_bp.route("/api/student-plan/<student_id>/gpa/simulate", methods=["POST"])
# def gpa_simulate(student_id):
#     body = request.get_json(silent=True) or {}
#     plans = body.get("plans") or body.get("expected") or []
#     data = simulate_expected_gpa(student_id, plans)
#     if not data.get("ok"):
#         return jsonify({"status": "error", "data": data}), 404
#     return jsonify({"status": "success", "data": data})

from flask import request, jsonify

@student_plan_bp.route("/api/student-plan/<student_id>/gpa/simulate", methods=["POST"])
def gpa_simulate(student_id):
    body = request.get_json(silent=True) or {}


    plans = (
        body.get("planned_courses")
        or body.get("plans")
        or body.get("expected")
        or []
    )

  
    normalized = []
    for item in plans:
        if not isinstance(item, dict):
            continue
        course_id = item.get("course_id") or item.get("id")
        expected_grade = item.get("expected_grade") or item.get("grade")
        if course_id and expected_grade:
            normalized.append({
                "course_id": str(course_id).strip().upper(),
                "expected_grade": str(expected_grade).strip().upper()
            })

    data = simulate_expected_gpa(student_id, normalized)

    if not data.get("ok"):
        return jsonify({"status": "error", "data": data}), 404

    return jsonify({"status": "success", "data": data})


@student_plan_bp.route("/api/student-plan/<student_id>/recommendations", methods=["GET"])
def recommendations(student_id):
    from flask import request
    max_courses = int(request.args.get("max_courses", 6))
    data = recommend_courses(student_id, max_courses=max_courses)
    if not data.get("ok"):
        return jsonify({"status": "error", "data": data}), 404
    return jsonify({"status": "success", "data": data})
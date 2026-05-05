from flask import Blueprint, jsonify, request
from firebase.firebase_config import db

test_bp = Blueprint("test", __name__)

@test_bp.route("/api/test/student/<student_id>", methods=["GET"])
def test_student(student_id):
    doc = db.collection("students").document(str(student_id)).get()
    if not doc.exists:
        return jsonify({"status": "error", "message": "Student not found", "student_id": student_id}), 404
    return jsonify({"status": "success", "data": doc.to_dict()})

@test_bp.route("/api/test/program/<program_id>", methods=["GET"])
def test_program(program_id):
    doc = db.collection("programs").document(str(program_id)).get()
    if not doc.exists:
        return jsonify({"status": "error", "message": "Program not found", "program_id": program_id}), 404
    return jsonify({"status": "success", "data": doc.to_dict()})

#  Course test: returns course doc 
@test_bp.route("/api/test/course/<course_id>", methods=["GET"])
def test_course(course_id):
    doc = db.collection("courses").document(str(course_id).upper()).get()
    if not doc.exists:
        return jsonify({"status": "error", "message": "Course not found", "course_id": course_id}), 404
    return jsonify({"status": "success", "data": doc.to_dict()})

# list courses for a specific program using program_ids array_contains
@test_bp.route("/api/test/program/<int:program_id>/courses", methods=["GET"])
def test_program_courses(program_id):
    limit = int(request.args.get("limit", 10))
    ref = db.collection("courses").where("program_ids", "array_contains", int(program_id)).limit(limit)
    docs = ref.stream()

    out = []
    for d in docs:
        row = d.to_dict() or {}
        row["_id"] = d.id
        out.append(row)

    return jsonify({
        "status": "success",
        "program_id": program_id,
        "count": len(out),
        "data": out
    })

#  check course offering for a program (course_type + prerequisites)
@test_bp.route("/api/test/course/<course_id>/offering/<int:program_id>", methods=["GET"])
def test_course_offering(course_id, program_id):
    doc = db.collection("courses").document(str(course_id).upper()).get()
    if not doc.exists:
        return jsonify({"status": "error", "message": "Course not found", "course_id": course_id}), 404

    data = doc.to_dict() or {}
    offerings = data.get("offerings", {})
    offering = offerings.get(str(program_id))

    if not offering:
        return jsonify({
            "status": "error",
            "message": "This course is not offered in this program",
            "course_id": course_id,
            "program_id": program_id,
            "program_ids_in_course": data.get("program_ids", [])
        }), 404

    return jsonify({
        "status": "success",
        "course_id": course_id,
        "program_id": program_id,
        "offering": offering
    })

@test_bp.route("/api/test/attempts/<student_id>", methods=["GET"])
def test_attempts(student_id):
    limit = int(request.args.get("limit", 5))
    ref = db.collection("students").document(str(student_id)).collection("attempts")
    docs = ref.limit(limit).stream()

    attempts = []
    for d in docs:
        row = d.to_dict() or {}
        row["_id"] = d.id
        attempts.append(row)

    return jsonify({"status": "success", "count": len(attempts), "data": attempts})

# services/credits_service.py

from services.snapshot_service import build_student_snapshot
from utils.normalize import norm_id, norm_passed


def compute_credits_summary(student_id: int | str) -> dict:
    snap = build_student_snapshot(student_id)
    if not snap.get("ok"):
        return {"ok": False, "error": snap.get("error"), "student_id": student_id}

    program = snap.get("program") or {}
    total_required_to_grad = program.get("total_credits") or 0
    elective_required_to_grad = program.get("major_elective_credits") or 0

    # index courses by course_id
    courses = snap.get("courses") or []
    course_index = {norm_id(c.get("course_id")): c for c in courses if norm_id(c.get("course_id"))}

    latest = snap.get("latest_attempts_per_course") or {}

    completed_total = 0
    completed_required = 0
    completed_elective = 0

    unknown_type_courses = []   # لو course_type = null
    missing_course_docs = []    # لو attempt موجود لكن course غير موجود في خطة البرنامج

    # نحسب من latest فقط (آخر محاولة)
    for cid, att in latest.items():
        cid = norm_id(cid)
        if not cid:
            continue

        # لازم يكون ناجح
        if not norm_passed(att.get("passed")):
            continue

        # credits:
        cdoc = course_index.get(cid)
        credits = None

        if cdoc:
            credits = cdoc.get("credits")
        if credits is None:
            credits = att.get("credits")

        try:
            credits = int(credits)
        except Exception:
            credits = 0

        completed_total += credits

        if not cdoc:
            missing_course_docs.append(cid)
            continue

        ctype = cdoc.get("course_type")  # required / elective / null
        if ctype == "required":
            completed_required += credits
        elif ctype == "elective":
            completed_elective += credits
        else:
            unknown_type_courses.append(cid)

    remaining_total = max(0, int(total_required_to_grad) - int(completed_total))
    remaining_elective = max(0, int(elective_required_to_grad) - int(completed_elective))

    # تحقق مقارنة مع student.completed_credits
    student = snap.get("student") or {}
    student_completed = student.get("completed_credits")
    student_completed_computed = student.get("completed_credits_computed")

    def safe_int(x):
        try:
            return int(x)
        except Exception:
            return None

    verify = {
        "student_completed_credits": student_completed,
        "student_completed_credits_computed": student_completed_computed,
        "engine_completed_total": completed_total,
        "match_with_student_completed": (safe_int(student_completed) == completed_total) if safe_int(student_completed) is not None else None,
        "match_with_student_completed_computed": (safe_int(student_completed_computed) == completed_total) if safe_int(student_completed_computed) is not None else None,
    }

    return {
        "ok": True,
        "student_id": snap.get("student_id"),
        "program_id": snap.get("program_id"),
        "program_name": program.get("program_name"),
        "totals": {
            "program_total_credits": total_required_to_grad,
            "program_major_elective_credits": elective_required_to_grad,
        },
        "completed": {
            "total": completed_total,
            "required": completed_required,
            "elective": completed_elective,
        },
        "remaining": {
            "total": remaining_total,
            "elective": remaining_elective,
        },
        "data_warnings": {
            "unknown_type_courses": unknown_type_courses,
            "missing_course_docs": missing_course_docs,
        },
        "verify": verify
    }

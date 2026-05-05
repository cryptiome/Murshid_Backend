# services/gpa_service.py

from services.snapshot_service import build_student_snapshot
from utils.normalize import norm_id
from utils.grading import grade_to_points, grade_to_score100


def get_gpa_summary(student_id: int | str) -> dict:
    snap = build_student_snapshot(student_id)
    if not snap.get("ok"):
        return {"ok": False, "error": snap.get("error"), "student_id": student_id}

    student = snap.get("student") or {}
    term = snap.get("term_gpa") or None
    cumulative = snap.get("cumulative_gpa") or None

    fallback = {
        "term_gpa_4": student.get("term_gpa_4"),
        "term_gpa_100": student.get("term_gpa_100"),
        "cumulative_gpa_4": student.get("cumulative_gpa_4") or student.get("gpa"),
        "cumulative_gpa_100": student.get("cumulative_gpa_100"),
    }

    return {
        "ok": True,
        "student_id": snap.get("student_id"),
        "program_id": snap.get("program_id"),
        "current_semester": snap.get("current_semester"),
        "official": {
            "term_gpa": term,               # من term_gpa/{semester}
            "cumulative_gpa": cumulative,   # من cumulative/cumulative
        },
        "fallback_from_student_doc": fallback
    }


def simulate_expected_gpa(student_id: int | str, plans: list[dict]) -> dict:
    """
    plans example:
    [
      {"course_id":"AI2001", "expected_grade":"B"},
      {"course_id":"CS2105", "expected_grade":"A"}
    ]
    """
    snap = build_student_snapshot(student_id)
    if not snap.get("ok"):
        return {"ok": False, "error": snap.get("error"), "student_id": student_id}

    student = snap.get("student") or {}
    program = snap.get("program") or {}

    # Current cumulative 
    cumulative = snap.get("cumulative_gpa") or {}
    current_cum_gpa4 = cumulative.get("cumulative_gpa_4")
    if current_cum_gpa4 is None:
        # fallback من student doc
        current_cum_gpa4 = student.get("cumulative_gpa_4") or student.get("gpa") or 0.0
    current_cum_gpa4 = float(current_cum_gpa4)

    # Completed credits (نستخدم computed لو موجود)
    completed_credits = student.get("completed_credits_computed")
    if completed_credits is None:
        completed_credits = student.get("completed_credits")
    completed_credits = int(completed_credits or 0)

    # Course index: course_id -> course normalized (credits موجودة)
    courses = snap.get("courses") or []
    course_index = {norm_id(c.get("course_id")): c for c in courses if norm_id(c.get("course_id"))}

    term_total_credits = 0
    term_total_points = 0.0
    details = []
    warnings = {
        "course_not_in_program": [],
        "missing_course_credits": [],
        "invalid_grade": [],
    }

    for item in plans or []:
        cid = norm_id(item.get("course_id"))
        exp_grade = item.get("expected_grade")

        if not cid:
            continue

        cdoc = course_index.get(cid)
        if not cdoc:
            warnings["course_not_in_program"].append(cid)
            continue

        credits = cdoc.get("credits")
        try:
            credits = int(credits)
        except Exception:
            credits = None

        if credits is None:
            warnings["missing_course_credits"].append(cid)
            continue

        gp = grade_to_points(exp_grade)
        if gp == 0.0 and str(exp_grade).strip().upper() != "F":
            # قد يكون دخل قيمة غير معروفة
            warnings["invalid_grade"].append({"course_id": cid, "expected_grade": exp_grade})

        quality_points = gp * credits

        term_total_credits += credits
        term_total_points += quality_points

        details.append({
            "course_id": cid,
            "course_name_en": cdoc.get("course_name_en"),
            "course_name_ar": cdoc.get("course_name_ar"),
            "credits": credits,
            "expected_grade": str(exp_grade).strip().upper() if exp_grade is not None else None,
            "expected_grade_points": gp,
            "expected_score_100": grade_to_score100(exp_grade),
            "quality_points": round(quality_points, 4),
        })

    # Term GPA expected
    expected_term_gpa4 = 0.0
    if term_total_credits > 0:
        expected_term_gpa4 = term_total_points / term_total_credits

    # New cumulative after term
    # cum_quality_points_current = current_gpa * completed_credits
    current_quality_points = current_cum_gpa4 * completed_credits
    new_total_credits = completed_credits + term_total_credits

    expected_cum_gpa4 = current_cum_gpa4
    if new_total_credits > 0:
        expected_cum_gpa4 = (current_quality_points + term_total_points) / new_total_credits

    return {
        "ok": True,
        "student_id": snap.get("student_id"),
        "program_id": snap.get("program_id"),
        "program_name": program.get("program_name"),
        "current": {
            "cumulative_gpa_4": round(current_cum_gpa4, 4),
            "completed_credits": completed_credits,
        },
        "simulation_input": {
            "planned_courses_count": len(details),
            "planned_total_credits": term_total_credits,
        },
        "expected": {
            "term_gpa_4": round(expected_term_gpa4, 4),
            "cumulative_gpa_4": round(expected_cum_gpa4, 4),
        },
        "delta": {
            "cumulative_gpa_4_change": round(expected_cum_gpa4 - current_cum_gpa4, 4)
        },
        "details": details,
        "warnings": warnings
    }

# services/prereq_service.py

from services.snapshot_service import build_student_snapshot
from utils.normalize import norm_id
from utils.course_graph import build_courses_index, build_dependency_graph


def check_course_eligibility(student_id: int | str, course_id: str) -> dict:
    """
    Check if student is eligible to take a course (within his program).
    Uses snapshot: passed_courses + courses (normalized per program).
    """

    sid = norm_id(student_id)
    cid = norm_id(course_id)

    snap = build_student_snapshot(sid)
    if not snap.get("ok"):
        return {"ok": False, "error": snap.get("error"), "student_id": sid}

    courses = snap.get("courses") or []
    passed = set(snap.get("passed_courses") or [])

    courses_index = build_courses_index(courses)
    graph = build_dependency_graph(courses)

    # 1) Course must belong to student's program offerings
    if cid not in courses_index:
        return {
            "ok": True,
            "student_id": snap.get("student_id"),
            "program_id": snap.get("program_id"),
            "course_id": cid,
            "eligible": False,
            "reason": "COURSE_NOT_IN_STUDENT_PROGRAM",
            "missing_prereqs": [],
            "already_passed": cid in passed,
        }

    course = courses_index[cid]

    # 2) If already passed, usually not recommended to take again
    if cid in passed:
        return {
            "ok": True,
            "student_id": snap.get("student_id"),
            "program_id": snap.get("program_id"),
            "course_id": cid,
            "course": course,
            "eligible": False,
            "reason": "ALREADY_PASSED",
            "missing_prereqs": [],
            "already_passed": True,
        }

    prereqs = graph.get(cid, [])  # prerequisites list
    missing = [p for p in prereqs if p not in passed]

    eligible = len(missing) == 0

    return {
        "ok": True,
        "student_id": snap.get("student_id"),
        "program_id": snap.get("program_id"),
        "course_id": cid,
        "course": course,
        "eligible": eligible,
        "reason": "OK" if eligible else "MISSING_PREREQUISITES",
        "prerequisites": prereqs,
        "missing_prereqs": missing,
        "already_passed": False,
        # مفيد للتوضيح: إيش اللي مع الطالب الآن
        "passed_courses_count": len(passed),
    }

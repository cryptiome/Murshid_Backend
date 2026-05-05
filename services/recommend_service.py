from services.snapshot_service import build_student_snapshot
from utils.normalize import norm_id, norm_passed, norm_int
from utils.course_graph import build_courses_index, build_dependency_graph


def _build_reverse_graph(graph: dict) -> dict:
    rev = {}
    for course, prereqs in graph.items():
        for p in prereqs or []:
            rev.setdefault(p, []).append(course)
    return rev


def recommend_courses(student_id: int | str, max_courses: int = 6) -> dict:
    snap = build_student_snapshot(student_id)
    if not snap.get("ok"):
        return {"ok": False, "error": snap.get("error"), "student_id": student_id}

    student = snap.get("student") or {}
    program = snap.get("program") or {}
    courses = snap.get("courses") or []
    passed = set(snap.get("passed_courses") or [])

    student_level = norm_int(student.get("level")) or 1
    program_id = snap.get("program_id")

    graph = build_dependency_graph(courses)
    rev = _build_reverse_graph(graph)

    def unlock_score(cid: str) -> int:
        return len(rev.get(cid, []))

    elective_required = int(program.get("major_elective_credits") or 0)

    course_index = build_courses_index(courses)
    completed_elective = 0
    for cid in passed:
        c = course_index.get(cid)
        if c and c.get("course_type") == "elective":
            try:
                completed_elective += int(c.get("credits") or 0)
            except Exception:
                pass
    remaining_elective = max(0, elective_required - completed_elective)

    eligible_pool = []
    blocked = []

    for c in courses:
        cid = norm_id(c.get("course_id"))
        if not cid:
            continue

        if cid in passed:
            continue

        clevel = norm_int(c.get("level")) or 1
        if clevel > student_level + 1:
            blocked.append({
                "course_id": cid,
                "course": c,
                "reason": "LEVEL_TOO_HIGH",
                "missing_prereqs": [],
            })
            continue

        prereqs = graph.get(cid, []) or []
        missing = [p for p in prereqs if p not in passed]
        if missing:
            blocked.append({
                "course_id": cid,
                "course": c,
                "reason": "MISSING_PREREQUISITES",
                "missing_prereqs": missing,
            })
            continue

        eligible_pool.append(c)

    def sort_key(c):
        cid = norm_id(c.get("course_id"))
        ctype = c.get("course_type")
        clevel = norm_int(c.get("level")) or 99
        type_rank = 0 if ctype == "required" else (1 if ctype == "elective" else 2)
        u = unlock_score(cid) if cid else 0
        return (type_rank, clevel, -u, cid)

    eligible_pool.sort(key=sort_key)

    recommended = []
    total_credits = 0

    recommended_max_credits = 15
    if str(student.get("status_computed")).lower() == "probation":
        recommended_max_credits = 12

    for c in eligible_pool:
        if len(recommended) >= int(max_courses):
            break

        try:
            cr = int(c.get("credits") or 0)
        except Exception:
            cr = 0

        if total_credits + cr > recommended_max_credits:
            continue

        recommended.append({
            "course_id": c.get("course_id"),
            "course_name_en": c.get("course_name_en"),
            "course_name_ar": c.get("course_name_ar"),
            "credits": c.get("credits"),
            "level": c.get("level"),
            "course_type": c.get("course_type"),
            "prerequisites": c.get("prerequisites") or [],
            "unlock_score": unlock_score(norm_id(c.get("course_id"))),
            "reason": _reason_text(c, remaining_elective)
        })
        total_credits += cr

    if remaining_elective > 0:
        has_elective = any(r["course_type"] == "elective" for r in recommended)
        if not has_elective:
            elective_candidates = [c for c in eligible_pool if c.get("course_type") == "elective"]
            for c in elective_candidates:
                cid = norm_id(c.get("course_id"))
                if any(r["course_id"] == cid for r in recommended):
                    continue
                try:
                    cr = int(c.get("credits") or 0)
                except Exception:
                    cr = 0
                if total_credits + cr > recommended_max_credits:
                    continue
                recommended.append({
                    "course_id": c.get("course_id"),
                    "course_name_en": c.get("course_name_en"),
                    "course_name_ar": c.get("course_name_ar"),
                    "credits": c.get("credits"),
                    "level": c.get("level"),
                    "course_type": c.get("course_type"),
                    "prerequisites": c.get("prerequisites") or [],
                    "unlock_score": unlock_score(cid),
                    "reason": "Elective needed (remaining elective credits)"
                })
                total_credits += cr
                break

    return {
        "ok": True,
        "student_id": snap.get("student_id"),
        "program_id": program_id,
        "program_name": program.get("program_name"),
        "student_level": student_level,
        "status": student.get("status_computed"),
        "rules": {
            "level_limit": student_level + 1,
            "recommended_max_credits": recommended_max_credits,
            "max_courses": int(max_courses)
        },
        "summary": {
            "recommended_count": len(recommended),
            "recommended_total_credits": total_credits,
            "eligible_pool_count": len(eligible_pool),
            "blocked_count": len(blocked),
            "remaining_elective_credits": remaining_elective
        },
        "recommended": recommended,
        "blocked": blocked[:40],
        "blocked_truncated": len(blocked) > 40
    }


def _reason_text(course: dict, remaining_elective: int) -> str:
    ctype = course.get("course_type")
    if ctype == "required":
        return "Required course (priority)"
    if ctype == "elective" and remaining_elective > 0:
        return "Elective course (needed to complete elective credits)"
    if ctype == "elective":
        return "Elective course"
    return "Eligible"

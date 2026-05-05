# services/snapshot_service.py

from repositories.students_repo import StudentsRepo
from repositories.programs_repo import ProgramsRepo
from repositories.courses_repo import CoursesRepo
from utils.attempts_latest import get_student_attempts_latest_per_course
from utils.normalize import norm_int, norm_passed, norm_id


def build_student_snapshot(student_id: int | str) -> dict:
    """
    Build a full snapshot for Study Plan Agent 
    Returns a dict ready for JSON response.
    """

    # 1) Student
    student = StudentsRepo.get_student(student_id)
    if not student:
        return {"ok": False, "error": "Student not found", "student_id": student_id}

    pid = norm_int(student.get("program_id"))
    if pid is None:
        return {"ok": False, "error": "Invalid program_id in student", "student_id": student_id}

    current_sem = student.get("current_semester")

    # 2) Program
    program = ProgramsRepo.get_program(pid)
    if not program:
        return {"ok": False, "error": "Program not found", "program_id": pid}

    # 3) Attempts + latest per course
    attempts = StudentsRepo.get_student_attempts(student_id)
    latest_by_course = get_student_attempts_latest_per_course(attempts)

    # 4) Passed courses set (from latest attempts only)
    passed_courses = set()
    for cid, att in latest_by_course.items():
        if norm_passed(att.get("passed")):
            passed_courses.add(norm_id(cid))

    # 5) Courses offered for this program
    raw_courses = CoursesRepo.get_courses_by_program(pid, limit=5000)

    # normalize each course to the program offering
    courses = []
    missing_offering = []
    for c in raw_courses:
        normalized = CoursesRepo.normalize_course_for_program(c, pid)

  
        if normalized.get("program_name") is None and (c.get("offerings") or {}).get(str(pid)) is None:
            missing_offering.append(c.get("course_id"))

        courses.append(normalized)

    # 6) Term GPA + Cumulative GPA 
    term_gpa = None
    if current_sem:
        term_gpa = StudentsRepo.get_term_gpa(student_id, current_sem)

    cumulative_gpa = StudentsRepo.get_cumulative_gpa(student_id)

    # 7) Build snapshot
    snapshot = {
        "ok": True,
        "student_id": norm_int(student.get("student_id")) or norm_int(student_id),
        "student": student,
        "program": program,
        "program_id": pid,
        "courses_count": len(courses),
        "courses": courses,  # normalized for this program
        "attempts_count": len(attempts),
        "attempts": attempts,
        "latest_attempts_per_course_count": len(latest_by_course),
        "latest_attempts_per_course": latest_by_course,
        "passed_courses_count": len(passed_courses),
        "passed_courses": sorted(list(passed_courses)),
        "current_semester": current_sem,
        "term_gpa": term_gpa,
        "cumulative_gpa": cumulative_gpa,
        "data_warnings": {
            "missing_offering_for_program": missing_offering  # لمتابعة صحة الداتا
        }
    }

    return snapshot

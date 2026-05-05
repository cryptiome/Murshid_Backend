# tests/quick_test_stage1.py
from repositories.students_repo import StudentsRepo
from repositories.programs_repo import ProgramsRepo
from repositories.courses_repo import CoursesRepo
from utils.attempts_latest import get_student_attempts_latest_per_course
from utils.normalize import norm_int

def run(student_id=1001, sample_course_id="HCI2011"):
    student = StudentsRepo.get_student(student_id)
    assert student, "Student not found"
    pid = norm_int(student.get("program_id"))
    print("student:", student.get("name_ar"), "| program_id:", pid, "| level:", student.get("level"))

    program = ProgramsRepo.get_program(pid)
    assert program, "Program not found"
    print("program:", program.get("program_name"), "| total_credits:", program.get("total_credits"))

    courses = CoursesRepo.get_courses_by_program(pid, limit=2000)
    print("courses_by_program:", len(courses))

    # test offering for a sample course
    offering = CoursesRepo.get_course_offering(sample_course_id, pid)
    print("offering for", sample_course_id, "in program", pid, "=>", offering)

    attempts = StudentsRepo.get_student_attempts(student_id)
    print("attempts:", len(attempts))

    latest = get_student_attempts_latest_per_course(attempts)
    print("latest_attempts_per_course:", len(latest))

 
    if latest:
        any_course = next(iter(latest.keys()))
        print("sample_latest_course:", any_course, "| semester:", latest[any_course].get("semester"))

if __name__ == "__main__":
    run(1001, "HCI2011")

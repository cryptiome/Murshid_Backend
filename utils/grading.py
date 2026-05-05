# utils/grading.py

def normalize_grade(g: str) -> str:
    if g is None:
        return ""
    return str(g).strip().upper()


GRADE_TO_POINTS = {
    "A+": 4.0,
    "A": 4.0,
    "B+": 3.5,
    "B": 3.0,
    "C+": 2.5,
    "C": 2.0,
    "D+": 1.5,
    "D": 1.0,
    "F": 0.0,
}


GRADE_TO_SCORE100 = {
    "A+": 95,
    "A": 90,
    "B+": 85,
    "B": 80,
    "C+": 75,
    "C": 70,
    "D+": 65,
    "D": 60,
    "F": 50,
}

def grade_to_points(grade: str) -> float:
    g = normalize_grade(grade)
    if g in GRADE_TO_POINTS:
        return float(GRADE_TO_POINTS[g])
    # لو المستخدم دخل رقم
    try:
        return float(g)
    except Exception:
        return 0.0

def grade_to_score100(grade: str) -> int:
    g = normalize_grade(grade)
    if g in GRADE_TO_SCORE100:
        return int(GRADE_TO_SCORE100[g])
    return 0

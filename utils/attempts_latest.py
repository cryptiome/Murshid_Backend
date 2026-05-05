# utils/attempts_latest.py
from utils.normalize import norm_id

def get_student_attempts_latest_per_course(attempts: list[dict]) -> dict:
    """
    Returns: {course_id: latest_attempt_dict}
    Uses semester string ordering as a baseline.
    """
    latest = {}

    def key(a):
        return str(a.get("semester", "")).strip()

    for a in sorted(attempts, key=key):
        cid = norm_id(a.get("course_id"))
        if not cid:
            continue
        latest[cid] = a
    return latest

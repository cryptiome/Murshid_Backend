import re
from typing import List, Dict, Optional

# Course code pattern: CS2105, AI4101, MTH1441, etc.
COURSE_RE = re.compile(r"\b[A-Z]{2,6}\d{3,4}\b")

# Grades we accept in simulation
# English: A, A-, B+, B, C+, C, D+, D, F
# Arabic: أ, ب+, ب, ج+, ج, د+, د
GRADE_RE = re.compile(r"\b(A\+?|A-|B\+?|B-|C\+?|C-|D\+?|D-|F|أ|ب\+|ب|ج\+|ج|د\+|د)\b", re.IGNORECASE)


def extract_course_id(text: str) -> Optional[str]:
    """Extract first course id from text. Example: 'هل أقدر أسجل CS2105؟' -> CS2105"""
    m = COURSE_RE.search(text or "")
    return m.group(0) if m else None


def extract_all_course_ids(text: str) -> List[str]:
    """Extract all unique course ids in order."""
    ids = COURSE_RE.findall(text or "")
    seen = set()
    out = []
    for cid in ids:
        if cid not in seen:
            out.append(cid)
            seen.add(cid)
    return out


def extract_max_courses(text: str) -> Optional[int]:
    """
    Extract a reasonable integer for max courses from text.
    Examples:
    - 'اقترح 6 مواد' -> 6
    - 'recommend 5 courses' -> 5
    """
    nums = re.findall(r"\b(\d{1,2})\b", text or "")
    if not nums:
        return None
    n = int(nums[0])
    if 1 <= n <= 12:
        return n
    return None


def normalize_grade(g: str) -> Optional[str]:
    g = (g or "").strip().upper()

    # Arabic mapping
    if g in ["أ", "ا"]:
        return "A"
    if g in ["ب+", "B+"]:
        return "B+"
    if g in ["ب", "B"]:
        return "B"
    if g in ["ج+", "C+"]:
        return "C+"
    if g in ["ج", "C"]:
        return "C"
    if g in ["د+", "D+"]:
        return "D+"
    if g in ["د", "D"]:
        return "D"
    if g in ["F"]:
        return "F"

    # English variants that may appear
    if g in ["A", "A+", "A-"]:
        return g
    if g in ["B", "B+", "B-"]:
        return g
    if g in ["C", "C+", "C-"]:
        return g
    if g in ["D", "D+", "D-"]:
        return g

    return None


def extract_simulation_plans(text: str) -> List[Dict]:
    """
    Extract simulation plans from a free text message.

    Supported patterns (simple & robust):
    1) 'A في CS2105 و B في AI2001'
    2) 'CS2105 A, AI2001 B'
    3) 'A:CS2105, B:AI2001'
    4) 'CS2105=A و AI2001=B'
    """

    t = text or ""
    course_ids = extract_all_course_ids(t)
    if not course_ids:
        return []

    plans: List[Dict] = []

    # Try: (GRADE ... COURSE)
    for cid in course_ids:
        # grade before course: "A في CS2105" / "B CS2105"
        p1 = re.compile(
        rf"(?<![A-Za-z])(?P<g>A\+?|A-|B\+?|B-|C\+?|C-|D\+?|D-|F|أ|ب\+|ب|ج\+|ج|د\+|د)\b\s*(?:في|for|:|=|\-)?\s*{cid}\b",
        re.IGNORECASE
    )
        m1 = p1.search(t)

        # course before grade: "CS2105 A" / "CS2105=B"
        p2 = re.compile(rf"\b{cid}\s*(?:=|:|\-)?\s*(?P<g>A\+?|A-|B\+?|B-|C\+?|C-|D\+?|D-|F|أ|ب\+|ب|ج\+|ج|د\+|د)\b", re.IGNORECASE)
        m2 = p2.search(t)

        g_raw = None
        if m1:
            g_raw = m1.group("g")
        elif m2:
            g_raw = m2.group("g")

        if g_raw:
            g = normalize_grade(g_raw)
            if g:
                plans.append({"course_id": cid, "expected_grade": g})

    # Remove duplicates by course_id 
    seen = set()
    uniq = []
    for p in plans:
        if p["course_id"] in seen:
            continue
        uniq.append(p)
        seen.add(p["course_id"])

    return uniq

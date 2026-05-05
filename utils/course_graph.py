# utils/course_graph.py

from utils.normalize import norm_id

def build_courses_index(courses: list[dict]) -> dict:
    """course_id -> course dict (normalized for the program)"""
    idx = {}
    for c in courses:
        cid = norm_id(c.get("course_id"))
        if cid:
            idx[cid] = c
    return idx

def build_dependency_graph(courses: list[dict]) -> dict:
    """course_id -> prerequisites list"""
    g = {}
    for c in courses:
        cid = norm_id(c.get("course_id"))
        if not cid:
            continue
        prereqs = c.get("prerequisites") or []
        prereqs = [norm_id(x) for x in prereqs if norm_id(x)]
        g[cid] = prereqs
    return g

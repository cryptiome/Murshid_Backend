# repositories/courses_repo.py
from firebase.firebase_config import db
from utils.normalize import norm_id, norm_int

class CoursesRepo:
    @staticmethod
    def get_course(course_id):
        doc = db.collection("courses").document(norm_id(course_id)).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def get_courses_by_program(program_id, limit=None):
        pid = norm_int(program_id)
        if pid is None:
            return []

        q = db.collection("courses").where("program_ids", "array_contains", pid)
        if limit:
            q = q.limit(int(limit))

        docs = q.stream()
        rows = []
        for d in docs:
            row = d.to_dict() or {}
            row["_id"] = d.id
            rows.append(row)
        return rows

    @staticmethod
    def get_course_offering(course_id, program_id):
        """
        Returns offering map for that program:
        {
          course_type, prerequisites, program_name, ...
        }
        """
        course = CoursesRepo.get_course(course_id)
        if not course:
            return None

        pid = norm_int(program_id)
        if pid is None:
            return None

        offerings = course.get("offerings") or {}
        # offerings keys are strings: "1", "3", "5"...
        off = offerings.get(str(pid))
        return off  # may be None

    @staticmethod
    def normalize_course_for_program(course_doc: dict, program_id):
        """
        Returns unified view for services:
        {
          course_id, course_name_ar, course_name_en, credits, level,
          program_id, program_name,
          course_type, prerequisites
        }
        """
        pid = norm_int(program_id)
        offerings = (course_doc.get("offerings") or {})
        off = offerings.get(str(pid)) or {}

        return {
            "course_id": course_doc.get("course_id"),
            "course_name_ar": course_doc.get("course_name_ar"),
            "course_name_en": course_doc.get("course_name_en"),
            "credits": course_doc.get("credits"),
            "level": course_doc.get("level"),
            "program_id": pid,
            "program_name": off.get("program_name"),
            "course_type": off.get("course_type"),
            "prerequisites": off.get("prerequisites") or [],
        }

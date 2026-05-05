# repositories/students_repo.py
from firebase.firebase_config import db
from utils.normalize import norm_id

class StudentsRepo:
    @staticmethod
    def get_student(student_id):
        doc = db.collection("students").document(norm_id(student_id)).get()
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def get_student_attempts(student_id, limit=None):
        ref = db.collection("students").document(norm_id(student_id)).collection("attempts")
        query = ref.limit(int(limit)) if limit else ref
        docs = query.stream()

        attempts = []
        for d in docs:
            row = d.to_dict() or {}
            row["_id"] = d.id
            attempts.append(row)
        return attempts

    @staticmethod
    def get_term_gpa(student_id, semester):
        doc = (
            db.collection("students")
            .document(norm_id(student_id))
            .collection("term_gpa")
            .document(str(semester))
            .get()
        )
        return doc.to_dict() if doc.exists else None

    @staticmethod
    def get_cumulative_gpa(student_id):
        doc = (
            db.collection("students")
            .document(norm_id(student_id))
            .collection("cumulative")
            .document("cumulative")
            .get()
        )
        return doc.to_dict() if doc.exists else None

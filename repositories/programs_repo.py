# repositories/programs_repo.py
from firebase.firebase_config import db
from utils.normalize import norm_id

class ProgramsRepo:
    @staticmethod
    def get_program(program_id):
        doc = db.collection("programs").document(norm_id(program_id)).get()
        return doc.to_dict() if doc.exists else None

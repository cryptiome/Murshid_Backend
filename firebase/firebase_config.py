import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()


SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")

def init_firestore():
    """
    Initialize Firebase Admin SDK and return Firestore client.
    Safe to call multiple times.
    """
    if not firebase_admin._apps:
        if not os.path.exists(SERVICE_ACCOUNT_PATH):
            raise FileNotFoundError(
                f"serviceAccountKey.json not found at: {SERVICE_ACCOUNT_PATH}\n"
                f"Set SERVICE_ACCOUNT_PATH in .env or put the file in project root."
            )
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)

    return firestore.client()

db = init_firestore()
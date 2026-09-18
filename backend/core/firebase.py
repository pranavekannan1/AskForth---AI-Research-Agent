import json
import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
firebase_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()

if firebase_json:
    cred = credentials.Certificate(json.loads(firebase_json))
elif firebase_path:
    cred = credentials.Certificate(firebase_path)
else:
    raise RuntimeError(
        "Firebase credentials are not configured. Set "
        "FIREBASE_SERVICE_ACCOUNT_JSON or FIREBASE_SERVICE_ACCOUNT_PATH in backend/.env."
    )

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token: str):
    return auth.verify_id_token(id_token)


def resolve_password_reset_email(identifier: str) -> str:
    value = identifier.strip()
    if "@" in value:
        return value

    user = auth.get_user(value)
    if not user.email:
        raise ValueError("Firebase user does not have an email address")

    return user.email

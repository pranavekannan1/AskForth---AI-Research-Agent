import json
import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import auth, credentials


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Load local .env if it exists
load_dotenv(BACKEND_DIR / ".env")


# ---------------------------------------------------------
# Firebase credentials
# ---------------------------------------------------------

firebase_json = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_JSON",
    ""
).strip()

firebase_path = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    ""
).strip()


def load_firebase_credentials():
    """
    Load Firebase Admin credentials.

    Priority:
    1. FIREBASE_SERVICE_ACCOUNT_JSON
       Used by Render/production.

    2. FIREBASE_SERVICE_ACCOUNT_PATH
       Used for local development.
    """

    # -----------------------------------------------------
    # Production / Render
    # -----------------------------------------------------

    if firebase_json:
        try:
            service_account = json.loads(firebase_json)

            return credentials.Certificate(service_account)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON contains invalid JSON."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load Firebase JSON credentials: {exc}"
            ) from exc

    # -----------------------------------------------------
    # Local development
    # -----------------------------------------------------

    if firebase_path:
        path = Path(firebase_path)

        # If a relative path is supplied, make it relative
        # to the backend directory.
        if not path.is_absolute():
            path = BACKEND_DIR / path

        if not path.exists():
            raise RuntimeError(
                f"Firebase service-account file not found: {path}"
            )

        try:
            return credentials.Certificate(str(path))

        except Exception as exc:
            raise RuntimeError(
                f"Failed to load Firebase service-account file: {exc}"
            ) from exc

    # -----------------------------------------------------
    # Nothing configured
    # -----------------------------------------------------

    raise RuntimeError(
        "Firebase credentials are not configured. "
        "Set FIREBASE_SERVICE_ACCOUNT_JSON for Render "
        "or FIREBASE_SERVICE_ACCOUNT_PATH for local development."
    )


# ---------------------------------------------------------
# Initialize Firebase
# ---------------------------------------------------------

if not firebase_admin._apps:
    firebase_credential = load_firebase_credentials()

    firebase_admin.initialize_app(
        firebase_credential
    )


# ---------------------------------------------------------
# Firebase token verification
# ---------------------------------------------------------

def verify_firebase_token(id_token: str):
    """
    Verify a Firebase ID token and return decoded user data.
    """

    return auth.verify_id_token(id_token)


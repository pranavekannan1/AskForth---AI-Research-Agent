from fastapi import Header, HTTPException

from core.firebase import verify_firebase_token


def get_current_user(authorization: str | None = Header(default=None)):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

    id_token = authorization[len("Bearer "):].strip()
    if not id_token:
        raise HTTPException(
            status_code=401,
            detail="Firebase ID token is missing",
        )

    try:
        return verify_firebase_token(id_token)
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Firebase token",
        ) from exc

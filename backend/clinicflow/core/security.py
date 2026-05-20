import base64
import hashlib
import hmac
import os
import secrets


SESSION_SECRET = os.getenv("SESSION_SECRET", "clinicflow-dev-secret-change-me")
SESSION_COOKIE = "clinicflow_session"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"{salt}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash or "$" not in password_hash:
        return False
    salt, stored = password_hash.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return hmac.compare_digest(base64.b64encode(digest).decode(), stored)


def sign_session(doctor_id: int) -> str:
    value = str(doctor_id)
    signature = hmac.new(SESSION_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{signature}"


def read_session(value: str | None) -> int | None:
    if not value or "." not in value:
        return None
    doctor_id, signature = value.split(".", 1)
    expected = hmac.new(SESSION_SECRET.encode(), doctor_id.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    return int(doctor_id) if doctor_id.isdigit() else None

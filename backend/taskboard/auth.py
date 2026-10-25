import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, Request

from .db import db

JWT_SECRET = os.environ["JWT_SECRET"]
TOKEN_DAYS = 7
MAX_FAILURES = 8
WINDOW_SECONDS = 15 * 60
_failures: dict[str, list[float]] = defaultdict(list)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def sign(user: dict) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=TOKEN_DAYS)
    return jwt.encode({"id": user["id"], "email": user["email"], "name": user["name"], "exp": exp}, JWT_SECRET, algorithm="HS256")


def client_key(request: Request, email: str) -> str:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "")
    return f"{ip}|{email}"


def check_throttle(key: str):
    cutoff = time.time() - WINDOW_SECONDS
    _failures[key] = [t for t in _failures[key] if t > cutoff]
    if len(_failures[key]) >= MAX_FAILURES:
        raise HTTPException(429, "Too many failed sign-in attempts. Please wait 15 minutes and try again.")


def record_failure(key: str):
    _failures[key].append(time.time())


def clear_failures(key: str):
    _failures.pop(key, None)


async def current_user(request: Request) -> dict:
    raw = request.headers.get("authorization", "")
    try:
        if not raw.startswith("Bearer "):
            raise ValueError
        claims = jwt.decode(raw[7:], JWT_SECRET, algorithms=["HS256"])
    except (ValueError, jwt.PyJWTError):
        raise HTTPException(401, "Please sign in to continue.")
    user = await db.users.find_one({"_id": claims.get("id")}, {"password_hash": 0})
    if not user:
        raise HTTPException(401, "Please sign in to continue.")
    return {"id": user["_id"], "name": user["name"], "email": user["email"]}

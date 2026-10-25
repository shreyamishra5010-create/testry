import asyncio
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


async def hash_password(password: str) -> str:
    return (await asyncio.to_thread(bcrypt.hashpw, password.encode(), bcrypt.gensalt())).decode()


async def check_password(password: str, hashed: str) -> bool:
    return await asyncio.to_thread(bcrypt.checkpw, password.encode(), hashed.encode())


def sign(user: dict) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=TOKEN_DAYS)
    return jwt.encode({"id": user["id"], "email": user["email"], "name": user["name"], "exp": exp}, JWT_SECRET, algorithm="HS256")


def throttle_keys(request: Request, email: str) -> list[str]:
    # Per-account limit can't be dodged by spoofing headers; per-IP uses the proxy-appended (right-most) hop.
    hops = [h.strip() for h in request.headers.get("x-forwarded-for", "").split(",") if h.strip()]
    ip = hops[-1] if hops else (request.client.host if request.client else "")
    return [f"email|{email}", f"ip|{ip}|{email}"]


def _recent(key: str) -> list[float]:
    cutoff = time.time() - WINDOW_SECONDS
    hits = [t for t in _failures.get(key, []) if t > cutoff]
    if hits:
        _failures[key] = hits
    else:
        _failures.pop(key, None)
    return hits


def check_throttle(keys: list[str]):
    if any(len(_recent(k)) >= MAX_FAILURES for k in keys):
        raise HTTPException(429, "Too many failed sign-in attempts. Please wait 15 minutes and try again.")


def record_failure(keys: list[str]):
    for k in keys:
        _failures[k].append(time.time())
    if len(_failures) > 5000:
        for k in list(_failures):
            _recent(k)


def reserve_attempt(keys: list[str]):
    """Check and count an attempt atomically (no await in between), so parallel bursts can't slip through."""
    check_throttle(keys)
    record_failure(keys)


def clear_failures(keys: list[str]):
    for k in keys:
        _failures.pop(k, None)


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

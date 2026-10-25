import re

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

from ..auth import check_password, check_throttle, clear_failures, client_key, current_user, hash_password, record_failure, sign
from ..db import db, next_id, now

router = APIRouter()
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def text(body: dict, key: str) -> str:
    value = body.get(key)
    return "" if value is None else str(value)


@router.post("/auth/register")
async def register(body: dict = Body(default_factory=dict)):
    name, email, password = text(body, "name").strip(), text(body, "email").strip().lower(), text(body, "password")
    if not name or not EMAIL.match(email) or len(password) < 8:
        raise HTTPException(400, "Name, a valid email, and an 8-character password are required.")
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "An account with that email already exists.")
    user_id = await next_id("users")
    try:
        await db.users.insert_one({"_id": user_id, "name": name, "email": email, "password_hash": hash_password(password), "created_at": now()})
    except DuplicateKeyError:
        raise HTTPException(409, "An account with that email already exists.")
    user = {"id": user_id, "name": name, "email": email}
    return JSONResponse({"token": sign(user), "user": user}, status_code=201)


@router.post("/auth/login")
async def login(request: Request, body: dict = Body(default_factory=dict)):
    email = text(body, "email").strip().lower()
    key = client_key(request, email)
    check_throttle(key)
    doc = await db.users.find_one({"email": email})
    if not doc or not check_password(text(body, "password"), doc["password_hash"]):
        record_failure(key)
        raise HTTPException(401, "Email or password is incorrect.")
    clear_failures(key)
    user = {"id": doc["_id"], "name": doc["name"], "email": doc["email"]}
    return {"token": sign(user), "user": user}


@router.get("/me")
async def me(user: dict = Depends(current_user)):
    return {"user": user}

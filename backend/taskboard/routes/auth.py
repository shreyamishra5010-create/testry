import re

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

from ..auth import check_password, clear_failures, current_user, hash_password, reserve_attempt, sign, throttle_keys
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
        await db.users.insert_one({"_id": user_id, "name": name, "email": email, "password_hash": await hash_password(password), "created_at": now()})
    except DuplicateKeyError:
        raise HTTPException(409, "An account with that email already exists.")
    user = {"id": user_id, "name": name, "email": email}
    return JSONResponse({"token": sign(user), "user": user}, status_code=201)


@router.post("/auth/login")
async def login(request: Request, body: dict = Body(default_factory=dict)):
    email = text(body, "email").strip().lower()
    keys = throttle_keys(request, email)
    reserve_attempt(keys)
    doc = await db.users.find_one({"email": email})
    if not doc or not await check_password(text(body, "password"), doc["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect.")
    clear_failures(keys)
    user = {"id": doc["_id"], "name": doc["name"], "email": doc["email"]}
    return {"token": sign(user), "user": user}


@router.get("/me")
async def me(user: dict = Depends(current_user)):
    return {"user": user}

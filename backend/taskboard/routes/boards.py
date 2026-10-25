from datetime import date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..access import board_payload, delete_tasks, log_activity, membership, owner_of, to_int
from ..auth import current_user
from ..db import db, next_id, now, pub

router = APIRouter(prefix="/boards")
DEFAULT_COLUMNS = [("To Do", "#0052CC"), ("In Progress", "#FFAB00"), ("Done", "#00875A")]


def clean(body: dict, key: str) -> str:
    return str(body.get(key) or "").strip()


@router.get("")
async def list_boards(user: dict = Depends(current_user)):
    links = {m["board_id"]: m["role"] async for m in db.board_members.find({"user_id": user["id"]})}
    today = date.today().isoformat()
    week = (date.today() + timedelta(days=7)).isoformat()
    boards = [b async for b in db.boards.find({"_id": {"$in": list(links)}}).sort("created_at", -1)]
    ids = [b["_id"] for b in boards]
    group = lambda match: db[match[0]].aggregate([{"$match": {"board_id": {"$in": ids}, **match[1]}}, {"$group": {"_id": "$board_id", "n": {"$sum": 1}}}])
    tasks = {r["_id"]: r["n"] async for r in group(("tasks", {}))}
    due = {r["_id"]: r["n"] async for r in group(("tasks", {"due_date": {"$gte": today, "$lte": week}}))}
    members = {r["_id"]: r["n"] async for r in group(("board_members", {}))}
    owners = {u["_id"]: u["name"] async for u in db.users.find({"_id": {"$in": [b["owner_id"] for b in boards]}}, {"name": 1})}
    return [{**pub(b), "owner_name": owners.get(b["owner_id"]), "role": links[b["_id"]], "task_count": tasks.get(b["_id"], 0),
             "due_soon": due.get(b["_id"], 0), "member_count": members.get(b["_id"], 0)} for b in boards]


@router.post("")
async def create_board(body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    name = clean(body, "name")
    if not name:
        raise HTTPException(400, "Board name is required.")
    board_id = await next_id("boards")
    await db.boards.insert_one({"_id": board_id, "name": name, "description": str(body.get("description") or ""), "owner_id": user["id"], "created_at": now()})
    await db.board_members.insert_one({"board_id": board_id, "user_id": user["id"], "role": "owner"})
    for i, (col, color) in enumerate(DEFAULT_COLUMNS):
        await db.columns.insert_one({"_id": await next_id("columns"), "board_id": board_id, "name": col, "position": i, "color": color})
    return JSONResponse(await board_payload(board_id), status_code=201)


@router.get("/{board_id}")
async def get_board(board_id: str, user: dict = Depends(current_user)):
    b = await membership(to_int(board_id), user["id"])
    return await board_payload(b["id"])


@router.patch("/{board_id}")
async def update_board(board_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    b = await owner_of(to_int(board_id), user["id"], "edit it")
    name = b["name"] if "name" not in body else clean(body, "name")
    if not name:
        raise HTTPException(400, "Board name is required.")
    description = b["description"] if "description" not in body else str(body.get("description") or "")
    await db.boards.update_one({"_id": b["id"]}, {"$set": {"name": name, "description": description}})
    return await board_payload(b["id"])


@router.delete("/{board_id}")
async def delete_board(board_id: str, user: dict = Depends(current_user)):
    b = await owner_of(to_int(board_id), user["id"], "delete it")
    await delete_tasks({"board_id": b["id"]})
    await db.columns.delete_many({"board_id": b["id"]})
    await db.board_members.delete_many({"board_id": b["id"]})
    await db.activity.delete_many({"board_id": b["id"]})
    await db.boards.delete_one({"_id": b["id"]})
    return {"ok": True}


@router.post("/{board_id}/members")
async def add_member(board_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    b = await owner_of(to_int(board_id), user["id"], "manage members")
    invitee = await db.users.find_one({"email": clean(body, "email").lower()})
    if not invitee:
        raise HTTPException(404, "No registered user found with that email.")
    await db.board_members.update_one({"board_id": b["id"], "user_id": invitee["_id"]},
                                      {"$setOnInsert": {"role": "member"}}, upsert=True)
    return await board_payload(b["id"])


@router.delete("/{board_id}/members/{user_id}")
async def remove_member(board_id: str, user_id: str, user: dict = Depends(current_user)):
    b = await owner_of(to_int(board_id), user["id"], "manage members")
    target = to_int(user_id)
    if target == b["owner_id"]:
        raise HTTPException(400, "The board owner cannot be removed.")
    await db.tasks.update_many({"board_id": b["id"], "assignee_id": target}, {"$set": {"assignee_id": None}})
    await db.board_members.delete_one({"board_id": b["id"], "user_id": target})
    return await board_payload(b["id"])


@router.post("/{board_id}/columns")
async def add_column(board_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    b = await membership(to_int(board_id), user["id"])
    name = clean(body, "name")
    if not name:
        raise HTTPException(400, "Column name is required.")
    last = await db.columns.find_one({"board_id": b["id"]}, sort=[("position", -1)])
    col = {"_id": await next_id("columns"), "board_id": b["id"], "name": name,
           "position": (last["position"] + 1) if last else 0, "color": body.get("color") or "#6554C0"}
    await db.columns.insert_one(col)
    await log_activity(b["id"], user["id"], "column.added", f'added column "{name}"')
    return JSONResponse(pub(col), status_code=201)


@router.get("/{board_id}/activity")
async def activity(board_id: str, limit: str | None = Query(None), user: dict = Depends(current_user)):
    b = await membership(to_int(board_id), user["id"])
    try:
        n = 50 if limit is None else min(max(int(float(limit)), 1), 200)
    except ValueError:
        n = 50
    items = [a async for a in db.activity.find({"board_id": b["id"]}).sort([("created_at", -1), ("_id", -1)]).limit(n)]
    users = {u["_id"]: u["name"] async for u in db.users.find({"_id": {"$in": list({a["user_id"] for a in items})}}, {"name": 1})}
    return [{"id": a["_id"], "action": a["action"], "message": a["message"], "created_at": a["created_at"],
             "user_id": a["user_id"], "user_name": users.get(a["user_id"], "Former user")} for a in items]

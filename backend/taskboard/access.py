from fastapi import HTTPException
from pymongo import UpdateOne

from .db import db, next_id, now, pub


def to_int(value, status: int = 404, message: str = "Not found."):
    try:
        if isinstance(value, bool):
            raise ValueError
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise HTTPException(status, message)


async def membership(board_id: int, user_id: int) -> dict:
    board = await db.boards.find_one({"_id": board_id})
    if not board:
        raise HTTPException(404, "Board not found.")
    member = await db.board_members.find_one({"board_id": board_id, "user_id": user_id})
    if not member:
        raise HTTPException(403, "You do not have access to this board.")
    return {**pub(board), "role": member["role"]}


async def owner_of(board_id: int, user_id: int, action: str) -> dict:
    board = await membership(board_id, user_id)
    if board["owner_id"] != user_id:
        raise HTTPException(403, f"Only the board owner can {action}.")
    return board


async def load_or_404(collection: str, raw_id) -> dict:
    doc = await db[collection].find_one({"_id": to_int(raw_id)})
    if not doc:
        raise HTTPException(404, "Not found.")
    return pub(doc)


async def names(user_ids) -> dict:
    ids = list({u for u in user_ids if u is not None})
    return {u["_id"]: u["name"] async for u in db.users.find({"_id": {"$in": ids}}, {"name": 1})}


async def board_payload(board_id: int) -> dict:
    board = pub(await db.boards.find_one({"_id": board_id}))
    columns = [pub(c) async for c in db.columns.find({"board_id": board_id}).sort([("position", 1), ("_id", 1)])]
    tasks = [pub(t) async for t in db.tasks.find({"board_id": board_id}).sort([("position", 1), ("_id", 1)])]
    counts = {r["_id"]: r["n"] async for r in db.comments.aggregate([
        {"$match": {"task_id": {"$in": [t["id"] for t in tasks]}}}, {"$group": {"_id": "$task_id", "n": {"$sum": 1}}}])}
    links = [m async for m in db.board_members.find({"board_id": board_id})]
    users = {u["_id"]: u async for u in db.users.find({"_id": {"$in": [m["user_id"] for m in links]}}, {"password_hash": 0})}
    who = await names([board["owner_id"], *[t["assignee_id"] for t in tasks]])
    for t in tasks:
        t["assignee_name"] = who.get(t["assignee_id"])
        t["comment_count"] = counts.get(t["id"], 0)
    for c in columns:
        c["tasks"] = [t for t in tasks if t["column_id"] == c["id"]]
    members = [{"id": m["user_id"], "name": users[m["user_id"]]["name"], "email": users[m["user_id"]]["email"], "role": m["role"]}
               for m in links if m["user_id"] in users]
    members.sort(key=lambda m: (m["role"] != "owner", m["name"]))
    return {**board, "owner_name": who.get(board["owner_id"]), "columns": columns, "members": members}


async def renumber(collection: str, query: dict):
    ids = [d["_id"] async for d in db[collection].find(query, {"_id": 1}).sort([("position", 1), ("_id", 1)])]
    await set_positions(collection, ids)


async def set_positions(collection: str, ids: list):
    if ids:
        await db[collection].bulk_write([UpdateOne({"_id": i}, {"$set": {"position": p}}) for p, i in enumerate(ids)])


async def place_task(task: dict, column_id: int, index=None):
    """Insert the task at `index` in the target column and renumber both columns densely."""
    siblings = [d["_id"] async for d in db.tasks.find({"column_id": column_id, "_id": {"$ne": task["id"]}}, {"_id": 1}).sort([("position", 1), ("_id", 1)])]
    at = max(0, min(index, len(siblings))) if isinstance(index, int) else len(siblings)
    siblings.insert(at, task["id"])
    await db.tasks.update_one({"_id": task["id"]}, {"$set": {"column_id": column_id, "updated_at": now()}})
    await set_positions("tasks", siblings)
    if task["column_id"] != column_id:
        await renumber("tasks", {"column_id": task["column_id"]})


async def log_activity(board_id: int, user_id: int, action: str, message: str):
    await db.activity.insert_one({"_id": await next_id("activity"), "board_id": board_id, "user_id": user_id,
                                  "action": action, "message": message, "created_at": now()})


async def column_name(column_id: int):
    col = await db.columns.find_one({"_id": column_id}, {"name": 1})
    return col["name"] if col else None


async def delete_tasks(query: dict) -> int:
    ids = [t["_id"] async for t in db.tasks.find(query, {"_id": 1})]
    if ids:
        await db.comments.delete_many({"task_id": {"$in": ids}})
        await db.tasks.delete_many({"_id": {"$in": ids}})
    return len(ids)

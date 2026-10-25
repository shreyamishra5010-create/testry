import re

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..access import column_name, load_or_404, log_activity, membership, place_task, to_int
from ..auth import current_user
from ..db import db, next_id, now, pub

router = APIRouter()
PRIORITIES = {"low", "medium", "high"}
EDITABLE = {"title": "title", "description": "description", "priority": "priority", "due_date": "due date", "assignee_id": "assignee"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def norm(v):
    return None if v in ("", None) else str(v)


async def column_on_board(column_id, board_id: int) -> dict:
    col = await db.columns.find_one({"_id": to_int(column_id, 400, "That column does not belong to this board."), "board_id": board_id})
    if not col:
        raise HTTPException(400, "That column does not belong to this board.")
    return pub(col)


async def valid_assignee(raw, board_id: int):
    if raw in (None, ""):
        return None
    assignee = to_int(raw, 400, "The assignee must be a member of this board.")
    if not await db.board_members.find_one({"board_id": board_id, "user_id": assignee}):
        raise HTTPException(400, "The assignee must be a member of this board.")
    return assignee


def valid_fields(body: dict):
    if "title" in body and not str(body.get("title") or "").strip():
        raise HTTPException(400, "Task title is required.")
    if "priority" in body and body.get("priority") not in PRIORITIES:
        raise HTTPException(400, "Priority must be low, medium, or high.")
    if body.get("due_date") and not DATE.match(str(body["due_date"])):
        raise HTTPException(400, "Due date must be YYYY-MM-DD.")


async def task_row(task_id: int) -> dict:
    t = pub(await db.tasks.find_one({"_id": task_id}))
    who = await db.users.find_one({"_id": t["assignee_id"]}, {"name": 1}) if t["assignee_id"] else None
    return {**t, "assignee_name": who["name"] if who else None}


async def task_for(task_id: str, user: dict) -> dict:
    t = await load_or_404("tasks", task_id)
    await membership(t["board_id"], user["id"])
    return t


@router.post("/boards/{board_id}/tasks")
async def create_task(board_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    b = await membership(to_int(board_id), user["id"])
    if not str(body.get("title") or "").strip():
        raise HTTPException(400, "Task title is required.")
    valid_fields(body)
    col = await column_on_board(body.get("column_id"), b["id"])
    assignee = await valid_assignee(body.get("assignee_id"), b["id"])
    last = await db.tasks.find_one({"column_id": col["id"]}, sort=[("position", -1)])
    title = str(body["title"]).strip()
    task_id = await next_id("tasks")
    await db.tasks.insert_one({"_id": task_id, "board_id": b["id"], "column_id": col["id"], "title": title,
                               "description": str(body.get("description") or ""), "priority": body.get("priority") or "medium",
                               "due_date": body.get("due_date") or None, "assignee_id": assignee,
                               "position": (last["position"] + 1) if last else 0, "created_by": user["id"],
                               "created_at": now(), "updated_at": now()})
    await log_activity(b["id"], user["id"], "task.created", f'created "{title}" in {col["name"]}')
    return JSONResponse(await task_row(task_id), status_code=201)


@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    t = await task_for(task_id, user)
    valid_fields(body)
    pick = lambda k: body[k] if k in body else t[k]
    assignee = await valid_assignee(body["assignee_id"], t["board_id"]) if "assignee_id" in body else t["assignee_id"]
    moving = body.get("column_id") is not None and to_int(body["column_id"], 400, "That column does not belong to this board.") != t["column_id"]
    col = await column_on_board(body["column_id"], t["board_id"]) if moving else None
    title = str(pick("title")).strip()
    after = {"title": title, "description": pick("description") or "", "priority": pick("priority"),
             "due_date": pick("due_date") or None, "assignee_id": assignee}
    await db.tasks.update_one({"_id": t["id"]}, {"$set": {**after, "updated_at": now()}})
    changed = [k for k in EDITABLE if k in body and norm(after[k]) != norm(t[k])]
    if changed:
        await log_activity(t["board_id"], user["id"], "task.updated", f'updated {", ".join(EDITABLE[k] for k in changed)} on "{title}"')
    if moving:
        await place_task(t, col["id"])
        await log_activity(t["board_id"], user["id"], "task.moved", f'moved "{title}" from {await column_name(t["column_id"])} to {col["name"]}')
    return await task_row(t["id"])


@router.patch("/tasks/{task_id}/move")
async def move_task(task_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    t = await task_for(task_id, user)
    col = await column_on_board(body.get("column_id"), t["board_id"])
    raw = body.get("position")
    index = raw if isinstance(raw, int) and not isinstance(raw, bool) else None
    if isinstance(raw, (float, str)) and not isinstance(raw, bool):
        try:
            value = float(raw)
            index = int(value) if value.is_integer() else None
        except ValueError:
            index = None
    origin = await column_name(t["column_id"])
    await place_task(t, col["id"], index)
    moved = await db.tasks.find_one({"_id": t["id"]}, {"position": 1})
    if col["id"] != t["column_id"]:
        await log_activity(t["board_id"], user["id"], "task.moved", f'moved "{t["title"]}" from {origin} to {col["name"]}')
    elif moved["position"] != t["position"]:
        await log_activity(t["board_id"], user["id"], "task.reordered", f'reordered "{t["title"]}" within {col["name"]}')
    cols = list({t["column_id"], col["id"]})
    return [{"id": d["_id"], "column_id": d["column_id"], "position": d["position"]}
            async for d in db.tasks.find({"column_id": {"$in": cols}}).sort([("column_id", 1), ("position", 1)])]


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(current_user)):
    t = await task_for(task_id, user)
    await db.comments.delete_many({"task_id": t["id"]})
    await db.tasks.delete_one({"_id": t["id"]})
    await log_activity(t["board_id"], user["id"], "task.deleted", f'deleted "{t["title"]}" from {await column_name(t["column_id"])}')
    return {"ok": True}


@router.get("/tasks/{task_id}/comments")
async def list_comments(task_id: str, user: dict = Depends(current_user)):
    t = await task_for(task_id, user)
    items = [c async for c in db.comments.find({"task_id": t["id"]}).sort([("created_at", 1), ("_id", 1)])]
    users = {u["_id"]: u["name"] async for u in db.users.find({"_id": {"$in": list({c["user_id"] for c in items})}}, {"name": 1})}
    return [{**pub(c), "author_name": users.get(c["user_id"], "Former user")} for c in items]


@router.post("/tasks/{task_id}/comments")
async def add_comment(task_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    t = await task_for(task_id, user)
    text = str(body.get("body") or "").strip()
    if not text:
        raise HTTPException(400, "Comment cannot be empty.")
    comment = {"_id": await next_id("comments"), "task_id": t["id"], "user_id": user["id"], "body": text, "created_at": now()}
    await db.comments.insert_one(comment)
    await log_activity(t["board_id"], user["id"], "comment.added", f'commented on "{t["title"]}"')
    return JSONResponse({**pub(comment), "author_name": user["name"]}, status_code=201)


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user: dict = Depends(current_user)):
    c = await load_or_404("comments", comment_id)
    if c["user_id"] != user["id"]:
        raise HTTPException(403, "You can only delete your own comments.")
    await db.comments.delete_one({"_id": c["id"]})
    return {"ok": True}

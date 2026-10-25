from fastapi import APIRouter, Body, Depends, HTTPException

from ..access import delete_tasks, load_or_404, log_activity, membership, renumber, set_positions
from ..auth import current_user
from ..db import db

router = APIRouter(prefix="/columns")


@router.patch("/{column_id}")
async def rename_column(column_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    c = await load_or_404("columns", column_id)
    await membership(c["board_id"], user["id"])
    name = str(body.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Column name is required.")
    await db.columns.update_one({"_id": c["id"]}, {"$set": {"name": name}})
    if name != c["name"]:
        await log_activity(c["board_id"], user["id"], "column.renamed", f'renamed column "{c["name"]}" to "{name}"')
    return {**c, "name": name}


@router.patch("/{column_id}/move")
async def move_column(column_id: str, body: dict = Body(default_factory=dict), user: dict = Depends(current_user)):
    """Move the column to a 0-based index among the board's columns, then renumber densely."""
    c = await load_or_404("columns", column_id)
    await membership(c["board_id"], user["id"])
    raw = body.get("position")
    try:
        if isinstance(raw, bool) or not (isinstance(raw, (int, float)) or (isinstance(raw, str) and raw.strip())):
            raise ValueError
        value = float(raw)
        if not value.is_integer():
            raise ValueError
        index = int(value)
    except ValueError:
        raise HTTPException(400, "Position must be a whole number.")
    ids = [d["_id"] async for d in db.columns.find({"board_id": c["board_id"], "_id": {"$ne": c["id"]}}, {"_id": 1}).sort([("position", 1), ("_id", 1)])]
    at = max(0, min(index, len(ids)))
    ids.insert(at, c["id"])
    await set_positions("columns", ids)
    if at != c["position"]:
        await log_activity(c["board_id"], user["id"], "column.moved", f'moved column "{c["name"]}" to position {at + 1}')
    return [{"id": d["_id"], "name": d["name"], "position": d["position"]}
            async for d in db.columns.find({"board_id": c["board_id"]}).sort("position", 1)]


@router.delete("/{column_id}")
async def delete_column(column_id: str, user: dict = Depends(current_user)):
    """Policy: deleting a column deletes its tasks (and their comments)."""
    c = await load_or_404("columns", column_id)
    await membership(c["board_id"], user["id"])
    n = await delete_tasks({"column_id": c["id"]})
    await db.columns.delete_one({"_id": c["id"]})
    await renumber("columns", {"board_id": c["board_id"]})
    suffix = f" and {n} task{'s' if n > 1 else ''}" if n else ""
    await log_activity(c["board_id"], user["id"], "column.deleted", f'deleted column "{c["name"]}"{suffix}')
    return {"ok": True, "deleted_tasks": n}

import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


async def next_id(name: str) -> int:
    doc = await db.counters.find_one_and_update(
        {"_id": name}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )
    return doc["seq"]


def pub(doc: dict | None, *drop: str) -> dict | None:
    """Mongo doc -> API dict: `_id` becomes `id`, listed private fields are removed."""
    if doc is None:
        return None
    out = {"id": doc["_id"]}
    out.update({k: v for k, v in doc.items() if k != "_id" and k not in drop})
    return out


async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.board_members.create_index([("board_id", 1), ("user_id", 1)], unique=True)
    await db.board_members.create_index("user_id")
    await db.columns.create_index([("board_id", 1), ("position", 1)])
    await db.tasks.create_index([("column_id", 1), ("position", 1)])
    await db.tasks.create_index("board_id")
    await db.comments.create_index("task_id")
    await db.activity.create_index([("board_id", 1), ("created_at", -1)])

from .db import db, now

# Both demo passwords are "demo1234" (bcrypt).
DEMO_HASH = "$2a$10$hrIhGPRBI/5a9v3sEJSKgeqX4rgOx6SvMYonFhzuPxtqQ03Y7vBUq"

USERS = [
    {"_id": 1, "name": "Alex Morgan", "email": "demo@taskboard.local"},
    {"_id": 2, "name": "Jordan Lee", "email": "jordan@taskboard.local"},
]
COLUMNS = [(1, "To Do", "#0052CC"), (2, "In Progress", "#FFAB00"), (3, "Done", "#00875A")]
TASKS = [
    (1, 1, "Audit onboarding flow", "Review activation drop-offs and list the top three fixes.", "high", "2026-07-03", 1, 0, 1),
    (2, 1, "Draft pricing FAQ", "Answer the ten most common billing questions from support.", "medium", "2026-07-10", 2, 1, 1),
    (3, 1, "Collect beta testimonials", "Reach out to five beta customers for short quotes.", "low", None, None, 2, 1),
    (4, 2, "Design release notes", "Draft the customer-facing release story with screenshots.", "medium", "2026-07-01", 2, 0, 1),
    (5, 2, "Fix checkout validation", "Card errors are shown twice on mobile Safari.", "high", "2026-06-28", 1, 1, 2),
    (6, 3, "QA regression pass", "Run the smoke test across the new workspace experience.", "low", None, 2, 0, 1),
]
COMMENTS = [
    (1, 1, 2, "I pulled the funnel numbers, step 3 loses 40% of new users.", "2026-06-02T10:00:00.000Z"),
    (2, 1, 1, "Great, let's start there. I will share fixes by Friday.", "2026-06-02T10:30:00.000Z"),
    (3, 5, 2, "Reproduced on iOS 19, looking into it.", "2026-06-03T14:00:00.000Z"),
]
ACTIVITY = [
    (1, 1, "task.created", 'created "Audit onboarding flow" in To Do', "2026-06-01T09:20:00.000Z"),
    (2, 2, "task.created", 'created "Fix checkout validation" in In Progress', "2026-06-01T09:24:00.000Z"),
    (3, 2, "comment.added", 'commented on "Audit onboarding flow"', "2026-06-02T10:00:00.000Z"),
    (4, 1, "comment.added", 'commented on "Audit onboarding flow"', "2026-06-02T10:30:00.000Z"),
    (5, 2, "task.moved", 'moved "QA regression pass" from In Progress to Done', "2026-06-03T16:00:00.000Z"),
]


async def seed_demo():
    """Load the sample board once, only into an empty database."""
    if await db.users.count_documents({}):
        return
    created = now()
    await db.users.insert_many([{**u, "password_hash": DEMO_HASH, "created_at": created} for u in USERS])
    await db.boards.insert_one({"_id": 1, "name": "Product Launch", "description": "Coordinate the next release from idea to shipped.", "owner_id": 1, "created_at": created})
    await db.board_members.insert_many([{"board_id": 1, "user_id": 1, "role": "owner"}, {"board_id": 1, "user_id": 2, "role": "member"}])
    await db.columns.insert_many([{"_id": i, "board_id": 1, "name": n, "position": i - 1, "color": c} for i, n, c in COLUMNS])
    await db.tasks.insert_many([
        {"_id": i, "board_id": 1, "column_id": col, "title": t, "description": d, "priority": p, "due_date": due,
         "assignee_id": a, "position": pos, "created_by": by, "created_at": created, "updated_at": created}
        for i, col, t, d, p, due, a, pos, by in TASKS])
    await db.comments.insert_many([{"_id": i, "task_id": t, "user_id": u, "body": b, "created_at": at} for i, t, u, b, at in COMMENTS])
    await db.activity.insert_many([{"_id": i, "board_id": 1, "user_id": u, "action": a, "message": m, "created_at": at} for i, u, a, m, at in ACTIVITY])
    for name, seq in {"users": 2, "boards": 1, "columns": 3, "tasks": 6, "comments": 3, "activity": 5}.items():
        await db.counters.update_one({"_id": name}, {"$set": {"seq": seq}}, upsert=True)

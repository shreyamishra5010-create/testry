# Manual helper (not collected by pytest): create/verify data around `supervisorctl restart backend`
import json
import os
import sys

import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
STATE = "/tmp/restart_state.json"


def login():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "demo@taskboard.local", "password": "demo1234"})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


if sys.argv[1] == "create":
    h = login()
    b = requests.get(f"{BASE_URL}/api/boards/1", headers=h).json()
    col = b["columns"][0]["id"]
    t = requests.post(f"{BASE_URL}/api/boards/1/tasks", headers=h, json={"title": "TEST_persist_restart", "column_id": col, "priority": "high"}).json()
    c = requests.post(f"{BASE_URL}/api/tasks/{t['id']}/comments", headers=h, json={"body": "TEST_persist comment"}).json()
    json.dump({"task": t["id"], "comment": c["id"], "token": h["Authorization"]}, open(STATE, "w"))
    print("created", t["id"], c["id"])
else:
    s = json.load(open(STATE))
    old = {"Authorization": s["token"]}
    print("old token after restart /me:", requests.get(f"{BASE_URL}/api/me", headers=old).status_code)
    h = login()
    b = requests.get(f"{BASE_URL}/api/boards/1", headers=h).json()
    ids = [t["id"] for c in b["columns"] for t in c["tasks"]]
    print("task persisted:", s["task"] in ids)
    cm = requests.get(f"{BASE_URL}/api/tasks/{s['task']}/comments", headers=h).json()
    print("comment persisted:", any(c["id"] == s["comment"] for c in cm))
    users = requests.get(f"{BASE_URL}/api/boards/1", headers=h).json()["members"]
    print("members:", [m["email"] for m in users])
    d = requests.delete(f"{BASE_URL}/api/tasks/{s['task']}", headers=h)
    print("cleanup delete:", d.status_code)

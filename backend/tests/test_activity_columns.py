# Column reordering (PATCH /columns/:id/move) + board activity feed tests
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"


def login(email, pw="demo1234"):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return r.json()


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def demo():
    return login("demo@taskboard.local")


@pytest.fixture(scope="module")
def jordan():
    return login("jordan@taskboard.local")


@pytest.fixture(scope="module")
def stranger():
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{API}/auth/register", json={"name": "TEST Stranger", "email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture(scope="module")
def board(demo):
    r = requests.post(f"{API}/boards", json={"name": "TEST_ActBoard"}, headers=H(demo["token"]))
    assert r.status_code == 201
    b = r.json()
    yield b
    requests.delete(f"{API}/boards/{b['id']}", headers=H(demo["token"]))


def acts(tok, bid, **params):
    r = requests.get(f"{API}/boards/{bid}/activity", headers=H(tok), params=params)
    assert r.status_code == 200, r.text
    return r.json()


def latest(tok, bid):
    a = acts(tok, bid, limit=1)
    return a[0] if a else None


def count(tok, bid):
    return len(acts(tok, bid, limit=200))


# ---- Column move
class TestColumnMove:
    def test_new_board_has_no_activity(self, demo, board):
        assert acts(demo["token"], board["id"]) == []

    def test_move_dense_and_clamp(self, demo, board):
        t = demo["token"]
        c = [col["id"] for col in board["columns"]]
        r = requests.patch(f"{API}/columns/{c[0]}/move", json={"position": 2}, headers=H(t))
        assert r.status_code == 200
        data = r.json()
        assert [x["id"] for x in data] == [c[1], c[2], c[0]]
        assert [x["position"] for x in data] == [0, 1, 2]
        a = latest(t, board["id"])
        assert a["action"] == "column.moved" and "position 3" in a["message"] and a["user_name"]
        # clamp high
        r = requests.patch(f"{API}/columns/{c[1]}/move", json={"position": 99}, headers=H(t))
        assert [x["id"] for x in r.json()] == [c[2], c[0], c[1]]
        # clamp low
        r = requests.patch(f"{API}/columns/{c[1]}/move", json={"position": -5}, headers=H(t))
        assert [x["id"] for x in r.json()] == [c[1], c[2], c[0]]
        assert [x["position"] for x in r.json()] == [0, 1, 2]
        # persisted
        g = requests.get(f"{API}/boards/{board['id']}", headers=H(t)).json()
        assert [x["id"] for x in g["columns"]] == [c[1], c[2], c[0]]

    def test_same_position_no_log(self, demo, board):
        t = demo["token"]
        g = requests.get(f"{API}/boards/{board['id']}", headers=H(t)).json()
        first = g["columns"][0]["id"]
        n = count(t, board["id"])
        r = requests.patch(f"{API}/columns/{first}/move", json={"position": 0}, headers=H(t))
        assert r.status_code == 200
        assert count(t, board["id"]) == n

    @pytest.mark.parametrize("pos", ["abc", 1.5, None, "1.2"])
    def test_non_integer_400(self, demo, board, pos):
        c = board["columns"][0]["id"]
        r = requests.patch(f"{API}/columns/{c}/move", json={"position": pos}, headers=H(demo["token"]))
        print(pos, r.status_code, r.text)
        assert r.status_code == 400 and "error" in r.json()

    def test_missing_position_400(self, demo, board):
        c = board["columns"][0]["id"]
        r = requests.patch(f"{API}/columns/{c}/move", json={}, headers=H(demo["token"]))
        assert r.status_code == 400

    def test_non_member_403_unknown_404(self, demo, stranger, board):
        c = board["columns"][0]["id"]
        r = requests.patch(f"{API}/columns/{c}/move", json={"position": 1}, headers=H(stranger["token"]))
        assert r.status_code == 403
        r = requests.patch(f"{API}/columns/999999/move", json={"position": 1}, headers=H(demo["token"]))
        assert r.status_code == 404
        r = requests.patch(f"{API}/columns/{c}/move", json={"position": 1})
        assert r.status_code == 401


# ---- Activity logging
class TestActivityLogging:
    def test_activity_403_non_member(self, stranger, board):
        r = requests.get(f"{API}/boards/{board['id']}/activity", headers=H(stranger["token"]))
        assert r.status_code == 403

    def test_column_add_rename_delete(self, demo, board):
        t, bid = demo["token"], board["id"]
        r = requests.post(f"{API}/boards/{bid}/columns", json={"name": "TEST_Col"}, headers=H(t))
        assert r.status_code == 201
        cid = r.json()["id"]
        a = latest(t, bid)
        assert a["action"] == "column.added" and "TEST_Col" in a["message"]
        n = count(t, bid)
        requests.patch(f"{API}/columns/{cid}", json={"name": "TEST_Col"}, headers=H(t))
        assert count(t, bid) == n  # unchanged name: no log
        requests.patch(f"{API}/columns/{cid}", json={"name": "TEST_Col2"}, headers=H(t))
        a = latest(t, bid)
        assert a["action"] == "column.renamed" and '"TEST_Col" to "TEST_Col2"' in a["message"]
        for i in range(2):
            requests.post(f"{API}/boards/{bid}/tasks", json={"title": f"TEST_t{i}", "column_id": cid}, headers=H(t))
        r = requests.delete(f"{API}/columns/{cid}", headers=H(t))
        assert r.json()["deleted_tasks"] == 2
        a = latest(t, bid)
        assert a["action"] == "column.deleted" and "2 tasks" in a["message"]

    def test_task_lifecycle(self, demo, jordan, board):
        t, bid = demo["token"], board["id"]
        cols = requests.get(f"{API}/boards/{bid}", headers=H(t)).json()["columns"]
        c1, c2 = cols[0], cols[1]
        r = requests.post(f"{API}/boards/{bid}/tasks", json={"title": "TEST_Life", "column_id": c1["id"], "description": ""}, headers=H(t))
        assert r.status_code == 201
        task = r.json()
        a = latest(t, bid)
        assert a["action"] == "task.created" and "TEST_Life" in a["message"] and c1["name"] in a["message"]
        # no-op edit (send whole object like the UI) -> no log
        n = count(t, bid)
        body = {k: task[k] for k in ["title", "description", "priority", "due_date", "assignee_id"]}
        r = requests.patch(f"{API}/tasks/{task['id']}", json=body, headers=H(t))
        assert r.status_code == 200
        assert count(t, bid) == n, acts(t, bid, limit=2)
        r = requests.patch(f"{API}/tasks/{task['id']}", json={**body, "due_date": ""}, headers=H(t))
        assert count(t, bid) == n
        # change priority + due date
        r = requests.patch(f"{API}/tasks/{task['id']}", json={**body, "priority": "high", "due_date": "2026-03-01"}, headers=H(t))
        a = latest(t, bid)
        assert a["action"] == "task.updated"
        assert "priority" in a["message"] and "due date" in a["message"] and "title" not in a["message"] and "description" not in a["message"]
        # assignee with string id
        r = requests.patch(f"{API}/tasks/{task['id']}", json={"assignee_id": str(demo["user"]["id"])}, headers=H(t))
        assert r.status_code == 200
        a = latest(t, bid)
        assert "assignee" in a["message"]
        n = count(t, bid)
        requests.patch(f"{API}/tasks/{task['id']}", json={"assignee_id": demo["user"]["id"]}, headers=H(t))
        assert count(t, bid) == n
        # second task to reorder within
        t2 = requests.post(f"{API}/boards/{bid}/tasks", json={"title": "TEST_Other", "column_id": c1["id"]}, headers=H(t)).json()
        r = requests.patch(f"{API}/tasks/{t2['id']}/move", json={"column_id": c1["id"], "position": 0}, headers=H(t))
        a = latest(t, bid)
        assert a["action"] == "task.reordered" and c1["name"] in a["message"]
        n = count(t, bid)
        requests.patch(f"{API}/tasks/{t2['id']}/move", json={"column_id": c1["id"], "position": 0}, headers=H(t))
        assert count(t, bid) == n  # same position: no log
        # move across
        requests.patch(f"{API}/tasks/{task['id']}/move", json={"column_id": c2["id"], "position": 0}, headers=H(t))
        a = latest(t, bid)
        assert a["action"] == "task.moved" and f"from {c1['name']} to {c2['name']}" in a["message"]
        # move via PATCH column_id
        r = requests.patch(f"{API}/tasks/{task['id']}", json={"column_id": c1["id"]}, headers=H(t))
        assert r.status_code == 200
        a = latest(t, bid)
        assert a["action"] == "task.moved" and f"from {c2['name']} to {c1['name']}" in a["message"]
        # comment
        r = requests.post(f"{API}/tasks/{task['id']}/comments", json={"body": "TEST hi"}, headers=H(t))
        assert r.status_code == 201
        a = latest(t, bid)
        assert a["action"] == "comment.added" and "TEST_Life" in a["message"]
        # delete
        requests.delete(f"{API}/tasks/{task['id']}", headers=H(t))
        a = latest(t, bid)
        assert a["action"] == "task.deleted" and "TEST_Life" in a["message"] and c1["name"] in a["message"]

    def test_invalid_column_patch_side_effect(self, demo, board):
        """PATCH with bad column_id: is the edit applied/logged before the 400?"""
        t, bid = demo["token"], board["id"]
        cols = requests.get(f"{API}/boards/{bid}", headers=H(t)).json()["columns"]
        task = requests.post(f"{API}/boards/{bid}/tasks", json={"title": "TEST_Side", "column_id": cols[0]["id"]}, headers=H(t)).json()
        n = count(t, bid)
        r = requests.patch(f"{API}/tasks/{task['id']}", json={"title": "TEST_Side_changed", "column_id": 999999}, headers=H(t))
        assert r.status_code == 400
        got = requests.get(f"{API}/boards/{bid}", headers=H(t)).json()
        titles = [x["title"] for c in got["columns"] for x in c["tasks"]]
        print("titles after failed PATCH:", titles, "activity delta:", count(t, bid) - n)
        assert "TEST_Side_changed" not in titles, "Edit was applied despite 400 (non-atomic PATCH)"

    def test_members_not_logged(self, demo, jordan, board):
        t, bid = demo["token"], board["id"]
        n = count(t, bid)
        r = requests.post(f"{API}/boards/{bid}/members", json={"email": "jordan@taskboard.local"}, headers=H(t))
        assert r.status_code == 200
        r = requests.delete(f"{API}/boards/{bid}/members/{jordan['user']['id']}", headers=H(t))
        assert r.status_code == 200
        assert count(t, bid) == n

    def test_order_limit_and_fields(self, demo, board):
        t, bid = demo["token"], board["id"]
        a = acts(t, bid)
        assert len(a) >= 5
        ids = [x["id"] for x in a]
        assert ids == sorted(ids, reverse=True)
        for k in ["id", "action", "message", "user_id", "user_name", "created_at"]:
            assert k in a[0]
        assert a[0]["user_name"] == demo["user"]["name"]
        assert len(acts(t, bid, limit=2)) == 2
        assert len(acts(t, bid, limit="abc")) == min(50, len(a))

    def test_seed_board_activity(self, demo, jordan):
        a = acts(jordan["token"], 1)
        assert len(a) >= 5
        assert all(x["user_name"] for x in a)

# Task Board API regression tests (auth, boards, members, columns, tasks/move, comments)
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


def hdr(tok):
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
    d = r.json()
    d["email"] = email
    return d


@pytest.fixture(scope="module")
def board(demo):
    r = requests.post(f"{API}/boards", json={"name": "TEST_Board", "description": "tmp"}, headers=hdr(demo["token"]))
    assert r.status_code == 201
    b = r.json()
    yield b
    requests.delete(f"{API}/boards/{b['id']}", headers=hdr(demo["token"]))


# ---- Auth
class TestAuth:
    def test_register_short_password(self):
        r = requests.post(f"{API}/auth/register", json={"name": "x", "email": "a@b.co", "password": "short"})
        assert r.status_code == 400 and "error" in r.json()

    def test_register_bad_email(self):
        r = requests.post(f"{API}/auth/register", json={"name": "x", "email": "bad", "password": "password123"})
        assert r.status_code == 400

    def test_register_duplicate(self):
        r = requests.post(f"{API}/auth/register", json={"name": "x", "email": "DEMO@taskboard.local", "password": "password123"})
        assert r.status_code == 409

    def test_login_wrong_password(self):
        r = requests.post(f"{API}/auth/login", json={"email": "demo@taskboard.local", "password": "wrongpass"})
        assert r.status_code == 401

    def test_login_and_me(self, demo):
        assert demo["user"]["email"] == "demo@taskboard.local"
        r = requests.get(f"{API}/me", headers=hdr(demo["token"]))
        assert r.status_code == 200 and r.json()["user"]["id"] == demo["user"]["id"]

    @pytest.mark.parametrize("method,path", [("get", "/boards"), ("get", "/boards/1"), ("get", "/me"),
                                             ("patch", "/tasks/1/move"), ("delete", "/comments/1"), ("get", "/tasks/1/comments")])
    def test_unauth_401(self, method, path):
        r = getattr(requests, method)(f"{API}{path}")
        assert r.status_code == 401
        r = getattr(requests, method)(f"{API}{path}", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401


# ---- Boards
class TestBoards:
    def test_list_has_product_launch(self, demo):
        r = requests.get(f"{API}/boards", headers=hdr(demo["token"]))
        b = [x for x in r.json() if x["id"] == 1]
        assert b and b[0]["role"] == "owner"
        for k in ("task_count", "due_soon", "member_count"):
            assert isinstance(b[0][k], int)

    def test_create_board_default_columns(self, board):
        assert [c["name"] for c in board["columns"]] == ["To Do", "In Progress", "Done"]
        assert board["members"][0]["role"] == "owner"

    def test_seed_board_positions_dense(self, demo):
        r = requests.get(f"{API}/boards/1", headers=hdr(demo["token"]))
        assert r.status_code == 200
        for c in r.json()["columns"]:
            assert [t["position"] for t in c["tasks"]] == list(range(len(c["tasks"])))

    def test_stranger_403(self, stranger):
        r = requests.get(f"{API}/boards/1", headers=hdr(stranger["token"]))
        assert r.status_code == 403

    def test_patch_board_owner_only(self, demo, jordan, board):
        r = requests.patch(f"{API}/boards/{board['id']}", json={"name": "TEST_Renamed", "description": "d2"}, headers=hdr(demo["token"]))
        assert r.status_code == 200 and r.json()["name"] == "TEST_Renamed"
        g = requests.get(f"{API}/boards/{board['id']}", headers=hdr(demo["token"])).json()
        assert g["description"] == "d2"
        assert requests.patch(f"{API}/boards/1", json={"name": "x"}, headers=hdr(jordan["token"])).status_code == 403
        assert requests.patch(f"{API}/boards/{board['id']}", json={"name": "  "}, headers=hdr(demo["token"])).status_code == 400


# ---- Members
class TestMembers:
    def test_invite_remove(self, demo, stranger, board):
        bid = board["id"]
        r = requests.post(f"{API}/boards/{bid}/members", json={"email": stranger["email"]}, headers=hdr(demo["token"]))
        assert r.status_code == 200 and any(m["id"] == stranger["user"]["id"] for m in r.json()["members"])
        assert requests.get(f"{API}/boards/{bid}", headers=hdr(stranger["token"])).status_code == 200
        # non-owner member cannot invite
        assert requests.post(f"{API}/boards/{bid}/members", json={"email": "jordan@taskboard.local"}, headers=hdr(stranger["token"])).status_code == 403
        r = requests.delete(f"{API}/boards/{bid}/members/{stranger['user']['id']}", headers=hdr(demo["token"]))
        assert r.status_code == 200
        assert requests.get(f"{API}/boards/{bid}", headers=hdr(stranger["token"])).status_code == 403

    def test_unknown_email_404(self, demo, board):
        r = requests.post(f"{API}/boards/{board['id']}/members", json={"email": "nobody_xyz@example.com"}, headers=hdr(demo["token"]))
        assert r.status_code == 404

    def test_owner_cannot_be_removed(self, demo, board):
        r = requests.delete(f"{API}/boards/{board['id']}/members/{demo['user']['id']}", headers=hdr(demo["token"]))
        assert r.status_code == 400

    def test_jordan_cannot_invite_on_seed(self, jordan, stranger):
        r = requests.post(f"{API}/boards/1/members", json={"email": stranger["email"]}, headers=hdr(jordan["token"]))
        assert r.status_code == 403


# ---- Tasks + move
class TestTasks:
    def _mk(self, tok, bid, col, title, **kw):
        r = requests.post(f"{API}/boards/{bid}/tasks", json={"column_id": col, "title": title, **kw}, headers=hdr(tok))
        assert r.status_code == 201, r.text
        return r.json()

    def _cols(self, tok, bid):
        return {c["id"]: [t["id"] for t in c["tasks"]] for c in requests.get(f"{API}/boards/{bid}", headers=hdr(tok)).json()["columns"]}

    def test_create_validation(self, demo, stranger, board):
        tok, bid, c0 = demo["token"], board["id"], board["columns"][0]["id"]
        assert requests.post(f"{API}/boards/{bid}/tasks", json={"column_id": c0, "title": "x", "priority": "urgent"}, headers=hdr(tok)).status_code == 400
        assert requests.post(f"{API}/boards/{bid}/tasks", json={"column_id": c0, "title": " "}, headers=hdr(tok)).status_code == 400
        assert requests.post(f"{API}/boards/{bid}/tasks", json={"column_id": c0, "title": "x", "assignee_id": stranger["user"]["id"]}, headers=hdr(tok)).status_code == 400
        # column from another board
        assert requests.post(f"{API}/boards/{bid}/tasks", json={"column_id": 1, "title": "x"}, headers=hdr(tok)).status_code == 400

    def test_create_and_edit(self, demo, board):
        tok, bid, c0 = demo["token"], board["id"], board["columns"][0]["id"]
        t = self._mk(tok, bid, c0, "TEST_A", priority="high", due_date="2026-02-01", assignee_id=demo["user"]["id"])
        assert t["priority"] == "high" and t["assignee_name"] and t["due_date"] == "2026-02-01"
        r = requests.patch(f"{API}/tasks/{t['id']}", json={"title": "TEST_A2", "assignee_id": None, "priority": "low"}, headers=hdr(tok))
        assert r.status_code == 200 and r.json()["title"] == "TEST_A2" and r.json()["assignee_id"] is None
        assert requests.patch(f"{API}/tasks/{t['id']}", json={"priority": "bad"}, headers=hdr(tok)).status_code == 400
        # string ids as sent by the frontend select
        r = requests.patch(f"{API}/tasks/{t['id']}", json={"assignee_id": str(demo["user"]["id"])}, headers=hdr(tok))
        assert r.status_code == 200 and r.json()["assignee_id"] == demo["user"]["id"]
        requests.delete(f"{API}/tasks/{t['id']}", headers=hdr(tok))

    def test_move_within_and_across(self, demo, board):
        tok, bid = demo["token"], board["id"]
        c0, c1 = board["columns"][0]["id"], board["columns"][1]["id"]
        ids = [self._mk(tok, bid, c0, f"TEST_M{i}")["id"] for i in range(4)]
        base = [x for x in self._cols(tok, bid)[c0]]
        # move last to index 0 in same column
        r = requests.patch(f"{API}/tasks/{ids[3]}/move", json={"column_id": c0, "position": 0}, headers=hdr(tok))
        assert r.status_code == 200
        exp = [ids[3]] + [x for x in base if x != ids[3]]
        assert self._cols(tok, bid)[c0] == exp
        # move first -> index 2 same column
        requests.patch(f"{API}/tasks/{ids[3]}/move", json={"column_id": c0, "position": 2}, headers=hdr(tok))
        rest = [x for x in exp if x != ids[3]]
        assert self._cols(tok, bid)[c0] == rest[:2] + [ids[3]] + rest[2:]
        # across: to c1 at 0, then another at 0 -> before it
        requests.patch(f"{API}/tasks/{ids[0]}/move", json={"column_id": c1, "position": 0}, headers=hdr(tok))
        requests.patch(f"{API}/tasks/{ids[1]}/move", json={"column_id": c1, "position": 0}, headers=hdr(tok))
        cols = self._cols(tok, bid)
        assert cols[c1][:2] == [ids[1], ids[0]] and ids[0] not in cols[c0]
        board_data = requests.get(f"{API}/boards/{bid}", headers=hdr(tok)).json()
        for c in board_data["columns"]:
            assert [t["position"] for t in c["tasks"]] == list(range(len(c["tasks"])))
        # other board column -> 400
        assert requests.patch(f"{API}/tasks/{ids[2]}/move", json={"column_id": 1, "position": 0}, headers=hdr(tok)).status_code == 400
        # PATCH column_id -> bottom
        requests.patch(f"{API}/tasks/{ids[2]}", json={"column_id": c1}, headers=hdr(tok))
        assert self._cols(tok, bid)[c1][-1] == ids[2]

    def test_stranger_cannot_touch_task(self, stranger):
        assert requests.patch(f"{API}/tasks/1", json={"title": "hack"}, headers=hdr(stranger["token"])).status_code == 403
        assert requests.get(f"{API}/tasks/1/comments", headers=hdr(stranger["token"])).status_code == 403


# ---- Columns
class TestColumns:
    def test_column_crud_deletes_tasks(self, demo, board):
        tok, bid = demo["token"], board["id"]
        r = requests.post(f"{API}/boards/{bid}/columns", json={"name": "TEST_Col"}, headers=hdr(tok))
        assert r.status_code == 201
        cid = r.json()["id"]
        assert requests.patch(f"{API}/columns/{cid}", json={"name": "TEST_Col2"}, headers=hdr(tok)).json()["name"] == "TEST_Col2"
        assert requests.patch(f"{API}/columns/{cid}", json={"name": ""}, headers=hdr(tok)).status_code == 400
        for i in range(2):
            requests.post(f"{API}/boards/{bid}/tasks", json={"column_id": cid, "title": f"TEST_c{i}"}, headers=hdr(tok))
        r = requests.delete(f"{API}/columns/{cid}", headers=hdr(tok))
        assert r.status_code == 200 and r.json()["deleted_tasks"] == 2
        b = requests.get(f"{API}/boards/{bid}", headers=hdr(tok)).json()
        assert cid not in [c["id"] for c in b["columns"]]
        assert [c["position"] for c in b["columns"]] == list(range(len(b["columns"])))


# ---- Comments
class TestComments:
    def test_comment_flow(self, demo, jordan):
        r = requests.post(f"{API}/tasks/1/comments", json={"body": "TEST_comment"}, headers=hdr(demo["token"]))
        assert r.status_code == 201 and r.json()["author_name"]
        cid = r.json()["id"]
        assert requests.post(f"{API}/tasks/1/comments", json={"body": " "}, headers=hdr(demo["token"])).status_code == 400
        lst = requests.get(f"{API}/tasks/1/comments", headers=hdr(jordan["token"])).json()
        assert any(c["id"] == cid for c in lst)
        assert requests.delete(f"{API}/comments/{cid}", headers=hdr(jordan["token"])).status_code == 403
        assert requests.delete(f"{API}/comments/{cid}", headers=hdr(demo["token"])).status_code == 200
        assert requests.delete(f"{API}/comments/{cid}", headers=hdr(demo["token"])).status_code == 404


# ---- Board delete
def test_board_delete_cascade(demo, jordan):
    tok = demo["token"]
    b = requests.post(f"{API}/boards", json={"name": "TEST_Del"}, headers=hdr(tok)).json()
    assert requests.delete(f"{API}/boards/{b['id']}", headers=hdr(jordan["token"])).status_code == 403
    assert requests.delete(f"{API}/boards/{b['id']}", headers=hdr(tok)).status_code == 200
    # membership() now checks existence first -> deleted board returns 404
    assert requests.get(f"{API}/boards/{b['id']}", headers=hdr(tok)).status_code == 404

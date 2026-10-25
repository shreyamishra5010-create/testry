# Manual probe: concurrent bursts vs login throttle (iteration 7 retest of the TOCTOU fix)
import os, uuid, requests
from concurrent.futures import ThreadPoolExecutor
B = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")


def new_user(tag):
    e = f"test_{tag}_{uuid.uuid4().hex[:8]}@example.com"
    assert requests.post(f"{B}/api/auth/register", json={"name": "TEST b", "email": e, "password": "goodpass123"}).status_code == 201
    return e


def burst(e, n, pw, xff=False):
    def go(i):
        h = {"X-Forwarded-For": f"198.51.{i // 250}.{i % 250 + 1}"} if xff else {}
        return requests.post(f"{B}/api/auth/login", json={"email": e, "password": pw(i)}, headers=h, timeout=60).status_code
    with ThreadPoolExecutor(n) as ex:
        return list(ex.map(go, range(n)))


for label, xff in [("plain", False), ("xff", True)]:
    e = new_user("burst")
    c = burst(e, 40, lambda i: f"bad{i}", xff)
    print(f"wrong burst [{label}] 401s:", c.count(401), "429s:", c.count(429), "other:", [x for x in c if x not in (401, 429)])

e = new_user("ok")
c = burst(e, 10, lambda i: "goodpass123")
print("correct burst x10:", c)
e = new_user("ok20")
c = burst(e, 20, lambda i: "goodpass123")
print("correct burst x20: 200s:", c.count(200), "429s:", c.count(429))

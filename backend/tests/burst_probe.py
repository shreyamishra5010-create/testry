# Manual probe: concurrent burst of wrong passwords vs throttle (TOCTOU check-then-await)
import os, uuid, requests
from concurrent.futures import ThreadPoolExecutor
B = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
e = f"test_burst_{uuid.uuid4().hex[:8]}@example.com"
assert requests.post(f"{B}/api/auth/register", json={"name": "TEST b", "email": e, "password": "goodpass123"}).status_code == 201
def go(i): return requests.post(f"{B}/api/auth/login", json={"email": e, "password": f"bad{i}"}, timeout=60).status_code
with ThreadPoolExecutor(40) as ex: codes = list(ex.map(go, range(40)))
print("401s:", codes.count(401), "429s:", codes.count(429))

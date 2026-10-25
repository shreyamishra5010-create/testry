# FastAPI+Mongo rewrite: health, error contract, JWT rejection, login throttling (iteration 5)
import os
import time
import uuid

import jwt
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


def new_user():
    email = f"test_{uuid.uuid4().hex[:10]}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={"name": "TEST Throttle", "email": email, "password": "goodpass123"})
    assert r.status_code == 201, r.text
    return email, r.json()


# Health
class TestHealth:
    def test_root_health(self):
        r = requests.get(f"{BASE_URL}/health")
        # /health without /api may be routed to the frontend by ingress; accept either JSON ok or HTML 200
        assert r.status_code == 200

    def test_api_health(self):
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
        assert r.json() == {"ok": True, "service": "task-board-api"}


# Error contract
class TestErrorContract:
    def test_unknown_api_route_404(self):
        r = requests.get(f"{BASE_URL}/api/does-not-exist")
        assert r.status_code == 404
        assert r.json() == {"error": "Not found."}

    def test_unknown_api_route_post_404(self):
        r = requests.post(f"{BASE_URL}/api/nope/x", json={})
        assert r.status_code == 404
        assert "error" in r.json()

    def test_malformed_json_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", data="{bad json", headers={"Content-Type": "application/json"})
        assert r.status_code == 400
        assert "error" in r.json()

    def test_malformed_json_register(self):
        r = requests.post(f"{BASE_URL}/api/auth/register", data="{\"name\":", headers={"Content-Type": "application/json"})
        assert r.status_code == 400
        assert "error" in r.json()

    def test_non_object_json_body(self):
        r = requests.post(f"{BASE_URL}/api/auth/register", json=[1, 2])
        assert r.status_code == 400
        assert "error" in r.json()

    def test_non_integer_board_id_404(self):
        email, data = new_user()
        r = requests.get(f"{BASE_URL}/api/boards/abc", headers={"Authorization": f"Bearer {data['token']}"})
        assert r.status_code == 404
        assert "error" in r.json()

    def test_security_headers(self):
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"


# JWT rejection
class TestTokens:
    @pytest.mark.parametrize("secret", ["dev-secret", "taskboard-dev-secret", "secret", "change-me"])
    def test_foreign_secret_token_rejected(self, secret):
        tok = jwt.encode({"id": 1, "email": "demo@taskboard.local", "name": "Alex Morgan", "exp": int(time.time()) + 3600}, secret, algorithm="HS256")
        r = requests.get(f"{BASE_URL}/api/me", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401
        assert r.json() == {"error": "Please sign in to continue."}

    def test_garbage_token(self):
        r = requests.get(f"{BASE_URL}/api/boards", headers={"Authorization": "Bearer garbage.token.here"})
        assert r.status_code == 401
        assert "error" in r.json()

    def test_alg_none_token(self):
        tok = jwt.encode({"id": 1, "email": "demo@taskboard.local", "name": "x"}, None, algorithm="none")
        r = requests.get(f"{BASE_URL}/api/me", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401

    def test_missing_and_wrong_scheme(self):
        assert requests.get(f"{BASE_URL}/api/me").status_code == 401
        assert requests.get(f"{BASE_URL}/api/me", headers={"Authorization": "Token abc"}).status_code == 401

    def test_valid_token_works(self):
        email, data = new_user()
        r = requests.get(f"{BASE_URL}/api/me", headers={"Authorization": f"Bearer {data['token']}"})
        assert r.status_code == 200
        assert r.json()["user"]["email"] == email
        assert isinstance(r.json()["user"]["id"], int)


# Login throttle (throwaway users only)
class TestThrottle:
    def test_eight_failures_then_429(self):
        email, _ = new_user()
        for i in range(8):
            r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": f"wrong{i}xx"})
            assert r.status_code == 401, f"attempt {i+1}: {r.status_code}"
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "wrong9xx"})
        assert r.status_code == 429
        assert "error" in r.json()
        # even the correct password is blocked while throttled
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "goodpass123"})
        assert r.status_code == 429

    def test_success_resets_counter(self):
        email, _ = new_user()
        for i in range(7):
            assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "bad"}).status_code == 401
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "goodpass123"}).status_code == 200
        for i in range(7):
            assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "bad"}).status_code == 401
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "goodpass123"}).status_code == 200

    def test_email_case_shares_counter(self):
        email, _ = new_user()
        for i in range(8):
            requests.post(f"{BASE_URL}/api/auth/login", json={"email": email.upper() if i % 2 else email, "password": "bad"})
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email.upper(), "password": "bad"})
        assert r.status_code == 429

    def test_spoofed_xff_bypass(self):
        """Security probe: rotating a client-supplied X-Forwarded-For should NOT reset the throttle."""
        email, _ = new_user()
        for i in range(8):
            requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "bad"})
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "bad"},
                          headers={"X-Forwarded-For": "203.0.113.77"})
        assert r.status_code == 429, f"throttle bypassed via spoofed X-Forwarded-For (got {r.status_code})"


# Iteration 6: per-account throttle ignores XFF; bcrypt in a thread (concurrency)
class TestThrottleXffAndConcurrency:
    def test_rotating_xff_every_request_still_429(self):
        email, _ = new_user()
        for i in range(8):
            r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "bad"},
                              headers={"X-Forwarded-For": f"198.51.100.{i + 1}"})
            assert r.status_code == 401, f"attempt {i+1}: {r.status_code}"
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "bad"},
                          headers={"X-Forwarded-For": "203.0.113.200"})
        assert r.status_code == 429
        assert "error" in r.json()
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "goodpass123"},
                          headers={"X-Forwarded-For": "192.0.2.55, 10.0.0.1"})
        assert r.status_code == 429

    def test_register_login_roundtrip(self):
        email, data = new_user()
        assert isinstance(data["token"], str) and data["user"]["email"] == email
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "goodpass123"})
        assert r.status_code == 200
        assert r.json()["user"]["email"] == email
        assert requests.get(f"{BASE_URL}/api/me", headers={"Authorization": f"Bearer {r.json()['token']}"}).status_code == 200

    def test_concurrent_logins_succeed(self):
        from concurrent.futures import ThreadPoolExecutor
        email, _ = new_user()
        def go(_):
            return requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "goodpass123"}, timeout=30).status_code
        with ThreadPoolExecutor(10) as ex:
            codes = list(ex.map(go, range(10)))
        assert codes == [200] * 10, codes


# Iteration 7: atomic reserve_attempt — concurrent wrong-password bursts must be capped at MAX_FAILURES
class TestThrottleBurst:
    def _burst(self, email, n, xff):
        from concurrent.futures import ThreadPoolExecutor
        def go(i):
            h = {"X-Forwarded-For": f"198.51.100.{i + 1}"} if xff else {}
            return requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": f"bad{i}"}, headers=h, timeout=60).status_code
        with ThreadPoolExecutor(n) as ex:
            return list(ex.map(go, range(n)))

    def test_wrong_burst_capped(self):
        email, _ = new_user()
        codes = self._burst(email, 40, False)
        assert codes.count(401) <= 8 and codes.count(401) + codes.count(429) == 40, codes

    def test_wrong_burst_spoofed_xff_capped(self):
        email, _ = new_user()
        codes = self._burst(email, 40, True)
        assert codes.count(401) <= 8 and codes.count(401) + codes.count(429) == 40, codes



# Iteration 8: per-account asyncio.Lock — correct bursts succeed, accounts independent
class TestAccountLock:
    def _par(self, jobs):
        from concurrent.futures import ThreadPoolExecutor
        def go(j):
            email, pw = j
            return email, requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": pw}, timeout=90).status_code
        with ThreadPoolExecutor(len(jobs)) as ex:
            return list(ex.map(go, jobs))

    def test_concurrent_20_correct_logins(self):
        email, _ = new_user()
        codes = [c for _, c in self._par([(email, "goodpass123")] * 20)]
        assert codes == [200] * 20, codes

    def test_accounts_independent_parallel(self):
        a, _ = new_user()
        b, _ = new_user()
        jobs = [(a, f"bad{i}") for i in range(20)] + [(b, "goodpass123")] * 10
        res = self._par(jobs)
        a_codes = [c for e, c in res if e == a]
        b_codes = [c for e, c in res if e == b]
        assert b_codes == [200] * 10, b_codes
        assert a_codes.count(401) == 8 and a_codes.count(429) == 12, a_codes
        # A is locked, B still logs in
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": a, "password": "goodpass123"}).status_code == 429
        assert requests.post(f"{BASE_URL}/api/auth/login", json={"email": b, "password": "goodpass123"}).status_code == 200

    def test_unknown_email_burst_capped(self):
        email = f"test_nouser_{uuid.uuid4().hex[:10]}@example.com"
        codes = [c for _, c in self._par([(email, "x")] * 30)]
        assert codes.count(401) == 8 and codes.count(429) == 22, codes

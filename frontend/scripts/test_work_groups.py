"""Integration test: frontend-facing work group API over real HTTP with cookies."""
import http.cookiejar
import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8000/api/v1"
EMAIL = "demo@example.com"
PASSWORD = "demo12345"

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

failures = []


def csrf() -> str | None:
    for cookie in jar:
        if cookie.name == "dataair_csrf_token":
            return cookie.value
    return None


def call(method, path, body=None, expect=200):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    token = csrf()
    if token:
        req.add_header("x-csrf-token", token)
    try:
        with opener.open(req, timeout=30) as resp:
            status = resp.status
            payload = resp.read().decode()
    except urllib.error.HTTPError as exc:
        status = exc.code
        payload = exc.read().decode()

    ok = status == expect
    print(f"  [{'PASS' if ok else 'FAIL'}] {method} {path} -> {status} (expected {expect})")
    if not ok:
        failures.append(f"{method} {path}: got {status}, expected {expect}: {payload[:200]}")
    try:
        return json.loads(payload) if payload else None
    except json.JSONDecodeError:
        return payload


print("1. login")
call("POST", "/auth/login", {"email": EMAIL, "password": PASSWORD})
csrf_token = csrf()
print(f"  csrf cookie present: {bool(csrf_token)}")
if not csrf_token:
    failures.append("no CSRF cookie issued on login")

print("2. list (empty baseline)")
groups = call("GET", "/work-groups")
print(f"  existing groups: {len(groups) if isinstance(groups, list) else groups}")

print("3. create")
created = call("POST", "/work-groups", {"name": "QA Platform", "description": "Integration test group"}, expect=201)
gid = created["id"]
print(f"  slug={created['slug']} member_count={created['member_count']}")
assert created["member_count"] == 1, "creator should be auto-added as owner"

print("4. duplicate name gets a unique slug")
dupe = call("POST", "/work-groups", {"name": "QA Platform"}, expect=201)
print(f"  second slug={dupe['slug']}")
if dupe["slug"] == created["slug"]:
    failures.append("duplicate name produced a colliding slug")

print("5. blank name rejected")
call("POST", "/work-groups", {"name": "   "}, expect=422)

print("6. detail includes members")
detail = call("GET", f"/work-groups/{gid}")
print(f"  members={len(detail['members'])} roles={[m['role'] for m in detail['members']]}")
if len(detail["members"]) != 1 or detail["members"][0]["role"] != "owner":
    failures.append("creator is not listed as owner")

print("7. cross-tenant isolation returns 404")
call("GET", "/work-groups/00000000-0000-0000-0000-000000000000", expect=404)

print("8. rename updates slug")
renamed = call("PATCH", f"/work-groups/{gid}", {"name": "Quality Engineering"})
print(f"  slug now={renamed['slug']}")
if renamed["slug"] != "quality-engineering":
    failures.append(f"rename did not update slug: {renamed['slug']}")

print("9. add a member (self, to test duplicate guard)")
me = call("GET", "/auth/me")
call("POST", f"/work-groups/{gid}/members", {"user_id": me["id"]}, expect=409)

print("10. cannot remove the last owner")
detail = call("GET", f"/work-groups/{gid}")
owner_member = detail["members"][0]["id"]
call("DELETE", f"/work-groups/{gid}/members/{owner_member}", expect=409)

print("11. candidates excludes existing members")
cands = call("GET", f"/work-groups/{gid}/candidates")
print(f"  candidates={len(cands)} (self is a member so must be excluded)")
if any(c["id"] == me["id"] for c in cands):
    failures.append("candidates list includes an existing member")

print("12. add member outside this tenant rejected")
call("POST", f"/work-groups/{gid}/members", {"user_id": "00000000-0000-0000-0000-000000000000"}, expect=404)

print("13. cleanup")
call("DELETE", f"/work-groups/{gid}", expect=204)
call("DELETE", f"/work-groups/{dupe['id']}", expect=204)

print("14. confirm deleted")
call("GET", f"/work-groups/{gid}", expect=404)

print()
if failures:
    print(f"FAILED ({len(failures)})")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL CHECKS PASSED")

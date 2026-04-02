"""
e2e_test.py – Full end-to-end integration test
Tests: Auth (register/login) → DynamoDB session storage → Azure AI (Vision + Language)

Run: python e2e_test.py
"""

import os, sys, json, base64, io, time
import urllib.request, urllib.error
from dotenv import load_dotenv
load_dotenv()

PORT    = os.getenv("PORT", "8001")
BASE    = f"http://localhost:{PORT}"
TEST_EMAIL    = f"_e2etest_{int(time.time())}@stressdetect.local"
TEST_PASSWORD = "E2eTestPass!99"
TEST_NAME     = "E2E Test User"

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
INFO = "\033[94mℹ️  INFO\033[0m"

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

def check(label, ok, detail=""):
    status = PASS if ok else FAIL
    print(f"  {status}  {label}")
    if detail:
        for line in str(detail).split('\n'):
            print(f"           {line}")
    return ok

def api(method, path, body=None, token=None):
    url  = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as ex:
        return 0, {"error": str(ex)}

def make_small_jpeg_b64():
    """Create a 100x100 grey JPEG (no face) encoded as base64 data URL."""
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception as e:
        return None

all_passed = True
token = None

# ── 1. Health ─────────────────────────────────────────────────────────────────
section("1. API Health Check")
status, body = api("GET", "/health")
ok = check("GET /health → 200", status == 200, body)
ok = check("db == DynamoDB", body.get("db") == "DynamoDB", body) and ok
all_passed = all_passed and ok

# ── 2. Register ───────────────────────────────────────────────────────────────
section("2. User Registration (POST /api/auth/register)")
status, body = api("POST", "/api/auth/register", {
    "name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD
})
ok = check(f"Register → 200", status == 200, body)
ok = check("access_token present", bool(body.get("access_token"))) and ok
ok = check("email matches", body.get("email") == TEST_EMAIL) and ok
if ok:
    token = body["access_token"]
    print(f"           Token: {token[:30]}…")
all_passed = all_passed and ok

# ── 3. Duplicate Register (should 409) ────────────────────────────────────────
section("3. Duplicate Registration Guard")
status2, body2 = api("POST", "/api/auth/register", {
    "name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD
})
ok = check("Duplicate register → 409", status2 == 409, body2)
all_passed = all_passed and ok

# ── 4. Login ──────────────────────────────────────────────────────────────────
section("4. Login (POST /api/auth/login)")
status, body = api("POST", "/api/auth/login", {
    "email": TEST_EMAIL, "password": TEST_PASSWORD
})
ok = check("Login → 200", status == 200, body)
ok = check("access_token present", bool(body.get("access_token"))) and ok
if ok:
    token = body["access_token"]  # use fresh token
ok2 = check("Wrong password → 401", True)  # tested below
status_w, _ = api("POST", "/api/auth/login", {"email": TEST_EMAIL, "password": "wrongpass"})
ok2 = check("Wrong password → 401", status_w == 401)
all_passed = all_passed and ok and ok2

# ── 5. /api/auth/me ───────────────────────────────────────────────────────────
section("5. Token Verification (GET /api/auth/me)")
status, body = api("GET", "/api/auth/me", token=token)
ok = check("/api/auth/me → 200", status == 200, body)
ok = check("email matches", body.get("email") == TEST_EMAIL) and ok
all_passed = all_passed and ok

# ── 6. Azure Vision (face/stress analysis) ───────────────────────────────────
section("6. Azure AI Vision  (POST /api/analyze)")
img_b64 = make_small_jpeg_b64()
if not img_b64:
    check("PIL available for test image", False, "pip install Pillow")
    all_passed = False
else:
    status, body = api("POST", "/api/analyze", {"image": img_b64}, token=token)
    ok = check("POST /api/analyze → 200", status == 200, body)
    ok = check("faces_detected key present", "faces_detected" in body) and ok
    ok = check("message returned", bool(body.get("message"))) and ok
    # Azure responded (even if no face detected in grey box — that's correct)
    print(f"           faces_detected : {body.get('faces_detected')}")
    print(f"           message        : {body.get('message')}")
    if body.get("stress"):
        print(f"           stress score   : {body['stress'].get('score')}")
        print(f"           stress level   : {body['stress'].get('level')}")
    all_passed = all_passed and ok

# ── 7. DynamoDB sessions stored ───────────────────────────────────────────────
section("7. DynamoDB Session Storage (GET /api/sessions)")
status, body = api("GET", "/api/sessions", token=token)
ok = check("GET /api/sessions → 200", status == 200, body)
ok = check("sessions key present", "sessions" in body) and ok
count = body.get("count", 0)
print(f"           Sessions in DB : {count}")
# If face was detected, a session should exist
all_passed = all_passed and ok

# ── 8. Azure Language (mood journal) ─────────────────────────────────────────
section("8. Azure AI Language  (POST /api/journal)")
status, body = api("POST", "/api/journal",
    {"text": "I am feeling overwhelmed and very anxious about my exams today."},
    token=token)
ok = check("POST /api/journal → 200", status == 200, body)
ok = check("sentiment returned", bool(body.get("sentiment"))) and ok
ok = check("stress_score returned", body.get("stress_score") is not None) and ok
print(f"           sentiment    : {body.get('sentiment')}")
print(f"           stress_score : {body.get('stress_score')}")
print(f"           stress_level : {body.get('stress_level')}")
print(f"           advice       : {body.get('advice', '')[:80]}")
all_passed = all_passed and ok

# ── 9. Journal history in DB ──────────────────────────────────────────────────
section("9. DynamoDB Journal Storage (GET /api/journal/history)")
status, body = api("GET", "/api/journal/history", token=token)
ok = check("GET /api/journal/history → 200", status == 200, body)
ok = check("entries key present", "entries" in body) and ok
print(f"           Journal entries in DB : {body.get('count', 0)}")
all_passed = all_passed and ok

# ── 10. Cleanup ───────────────────────────────────────────────────────────────
section("10. Cleanup (removing test user from DynamoDB)")
try:
    import boto3
    from dotenv import dotenv_values
    env = dotenv_values()
    kwargs = {"region_name": env.get("AWS_REGION", "us-east-1"),
              "aws_access_key_id": env.get("AWS_ACCESS_KEY_ID"),
              "aws_secret_access_key": env.get("AWS_SECRET_ACCESS_KEY")}
    if env.get("AWS_SESSION_TOKEN"):
        kwargs["aws_session_token"] = env.get("AWS_SESSION_TOKEN")
    ddb   = boto3.resource("dynamodb", **kwargs)
    table = ddb.Table(env.get("DYNAMODB_USERS_TABLE", "stressdetect-users"))
    table.delete_item(Key={"email": TEST_EMAIL})
    check("Test user deleted from DynamoDB", True, TEST_EMAIL)
except Exception as e:
    check("Cleanup", False, str(e))

# ── Summary ───────────────────────────────────────────────────────────────────
section("SUMMARY")
if all_passed:
    print("  \033[92m🎉 All checks passed! Auth + DynamoDB + Azure AI all working.\033[0m\n")
else:
    print("  \033[91m⚠️  Some checks failed — see details above.\033[0m\n")
    sys.exit(1)

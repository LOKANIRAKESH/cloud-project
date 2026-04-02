"""
test_dynamodb.py — Quick integration smoke test.
Run: python test_dynamodb.py
"""

import os, sys, json
from dotenv import load_dotenv
load_dotenv()

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

REGION         = os.getenv("AWS_REGION", "us-east-1")
ACCESS_KEY     = os.getenv("AWS_ACCESS_KEY_ID")
SECRET_KEY     = os.getenv("AWS_SECRET_ACCESS_KEY")
SESSION_TOKEN  = os.getenv("AWS_SESSION_TOKEN")
USERS_TABLE    = os.getenv("DYNAMODB_USERS_TABLE",    "stressdetect-users")
SESSIONS_TABLE = os.getenv("DYNAMODB_SESSIONS_TABLE", "stressdetect-sessions")
JOURNAL_TABLE  = os.getenv("DYNAMODB_JOURNAL_TABLE",  "stressdetect-journal")

PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"

def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")

def check(label, ok, detail=""):
    status = PASS if ok else FAIL
    print(f"  {status}  {label}")
    if detail:
        print(f"       {detail}")
    return ok

all_passed = True

# ── 1. Credentials loaded ─────────────────────────────────────────────────────
section("1. Credentials from .env")
check("AWS_ACCESS_KEY_ID set",   bool(ACCESS_KEY),    ACCESS_KEY[:8]+"…" if ACCESS_KEY else "MISSING")
check("AWS_SECRET_ACCESS_KEY set", bool(SECRET_KEY),  "***hidden***" if SECRET_KEY else "MISSING")
check("AWS_SESSION_TOKEN set",   bool(SESSION_TOKEN), "present (temporary creds)" if SESSION_TOKEN else "not set (permanent key)")
check("AWS_REGION set",          bool(REGION),        REGION)

# ── 2. boto3 connection ───────────────────────────────────────────────────────
section("2. AWS DynamoDB Connection")
try:
    kwargs = dict(region_name=REGION,
                  aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY)
    if SESSION_TOKEN:
        kwargs["aws_session_token"] = SESSION_TOKEN

    ddb = boto3.resource("dynamodb", **kwargs)

    # List tables — this makes an actual API call
    existing_tables = [t.name for t in ddb.tables.all()]
    check("Connected to DynamoDB", True, f"Region: {REGION}")
    check(f"Table '{USERS_TABLE}' exists",    USERS_TABLE    in existing_tables, f"Tables found: {existing_tables}")
    check(f"Table '{SESSIONS_TABLE}' exists", SESSIONS_TABLE in existing_tables)
    check(f"Table '{JOURNAL_TABLE}' exists",  JOURNAL_TABLE  in existing_tables)

except NoCredentialsError:
    check("Connected to DynamoDB", False, "No credentials found — check .env")
    all_passed = False
    sys.exit(1)
except ClientError as e:
    code = e.response["Error"]["Code"]
    msg  = e.response["Error"]["Message"]
    check("Connected to DynamoDB", False, f"{code}: {msg}")
    all_passed = False
    sys.exit(1)

# ── 3. Write & Read (users table) ─────────────────────────────────────────────
section("3. Write → Read → Delete (users table)")
TEST_EMAIL = "_test_probe@stressdetect.local"

try:
    table = ddb.Table(USERS_TABLE)

    # Write
    table.put_item(Item={
        "email": TEST_EMAIL,
        "id": "test-probe-id",
        "name": "Test Probe",
        "hashed_password": "x",
        "created_at": "2026-01-01T00:00:00+00:00",
    })
    check("put_item (write)", True)

    # Read back
    resp = table.get_item(Key={"email": TEST_EMAIL})
    item = resp.get("Item")
    check("get_item (read back)", item is not None and item.get("name") == "Test Probe",
          f"name={item.get('name') if item else 'NOT FOUND'}")

    # Delete cleanup
    table.delete_item(Key={"email": TEST_EMAIL})
    check("delete_item (cleanup)", True)

except ClientError as e:
    check("Write/Read/Delete", False, str(e))
    all_passed = False

# ── 4. Write & Read (sessions table) ─────────────────────────────────────────
section("4. Write → Read → Delete (sessions table)")
TEST_USER = "probe-user-001"
TEST_TS   = "2026-01-01T00:00:00+00:00"

try:
    table = ddb.Table(SESSIONS_TABLE)
    table.put_item(Item={
        "userId": TEST_USER, "timestamp": TEST_TS,
        "id": "probe-session", "score": "42.5", "level": "Moderate",
        "emotions": {"neutral": "0.6", "happiness": "0.4"},
    })
    check("put_item sessions", True)

    from boto3.dynamodb.conditions import Key
    resp  = table.query(KeyConditionExpression=Key("userId").eq(TEST_USER))
    items = resp.get("Items", [])
    check("query sessions", len(items) > 0, f"{len(items)} item(s) found")

    table.delete_item(Key={"userId": TEST_USER, "timestamp": TEST_TS})
    check("delete_item sessions", True)

except ClientError as e:
    check("Sessions table CRUD", False, str(e))
    all_passed = False

# ── 5. API health endpoint ─────────────────────────────────────────────────────
section("5. FastAPI /health endpoint")
try:
    import urllib.request
    PORT = os.getenv("PORT", "8001")
    with urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=5) as r:
        body = json.loads(r.read())
    check("/health returns 200",  r.status == 200, f"HTTP {r.status}")
    check("status == ok",         body.get("status") == "ok", str(body))
    check("db == DynamoDB",       body.get("db") == "DynamoDB", str(body))
except Exception as e:
    check("/health reachable", False, str(e))
    all_passed = False

# ── Summary ────────────────────────────────────────────────────────────────────
section("Summary")
if all_passed:
    print("  \033[92m🎉 All checks passed — DynamoDB + API are fully operational!\033[0m\n")
else:
    print("  \033[91m⚠️  Some checks failed — see details above.\033[0m\n")
    sys.exit(1)

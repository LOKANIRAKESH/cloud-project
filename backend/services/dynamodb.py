"""
dynamodb.py – AWS DynamoDB service for StressDetect.

Tables (PAY_PER_REQUEST / on-demand billing):
  stressdetect-users     – user accounts      (PK: email)
  stressdetect-sessions  – stress scan history (PK: userId, SK: timestamp)
  stressdetect-journal   – mood journal        (PK: userId, SK: timestamp)

Boto3 resource API is used (higher-level than client).
Floats are transparently converted to/from Decimal as required by DynamoDB.
"""

import os
import uuid
import logging
import threading
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

AWS_REGION        = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY    = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY    = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN", "")  # required for temporary credentials

USERS_TABLE    = os.getenv("DYNAMODB_USERS_TABLE",    "stressdetect-users")
SESSIONS_TABLE = os.getenv("DYNAMODB_SESSIONS_TABLE", "stressdetect-sessions")
JOURNAL_TABLE  = os.getenv("DYNAMODB_JOURNAL_TABLE",  "stressdetect-journal")

# Optional: DynamoDB Local endpoint for dev/testing
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT_URL", "")  # e.g. http://localhost:8000

# ── Singleton ──────────────────────────────────────────────────────────────────

_lock     = threading.Lock()
_resource = None
_tables:  dict = {}


def _get_resource():
    """Return a thread-safe DynamoDB resource (lazy singleton)."""
    global _resource
    with _lock:
        if _resource is None:
            kwargs: dict = {"region_name": AWS_REGION}
            if AWS_ACCESS_KEY and AWS_SECRET_KEY:
                kwargs["aws_access_key_id"]     = AWS_ACCESS_KEY
                kwargs["aws_secret_access_key"] = AWS_SECRET_KEY
                if AWS_SESSION_TOKEN:
                    kwargs["aws_session_token"] = AWS_SESSION_TOKEN
            if DYNAMODB_ENDPOINT:
                kwargs["endpoint_url"] = DYNAMODB_ENDPOINT
            _resource = boto3.resource("dynamodb", **kwargs)
            logger.info("[DynamoDB] Resource initialised  region=%s", AWS_REGION)
    return _resource


def _get_table(name: str):
    if name not in _tables:
        _tables[name] = _get_resource().Table(name)
    return _tables[name]


# ── Table bootstrap ───────────────────────────────────────────────────────────

def ensure_tables() -> None:
    """
    Create DynamoDB tables if they do not already exist.
    Safe to call on every startup — uses PAY_PER_REQUEST (no capacity planning).
    """
    ddb      = _get_resource()
    existing = {t.name for t in ddb.tables.all()}

    table_specs = [
        {
            "TableName": USERS_TABLE,
            "KeySchema": [
                {"AttributeName": "email", "KeyType": "HASH"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [{"Key": "app", "Value": "stressdetect"}],
        },
        {
            "TableName": SESSIONS_TABLE,
            "KeySchema": [
                {"AttributeName": "userId",    "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "userId",    "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [{"Key": "app", "Value": "stressdetect"}],
        },
        {
            "TableName": JOURNAL_TABLE,
            "KeySchema": [
                {"AttributeName": "userId",    "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "userId",    "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "Tags": [{"Key": "app", "Value": "stressdetect"}],
        },
    ]

    for spec in table_specs:
        tname = spec["TableName"]
        if tname in existing:
            logger.info("[DynamoDB] Table already exists: %s", tname)
            continue
        try:
            ddb.create_table(**spec)
            logger.info("[DynamoDB] Created table: %s", tname)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code == "ResourceInUseException":
                logger.info("[DynamoDB] Table race-condition skip: %s", tname)
            else:
                logger.exception("[DynamoDB] Failed to create table %s", tname)
                raise


# ── Type helpers ──────────────────────────────────────────────────────────────

def _to_dec(val):
    """Recursively convert float → Decimal (required by boto3 resource API)."""
    if isinstance(val, float):
        return Decimal(str(val))
    if isinstance(val, dict):
        return {k: _to_dec(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_to_dec(v) for v in val]
    return val


def _from_dec(val):
    """Recursively convert Decimal → float for JSON serialisation."""
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, dict):
        return {k: _from_dec(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_from_dec(v) for v in val]
    return val


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(email: str, name: str, hashed_password: str) -> dict:
    """Insert a new user document. Raises if the email already exists."""
    table = _get_table(USERS_TABLE)
    user  = {
        "id":              str(uuid.uuid4()),
        "email":           email.lower().strip(),
        "name":            name.strip(),
        "hashed_password": hashed_password,
        "created_at":      datetime.now(timezone.utc).isoformat(),
    }
    # condition_expression prevents silent overwrites
    table.put_item(
        Item=user,
        ConditionExpression="attribute_not_exists(email)",
    )
    logger.info("[DynamoDB] Created user: %s", email)
    return user


def get_user_by_email(email: str) -> dict | None:
    """Fetch a user by email (primary key lookup — O(1))."""
    table = _get_table(USERS_TABLE)
    resp  = table.get_item(Key={"email": email.lower().strip()})
    item  = resp.get("Item")
    return _from_dec(item) if item else None


# ── Sessions (stress scans) ───────────────────────────────────────────────────

def save_session(user_id: str, score: float, level: str, emotions: dict) -> dict:
    """Persist a stress scan reading."""
    table = _get_table(SESSIONS_TABLE)
    ts    = datetime.now(timezone.utc).isoformat()
    doc   = {
        "userId":    user_id,
        "timestamp": ts,
        "id":        str(uuid.uuid4()),
        "score":     _to_dec(score),
        "level":     level,
        "emotions":  _to_dec(emotions),
    }
    table.put_item(Item=doc)
    logger.debug("[DynamoDB] Saved session for user %s  score=%s", user_id, score)
    return _from_dec(doc)


def get_sessions(user_id: str, limit: int = 50) -> list:
    """Return the N most-recent stress sessions for a user (newest first)."""
    table = _get_table(SESSIONS_TABLE)
    resp  = table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
        ScanIndexForward=False,   # descending timestamp
        Limit=limit,
    )
    return [_from_dec(item) for item in resp.get("Items", [])]


# ── Journal entries ───────────────────────────────────────────────────────────

def save_journal_entry(
    user_id: str,
    text: str,
    sentiment: str,
    stress_score: float,
    confidence: dict,
) -> dict:
    """Persist a mood journal entry."""
    table = _get_table(JOURNAL_TABLE)
    ts    = datetime.now(timezone.utc).isoformat()
    doc   = {
        "userId":       user_id,
        "timestamp":    ts,
        "id":           str(uuid.uuid4()),
        "text":         text,
        "sentiment":    sentiment,
        "stress_score": _to_dec(stress_score),
        "confidence":   _to_dec(confidence),
    }
    table.put_item(Item=doc)
    logger.debug("[DynamoDB] Saved journal for user %s  sentiment=%s", user_id, sentiment)
    return _from_dec(doc)


def get_journal_entries(user_id: str, limit: int = 30) -> list:
    """Return the N most-recent journal entries for a user (newest first)."""
    table = _get_table(JOURNAL_TABLE)
    resp  = table.query(
        KeyConditionExpression=Key("userId").eq(user_id),
        ScanIndexForward=False,
        Limit=limit,
    )
    return [_from_dec(item) for item in resp.get("Items", [])]

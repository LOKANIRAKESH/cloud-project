"""
cosmos_db.py – Azure Cosmos DB service for StressDetect.

Collections:
  users    – user accounts (partition key: /email)
  sessions – stress scan readings (partition key: /userId)
  journal  – mood journal entries (partition key: /userId)
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, PartitionKey, exceptions

logger = logging.getLogger(__name__)

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "")
COSMOS_KEY      = os.getenv("COSMOS_KEY", "")
COSMOS_DB_NAME  = os.getenv("COSMOS_DB", "stressdetect")

_client = None
_db     = None

def _get_db():
    global _client, _db
    if _db is None:
        _client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
        _db = _client.create_database_if_not_exists(id=COSMOS_DB_NAME)
        # Create containers if they don't exist
        _db.create_container_if_not_exists(
            id="users",
            partition_key=PartitionKey(path="/email"),
            offer_throughput=400,
        )
        _db.create_container_if_not_exists(
            id="sessions",
            partition_key=PartitionKey(path="/userId"),
            offer_throughput=400,
        )
        _db.create_container_if_not_exists(
            id="journal",
            partition_key=PartitionKey(path="/userId"),
            offer_throughput=400,
        )
        logger.info("[CosmosDB] Connected and containers ready")
    return _db


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(email: str, name: str, hashed_password: str) -> dict:
    db = _get_db()
    container = db.get_container_client("users")
    user = {
        "id":              str(uuid.uuid4()),
        "email":           email.lower().strip(),
        "name":            name.strip(),
        "hashed_password": hashed_password,
        "created_at":      datetime.now(timezone.utc).isoformat(),
    }
    container.create_item(body=user)
    logger.info(f"[CosmosDB] Created user: {email}")
    return user


def get_user_by_email(email: str) -> dict | None:
    db = _get_db()
    container = db.get_container_client("users")
    query = "SELECT * FROM c WHERE c.email = @email"
    params = [{"name": "@email", "value": email.lower().strip()}]
    items = list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))
    return items[0] if items else None


# ── Sessions (stress scans) ───────────────────────────────────────────────────

def save_session(user_id: str, score: float, level: str, emotions: dict) -> dict:
    db = _get_db()
    container = db.get_container_client("sessions")
    doc = {
        "id":        str(uuid.uuid4()),
        "userId":    user_id,
        "score":     score,
        "level":     level,
        "emotions":  emotions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    container.create_item(body=doc)
    return doc


def get_sessions(user_id: str, limit: int = 50) -> list:
    db = _get_db()
    container = db.get_container_client("sessions")
    query = "SELECT * FROM c WHERE c.userId = @uid ORDER BY c.timestamp DESC OFFSET 0 LIMIT @lim"
    params = [{"name": "@uid", "value": user_id}, {"name": "@lim", "value": limit}]
    return list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))


# ── Journal entries ───────────────────────────────────────────────────────────

def save_journal_entry(user_id: str, text: str, sentiment: str, stress_score: float, confidence: dict) -> dict:
    db = _get_db()
    container = db.get_container_client("journal")
    doc = {
        "id":           str(uuid.uuid4()),
        "userId":       user_id,
        "text":         text,
        "sentiment":    sentiment,
        "stress_score": stress_score,
        "confidence":   confidence,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }
    container.create_item(body=doc)
    return doc


def get_journal_entries(user_id: str, limit: int = 30) -> list:
    db = _get_db()
    container = db.get_container_client("journal")
    query = "SELECT * FROM c WHERE c.userId = @uid ORDER BY c.timestamp DESC OFFSET 0 LIMIT @lim"
    params = [{"name": "@uid", "value": user_id}, {"name": "@lim", "value": limit}]
    return list(container.query_items(query=query, parameters=params, enable_cross_partition_query=True))

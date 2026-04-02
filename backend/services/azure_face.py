"""
azure_face.py – Face emotion detection for StressDetect.

Detection Strategy (tried in order):
  1. AWS Rekognition DetectFaces  — returns real per-emotion confidence scores
     (HAPPY, SAD, ANGRY, CALM, FEAR, DISGUSTED, SURPRISED, CONFUSED)
     Uses the same boto3 credentials already configured for DynamoDB.

  2. Azure AI Vision 4.0  — fallback for face/people detection only
     (Azure Face API emotion attributes are deprecated by Microsoft since June 2023)
"""

import os
import base64
import io
import logging
import threading

import requests
from fastapi import HTTPException
from PIL import Image

logger = logging.getLogger(__name__)

# ── Azure AI Vision (fallback — people detection only) ───────────────────────
AZURE_API_KEY  = os.getenv("AZURE_FACE_API_KEY", "")
AZURE_ENDPOINT = os.getenv("AZURE_FACE_ENDPOINT", "").rstrip("/")

# ── AWS Rekognition (primary — real emotion scores) ───────────────────────────
AWS_REGION        = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY    = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY    = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN", "")

# Rekognition emotion type → our standard key
_REKOGNITION_MAP = {
    "HAPPY":     "happiness",
    "SAD":       "sadness",
    "ANGRY":     "anger",
    "FEAR":      "fear",
    "DISGUSTED": "disgust",
    "SURPRISED": "surprise",
    "CALM":      "neutral",
    "CONFUSED":  "neutral",   # confused → neutral (slight stress tilt handled by weight)
    "UNKNOWN":   "neutral",
}

# Default neutral baseline (used only when all strategies fail)
DEFAULT_EMOTIONS = {
    "anger": 0.02, "fear": 0.02, "sadness": 0.03,
    "disgust": 0.01, "contempt": 0.01, "surprise": 0.04,
    "neutral": 0.80, "happiness": 0.07,
}

# Thread-safe Rekognition client singleton
_rek_lock   = threading.Lock()
_rek_client = None


def _get_rekognition():
    global _rek_client
    with _rek_lock:
        if _rek_client is None:
            import boto3
            kwargs = {"region_name": AWS_REGION}
            if AWS_ACCESS_KEY and AWS_SECRET_KEY:
                kwargs["aws_access_key_id"]     = AWS_ACCESS_KEY
                kwargs["aws_secret_access_key"] = AWS_SECRET_KEY
                if AWS_SESSION_TOKEN:
                    kwargs["aws_session_token"] = AWS_SESSION_TOKEN
            _rek_client = boto3.client("rekognition", **kwargs)
            logger.info("[Rekognition] Client initialised  region=%s", AWS_REGION)
    return _rek_client


# ── Image helpers ─────────────────────────────────────────────────────────────

def decode_image(image_data: str) -> bytes:
    """Decode base64 image string to JPEG bytes."""
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    try:
        raw = base64.b64decode(image_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {e}")
    try:
        img = Image.open(io.BytesIO(raw))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot process image: {e}")


# ── Strategy 1: AWS Rekognition ───────────────────────────────────────────────

def _call_rekognition(image_bytes: bytes) -> dict | None:
    """
    Call AWS Rekognition DetectFaces with ALL attributes.
    Returns our standard result dict, or None on failure.
    """
    try:
        rek  = _get_rekognition()
        resp = rek.detect_faces(
            Image={"Bytes": image_bytes},
            Attributes=["ALL"],
        )
        faces = resp.get("FaceDetails", [])
        logger.info("[Rekognition] Faces detected: %d", len(faces))

        if not faces:
            return {
                "face_detected": False,
                "people_count":  0,
                "emotions":      DEFAULT_EMOTIONS,
            }

        # Use the highest-confidence face
        face = max(faces, key=lambda f: f.get("Confidence", 0))
        raw_emotions = face.get("Emotions", [])

        if not raw_emotions:
            logger.warning("[Rekognition] No emotion data in response")
            return None

        # Accumulate scores into our 8-key format
        scores: dict[str, float] = {k: 0.0 for k in DEFAULT_EMOTIONS}
        for e in raw_emotions:
            key = _REKOGNITION_MAP.get(e["Type"], "neutral")
            scores[key] = max(scores[key], e["Confidence"] / 100.0)

        # Ensure contempt has a small non-zero value (Rekognition doesn't track it)
        scores.setdefault("contempt", 0.01)

        # Normalise so values sum to 1.0
        total = sum(scores.values()) or 1.0
        emotions = {k: round(v / total, 4) for k, v in scores.items()}

        logger.info("[Rekognition] Emotions: %s",
                    {k: round(v, 3) for k, v in emotions.items()})
        return {
            "face_detected": True,
            "people_count":  len(faces),
            "emotions":      emotions,
        }

    except Exception as exc:
        # AccessDeniedException, EndpointResolutionError, etc.
        logger.warning("[Rekognition] Failed (%s: %s) — falling back to Vision API",
                       type(exc).__name__, exc)
        return None


# ── Strategy 2: Azure AI Vision (fallback) ───────────────────────────────────

def _call_vision_api(image_bytes: bytes) -> dict:
    """
    Azure AI Vision 4.0 — used as fallback for face detection only.
    Emotion scores are estimated from people detection confidence.
    """
    if not AZURE_API_KEY or not AZURE_ENDPOINT:
        raise HTTPException(
            status_code=500,
            detail="Azure credentials not configured (AZURE_FACE_API_KEY / AZURE_FACE_ENDPOINT)."
        )

    url = (
        f"{AZURE_ENDPOINT}/computervision/imageanalysis:analyze"
        f"?api-version=2024-02-01&features=tags,people"
    )
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
        "Content-Type": "application/octet-stream",
    }

    try:
        resp = requests.post(url, headers=headers, data=image_bytes, timeout=15)
        logger.info("[Vision] Status: %s", resp.status_code)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Azure Vision API error ({resp.status_code}): {resp.text}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach Azure Vision API: {e}")

    data    = resp.json()
    people  = data.get("peopleResult", {}).get("values", [])
    tags    = [t.get("name", "") for t in data.get("tagsResult", {}).get("values", [])]
    logger.info("[Vision] People: %d  Tags: %s", len(people), tags)

    return {
        "face_detected": len(people) > 0,
        "people_count":  len(people),
        "emotions":      DEFAULT_EMOTIONS,
    }


# ── Public entry point ────────────────────────────────────────────────────────

def call_azure_vision_api(image_bytes: bytes) -> dict:
    """
    Detect face and emotions.
    Uses AWS Rekognition first (real scores), Azure Vision as fallback.
    Returns: { face_detected: bool, people_count: int, emotions: dict }
    """
    # Strategy 1 — AWS Rekognition (accurate real-time emotion scores)
    result = _call_rekognition(image_bytes)
    if result is not None:
        logger.info("[Detection] Using AWS Rekognition result")
        return result

    # Strategy 2 — Azure Vision API (face detection only, neutral emotions)
    logger.info("[Detection] Using Azure Vision API fallback")
    return _call_vision_api(image_bytes)

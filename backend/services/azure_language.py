"""
azure_language.py – Azure AI Language (Text Analytics) service.

Uses the same multi-service Cognitive Services key and endpoint.
Endpoint path: /language/:analyze-text?api-version=2023-04-01
"""

import os
import logging
import requests
from fastapi import HTTPException

logger = logging.getLogger(__name__)

AZURE_API_KEY  = os.getenv("AZURE_FACE_API_KEY", "")
AZURE_ENDPOINT = os.getenv("AZURE_FACE_ENDPOINT", "").rstrip("/")

# Map Azure sentiment → stress contribution (0.0–1.0)
SENTIMENT_STRESS = {
    "negative": 0.85,
    "mixed":    0.55,
    "neutral":  0.25,
    "positive": 0.05,
}


def analyze_sentiment(text: str) -> dict:
    """
    Call Azure AI Language analyze-text API for sentiment + key phrases.

    Returns:
        {
          sentiment: str,          # 'positive'|'negative'|'neutral'|'mixed'
          confidence: dict,        # {positive, neutral, negative} 0.0–1.0
          key_phrases: list[str],
          stress_score: float,     # 0–100
          stress_level: str,       # 'Low'|'Moderate'|'High'
          stress_color: str,       # hex color
          advice: str,
        }
    """
    if not AZURE_API_KEY or not AZURE_ENDPOINT:
        raise HTTPException(
            status_code=500,
            detail="Azure credentials not set in .env"
        )

    url = f"{AZURE_ENDPOINT}/language/:analyze-text?api-version=2023-04-01"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "kind": "SentimentAnalysis",
        "parameters": {"modelVersion": "latest", "opinionMining": True},
        "analysisInput": {
            "documents": [{"id": "1", "language": "en", "text": text}]
        },
    }

    logger.info(f"[Language] POST → {url}")
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        logger.info(f"[Language] Status: {resp.status_code} | Body: {resp.text[:400]}")
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Azure Language error ({resp.status_code}): {resp.text}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach Azure Language API: {e}")

    data = resp.json()
    doc  = data["results"]["documents"][0]

    sentiment   = doc["sentiment"]
    confidence  = doc["confidenceScores"]  # {positive, neutral, negative}
    key_phrases = []  # SentimentAnalysis doesn't return key phrases, need separate call

    # Compute stress score from sentiment
    raw_score   = SENTIMENT_STRESS.get(sentiment, 0.25)
    # Weight by negative confidence for finer granularity
    neg_conf    = confidence.get("negative", 0)
    stress_raw  = raw_score * 0.6 + neg_conf * 0.4
    stress_score = round(min(stress_raw * 100, 100), 1)

    if stress_score >= 70:
        level = "High"
        color = "#ef4444"
        advice = "Your words suggest high stress. Try jotting down 3 things you're grateful for, or step away for 5 minutes."
    elif stress_score >= 40:
        level = "Moderate"
        color = "#f59e0b"
        advice = "You seem a bit stressed. Take a few slow breaths and break your tasks into smaller steps."
    else:
        level = "Low"
        color = "#22c55e"
        advice = "Your mood looks positive! Keep up the great mental energy."

    return {
        "sentiment":    sentiment,
        "confidence":   confidence,
        "key_phrases":  key_phrases,
        "stress_score": stress_score,
        "stress_level": level,
        "stress_color": color,
        "advice":       advice,
    }

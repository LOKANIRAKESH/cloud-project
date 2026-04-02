# Stress score weights per emotion (0.0 – 1.0)
# Higher weight = contributes more to stress score
STRESS_WEIGHTS: dict[str, float] = {
    "anger":    0.95,
    "fear":     0.90,
    "sadness":  0.80,
    "disgust":  0.70,
    "contempt": 0.60,
    "surprise": 0.30,
    "neutral":  0.10,
    "happiness": 0.00,
}


def calculate_stress(emotions: dict) -> dict:
    """
    Compute a stress score (0–100) from Azure emotion probabilities.

    Args:
        emotions: dict mapping emotion name → probability (0.0–1.0)

    Returns:
        dict with score, level, color, advice
    """
    raw = sum(STRESS_WEIGHTS.get(emo, 0) * val for emo, val in emotions.items())
    score = round(min(raw * 100, 100), 1)

    if score >= 70:
        level  = "High"
        color  = "#ef4444"
        advice = ("You appear highly stressed. Consider taking a short break, "
                  "doing deep breathing exercises, or going for a short walk.")
    elif score >= 40:
        level  = "Moderate"
        color  = "#f59e0b"
        advice = ("You seem moderately stressed. Try relaxing your shoulders, "
                  "closing your eyes for 30 seconds, and taking a few deep breaths.")
    else:
        level  = "Low"
        color  = "#22c55e"
        advice = "You look calm and relaxed. Great job managing your stress — keep it up!"

    return {"score": score, "level": level, "color": color, "advice": advice}

from pydantic import BaseModel


class ImagePayload(BaseModel):
    """Request body for /api/analyze endpoint."""
    image: str


class JournalPayload(BaseModel):
    """Request body for /api/journal endpoint."""
    text: str


# ── Notifications ─────────────────────────────────────────────────────────────

class SendStressAlertPayload(BaseModel):
    """Request body for /api/notifications/send-stress-alert endpoint."""
    stress_score: float
    recommendation: str
    user_id: str | None = None  # Optional - ignored if provided


class SendJournalReminderPayload(BaseModel):
    """Request body for /api/notifications/send-journal-reminder endpoint."""
    streak_days: int = 0


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterPayload(BaseModel):
    name:     str
    email:    str
    password: str


class LoginPayload(BaseModel):
    email:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      str
    name:         str
    email:        str


# ── Existing result models ─────────────────────────────────────────────────────

class StressResult(BaseModel):
    score:  float
    level:  str
    color:  str
    advice: str


class AnalyzeResponse(BaseModel):
    faces_detected: int
    stress:         StressResult | None
    emotions:       dict | None
    face_rectangle: dict | None = None
    message:        str

"""
app.py – Main FastAPI application entry point.
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv

# load_dotenv() MUST be before service imports (they read os.getenv at module level)
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models.schemas import (
    ImagePayload, JournalPayload,
    RegisterPayload, LoginPayload, TokenResponse,
    SendStressAlertPayload, SendJournalReminderPayload,
)
from services.azure_face    import decode_image, call_azure_vision_api
from services.azure_language import analyze_sentiment
from services.auth          import hash_password, verify_password, create_token, get_current_user, get_optional_user
from services.dynamodb      import (
    ensure_tables,
    create_user, get_user_by_email,
    save_session, get_sessions,
    save_journal_entry, get_journal_entries,
)
from services.gmail_email import GmailEmailService
from services.aws_s3 import S3StorageService
from services.aws_cloudwatch import CloudWatchMonitoringService
from services.aws_lambda import LambdaServerlessService
from services.azure_text_analytics import AzureTextAnalyticsService
from services.azure_signalr import AzureSignalRService
from utils.stress import calculate_stress

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Helper Functions ──────────────────────────────────────────────────────────

def get_stress_recommendation(stress_level: str) -> str:
    """Get personalized recommendation based on stress level"""
    recommendations = {
        "low": "Great job managing your stress! Keep up the good work.",
        "moderate": "Consider taking a 5-minute break or doing some light stretching.",
        "high": "Your stress is elevated. Try deep breathing exercises or a short walk.",
        "critical": "You're experiencing high stress. Please take immediate action: breathe deeply, step outside, or talk to someone."
    }
    return recommendations.get(stress_level, "Take care of yourself!")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bootstrap services on startup."""
    logger.info("[Startup] Ensuring DynamoDB tables exist …")
    ensure_tables()
    logger.info("[Startup] DynamoDB ready.")
    
    # Initialize email service
    logger.info("[Startup] Initializing email service...")
    app.state.email_service = GmailEmailService()
    logger.info("[Startup] Gmail email service initialized.")
    
    # Initialize AWS Services
    logger.info("[Startup] Initializing AWS services...")
    app.state.s3_service = S3StorageService(
        bucket_name=os.getenv('AWS_S3_BUCKET', 'stressdetect-exports'),
        aws_region=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    # Create S3 bucket if it doesn't exist
    try:
        bucket_result = await app.state.s3_service.create_bucket_if_not_exists()
        logger.info(f"[Startup] S3 bucket: {bucket_result['status']} - {bucket_result['bucket']}")
    except Exception as e:
        logger.warning(f"[Startup] S3 bucket creation failed: {str(e)}")
    
    app.state.monitor_service = CloudWatchMonitoringService(aws_region=os.getenv('AWS_REGION', 'us-east-1'))
    app.state.lambda_service = LambdaServerlessService(aws_region=os.getenv('AWS_REGION', 'us-east-1'))
    logger.info("[Startup] AWS services initialized.")
    
    # Initialize Azure Services
    logger.info("[Startup] Initializing Azure services...")
    try:
        app.state.text_analytics_service = AzureTextAnalyticsService(
            api_key=os.getenv('AZURE_TEXT_ANALYTICS_KEY'),
            endpoint=os.getenv('AZURE_TEXT_ANALYTICS_ENDPOINT')
        )
        logger.info("[Startup] Azure Text Analytics initialized.")
    except Exception as e:
        logger.warning(f"[Startup] Azure Text Analytics failed: {e}")
    
    try:
        app.state.signalr_service = AzureSignalRService(
            hub_name='stressdetect',
            connection_string=os.getenv('AZURE_SIGNALR_CONNECTION_STRING')
        )
        logger.info("[Startup] Azure SignalR initialized.")
    except Exception as e:
        logger.warning(f"[Startup] Azure SignalR failed: {e}")
    
    logger.info("[Startup] All services ready. StressDetect API started.")
    yield
    logger.info("[Shutdown] StressDetect API stopped.")

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="StressDetect API",
    description="Real-time stress detection powered by Azure AI + AWS DynamoDB",
    version="2.1.0",
    lifespan=lifespan,
)

_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://localhost:4173",
)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global error handler ──────────────────────────────────────────────────────

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "StressDetect API", "version": "2.1.0", "db": "DynamoDB"}


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/api/auth/register", response_model=TokenResponse, tags=["Auth"])
async def register(payload: RegisterPayload):
    """Register a new user. Returns a JWT token."""
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = hash_password(payload.password)
    user   = create_user(
        email=payload.email,
        name=payload.name,
        hashed_password=hashed,
    )
    token = create_token(user["id"], user["email"], user["name"])
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        name=user["name"],
        email=user["email"],
    )


@app.post("/api/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(payload: LoginPayload):
    """Login with email + password. Returns a JWT token."""
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["id"], user["email"], user["name"])
    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        name=user["name"],
        email=user["email"],
    )


@app.get("/api/auth/me", tags=["Auth"])
async def me(current_user: dict = Depends(get_current_user)):
    """Return current user info from JWT."""
    return {"user_id": current_user["sub"], "email": current_user["email"], "name": current_user["name"]}


# ── Stress Analysis ───────────────────────────────────────────────────────────

@app.post("/api/analyze", tags=["Analysis"])
async def analyze_stress(
    payload: ImagePayload,
    current_user: dict | None = Depends(get_optional_user),
):
    """Analyze webcam frame. If authenticated, saves reading to Cosmos DB and sends email report."""
    image_bytes = decode_image(payload.image)
    result      = call_azure_vision_api(image_bytes)

    if not result["face_detected"]:
        return {
            "faces_detected": 0, "stress": None, "emotions": None,
            "message": "No person detected. Ensure your face is clearly visible.",
        }

    emotions = result["emotions"]
    stress   = calculate_stress(emotions)

    # Save to Cosmos DB if user is logged in
    if current_user:
        save_session(
            user_id=current_user["sub"],
            score=stress["score"],
            level=stress["level"],
            emotions={k: round(v * 100, 1) for k, v in emotions.items()},
        )
        
        # Get recent sessions for Lambda analysis
        sessions = get_sessions(user_id=current_user["sub"], limit=10)
        
        # Trigger Lambda for background stress pattern analysis
        try:
            lambda_result = await app.state.lambda_service.invoke_stress_analysis_lambda(
                user_id=current_user["sub"],
                sessions_data=sessions
            )
            logger.info(f"Lambda invoked: {lambda_result.get('request_id')}")
        except Exception as e:
            logger.warning(f"Lambda invocation failed: {str(e)}")
        
        # Monitor with CloudWatch
        try:
            await app.state.monitor_service.put_metric_data(
                namespace='StressDetect',
                metric_name='StressScore',
                value=stress["score"],
                unit='Percent'
            )
            logger.info(f"CloudWatch metric recorded: {stress['score']}%")
        except Exception as e:
            logger.warning(f"CloudWatch logging failed: {str(e)}")
        
        # Send email report after analysis
        try:
            user = get_user_by_email(current_user["email"])
            if user:
                recommendation = get_stress_recommendation(stress["level"])
                
                await app.state.email_service.send_analysis_report_email(
                    user_email=current_user["email"],
                    user_name=user.get('name', 'User'),
                    stress_score=stress["score"],
                    stress_level=stress["level"],
                    emotions={k: round(v * 100, 1) for k, v in emotions.items()},
                    recommendation=recommendation,
                    timestamp=datetime.now().isoformat()
                )
                logger.info(f"Analysis report email sent to {current_user['email']}")
        except Exception as e:
            logger.warning(f"Failed to send analysis report email: {str(e)}")

    return {
        "faces_detected": result["people_count"],
        "stress":         stress,
        "emotions":       {k: round(v * 100, 1) for k, v in emotions.items()},
        "face_rectangle": None,
        "message":        "Analysis complete. Report sent to email!",
    }


# ── Journal ───────────────────────────────────────────────────────────────────

@app.post("/api/journal", tags=["Analysis"])
async def analyze_journal(
    payload: JournalPayload,
    current_user: dict | None = Depends(get_optional_user),
):
    """Analyze mood journal entry. If authenticated, saves to Cosmos DB and sends email report."""
    result = analyze_sentiment(payload.text)

    if current_user:
        save_journal_entry(
            user_id=current_user["sub"],
            text=payload.text,
            sentiment=result["sentiment"],
            stress_score=result["stress_score"],
            confidence=result["confidence"],
        )
        
        # Send email report after journal analysis
        try:
            user = get_user_by_email(current_user["sub"])
            if user:
                await app.state.email_service.send_journal_analysis_email(
                    user_email=current_user["sub"],
                    user_name=user.get('name', 'User'),
                    journal_text=payload.text[:200],  # First 200 chars
                    sentiment=result["sentiment"],
                    stress_score=result["stress_score"],
                    confidence=result["confidence"],
                    timestamp=datetime.now().isoformat()
                )
                logger.info(f"Journal analysis report sent to {current_user['sub']}")
        except Exception as e:
            logger.warning(f"Failed to send journal analysis email: {str(e)}")

    return result


# ── Per-user history ──────────────────────────────────────────────────────────

@app.get("/api/sessions", tags=["History"])
async def get_user_sessions(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's stress scan history."""
    sessions = get_sessions(user_id=current_user["sub"])
    return {"sessions": sessions, "count": len(sessions)}


@app.get("/api/journal/history", tags=["History"])
async def get_user_journals(current_user: dict = Depends(get_current_user)):
    """Return the authenticated user's journal history."""
    entries = get_journal_entries(user_id=current_user["sub"])
    return {"entries": entries, "count": len(entries)}


# ── Cloud Services: Email Notifications ───────────────────────────────────────

@app.post("/api/notifications/send-stress-alert", tags=["Cloud Services"])
async def send_stress_alert(
    payload: SendStressAlertPayload,
    current_user: dict = Depends(get_current_user)
):
    """Send stress alert email via AWS SNS/SES"""
    try:
        # Get the current user's info from the JWT token
        user = get_user_by_email(current_user["email"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = await app.state.email_service.send_stress_alert_email(
            user_email=current_user["email"],
            stress_score=payload.stress_score,
            recommendation=payload.recommendation,
            user_name=current_user.get('name', 'User')
        )
        return result
    except Exception as e:
        logger.error(f"Error sending stress alert: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/notifications/send-journal-reminder", tags=["Cloud Services"])
async def send_journal_reminder(
    payload: SendJournalReminderPayload,
    current_user: dict = Depends(get_current_user)
):
    """Send journal reminder email"""
    try:
        user = get_user_by_email(current_user["email"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = await app.state.email_service.send_journal_reminder_email(
            user_email=current_user["email"],
            user_name=current_user.get('name', 'User'),
            streak_days=payload.streak_days
        )
        return result
    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Cloud Services: S3 Storage ────────────────────────────────────────────────

@app.post("/api/storage/backup-user-data", tags=["Cloud Services"])
async def backup_to_s3(current_user: dict = Depends(get_current_user)):
    """Backup user data to S3"""
    try:
        sessions = get_sessions(user_id=current_user["sub"])
        entries = get_journal_entries(user_id=current_user["sub"])
        
        backup_data = {
            "user_id": current_user["sub"],
            "backup_date": datetime.now().isoformat(),
            "sessions": sessions,
            "journal_entries": entries
        }
        
        result = await app.state.s3_service.backup_user_data(
            user_id=current_user["sub"],
            data=backup_data
        )
        return result
    except Exception as e:
        logger.error(f"Error backing up data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/storage/list-exports", tags=["Cloud Services"])
async def list_exports(current_user: dict = Depends(get_current_user)):
    """List user's S3 exports"""
    try:
        result = await app.state.s3_service.list_user_exports(
            user_id=current_user["sub"]
        )
        return result
    except Exception as e:
        logger.error(f"Error listing exports: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Cloud Services: Monitoring ────────────────────────────────────────────────

@app.get("/api/monitoring/health", tags=["Cloud Services"])
async def monitoring_health(current_user: dict = Depends(get_current_user)):
    """Get system monitoring health"""
    try:
        dashboard = await app.state.monitor_service.get_dashboard_data(hours=24)
        return dashboard
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Cloud Services: Real-time (SignalR) ───────────────────────────────────────

@app.get("/api/realtime/token", tags=["Cloud Services"])
async def get_signalr_token(current_user: dict = Depends(get_current_user)):
    """Get SignalR access token for real-time updates"""
    try:
        if not hasattr(app.state, 'signalr_service'):
            raise HTTPException(status_code=503, detail="SignalR service not available")
        
        token_info = await app.state.signalr_service.get_client_access_token(
            user_id=current_user["sub"],
            minutes_to_live=60
        )
        return token_info
    except Exception as e:
        logger.error(f"Error getting SignalR token: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/realtime/active-users", tags=["Cloud Services"])
async def get_active_users(current_user: dict = Depends(get_current_user)):
    """Get list of active connected users"""
    try:
        if not hasattr(app.state, 'signalr_service'):
            return {"total_active": 0, "users": []}
        
        active = app.state.signalr_service.get_active_users()
        return active
    except Exception as e:
        logger.error(f"Error getting active users: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Cloud Services: NLP Analysis ──────────────────────────────────────────────

@app.post("/api/nlp/analyze-sentiment", tags=["Cloud Services"])
async def analyze_sentiment_nlp(
    text: str,
    current_user: dict = Depends(get_current_user)
):
    """Analyze text sentiment using Azure Text Analytics"""
    try:
        if not hasattr(app.state, 'text_analytics_service'):
            raise HTTPException(status_code=503, detail="Text Analytics service not available")
        
        result = await app.state.text_analytics_service.analyze_journal_sentiment(
            journal_entry=text,
            entry_id=f"{current_user['sub']}_analysis"
        )
        return result
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Integrated Cloud Services: Data Export ────────────────────────────────────

@app.post("/api/export/user-data", tags=["Integration"])
async def export_user_data(current_user: dict = Depends(get_current_user)):
    """Export all user data to S3"""
    try:
        if not hasattr(app.state, 's3_service'):
            raise HTTPException(status_code=503, detail="S3 service not available")
        
        # Get user data
        sessions = get_sessions(user_id=current_user["email"], limit=None)
        journal = get_journal_entries(user_id=current_user["email"])
        
        # Export to S3
        result = await app.state.s3_service.backup_user_data(
            user_id=current_user["email"],
            user_data={
                "sessions": sessions,
                "journal": journal,
                "exported_at": datetime.now().isoformat()
            }
        )
        
        logger.info(f"User data exported for {current_user['email']}")
        return {"status": "exported", "location": result}
    except Exception as e:
        logger.error(f"Error exporting user data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/export/list", tags=["Integration"])
async def list_user_exports(current_user: dict = Depends(get_current_user)):
    """List all user exports from S3"""
    try:
        if not hasattr(app.state, 's3_service'):
            raise HTTPException(status_code=503, detail="S3 service not available")
        
        exports = await app.state.s3_service.list_user_exports(
            user_id=current_user["email"]
        )
        return {"exports": exports}
    except Exception as e:
        logger.error(f"Error listing exports: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Integrated Cloud Services: Lambda Background Jobs ────────────────────────

@app.post("/api/tasks/schedule-backup", tags=["Integration"])
async def schedule_backup(current_user: dict = Depends(get_current_user)):
    """Schedule automated backup via Lambda"""
    try:
        if not hasattr(app.state, 'lambda_service'):
            raise HTTPException(status_code=503, detail="Lambda service not available")
        
        user = get_user_by_email(current_user["email"])
        result = await app.state.lambda_service.invoke_backup_lambda(
            user_id=current_user["email"],
            user_data={"user": user}
        )
        
        logger.info(f"Backup scheduled for {current_user['email']}")
        return result
    except Exception as e:
        logger.error(f"Error scheduling backup: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/tasks/schedule-reminder", tags=["Integration"])
async def schedule_journal_reminder(
    day_of_week: int = 3,
    hour: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Schedule daily journal reminders via Lambda + EventBridge"""
    try:
        if not hasattr(app.state, 'lambda_service'):
            raise HTTPException(status_code=503, detail="Lambda service not available")
        
        result = await app.state.lambda_service.create_scheduled_journal_reminder(
            user_id=current_user["email"],
            email=current_user["email"]
        )
        
        logger.info(f"Journal reminder scheduled for {current_user['email']}")
        return result
    except Exception as e:
        logger.error(f"Error scheduling reminder: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Integrated Cloud Services: Monitoring ─────────────────────────────────────

@app.get("/api/analytics/dashboard", tags=["Integration"])
async def get_analytics_dashboard(
    hours: int = 24,
    current_user: dict = Depends(get_current_user)
):
    """Get analytics dashboard with CloudWatch metrics"""
    try:
        if not hasattr(app.state, 'monitor_service'):
            raise HTTPException(status_code=503, detail="Monitoring service not available")
        
        # Get CloudWatch dashboard
        dashboard = await app.state.monitor_service.get_dashboard_data(hours=hours)
        
        # Get user sessions for additional stats
        sessions = get_sessions(user_id=current_user["email"], limit=30)
        
        avg_stress = sum(s["score"] for s in sessions) / len(sessions) if sessions else 0
        
        return {
            "cloudwatch": dashboard,
            "user_stats": {
                "total_sessions": len(sessions),
                "average_stress": round(avg_stress, 2),
                "sessions": sessions
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analytics/event", tags=["Integration"])
async def log_analytics_event(
    event_name: str,
    event_data: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """Log custom analytics event to CloudWatch"""
    try:
        if not hasattr(app.state, 'monitor_service'):
            raise HTTPException(status_code=503, detail="Monitoring service not available")
        
        await app.state.monitor_service.put_metric_data(
            namespace='StressDetect/UserEvents',
            metric_name=event_name,
            value=1,
            unit='Count',
            dimensions={'UserId': current_user["email"]}
        )
        
        logger.info(f"Analytics event logged: {event_name}")
        return {"status": "logged", "event": event_name}
    except Exception as e:
        logger.error(f"Error logging event: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ── Serve React frontend (production) ────────────────────────────────────────
# The built Vite output is copied to backend/dist before packaging.
# In development this folder won't exist, so we skip it gracefully.

_DIST = os.path.join(os.path.dirname(__file__), "dist")

if os.path.isdir(_DIST):
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(_DIST, "assets")), name="assets")

    # Catch-all: serve index.html for all non-API routes (React Router)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        return FileResponse(os.path.join(_DIST, "index.html"))


# ── Dev server ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port   = int(os.getenv("PORT", 8001))
    debug  = os.getenv("ENVIRONMENT", "production").lower() == "development"
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=debug)

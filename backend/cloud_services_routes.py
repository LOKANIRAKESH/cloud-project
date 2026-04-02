"""
Cloud Services API Routes
Add these endpoints to backend/app.py to expose cloud services
"""

# ============================================================================
# ADD THESE IMPORTS TO TOP OF app.py
# ============================================================================

from services import (
    # Cloud services
    EmailNotificationService,
    S3StorageService,
    StorageType,
    CloudWatchMonitoringService,
    MetricType,
    LambdaServerlessService,
    AzureTextAnalyticsService,
    SentimentLevel,
    AzureSignalRService,
    SignalRMessageType,
)
from fastapi.responses import FileResponse, StreamingResponse
import io


# ============================================================================
# INITIALIZE CLOUD SERVICES IN LIFESPAN STARTUP
# ============================================================================

# AWS Services
email_service = EmailNotificationService(aws_region="us-east-1")
s3_service = S3StorageService(
    bucket_name="stressdetect-exports",
    aws_region="us-east-1"
)
monitor_service = CloudWatchMonitoringService(aws_region="us-east-1")
lambda_service = LambdaServerlessService(aws_region="us-east-1")

# Azure Services
text_analytics_service = AzureTextAnalyticsService(
    api_key=os.getenv("AZURE_TEXT_ANALYTICS_KEY"),
    endpoint=os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")
)
signalr_service = AzureSignalRService(
    hub_name="stressdetect",
    connection_string=os.getenv("AZURE_SIGNALR_CONNECTION_STRING")
)


# ============================================================================
# EMAIL NOTIFICATION ENDPOINTS (AWS SNS + SES)
# ============================================================================

@app.post("/api/notifications/send-stress-alert")
async def send_stress_alert_email(
    user_id: str = Query(...),
    stress_score: float = Query(...),
    recommendation: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Send stress alert email via AWS SES"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get user email from database
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        result = await email_service.send_stress_alert_email(
            user_email=user.get('email'),
            stress_score=stress_score,
            recommendation=recommendation,
            user_name=user.get('name', 'User')
        )
        
        # Log the action
        await audit_service.log_event(
            user_id, AuditEventType.SYSTEM_EVENT,
            "notifications", "send_stress_alert"
        )
        
        return result
    except Exception as e:
        logger.error(f"Error sending stress alert: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/notifications/send-journal-reminder")
async def send_journal_reminder_email(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Send journal reminder email"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get journal streak
        user_data = await db.get_user_data(user_id)
        streak = user_data.get('journal_streak', 0)
        
        result = await email_service.send_journal_reminder_email(
            user_email=user.get('email'),
            user_name=user.get('name', 'User'),
            streak_days=streak
        )
        
        return result
    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/notifications/send-weekly-summary")
async def send_weekly_summary_email(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Send weekly summary report via email"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get weekly summary
        summary = await analytics_service.get_weekly_summary(user_id)
        
        result = await email_service.send_weekly_summary_email(
            user_email=user.get('email'),
            user_name=user.get('name', 'User'),
            summary_data=summary
        )
        
        return result
    except Exception as e:
        logger.error(f"Error sending summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/notifications/subscribe-sns-topic")
async def subscribe_to_notifications(
    user_id: str = Query(...),
    topic_arn: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Subscribe user to SNS topic"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        user = await db.get_user(user_id)
        result = await email_service.subscribe_to_notifications(
            topic_arn=topic_arn,
            email=user.get('email')
        )
        return result
    except Exception as e:
        logger.error(f"Error subscribing to SNS: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# S3 STORAGE ENDPOINTS (AWS S3)
# ============================================================================

@app.post("/api/storage/upload-export")
async def upload_export_file(
    user_id: str = Query(...),
    file_name: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Upload exported file to S3"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get stress data and compile as bytes
        export_data = await export_service.export_stress_data(
            user_id, ExportFormat.CSV
        )
        
        result = await s3_service.upload_file(
            user_id=user_id,
            file_name=file_name,
            file_content=export_data,
            storage_type=StorageType.EXPORT
        )
        
        await audit_service.log_event(
            user_id, AuditEventType.DATA_EXPORT,
            "s3", "upload", metadata={"file": file_name}
        )
        
        return result
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/storage/list-exports")
async def list_user_exports(
    user_id: str = Query(...),
    limit: int = Query(50, ge=1, le=100),
    current_user: str = Depends(verify_token)
):
    """List all exports for user from S3"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await s3_service.list_user_exports(
            user_id=user_id,
            storage_type=StorageType.EXPORT,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error listing exports: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/storage/download/{s3_key}")
async def download_export(
    s3_key: str,
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Download file from S3"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        file_content = await s3_service.download_file(user_id, s3_key)
        
        # Return file for download
        return StreamingResponse(
            iter([file_content]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={s3_key.split('/')[-1]}"}
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/storage/backup-user-data")
async def backup_user_data_to_s3(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Backup all user data to S3"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Gather all user data
        sessions = await db.get_user_sessions(user_id, days=365)
        journal = await db.get_journal_entries(user_id, days=365)
        user_info = await db.get_user(user_id)
        
        backup_data = {
            "user_id": user_id,
            "backup_date": datetime.utcnow().isoformat(),
            "sessions": sessions,
            "journal_entries": journal,
            "user_info": user_info
        }
        
        result = await s3_service.backup_user_data(user_id, backup_data)
        
        return {
            "status": "backed_up",
            "backup_info": result,
            "items_backed_up": len(sessions) + len(journal)
        }
    except Exception as e:
        logger.error(f"Error backing up data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/storage/stats")
async def get_storage_stats(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Get storage usage statistics"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        stats = await s3_service.get_storage_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MONITORING ENDPOINTS (AWS CloudWatch)
# ============================================================================

@app.get("/api/monitoring/metrics/{metric_type}")
async def get_metrics(
    metric_type: str,
    user_id: str = Query(None),
    hours: int = Query(24, ge=1, le=720),
    current_user: str = Depends(verify_token)
):
    """Get metrics from CloudWatch"""
    try:
        # Parse metric type
        metric = MetricType(metric_type)
        
        from datetime import timedelta
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        stats = await monitor_service.get_metric_statistics(
            metric, start_time, end_time, period=3600
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/monitoring/dashboard")
async def get_monitoring_dashboard(
    user_id: str = Query(None),
    current_user: str = Depends(verify_token)
):
    """Get system monitoring dashboard"""
    try:
        dashboard = await monitor_service.get_dashboard_data(hours=24)
        return dashboard
    except Exception as e:
        logger.error(f"Error getting dashboard: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/monitoring/logs")
async def get_application_logs(
    log_group: str = Query("/stressdetect/api"),
    limit: int = Query(100, ge=1, le=500),
    current_user: str = Depends(verify_token)
):
    """Get recent application logs"""
    try:
        logs = await monitor_service.list_application_logs(
            log_group, limit=limit
        )
        return logs
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# SCHEDULED TASKS ENDPOINTS (AWS Lambda + EventBridge)
# ============================================================================

@app.post("/api/tasks/schedule-daily-reminder")
async def schedule_journal_reminder(
    user_id: str = Query(...),
    hour: int = Query(20, ge=0, le=23),
    current_user: str = Depends(verify_token)
):
    """Schedule daily journal reminder"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        user = await db.get_user(user_id)
        cron = f"cron(0 {hour} * * ? *)"
        
        result = await lambda_service.create_scheduled_journal_reminder(
            user_id=user_id,
            email=user.get('email'),
            cron_expression=cron
        )
        
        return result
    except Exception as e:
        logger.error(f"Error scheduling reminder: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/tasks/schedule-weekly-summary")
async def schedule_weekly_summary(
    user_id: str = Query(...),
    day_of_week: int = Query(0, ge=0, le=6),  # 0=Monday
    hour: int = Query(9, ge=0, le=23),
    current_user: str = Depends(verify_token)
):
    """Schedule weekly summary report"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        user = await db.get_user(user_id)
        
        result = await lambda_service.create_scheduled_weekly_summary(
            user_id=user_id,
            email=user.get('email'),
            day_of_week=day_of_week,
            hour=hour
        )
        
        return result
    except Exception as e:
        logger.error(f"Error scheduling summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks/scheduled-rules")
async def list_scheduled_rules(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """List scheduled rules for user"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        rules = await lambda_service.list_scheduled_rules(user_id)
        return rules
    except Exception as e:
        logger.error(f"Error listing rules: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/tasks/rule/{rule_name}")
async def delete_scheduled_rule(
    rule_name: str,
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Delete a scheduled rule"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await lambda_service.delete_scheduled_rule(rule_name)
        return result
    except Exception as e:
        logger.error(f"Error deleting rule: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# NLP ENDPOINTS (Azure Text Analytics)
# ============================================================================

@app.post("/api/nlp/analyze-journal-sentiment")
async def analyze_journal_sentiment(
    user_id: str = Query(...),
    entry_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Analyze sentiment of journal entry"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get journal entry
        entry = await db.get_journal_entry(user_id, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        result = await text_analytics_service.analyze_journal_sentiment(
            entry.get('content', ''),
            entry_id
        )
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/nlp/comprehensive-analysis")
async def comprehensive_journal_analysis(
    user_id: str = Query(...),
    entry_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Perform comprehensive NLP analysis"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        entry = await db.get_journal_entry(user_id, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        result = await text_analytics_service.perform_comprehensive_analysis(
            entry.get('content', ''),
            entry_id,
            user_id
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/nlp/journal-trends")
async def get_journal_trends(
    user_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(verify_token)
):
    """Get emotional trends from journal entries"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        entries = await db.get_journal_entries(user_id, days=days)
        
        result = await text_analytics_service.trend_analysis_on_journal_entries(
            entries, user_id
        )
        
        return result
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# REAL-TIME ENDPOINTS (Azure SignalR)
# ============================================================================

@app.get("/api/realtime/token")
async def get_signalr_token(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Get SignalR access token for client"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        token_info = await signalr_service.get_client_access_token(
            user_id=user_id,
            minutes_to_live=60
        )
        
        return token_info
    except Exception as e:
        logger.error(f"Error getting SignalR token: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/realtime/active-users")
async def get_active_realtime_users(
    current_user: str = Depends(verify_token)
):
    """Get list of active connected users"""
    try:
        active = signalr_service.get_active_users()
        return active
    except Exception as e:
        logger.error(f"Error getting active users: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# MIDDLEWARE TO LOG ALL API REQUESTS
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests to CloudWatch"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000  # Convert to ms
    
    # Extract user ID from token if available
    user_id = None
    try:
        if "authorization" in request.headers:
            token = request.headers["authorization"].split(" ")[1]
            payload = decode_token(token)  # Your existing decode function
            user_id = payload.get("sub")
    except:
        pass
    
    # Log to CloudWatch
    try:
        await monitor_service.log_api_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            response_time_ms=process_time,
            user_id=user_id
        )
    except:
        pass  # Don't fail request if logging fails
    
    return response


# ============================================================================
# END OF CLOUD SERVICES ROUTES
# ============================================================================

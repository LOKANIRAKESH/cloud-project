"""
Enhanced API Routes - New endpoints for analytics, recommendations, and advanced features
Add these routes to backend/app.py
"""

# ============================================================================
# ADD THESE IMPORTS TO THE TOP OF app.py
# ============================================================================
from services.analytics import AnalyticsService
from services.recommendations import RecommendationsService
from services.notifications import NotificationsService, NotificationType
from services.audit import AuditLogsService, AuditEventType
from services.export import ExportService, ExportFormat
from services.prediction import PredictionService

# ============================================================================
# INITIALIZE SERVICES AFTER CREATING DYNAMODB SERVICE
# ============================================================================
# In the lifespan context manager, after initializing DynamoDB:
analytics_service = AnalyticsService(db)
recommendations_service = RecommendationsService(analytics_service)
notifications_service = NotificationsService(db)
audit_service = AuditLogsService(db)
export_service = ExportService(db)
prediction_service = PredictionService(db)

# ============================================================================
# ADD THESE ROUTE GROUPS TO app.py
# ============================================================================

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================
@app.get("/api/analytics/stress-trends")
async def get_stress_trends(
    user_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(verify_token)
):
    """Get stress trends over specified period"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        trends = await analytics_service.get_stress_trends(user_id, days)
        await audit_service.log_event(
            user_id, AuditEventType.SYSTEM_EVENT, 
            "analytics", "view_stress_trends"
        )
        return trends
    except Exception as e:
        logger.error(f"Error getting stress trends: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/analytics/emotion-distribution")
async def get_emotion_distribution(
    user_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(verify_token)
):
    """Get emotion distribution analysis"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        emotions = await analytics_service.get_emotion_distribution(user_id, days)
        return emotions
    except Exception as e:
        logger.error(f"Error getting emotion distribution: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/analytics/weekly-summary")
async def get_weekly_summary(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Get weekly summary statistics"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        summary = await analytics_service.get_weekly_summary(user_id)
        return summary
    except Exception as e:
        logger.error(f"Error getting weekly summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/analytics/insights")
async def get_stress_insights(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Get AI-driven insights on stress patterns"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        insights = await analytics_service.get_stress_insights(user_id)
        return insights
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/analytics/peak-hours")
async def get_peak_stress_hours(
    user_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(verify_token)
):
    """Get peak stress hours analysis"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        peak_hours = await analytics_service.get_peak_stress_hours(user_id, days)
        return peak_hours
    except Exception as e:
        logger.error(f"Error getting peak hours: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# RECOMMENDATIONS ENDPOINTS
# ============================================================================
@app.get("/api/recommendations/personalized")
async def get_personalized_recommendations(
    user_id: str = Query(...),
    limit: int = Query(5, ge=1, le=20),
    current_user: str = Depends(verify_token)
):
    """Get personalized wellness recommendations"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        recommendations = await recommendations_service.get_personalized_recommendations(user_id, limit)
        await audit_service.log_event(
            user_id, AuditEventType.SYSTEM_EVENT,
            "recommendations", "view_personalized"
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/recommendations/daily")
async def get_daily_recommendation(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Get daily recommendation"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        recommendation = await recommendations_service.get_daily_recommendation(user_id)
        return recommendation
    except Exception as e:
        logger.error(f"Error getting daily recommendation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/recommendations/by-time")
async def get_recommendations_by_time(
    user_id: str = Query(...),
    time_available_minutes: int = Query(15, ge=1, le=120),
    current_user: str = Depends(verify_token)
):
    """Get recommendations filtered by available time"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        recommendations = await recommendations_service.get_recommendations_by_time(
            user_id, time_available_minutes
        )
        return recommendations
    except Exception as e:
        logger.error(f"Error getting time-filtered recommendations: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================
@app.get("/api/predict/stress-level")
async def predict_stress_level(
    user_id: str = Query(...),
    hours_ahead: int = Query(24, ge=1, le=168),
    current_user: str = Depends(verify_token)
):
    """Predict stress level for specified hours ahead"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        prediction = await prediction_service.predict_stress_level(user_id, hours_ahead)
        return prediction
    except Exception as e:
        logger.error(f"Error predicting stress level: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/predict/weekly-pattern")
async def predict_weekly_pattern(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Predict weekly stress patterns"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        pattern = await prediction_service.predict_weekly_pattern(user_id)
        return pattern
    except Exception as e:
        logger.error(f"Error predicting weekly pattern: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/predict/triggers")
async def predict_stress_triggers(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Identify potential stress triggers"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        triggers = await prediction_service.predict_stress_triggers(user_id)
        return triggers
    except Exception as e:
        logger.error(f"Error identifying triggers: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/predict/intervention-time")
async def predict_intervention_time(
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Predict optimal time for stress interventions"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        optimal_time = await prediction_service.predict_optimal_intervention_time(user_id)
        return optimal_time
    except Exception as e:
        logger.error(f"Error predicting intervention time: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================
@app.get("/api/export/stress-data")
async def export_stress_data(
    user_id: str = Query(...),
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(verify_token)
):
    """Export stress data in specified format"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        export_format = ExportFormat(format)
        data = await export_service.export_stress_data(user_id, export_format, days)
        
        await audit_service.log_event(
            user_id, AuditEventType.DATA_EXPORT,
            "stress_data", "export", metadata={"format": format, "days": days}
        )
        
        filename = export_service.get_export_filename(user_id, export_format, "stress")
        return {
            "data": data,
            "filename": filename,
            "format": format
        }
    except Exception as e:
        logger.error(f"Error exporting stress data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/export/journal")
async def export_journal_entries(
    user_id: str = Query(...),
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(verify_token)
):
    """Export journal entries in specified format"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        export_format = ExportFormat(format)
        data = await export_service.export_journal_entries(user_id, export_format, days)
        
        await audit_service.log_event(
            user_id, AuditEventType.DATA_EXPORT,
            "journal", "export", metadata={"format": format, "days": days}
        )
        
        filename = export_service.get_export_filename(user_id, export_format, "journal")
        return {
            "data": data,
            "filename": filename,
            "format": format
        }
    except Exception as e:
        logger.error(f"Error exporting journal: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/export/comprehensive-report")
async def export_comprehensive_report(
    user_id: str = Query(...),
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(verify_token)
):
    """Export comprehensive report"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        export_format = ExportFormat(format)
        report = await export_service.export_comprehensive_report(user_id, export_format, days)
        
        await audit_service.log_event(
            user_id, AuditEventType.DATA_EXPORT,
            "comprehensive_report", "export", metadata={"format": format}
        )
        
        filename = export_service.get_export_filename(user_id, export_format, "report")
        return {
            "report": report,
            "filename": filename,
            "format": format
        }
    except Exception as e:
        logger.error(f"Error exporting comprehensive report: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================
@app.get("/api/admin/audit-logs/user")
async def get_user_audit_logs(
    user_id: str = Query(...),
    limit: int = Query(50, ge=1, le=100),
    current_user: str = Depends(verify_token)
):
    """Get audit logs for a user (admin or self)"""
    # Allow users to view their own logs, or admin to view any
    if current_user != user_id:  # In production, check admin role
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        logs = await audit_service.get_user_audit_logs(user_id, limit)
        return logs
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/activity-summary")
async def get_activity_summary(
    user_id: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: str = Depends(verify_token)
):
    """Get user activity summary"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        summary = await audit_service.get_user_activity_summary(user_id, days)
        return summary
    except Exception as e:
        logger.error(f"Error generating activity summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# NOTIFICATIONS ENDPOINTS
# ============================================================================
@app.get("/api/notifications")
async def get_notifications(
    user_id: str = Query(...),
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    current_user: str = Depends(verify_token)
):
    """Get user notifications"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        notifications = await notifications_service.get_user_notifications(
            user_id, unread_only, limit
        )
        return notifications
    except Exception as e:
        logger.error(f"Error retrieving notifications: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Query(...),
    current_user: str = Depends(verify_token)
):
    """Mark notification as read"""
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await notifications_service.mark_notification_read(notification_id)
        return result
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# END OF NEW ROUTES
# ============================================================================

"""
Audit Logging Service - Track all user actions and system events
Provides comprehensive audit trail for security and compliance
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

class AuditEventType(str, Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_SIGNUP = "user_signup"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    JOURNAL_CREATE = "journal_create"
    JOURNAL_UPDATE = "journal_update"
    JOURNAL_DELETE = "journal_delete"
    DATA_EXPORT = "data_export"
    SETTINGS_CHANGE = "settings_change"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_RESET = "password_reset"
    API_ERROR = "api_error"
    SYSTEM_EVENT = "system_event"

class AuditLogsService:
    """
    Comprehensive audit logging system for tracking user actions and system events
    """
    
    def __init__(self, dynamodb_service):
        self.db = dynamodb_service
    
    async def log_event(
        self,
        user_id: str,
        event_type: AuditEventType,
        resource: str,
        action: str,
        status: str = "success",
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict:
        """
        Log an audit event to the system
        """
        try:
            event_id = str(uuid.uuid4())
            
            audit_log = {
                "event_id": event_id,
                "user_id": user_id,
                "event_type": event_type.value,
                "resource": resource,
                "action": action,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "error_message": error_message
            }
            
            # Store in audit logs table
            # Implementation would save to DynamoDB audit_logs table
            
            return audit_log
        except Exception as e:
            raise Exception(f"Error logging audit event: {str(e)}")
    
    async def get_user_audit_logs(self, user_id: str, limit: int = 50, days: int = 30) -> Dict:
        """
        Retrieve audit logs for a specific user
        """
        try:
            # Query audit logs from database
            logs = []
            
            # Filter by date range
            # Would query: timestamp >= now - days
            
            return {
                "user_id": user_id,
                "logs": logs[:limit],
                "total_count": len(logs),
                "days_range": days
            }
        except Exception as e:
            raise Exception(f"Error retrieving audit logs: {str(e)}")
    
    async def get_event_logs(
        self,
        event_type: Optional[AuditEventType] = None,
        status: Optional[str] = None,
        limit: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Get system-wide event logs with filtering
        """
        try:
            logs = []
            
            # Apply filters if provided
            if event_type:
                logs = [log for log in logs if log.get("event_type") == event_type.value]
            
            if status:
                logs = [log for log in logs if log.get("status") == status]
            
            return {
                "logs": logs[:limit],
                "total_count": len(logs),
                "filters": {
                    "event_type": event_type.value if event_type else None,
                    "status": status,
                    "date_range": {"start": start_date, "end": end_date}
                }
            }
        except Exception as e:
            raise Exception(f"Error retrieving event logs: {str(e)}")
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict:
        """
        Get a summary of user's recent activity
        """
        try:
            logs = []
            
            # Get logs for specified period
            # Group by event type
            activity_summary = {}
            for log in logs:
                event_type = log.get("event_type")
                activity_summary[event_type] = activity_summary.get(event_type, 0) + 1
            
            return {
                "user_id": user_id,
                "period_days": days,
                "activity_summary": activity_summary,
                "last_activity": logs[0] if logs else None,
                "total_events": len(logs)
            }
        except Exception as e:
            raise Exception(f"Error generating activity summary: {str(e)}")
    
    async def log_login(self, user_id: str, ip_address: Optional[str] = None) -> Dict:
        """Log user login"""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.USER_LOGIN,
            resource="auth",
            action="login",
            ip_address=ip_address
        )
    
    async def log_logout(self, user_id: str) -> Dict:
        """Log user logout"""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.USER_LOGOUT,
            resource="auth",
            action="logout"
        )
    
    async def log_session_start(self, user_id: str, session_id: str) -> Dict:
        """Log session start"""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.SESSION_START,
            resource=f"session/{session_id}",
            action="start"
        )
    
    async def log_session_end(self, user_id: str, session_id: str, duration: int) -> Dict:
        """Log session end"""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.SESSION_END,
            resource=f"session/{session_id}",
            action="end",
            metadata={"duration_seconds": duration}
        )
    
    async def log_journal_action(self, user_id: str, action: str, journal_id: Optional[str] = None) -> Dict:
        """Log journal-related actions"""
        event_type_map = {
            "create": AuditEventType.JOURNAL_CREATE,
            "update": AuditEventType.JOURNAL_UPDATE,
            "delete": AuditEventType.JOURNAL_DELETE
        }
        
        event_type = event_type_map.get(action, AuditEventType.SYSTEM_EVENT)
        
        return await self.log_event(
            user_id=user_id,
            event_type=event_type,
            resource=f"journal/{journal_id}" if journal_id else "journal",
            action=action
        )
    
    async def log_api_error(self, user_id: str, endpoint: str, error_message: str) -> Dict:
        """Log API errors"""
        return await self.log_event(
            user_id=user_id,
            event_type=AuditEventType.API_ERROR,
            resource=endpoint,
            action="error",
            status="error",
            error_message=error_message
        )

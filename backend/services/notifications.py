"""
Notifications Service - Real-time alerts and notifications
Manages user alerts for high stress, recommendations, and journal insights
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import uuid

class NotificationType(str, Enum):
    STRESS_ALERT = "stress_alert"
    RECOMMENDATION = "recommendation"
    INSIGHT = "insight"
    JOURNAL_REMINDER = "journal_reminder"
    ACHIEVEMENT = "achievement"
    SESSION_SUMMARY = "session_summary"

class NotificationsPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationsService:
    """
    Manages real-time and scheduled notifications for users
    Stores notifications and provides delivery mechanisms
    """
    
    def __init__(self, dynamodb_service):
        self.db = dynamodb_service
    
    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationsPriority = NotificationsPriority.NORMAL,
        data: Dict = None,
        scheduled_time: Optional[str] = None
    ) -> Dict:
        """
        Create a new notification for a user
        """
        try:
            notification_id = str(uuid.uuid4())
            
            notification = {
                "notification_id": notification_id,
                "user_id": user_id,
                "type": notification_type.value,
                "title": title,
                "message": message,
                "priority": priority.value,
                "read": False,
                "created_at": datetime.utcnow().isoformat(),
                "scheduled_time": scheduled_time,
                "data": data or {},
                "delivered": False,
                "delivered_at": None
            }
            
            # Store in database (would need notifications table in DynamoDB)
            # For now, return the notification structure
            return notification
        except Exception as e:
            raise Exception(f"Error creating notification: {str(e)}")
    
    async def get_user_notifications(self, user_id: str, unread_only: bool = False, limit: int = 20) -> Dict:
        """
        Retrieve notifications for a user
        """
        try:
            # Query notifications from database
            # This would query the notifications table
            notifications = []
            
            # Filter if needed
            if unread_only:
                notifications = [n for n in notifications if not n.get("read", False)]
            
            notifications = notifications[:limit]
            
            return {
                "user_id": user_id,
                "notifications": notifications,
                "total_count": len(notifications),
                "unread_count": len([n for n in notifications if not n.get("read", False)])
            }
        except Exception as e:
            raise Exception(f"Error retrieving notifications: {str(e)}")
    
    async def mark_notification_read(self, notification_id: str) -> Dict:
        """
        Mark a notification as read
        """
        try:
            # Update notification status in database
            return {
                "notification_id": notification_id,
                "read": True,
                "read_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error marking notification as read: {str(e)}")
    
    async def create_stress_alert(self, user_id: str, stress_score: float, threshold: float) -> Optional[Dict]:
        """
        Create a stress alert if threshold is exceeded
        """
        try:
            if stress_score > threshold:
                alert = await self.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.STRESS_ALERT,
                    title="High Stress Alert 🚨",
                    message=f"Your stress level is {stress_score:.1f}%. Consider taking a break.",
                    priority=NotificationsPriority.HIGH if stress_score > 80 else NotificationsPriority.NORMAL,
                    data={"stress_score": stress_score, "threshold": threshold}
                )
                return alert
            return None
        except Exception as e:
            raise Exception(f"Error creating stress alert: {str(e)}")
    
    async def create_recommendation_notification(self, user_id: str, recommendation: Dict) -> Dict:
        """
        Create a notification with a wellness recommendation
        """
        try:
            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.RECOMMENDATION,
                title=f"💡 {recommendation.get('title', 'New Recommendation')}",
                message=recommendation.get('description', ''),
                priority=NotificationsPriority.NORMAL,
                data=recommendation
            )
            return notification
        except Exception as e:
            raise Exception(f"Error creating recommendation notification: {str(e)}")
    
    async def create_journal_reminder(self, user_id: str) -> Dict:
        """
        Create a journal reminder notification
        """
        try:
            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.JOURNAL_REMINDER,
                title="📝 Journal Reminder",
                message="Take a moment to reflect and write in your journal. It helps process emotions.",
                priority=NotificationsPriority.LOW
            )
            return notification
        except Exception as e:
            raise Exception(f"Error creating journal reminder: {str(e)}")
    
    async def create_achievement_notification(self, user_id: str, achievement: str) -> Dict:
        """
        Create an achievement/milestone notification
        """
        try:
            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.ACHIEVEMENT,
                title="🏆 Achievement Unlocked!",
                message=achievement,
                priority=NotificationsPriority.NORMAL
            )
            return notification
        except Exception as e:
            raise Exception(f"Error creating achievement notification: {str(e)}")
    
    async def create_session_summary_notification(self, user_id: str, session_data: Dict) -> Dict:
        """
        Create a notification with session summary
        """
        try:
            stress_score = session_data.get('stress_score', 'Unknown')
            dominant_emotion = session_data.get('dominant_emotion', 'Unknown')
            duration = session_data.get('duration_seconds', 0) // 60
            
            message = f"Session: {duration}min | Stress: {stress_score} | Emotion: {dominant_emotion}"
            
            notification = await self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.SESSION_SUMMARY,
                title="✅ Session Completed",
                message=message,
                priority=NotificationsPriority.NORMAL,
                data=session_data
            )
            return notification
        except Exception as e:
            raise Exception(f"Error creating session summary notification: {str(e)}")

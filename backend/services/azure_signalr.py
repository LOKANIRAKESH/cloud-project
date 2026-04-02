"""
Azure SignalR Service for Real-time Communication
Enables WebSocket-based real-time updates, live notifications, and bi-directional communication
"""
import asyncio
import json
import os
from typing import Dict, Optional, List, Callable
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class SignalRMessageType(str, Enum):
    STRESS_ALERT = "stress_alert"
    RECOMMENDATION = "recommendation"
    USER_CONNECTED = "user_connected"
    USER_DISCONNECTED = "user_disconnected"
    SESSION_UPDATE = "session_update"
    NOTIFICATION = "notification"
    LIVE_METRIC = "live_metric"

class AzureSignalRService:
    """
    Azure SignalR Service for real-time communication
    Enables live updates without polling
    """
    
    def __init__(self, hub_name: str = "stressdetect", connection_string: str = None):
        self.hub_name = hub_name
        self.connection_string = connection_string or os.getenv('AZURE_SIGNALR_CONNECTION_STRING')
        self.active_connections: Dict[str, Dict] = {}
    
    async def get_client_access_token(
        self,
        user_id: str,
        hub_name: str = None,
        minutes_to_live: int = 60
    ) -> Dict:
        """
        Get SignalR client access token for user
        Client uses this to establish WebSocket connection
        """
        try:
            from azure.messaging.signalrbuildingblocks import SignalRClient
            
            client = SignalRClient.from_connection_string(self.connection_string)
            
            token = client.get_client_access_token(
                hub=hub_name or self.hub_name,
                user_id=user_id,
                minutes_to_live=minutes_to_live
            )
            
            return {
                "access_token": token,
                "url": client.get_connection_url(),
                "user_id": user_id,
                "hub": hub_name or self.hub_name,
                "expires_in_minutes": minutes_to_live,
                "token_generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error getting access token: {str(e)}")
    
    async def send_real_time_stress_alert(
        self,
        user_id: str,
        stress_score: float,
        recommendation: str
    ) -> Dict:
        """
        Send real-time stress alert to connected user
        """
        try:
            from azure.messaging.signalrbuildingblocks import SignalRClient
            
            client = SignalRClient.from_connection_string(self.connection_string)
            
            message = {
                "type": SignalRMessageType.STRESS_ALERT.value,
                "stress_score": stress_score,
                "recommendation": recommendation,
                "timestamp": datetime.utcnow().isoformat(),
                "alert_level": "high" if stress_score > 80 else "medium" if stress_score > 60 else "low"
            }
            
            client.send_user_message(
                user=user_id,
                hub=self.hub_name,
                target="ReceiveStressAlert",
                args=[message]
            )
            
            return {
                "status": "sent",
                "message_type": SignalRMessageType.STRESS_ALERT.value,
                "recipient": user_id,
                "stress_score": stress_score,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error sending alert: {str(e)}")
    
    async def send_live_recommendation(
        self,
        user_id: str,
        recommendation: Dict
    ) -> Dict:
        """
        Send recommendation in real-time to user
        """
        try:
            from azure.messaging.signalrbuildingblocks import SignalRClient
            
            client = SignalRClient.from_connection_string(self.connection_string)
            
            message = {
                "type": SignalRMessageType.RECOMMENDATION.value,
                "title": recommendation.get('title'),
                "description": recommendation.get('description'),
                "category": recommendation.get('category'),
                "duration": recommendation.get('duration_minutes'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            client.send_user_message(
                user=user_id,
                hub=self.hub_name,
                target="ReceiveRecommendation",
                args=[message]
            )
            
            return {
                "status": "sent",
                "message_type": SignalRMessageType.RECOMMENDATION.value,
                "recipient": user_id
            }
        except Exception as e:
            raise Exception(f"Error sending recommendation: {str(e)}")
    
    async def broadcast_live_metrics(
        self,
        metric_data: Dict
    ) -> Dict:
        """
        Broadcast live metrics to all connected users
        For admin dashboard monitoring
        """
        try:
            from azure.messaging.signalrbuildingblocks import SignalRClient
            
            client = SignalRClient.from_connection_string(self.connection_string)
            
            message = {
                "type": SignalRMessageType.LIVE_METRIC.value,
                "metrics": metric_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            client.send_hub_message(
                hub=self.hub_name,
                target="ReceiveLiveMetrics",
                args=[message]
            )
            
            return {
                "status": "broadcast",
                "target_audience": "all_admin_users",
                "metrics_count": len(metric_data),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error broadcasting metrics: {str(e)}")
    
    async def send_group_notification(
        self,
        group_name: str,
        notification: Dict,
        message_type: SignalRMessageType = SignalRMessageType.NOTIFICATION
    ) -> Dict:
        """
        Send notification to a group of users
        Groups can be: therapists, researchers, etc.
        """
        try:
            from azure.messaging.signalrbuildingblocks import SignalRClient
            
            client = SignalRClient.from_connection_string(self.connection_string)
            
            message = {
                "type": message_type.value,
                "notification": notification,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            client.send_group_message(
                group=group_name,
                hub=self.hub_name,
                target="ReceiveNotification",
                args=[message]
            )
            
            return {
                "status": "sent_to_group",
                "group": group_name,
                "message_type": message_type.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error sending group notification: {str(e)}")
    
    async def add_user_to_group(
        self,
        user_id: str,
        group_name: str
    ) -> Dict:
        """
        Add user to a SignalR group
        """
        try:
            from azure.messaging.signalrbuildingblocks import SignalRClient
            
            client = SignalRClient.from_connection_string(self.connection_string)
            
            client.add_user_to_group(
                user=user_id,
                group=group_name,
                hub=self.hub_name
            )
            
            return {
                "status": "added",
                "user_id": user_id,
                "group": group_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error adding user to group: {str(e)}")
    
    async def remove_user_from_group(
        self,
        user_id: str,
        group_name: str
    ) -> Dict:
        """
        Remove user from SignalR group
        """
        try:
            from azure.messaging.signalrbuildingblocks import SignalRClient
            
            client = SignalRClient.from_connection_string(self.connection_string)
            
            client.remove_user_from_group(
                user=user_id,
                group=group_name,
                hub=self.hub_name
            )
            
            return {
                "status": "removed",
                "user_id": user_id,
                "group": group_name
            }
        except Exception as e:
            raise Exception(f"Error removing user from group: {str(e)}")
    
    async def send_session_update(
        self,
        user_id: str,
        session_data: Dict
    ) -> Dict:
        """
        Send live session data updates
        """
        try:
            from azure.messaging.signalrbuildingblocks import SignalRClient
            
            client = SignalRClient.from_connection_string(self.connection_string)
            
            message = {
                "type": SignalRMessageType.SESSION_UPDATE.value,
                "session": session_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            client.send_user_message(
                user=user_id,
                hub=self.hub_name,
                target="ReceiveSessionUpdate",
                args=[message]
            )
            
            return {
                "status": "sent",
                "message_type": SignalRMessageType.SESSION_UPDATE.value,
                "recipient": user_id
            }
        except Exception as e:
            raise Exception(f"Error sending session update: {str(e)}")
    
    async def track_user_presence(
        self,
        user_id: str,
        is_connected: bool
    ) -> Dict:
        """
        Track when user connects/disconnects
        """
        try:
            if is_connected:
                self.active_connections[user_id] = {
                    "connected_at": datetime.utcnow().isoformat(),
                    "status": "active"
                }
                status = SignalRMessageType.USER_CONNECTED.value
            else:
                if user_id in self.active_connections:
                    del self.active_connections[user_id]
                status = SignalRMessageType.USER_DISCONNECTED.value
            
            return {
                "user_id": user_id,
                "status": status,
                "active_users": len(self.active_connections),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error tracking presence: {str(e)}")
    
    def get_active_connection_count(self) -> int:
        """Get number of active connected users"""
        return len(self.active_connections)
    
    def get_active_users(self) -> Dict:
        """Get list of active users"""
        return {
            "total_active": len(self.active_connections),
            "users": [
                {
                    "user_id": uid,
                    "connected_at": info.get("connected_at"),
                    "status": info.get("status")
                }
                for uid, info in self.active_connections.items()
            ]
        }

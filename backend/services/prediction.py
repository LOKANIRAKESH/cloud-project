"""
Prediction Service - Machine Learning based stress prediction
Predicts future stress levels based on historical patterns
"""
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

class PredictionService:
    """
    ML-based prediction service for forecasting stress levels
    Uses historical data patterns to predict future stress
    """
    
    def __init__(self, dynamodb_service):
        self.db = dynamodb_service
    
    async def predict_stress_level(self, user_id: str, hours_ahead: int = 24) -> Dict:
        """
        Predict stress level for specified hours ahead
        Uses simple time-series forecasting
        """
        try:
            # Get historical data for pattern analysis
            sessions = await self.db.get_user_sessions(user_id, days=30)
            
            if not sessions or len(sessions) < 5:
                return {
                    "user_id": user_id,
                    "prediction": None,
                    "confidence": 0,
                    "reason": "Insufficient historical data for prediction"
                }
            
            # Extract stress scores
            stress_scores = [float(s.get('stress_score', 0)) for s in sessions]
            
            # Calculate trend (simple linear trend)
            if len(stress_scores) >= 2:
                trend = (stress_scores[-1] - stress_scores[0]) / len(stress_scores)
            else:
                trend = 0
            
            # Calculate average with trend projection
            current_avg = statistics.mean(stress_scores[-7:]) if len(stress_scores) >= 7 else statistics.mean(stress_scores)
            predicted_stress = current_avg + (trend * (hours_ahead / 24))
            
            # Clamp to valid range (0-100)
            predicted_stress = max(0, min(100, predicted_stress))
            
            # Calculate confidence based on data consistency
            std_dev = statistics.stdev(stress_scores) if len(stress_scores) > 1 else 0
            confidence = max(0, 100 - (std_dev * 1.5))  # More consistent data = higher confidence
            
            return {
                "user_id": user_id,
                "prediction": {
                    "predicted_stress_score": round(predicted_stress, 2),
                    "hours_ahead": hours_ahead,
                    "confidence": round(confidence, 2),
                    "trend": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"
                },
                "analysis": {
                    "current_average": round(current_avg, 2),
                    "trend_rate": round(trend, 4),
                    "data_points_used": len(stress_scores)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error predicting stress level: {str(e)}")
    
    async def predict_weekly_pattern(self, user_id: str) -> Dict:
        """
        Predict stress patterns for each day of the week
        Identifies which days tend to be more stressful
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=60)
            
            if not sessions:
                return {
                    "user_id": user_id,
                    "weekly_pattern": None,
                    "reason": "Insufficient data"
                }
            
            # Organize by day of week
            day_stress = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for session in sessions:
                try:
                    timestamp = session.get('timestamp', '')
                    date_obj = datetime.fromisoformat(timestamp)
                    day_of_week = date_obj.weekday()
                    stress = float(session.get('stress_score', 0))
                    day_stress[day_of_week].append(stress)
                except:
                    pass
            
            # Calculate average stress per day
            weekly_pattern = []
            for day_idx in range(7):
                if day_stress[day_idx]:
                    avg_stress = statistics.mean(day_stress[day_idx])
                    weekly_pattern.append({
                        "day": day_names[day_idx],
                        "average_stress": round(avg_stress, 2),
                        "samples": len(day_stress[day_idx])
                    })
            
            return {
                "user_id": user_id,
                "weekly_pattern": weekly_pattern,
                "highest_stress_day": max(weekly_pattern, key=lambda x: x['average_stress'])['day'] if weekly_pattern else None,
                "lowest_stress_day": min(weekly_pattern, key=lambda x: x['average_stress'])['day'] if weekly_pattern else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error predicting weekly pattern: {str(e)}")
    
    async def predict_stress_triggers(self, user_id: str) -> Dict:
        """
        Identify potential stress triggers based on patterns
        Correlates emotions and stress levels with timestamps
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=30)
            
            if not sessions:
                return {
                    "user_id": user_id,
                    "triggers": [],
                    "reason": "Insufficient data"
                }
            
            # Analyze high-stress sessions
            high_stress_sessions = [s for s in sessions if float(s.get('stress_score', 0)) > 70]
            
            if not high_stress_sessions:
                return {
                    "user_id": user_id,
                    "triggers": [],
                    "insight": "No high-stress sessions detected"
                }
            
            # Identify common patterns
            common_emotions = {}
            common_activities = {}
            common_hours = {}
            
            for session in high_stress_sessions:
                # Analyze emotions
                emotions = session.get('emotions', {})
                for emotion in emotions:
                    common_emotions[emotion] = common_emotions.get(emotion, 0) + 1
                
                # Analyze notes/activities
                notes = session.get('notes', '')
                if notes:
                    # Simple keyword extraction (in production would use NLP)
                    common_activities[notes] = common_activities.get(notes, 0) + 1
                
                # Analyze time of day
                try:
                    timestamp = session.get('timestamp', '')
                    hour = datetime.fromisoformat(timestamp).hour
                    common_hours[hour] = common_hours.get(hour, 0) + 1
                except:
                    pass
            
            triggers = []
            
            # Emotion triggers
            if common_emotions:
                top_emotion = max(common_emotions, key=common_emotions.get)
                triggers.append({
                    "type": "emotion",
                    "trigger": top_emotion,
                    "frequency": common_emotions[top_emotion],
                    "recommendation": f"Practice grounding techniques when feeling {top_emotion.lower()}"
                })
            
            # Time-based triggers
            if common_hours:
                peak_hour = max(common_hours, key=common_hours.get)
                triggers.append({
                    "type": "time_of_day",
                    "trigger": f"{peak_hour:02d}:00",
                    "frequency": common_hours[peak_hour],
                    "recommendation": f"Plan stress-relief activities around {peak_hour}:00"
                })
            
            return {
                "user_id": user_id,
                "high_stress_sessions_analyzed": len(high_stress_sessions),
                "triggers": triggers,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error identifying stress triggers: {str(e)}")
    
    async def predict_optimal_intervention_time(self, user_id: str) -> Dict:
        """
        Predict when preventive interventions would be most effective
        Based on stress pattern analysis
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=30)
            
            if not sessions:
                return {
                    "user_id": user_id,
                    "optimal_time": None,
                    "reason": "Insufficient data"
                }
            
            # Find lowest stress points for interventions
            stress_scores = [float(s.get('stress_score', 0)) for s in sessions]
            avg_stress = statistics.mean(stress_scores)
            
            # Find sessions with low stress
            low_stress_sessions = [s for s in sessions if float(s.get('stress_score', 0)) < avg_stress * 0.7]
            
            if not low_stress_sessions:
                return {
                    "user_id": user_id,
                    "optimal_time": "Early morning (typically lower stress)",
                    "reason": "General recommendation"
                }
            
            # Analyze timestamp patterns
            hours = {}
            for session in low_stress_sessions:
                try:
                    timestamp = session.get('timestamp', '')
                    hour = datetime.fromisoformat(timestamp).hour
                    hours[hour] = hours.get(hour, 0) + 1
                except:
                    pass
            
            if hours:
                optimal_hour = max(hours, key=hours.get)
                return {
                    "user_id": user_id,
                    "optimal_time": f"{optimal_hour:02d}:00",
                    "reason": "Based on historical low-stress periods",
                    "suggestion": "Schedule preventive activities during this time"
                }
            
            return {
                "user_id": user_id,
                "optimal_time": "Morning hours",
                "reason": "General pattern"
            }
        except Exception as e:
            raise Exception(f"Error predicting intervention time: {str(e)}")

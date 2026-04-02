"""
Analytics Service - Stress trends, emotion patterns, and insights
Analyzes historical data to provide actionable insights on user stress levels
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import statistics
from collections import Counter

class AnalyticsService:
    def __init__(self, dynamodb_service):
        self.db = dynamodb_service
    
    async def get_stress_trends(self, user_id: str, days: int = 30) -> Dict:
        """
        Analyze stress trends over specified days
        Returns daily average stress scores and emotion distribution
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=days)
            if not sessions:
                return {
                    "user_id": user_id,
                    "period_days": days,
                    "trend": [],
                    "average_stress": 0,
                    "stress_range": {"min": 0, "max": 0},
                    "total_sessions": 0
                }
            
            # Group sessions by date
            daily_data = {}
            for session in sessions:
                date = session.get('timestamp', '')[:10]  # YYYY-MM-DD
                if date not in daily_data:
                    daily_data[date] = []
                
                stress_score = float(session.get('stress_score', 0))
                daily_data[date].append(stress_score)
            
            # Calculate daily averages
            trend = []
            all_scores = []
            for date in sorted(daily_data.keys()):
                avg_score = statistics.mean(daily_data[date])
                trend.append({
                    "date": date,
                    "average_stress": round(avg_score, 2),
                    "session_count": len(daily_data[date])
                })
                all_scores.extend(daily_data[date])
            
            return {
                "user_id": user_id,
                "period_days": days,
                "trend": trend,
                "average_stress": round(statistics.mean(all_scores), 2) if all_scores else 0,
                "stress_range": {
                    "min": round(min(all_scores), 2) if all_scores else 0,
                    "max": round(max(all_scores), 2) if all_scores else 0
                },
                "total_sessions": len(sessions),
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error analyzing stress trends: {str(e)}")
    
    async def get_emotion_distribution(self, user_id: str, days: int = 30) -> Dict:
        """
        Get distribution of emotions detected in recent sessions
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=days)
            emotion_counter = Counter()
            
            for session in sessions:
                emotions = session.get('emotions', {})
                for emotion, confidence in emotions.items():
                    emotion_counter[emotion] += confidence
            
            total = sum(emotion_counter.values())
            distribution = {
                emotion: round((count / total * 100), 2) 
                for emotion, count in emotion_counter.most_common()
            } if total > 0 else {}
            
            return {
                "user_id": user_id,
                "period_days": days,
                "emotions": distribution,
                "total_detections": total,
                "dominant_emotion": emotion_counter.most_common(1)[0][0] if emotion_counter else None,
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error analyzing emotion distribution: {str(e)}")
    
    async def get_weekly_summary(self, user_id: str) -> Dict:
        """
        Get summary statistics for the current week
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=7)
            if not sessions:
                return {
                    "user_id": user_id,
                    "week": "current",
                    "total_sessions": 0,
                    "average_stress": 0,
                    "peak_stress_time": None
                }
            
            stress_scores = [float(s.get('stress_score', 0)) for s in sessions]
            timestamps = [s.get('timestamp', '') for s in sessions]
            
            peak_idx = stress_scores.index(max(stress_scores))
            
            return {
                "user_id": user_id,
                "week": "current",
                "total_sessions": len(sessions),
                "average_stress": round(statistics.mean(stress_scores), 2),
                "median_stress": round(statistics.median(stress_scores), 2),
                "peak_stress": round(max(stress_scores), 2),
                "peak_stress_time": timestamps[peak_idx] if timestamps else None,
                "std_deviation": round(statistics.stdev(stress_scores), 2) if len(stress_scores) > 1 else 0,
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error generating weekly summary: {str(e)}")
    
    async def get_stress_insights(self, user_id: str) -> Dict:
        """
        Generate AI-like insights from user's stress patterns
        """
        try:
            trends = await self.get_stress_trends(user_id, days=30)
            emotions = await self.get_emotion_distribution(user_id, days=30)
            weekly = await self.get_weekly_summary(user_id)
            
            insights = []
            
            # Generate insights based on patterns
            if trends.get('average_stress', 0) > 70:
                insights.append({
                    "type": "warning",
                    "message": "Your average stress level is high (>70%). Consider practicing relaxation techniques.",
                    "severity": "high"
                })
            elif trends.get('average_stress', 0) > 50:
                insights.append({
                    "type": "info",
                    "message": "Moderate stress levels detected. Try to incorporate wellness activities.",
                    "severity": "medium"
                })
            
            if emotions.get('dominant_emotion') == 'ANXIOUS':
                insights.append({
                    "type": "insight",
                    "message": "Anxiety is prominent in your recent sessions. Breathing exercises may help.",
                    "severity": "medium"
                })
            
            # Time-based insights
            if len(trends.get('trend', [])) > 7:
                recent = trends['trend'][-7:]
                older = trends['trend'][-14:-7] if len(trends['trend']) > 14 else []
                
                if recent and older:
                    recent_avg = statistics.mean([t['average_stress'] for t in recent])
                    older_avg = statistics.mean([t['average_stress'] for t in older])
                    
                    if recent_avg < older_avg:
                        insights.append({
                            "type": "positive",
                            "message": "Great! Your stress levels are trending downward this week.",
                            "severity": "low"
                        })
                    elif recent_avg > older_avg:
                        insights.append({
                            "type": "warning",
                            "message": "Stress levels are increasing. Check for lifestyle changes.",
                            "severity": "medium"
                        })
            
            return {
                "user_id": user_id,
                "insights": insights,
                "analysis_period": "30_days",
                "total_insights": len(insights),
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error generating insights: {str(e)}")
    
    async def get_peak_stress_hours(self, user_id: str, days: int = 30) -> Dict:
        """
        Identify times of day when stress is typically highest
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=days)
            hour_stress = {}
            
            for session in sessions:
                timestamp = session.get('timestamp', '')
                if timestamp:
                    try:
                        hour = datetime.fromisoformat(timestamp).hour
                        stress = float(session.get('stress_score', 0))
                        if hour not in hour_stress:
                            hour_stress[hour] = []
                        hour_stress[hour].append(stress)
                    except:
                        pass
            
            peak_hours = []
            for hour in sorted(hour_stress.keys()):
                avg_stress = statistics.mean(hour_stress[hour])
                peak_hours.append({
                    "hour": f"{hour:02d}:00",
                    "average_stress": round(avg_stress, 2),
                    "samples": len(hour_stress[hour])
                })
            
            return {
                "user_id": user_id,
                "peak_hours": peak_hours,
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error analyzing peak stress hours: {str(e)}")

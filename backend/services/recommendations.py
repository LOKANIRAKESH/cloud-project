"""
Recommendations Service - AI-powered wellness suggestions
Generates personalized recommendations based on user's stress patterns
"""
import random
from datetime import datetime
from typing import Dict, List

class RecommendationsService:
    """Generate personalized wellness recommendations based on stress patterns"""
    
    # Recommendation database organized by category and emotion
    RECOMMENDATIONS = {
        "breathing": [
            {
                "title": "4-7-8 Breathing Technique",
                "description": "Inhale for 4 counts, hold for 7, exhale for 8. Repeat 4 times.",
                "duration_minutes": 5,
                "difficulty": "easy",
                "effectiveness_score": 0.85
            },
            {
                "title": "Box Breathing",
                "description": "Breathe in for 4, hold for 4, breathe out for 4, hold for 4.",
                "duration_minutes": 3,
                "difficulty": "easy",
                "effectiveness_score": 0.82
            },
            {
                "title": "Deep Belly Breathing",
                "description": "Place hands on belly, breathe deeply to expand abdomen.",
                "duration_minutes": 5,
                "difficulty": "easy",
                "effectiveness_score": 0.78
            }
        ],
        "mindfulness": [
            {
                "title": "Body Scan Meditation",
                "description": "Progressively relax each body part from head to toe.",
                "duration_minutes": 10,
                "difficulty": "medium",
                "effectiveness_score": 0.88
            },
            {
                "title": "Mindful Walking",
                "description": "Take a slow walk, focusing on each step and surroundings.",
                "duration_minutes": 15,
                "difficulty": "easy",
                "effectiveness_score": 0.78
            },
            {
                "title": "5-Minute Meditation",
                "description": "Sit quietly, focus on breath, let thoughts pass without judgment.",
                "duration_minutes": 5,
                "difficulty": "medium",
                "effectiveness_score": 0.81
            }
        ],
        "exercise": [
            {
                "title": "Gentle Yoga",
                "description": "Low-intensity yoga stretches to release tension.",
                "duration_minutes": 15,
                "difficulty": "easy",
                "effectiveness_score": 0.84
            },
            {
                "title": "Quick Workout",
                "description": "20 minutes of light cardio or HIIT training.",
                "duration_minutes": 20,
                "difficulty": "hard",
                "effectiveness_score": 0.90
            },
            {
                "title": "Stretching Routine",
                "description": "Full body stretching to relieve muscle tension.",
                "duration_minutes": 10,
                "difficulty": "easy",
                "effectiveness_score": 0.75
            }
        ],
        "lifestyle": [
            {
                "title": "Nature Walk",
                "description": "Spend 20-30 minutes in nature for stress relief.",
                "duration_minutes": 30,
                "difficulty": "easy",
                "effectiveness_score": 0.86
            },
            {
                "title": "Journaling",
                "description": "Write about your feelings and experiences for 10-15 minutes.",
                "duration_minutes": 15,
                "difficulty": "easy",
                "effectiveness_score": 0.79
            },
            {
                "title": "Social Connection",
                "description": "Call or meet a friend to talk and share experiences.",
                "duration_minutes": 30,
                "difficulty": "easy",
                "effectiveness_score": 0.83
            }
        ],
        "sleep": [
            {
                "title": "Sleep Hygiene",
                "description": "Go to bed at same time, keep room cool and dark.",
                "duration_minutes": 0,
                "difficulty": "easy",
                "effectiveness_score": 0.89
            },
            {
                "title": "Wind Down Routine",
                "description": "30 min before bed: dim lights, avoid screens, drink herbal tea.",
                "duration_minutes": 30,
                "difficulty": "easy",
                "effectiveness_score": 0.87
            }
        ],
        "nutrition": [
            {
                "title": "Hydration",
                "description": "Drink 8-10 glasses of water throughout the day.",
                "duration_minutes": 0,
                "difficulty": "easy",
                "effectiveness_score": 0.7
            },
            {
                "title": "Healthy Snacking",
                "description": "Choose nuts, fruits, or yogurt instead of sugary foods.",
                "duration_minutes": 0,
                "difficulty": "easy",
                "effectiveness_score": 0.72
            }
        ]
    }
    
    # Emotion-specific recommendations
    EMOTION_RECOMMENDATIONS = {
        "ANXIOUS": ["breathing", "mindfulness", "exercise"],
        "STRESSED": ["exercise", "mindfulness", "nature"],
        "SAD": ["social", "nature", "exercise"],
        "ANGRY": ["exercise", "breathing", "nature"],
        "CALM": ["mindfulness", "journaling", "sleep"],
        "HAPPY": ["social", "lifestyle", "nature"]
    }
    
    def __init__(self, analytics_service):
        self.analytics = analytics_service
    
    async def get_personalized_recommendations(self, user_id: str, limit: int = 5) -> Dict:
        """
        Generate personalized recommendations based on user's stress patterns
        """
        try:
            # Get user's emotion distribution and stress levels
            emotions = await self.analytics.get_emotion_distribution(user_id, days=7)
            trends = await self.analytics.get_stress_trends(user_id, days=7)
            peak_hours = await self.analytics.get_peak_stress_hours(user_id, days=7)
            
            dominant_emotion = emotions.get("dominant_emotion", "STRESSED")
            stress_level = trends.get("average_stress", 50)
            
            # Select recommendation categories based on dominant emotion
            categories = self.EMOTION_RECOMMENDATIONS.get(dominant_emotion, ["breathing", "mindfulness"])
            
            # Collect recommendations from selected categories
            recommendations = []
            for category in categories:
                category_recs = self.RECOMMENDATIONS.get(category, [])
                recommendations.extend([
                    {
                        **rec,
                        "category": category,
                        "reason": f"Based on your {dominant_emotion.lower()} emotion pattern"
                    }
                    for rec in category_recs
                ])
            
            # Adjust based on stress level
            if stress_level > 80:
                # High stress - prioritize quick, effective techniques
                recommendations = sorted(
                    recommendations,
                    key=lambda x: (x["effectiveness_score"] / x["duration_minutes"]) if x["duration_minutes"] > 0 else x["effectiveness_score"],
                    reverse=True
                )
            elif stress_level < 40:
                # Low stress - suggest maintenance activities
                maintenance = self.RECOMMENDATIONS.get("sleep", [])
                recommendations.extend([
                    {**rec, "category": "sleep", "reason": "Maintain your wellness"} 
                    for rec in maintenance
                ])
            
            # Limit recommendations
            selected = recommendations[:limit]
            
            return {
                "user_id": user_id,
                "recommendations": selected,
                "based_on": {
                    "dominant_emotion": dominant_emotion,
                    "stress_level": stress_level
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error generating recommendations: {str(e)}")
    
    async def get_daily_recommendation(self, user_id: str) -> Dict:
        """
        Get a single daily recommendation
        """
        try:
            recs = await self.get_personalized_recommendations(user_id, limit=1)
            if recs["recommendations"]:
                return {
                    "user_id": user_id,
                    "daily_recommendation": recs["recommendations"][0],
                    "timestamp": datetime.utcnow().isoformat()
                }
            return {
                "user_id": user_id,
                "daily_recommendation": None,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error getting daily recommendation: {str(e)}")
    
    async def get_recommendations_by_time(self, user_id: str, time_available_minutes: int) -> Dict:
        """
        Get recommendations that fit the user's available time
        """
        try:
            recs = await self.get_personalized_recommendations(user_id, limit=10)
            filtered = [
                r for r in recs["recommendations"]
                if r["duration_minutes"] <= time_available_minutes
            ]
            
            return {
                "user_id": user_id,
                "time_available_minutes": time_available_minutes,
                "recommendations": filtered,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error filtering recommendations by time: {str(e)}")

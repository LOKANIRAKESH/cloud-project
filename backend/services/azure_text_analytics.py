"""
Azure Text Analytics Service
Analyzes journal entries for sentiment, key phrases, and entities
Integrates with Azure Cognitive Services
"""
import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

load_dotenv()

class SentimentLevel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"

class AzureTextAnalyticsService:
    """
    Azure Text Analytics integration for advanced NLP
    Analyzes emotional content in journal entries
    """
    
    def __init__(self, api_key: str = None, endpoint: str = None, language: str = "en"):
        api_key = api_key or os.getenv('AZURE_TEXT_ANALYTICS_KEY')
        endpoint = endpoint or os.getenv('AZURE_TEXT_ANALYTICS_ENDPOINT')
        
        self.client = TextAnalyticsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        self.language = language
    
    async def analyze_journal_sentiment(
        self,
        journal_entry: str,
        entry_id: str = None
    ) -> Dict:
        """
        Analyze sentiment of journal entry
        Returns sentiment score and labels
        """
        try:
            result = self.client.analyze_sentiment(
                documents=[journal_entry],
                language=self.language
            )[0]
            
            return {
                "entry_id": entry_id,
                "text_length": len(journal_entry),
                "sentiment": {
                    "overall": result.sentiment,
                    "positive_score": result.confidence_scores.positive,
                    "negative_score": result.confidence_scores.negative,
                    "neutral_score": result.confidence_scores.neutral
                },
                "sentences": [
                    {
                        "text": sent.text,
                        "sentiment": sent.sentiment,
                        "scores": {
                            "positive": sent.confidence_scores.positive,
                            "negative": sent.confidence_scores.negative,
                            "neutral": sent.confidence_scores.neutral
                        }
                    }
                    for sent in result.sentences
                ],
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error analyzing sentiment: {str(e)}")
    
    async def extract_key_phrases(
        self,
        journal_entry: str,
        entry_id: str = None
    ) -> Dict:
        """
        Extract key phrases and topics from journal entry
        Useful for identifying recurring themes
        """
        try:
            result = self.client.extract_key_phrases(
                documents=[journal_entry],
                language=self.language
            )[0]
            
            return {
                "entry_id": entry_id,
                "key_phrases": result.key_phrases,
                "phrase_count": len(result.key_phrases),
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error extracting key phrases: {str(e)}")
    
    async def recognize_entities(
        self,
        journal_entry: str,
        entry_id: str = None
    ) -> Dict:
        """
        Recognize named entities (people, places, things mentioned)
        Helps understand context of stress
        """
        try:
            result = self.client.recognize_entities(
                documents=[journal_entry],
                language=self.language
            )[0]
            
            entities = {}
            for entity in result.entities:
                category = entity.category
                if category not in entities:
                    entities[category] = []
                entities[category].append({
                    "text": entity.text,
                    "confidence": entity.confidence_score
                })
            
            return {
                "entry_id": entry_id,
                "entities": entities,
                "total_entities": len(result.entities),
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error recognizing entities: {str(e)}")
    
    async def perform_comprehensive_analysis(
        self,
        journal_entry: str,
        entry_id: str = None,
        user_id: str = None
    ) -> Dict:
        """
        Perform comprehensive text analysis
        Combines sentiment, key phrases, and entities
        """
        try:
            # Run all analyses
            sentiment_result = await self.analyze_journal_sentiment(journal_entry, entry_id)
            phrases_result = await self.extract_key_phrases(journal_entry, entry_id)
            entities_result = await self.recognize_entities(journal_entry, entry_id)
            
            # Generate insights
            insights = []
            
            # Sentiment-based insights
            sentiment_score = sentiment_result['sentiment']['positive_score']
            if sentiment_score < 0.3:
                insights.append({
                    "type": "concern",
                    "message": "This entry contains predominantly negative sentiment. Consider wellness activities.",
                    "severity": "high"
                })
            elif sentiment_score > 0.7:
                insights.append({
                    "type": "positive",
                    "message": "This entry shows positive sentiment. Great to see optimism!",
                    "severity": "low"
                })
            
            # Recurring themes
            if phrases_result['key_phrases']:
                insights.append({
                    "type": "theme",
                    "message": f"Key themes in this entry: {', '.join(phrases_result['key_phrases'][:3])}",
                    "severity": "info"
                })
            
            # Return comprehensive analysis
            return {
                "entry_id": entry_id,
                "user_id": user_id,
                "sentiment": sentiment_result['sentiment'],
                "key_phrases": phrases_result['key_phrases'],
                "entities": entities_result['entities'],
                "insights": insights,
                "overall_emotional_tone": sentiment_result['sentiment']['overall'],
                "word_count": len(journal_entry.split()),
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error performing comprehensive analysis: {str(e)}")
    
    async def trend_analysis_on_journal_entries(
        self,
        journal_entries: List[Dict],
        user_id: str = None
    ) -> Dict:
        """
        Analyze sentiment trends across multiple journal entries
        Shows emotional progression over time
        """
        try:
            sentiment_scores = []
            emotion_changes = []
            
            for entry in sorted(journal_entries, key=lambda x: x.get('timestamp', '')):
                text = entry.get('content', '')
                if not text:
                    continue
                
                sentiment = await self.analyze_journal_sentiment(text, entry.get('id'))
                sentiment_scores.append({
                    "date": entry.get('timestamp', ''),
                    "sentiment": sentiment['sentiment']['overall'],
                    "score": sentiment['sentiment']['positive_score']
                })
            
            # Calculate trend
            if len(sentiment_scores) > 1:
                first_score = sentiment_scores[0]['score']
                last_score = sentiment_scores[-1]['score']
                trend = "improving" if last_score > first_score else "declining" if last_score < first_score else "stable"
                
                emotion_changes.append({
                    "type": "overall_trend",
                    "from": sentiment_scores[0]['sentiment'],
                    "to": sentiment_scores[-1]['sentiment'],
                    "trend": trend,
                    "change_percentage": round(((last_score - first_score) / first_score * 100) if first_score > 0 else 0, 2)
                })
            
            return {
                "user_id": user_id,
                "total_entries_analyzed": len(sentiment_scores),
                "sentiment_scores": sentiment_scores,
                "trends": emotion_changes,
                "average_sentiment": sum(s['score'] for s in sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error analyzing trends: {str(e)}")
    
    async def detect_concerning_journal_entries(
        self,
        journal_entries: List[Dict],
        negative_threshold: float = 0.7,
        user_id: str = None
    ) -> Dict:
        """
        Identify journal entries that might indicate deteriorating mental health
        Alerts system to check if user needs support
        """
        try:
            concerning_entries = []
            
            for entry in journal_entries:
                text = entry.get('content', '')
                if not text:
                    continue
                
                sentiment = await self.analyze_journal_sentiment(text, entry.get('id'))
                negative_score = sentiment['sentiment']['negative_score']
                
                if negative_score >= negative_threshold:
                    concerning_entries.append({
                        "entry_id": entry.get('id'),
                        "date": entry.get('timestamp'),
                        "negative_score": negative_score,
                        "excerpt": text[:100] + "...",
                        "recommendation": "Consider reaching out to a mental health professional"
                    })
            
            return {
                "user_id": user_id,
                "concerning_entries_found": len(concerning_entries),
                "concerning_entries": concerning_entries,
                "action_required": len(concerning_entries) > 0,
                "analysis_date": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error detecting concerning entries: {str(e)}")

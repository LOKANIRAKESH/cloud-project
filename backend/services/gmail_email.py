"""
Gmail Email Service
Uses SMTP to send emails via Gmail
Much simpler than AWS SES for development/lab environments
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GmailEmailService:
    """Gmail-based email service using SMTP"""
    
    def __init__(self):
        self.sender_email = os.getenv('GMAIL_ADDRESS')
        self.sender_password = os.getenv('GMAIL_APP_PASSWORD', '').replace(' ', '')  # Remove spaces
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        if not self.sender_email or not self.sender_password:
            logger.warning("Gmail credentials not configured. Email notifications disabled.")
        else:
            logger.info(f"Gmail service initialized for {self.sender_email}")
    
    async def send_stress_alert_email(
        self,
        user_email: str,
        stress_score: float,
        recommendation: str,
        user_name: str = "User"
    ) -> Dict:
        """Send high stress alert via Gmail SMTP"""
        try:
            subject = f"🚨 High Stress Alert - Action Needed"
            
            html_body = f"""
            <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #d32f2f;">Stress Alert Notification</h2>
                    
                    <p>Hi {user_name},</p>
                    
                    <p>Your stress level has reached <strong style="color: #d32f2f; font-size: 18px;">{stress_score:.1f}%</strong>, 
                    which is above your safe threshold.</p>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <h3>🎯 Recommended Action:</h3>
                        <p><strong>{recommendation}</strong></p>
                    </div>
                    
                    <p>Taking a few minutes for this activity can help reduce your stress levels.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <p style="color: #666;">
                            <a href="https://stressdetect.app/analytics" style="color: #1976d2; text-decoration: none;">
                                View Your Analytics
                            </a> | 
                            <a href="https://stressdetect.app/settings" style="color: #1976d2; text-decoration: none;">
                                Adjust Settings
                            </a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = user_email
            
            text_part = MIMEText(f"Stress Alert: {stress_score:.1f}%\n{recommendation}", "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email via Gmail SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, user_email, message.as_string())
            
            logger.info(f"✓ Stress alert email sent to {user_email}")
            return {
                "status": "sent",
                "message_id": f"gmail-{datetime.utcnow().timestamp()}",
                "email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending stress alert: {str(e)}")
            raise Exception(f"Error sending email: {str(e)}")
    
    async def send_journal_reminder_email(
        self,
        user_email: str,
        user_name: str = "User",
        streak_days: int = 0
    ) -> Dict:
        """Send journal reminder email via Gmail"""
        try:
            subject = "📝 Time to Reflect - Daily Journal"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #1976d2;">Journal Reminder</h2>
                    
                    <p>Hi {user_name},</p>
                    
                    <p>It's time to reflect on your day and write in your journal. 
                    Taking a few minutes to write can help you process emotions and reduce stress.</p>
                    
                    {f'<p style="color: #4caf50; font-size: 16px; font-weight: bold;">🔥 You have a {streak_days}-day streak!</p>' if streak_days > 0 else ''}
                    
                    <div style="margin: 30px 0; text-align: center;">
                        <a href="https://stressdetect.app/journal" style="background-color: #1976d2; color: white; 
                        padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                            Open Journal
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        Topics to consider: How was your day? What stressed you? What went well?
                    </p>
                </div>
            </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = user_email
            
            text_part = MIMEText(f"Journal Reminder for {user_name}", "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, user_email, message.as_string())
            
            logger.info(f"✓ Journal reminder email sent to {user_email}")
            return {
                "status": "sent",
                "type": "journal_reminder",
                "message_id": f"gmail-{datetime.utcnow().timestamp()}",
                "email": user_email
            }
            
        except Exception as e:
            logger.error(f"Error sending journal reminder: {str(e)}")
            raise Exception(f"Error sending journal reminder: {str(e)}")
    
    async def send_analysis_report_email(
        self,
        user_email: str,
        user_name: str,
        stress_score: float,
        stress_level: str,
        emotions: Dict,
        recommendation: str,
        timestamp: str
    ) -> Dict:
        """Send stress analysis report via Gmail"""
        try:
            stress_colors = {
                "low": "#4caf50",
                "moderate": "#ff9800", 
                "high": "#f44336",
                "critical": "#c62828"
            }
            stress_color = stress_colors.get(stress_level, "#666")
            
            emotions_html = ""
            for emotion, value in emotions.items():
                emotions_html += f"<tr><td style='padding: 8px;'>{emotion.title()}:</td><td style='padding: 8px; font-weight: bold;'>{value:.1f}%</td></tr>"
            
            subject = f"📊 Your Stress Analysis Report - {stress_level.upper()}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #1976d2;">📊 Stress Analysis Report</h2>
                    <p style="color: #666;">Generated: {timestamp}</p>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid {stress_color};">
                        <h3 style="color: {stress_color}; margin-top: 0;">Stress Level: {stress_level.upper()}</h3>
                        
                        <div style="text-align: center; margin: 20px 0;">
                            <span style="font-size: 48px; font-weight: bold; color: {stress_color};">
                                {stress_score:.1f}%
                            </span>
                            <p style="color: #666; margin-top: 5px;">Current Stress Score</p>
                        </div>
                    </div>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #1976d2; margin-top: 0;">😊 Emotion Breakdown:</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            {emotions_html}
                        </table>
                    </div>
                    
                    <div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #1976d2; margin: 20px 0; border-radius: 4px;">
                        <h3 style="color: #1976d2; margin-top: 0;">💡 Recommendation:</h3>
                        <p style="font-size: 16px; color: #333;">{recommendation}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = user_email
            
            text_part = MIMEText(f"Stress Score: {stress_score}%\nLevel: {stress_level}", "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, user_email, message.as_string())
            
            logger.info(f"✓ Analysis report email sent to {user_email}")
            return {
                "status": "sent",
                "type": "analysis_report",
                "message_id": f"gmail-{datetime.utcnow().timestamp()}",
                "email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending analysis report: {str(e)}")
            raise Exception(f"Error sending analysis report: {str(e)}")
    
    async def send_journal_analysis_email(
        self,
        user_email: str,
        user_name: str,
        journal_text: str,
        sentiment: str,
        stress_score: float,
        confidence: float,
        timestamp: str
    ) -> Dict:
        """Send journal analysis report via Gmail"""
        try:
            sentiment_colors = {
                "positive": "#4caf50",
                "neutral": "#ff9800",
                "negative": "#f44336",
                "mixed": "#1976d2"
            }
            sentiment_color = sentiment_colors.get(sentiment, "#666")
            
            subject = f"📝 Your Journal Analysis - {sentiment.upper()} Sentiment"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #1976d2;">📝 Journal Analysis Report</h2>
                    <p style="color: #666;">Generated: {timestamp}</p>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid {sentiment_color};">
                        <h3 style="color: {sentiment_color}; margin-top: 0;">Sentiment: {sentiment.upper()}</h3>
                        
                        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 4px; margin: 15px 0;">
                            <p style="color: #666; margin: 0; font-style: italic;">
                                "{journal_text}..."
                            </p>
                        </div>
                    </div>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #1976d2; margin-top: 0;">📊 Analysis Details:</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px;">Sentiment:</td>
                                <td style="padding: 10px; font-weight: bold; color: {sentiment_color};">{sentiment}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #ddd;">
                                <td style="padding: 10px;">Stress Score:</td>
                                <td style="padding: 10px; font-weight: bold;">{stress_score:.1f}%</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;">Confidence:</td>
                                <td style="padding: 10px; font-weight: bold;">{confidence*100:.1f}%</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = user_email
            
            text_part = MIMEText(f"Sentiment: {sentiment}\nStress Score: {stress_score}%", "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, user_email, message.as_string())
            
            logger.info(f"✓ Journal analysis email sent to {user_email}")
            return {
                "status": "sent",
                "type": "journal_analysis",
                "message_id": f"gmail-{datetime.utcnow().timestamp()}",
                "email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending journal analysis email: {str(e)}")
            raise Exception(f"Error sending journal analysis email: {str(e)}")

"""
Data Export Service - Export user data in multiple formats
Supports CSV, PDF, and JSON export functionality
"""
import io
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, BinaryIO
from enum import Enum

class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"

class ExportService:
    """
    Service for exporting user data in various formats
    Handles stress reports, session history, journal entries
    """
    
    def __init__(self, dynamodb_service):
        self.db = dynamodb_service
    
    async def export_stress_data(
        self,
        user_id: str,
        format: ExportFormat,
        days: int = 30
    ) -> BinaryIO:
        """
        Export stress data and analytics in specified format
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=days)
            
            if format == ExportFormat.CSV:
                return await self._export_to_csv(sessions)
            elif format == ExportFormat.JSON:
                return await self._export_to_json(sessions)
            elif format == ExportFormat.PDF:
                return await self._export_to_pdf(sessions)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise Exception(f"Error exporting stress data: {str(e)}")
    
    async def export_journal_entries(
        self,
        user_id: str,
        format: ExportFormat,
        days: int = 30
    ) -> BinaryIO:
        """
        Export journal entries in specified format
        """
        try:
            # Get journal entries
            entries = await self.db.get_journal_entries(user_id, days=days)
            
            if format == ExportFormat.CSV:
                return await self._export_journal_to_csv(entries)
            elif format == ExportFormat.JSON:
                return await self._export_journal_to_json(entries)
            elif format == ExportFormat.PDF:
                return await self._export_journal_to_pdf(entries)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise Exception(f"Error exporting journal entries: {str(e)}")
    
    async def export_comprehensive_report(
        self,
        user_id: str,
        format: ExportFormat,
        days: int = 30
    ) -> Dict:
        """
        Export comprehensive report including stress data, journal, and insights
        """
        try:
            sessions = await self.db.get_user_sessions(user_id, days=days)
            entries = await self.db.get_journal_entries(user_id, days=days)
            
            report = {
                "export_date": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "period_days": days,
                "sessions": sessions,
                "journal_entries": entries,
                "summary": {
                    "total_sessions": len(sessions),
                    "total_journal_entries": len(entries)
                }
            }
            
            if format == ExportFormat.JSON:
                return report
            elif format == ExportFormat.CSV:
                # CSV is less suitable for nested data, use summary export
                return await self._export_summary_to_csv(report)
            elif format == ExportFormat.PDF:
                return await self._export_report_to_pdf(report)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise Exception(f"Error exporting comprehensive report: {str(e)}")
    
    async def _export_to_csv(self, sessions: List[Dict]) -> BinaryIO:
        """Export sessions to CSV format"""
        try:
            output = io.StringIO()
            if not sessions:
                return output
            
            fieldnames = ['timestamp', 'stress_score', 'emotion', 'duration_seconds', 'notes']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            for session in sessions:
                writer.writerow({
                    'timestamp': session.get('timestamp', ''),
                    'stress_score': session.get('stress_score', ''),
                    'emotion': session.get('dominant_emotion', ''),
                    'duration_seconds': session.get('duration_seconds', ''),
                    'notes': session.get('notes', '')
                })
            
            return output
        except Exception as e:
            raise Exception(f"Error converting to CSV: {str(e)}")
    
    async def _export_to_json(self, sessions: List[Dict]) -> Dict:
        """Export sessions to JSON format"""
        try:
            return {
                "export_date": datetime.utcnow().isoformat(),
                "sessions": sessions
            }
        except Exception as e:
            raise Exception(f"Error converting to JSON: {str(e)}")
    
    async def _export_to_pdf(self, sessions: List[Dict]) -> BinaryIO:
        """Export sessions to PDF format"""
        try:
            # PDF export would require additional library like reportlab
            # This is a placeholder for the implementation
            pdf_content = io.BytesIO()
            
            # Would use reportlab or similar library to generate PDF
            # For now, returning empty BytesIO
            
            return pdf_content
        except Exception as e:
            raise Exception(f"Error converting to PDF: {str(e)}")
    
    async def _export_journal_to_csv(self, entries: List[Dict]) -> BinaryIO:
        """Export journal entries to CSV"""
        try:
            output = io.StringIO()
            if not entries:
                return output
            
            fieldnames = ['timestamp', 'title', 'emotion', 'content_summary']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            for entry in entries:
                writer.writerow({
                    'timestamp': entry.get('timestamp', ''),
                    'title': entry.get('title', ''),
                    'emotion': entry.get('emotion', ''),
                    'content_summary': entry.get('content', '')[:100]  # First 100 chars
                })
            
            return output
        except Exception as e:
            raise Exception(f"Error converting journal to CSV: {str(e)}")
    
    async def _export_journal_to_json(self, entries: List[Dict]) -> Dict:
        """Export journal entries to JSON"""
        try:
            return {
                "export_date": datetime.utcnow().isoformat(),
                "entries": entries
            }
        except Exception as e:
            raise Exception(f"Error converting journal to JSON: {str(e)}")
    
    async def _export_journal_to_pdf(self, entries: List[Dict]) -> BinaryIO:
        """Export journal entries to PDF"""
        try:
            pdf_content = io.BytesIO()
            # PDF generation would use reportlab
            return pdf_content
        except Exception as e:
            raise Exception(f"Error converting journal to PDF: {str(e)}")
    
    async def _export_summary_to_csv(self, report: Dict) -> BinaryIO:
        """Export summary report to CSV"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['Export Date', report.get('export_date')])
            writer.writerow(['Period Days', report.get('period_days')])
            writer.writerow(['Total Sessions', report.get('summary', {}).get('total_sessions')])
            writer.writerow(['Total Journal Entries', report.get('summary', {}).get('total_journal_entries')])
            
            return output
        except Exception as e:
            raise Exception(f"Error exporting summary to CSV: {str(e)}")
    
    async def _export_report_to_pdf(self, report: Dict) -> BinaryIO:
        """Export comprehensive report to PDF"""
        try:
            pdf_content = io.BytesIO()
            # PDF generation implementation
            return pdf_content
        except Exception as e:
            raise Exception(f"Error generating PDF report: {str(e)}")
    
    def get_export_filename(self, user_id: str, format: ExportFormat, report_type: str = "stress") -> str:
        """Generate appropriate filename for export"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = format.value
        return f"{report_type}_{user_id}_{timestamp}.{extension}"

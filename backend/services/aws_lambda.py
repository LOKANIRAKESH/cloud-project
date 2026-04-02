"""
AWS Lambda Serverless Functions Service
Manages serverless compute for background tasks
Handles event processing and scheduled jobs
"""
import boto3
import json
import os
from typing import Dict, Optional, Any
from datetime import datetime
import base64
from dotenv import load_dotenv

load_dotenv()

class LambdaServerlessService:
    """
    AWS Lambda integration for serverless compute
    Handles background processing, scheduled tasks, and event-driven workflows
    """
    
    def __init__(self, aws_region: str = "us-east-1"):
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')
        
        client_kwargs = {
            'region_name': aws_region,
            'aws_access_key_id': aws_access_key,
            'aws_secret_access_key': aws_secret_key
        }
        
        if aws_session_token:
            client_kwargs['aws_session_token'] = aws_session_token
        
        self.lambda_client = boto3.client('lambda', **client_kwargs)
        self.events_client = boto3.client('events', **client_kwargs)
        self.region = aws_region
    
    async def invoke_stress_analysis_lambda(
        self,
        user_id: str,
        sessions_data: list
    ) -> Dict:
        """
        Invoke Lambda function to analyze stress patterns
        Runs asynchronously for better performance
        """
        try:
            payload = {
                "action": "analyze_stress",
                "user_id": user_id,
                "sessions": sessions_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.lambda_client.invoke(
                FunctionName='stressdetect-stress-analyzer',
                InvocationType='Async',  # Asynchronous invocation
                Payload=json.dumps(payload)
            )
            
            return {
                "status": "invoked",
                "function": 'stressdetect-stress-analyzer',
                "request_id": response['ResponseMetadata']['RequestId'],
                "status_code": response['StatusCode'],
                "invocation_type": "async",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error invoking Lambda: {str(e)}")
    
    async def invoke_email_sender_lambda(
        self,
        recipient_email: str,
        email_type: str,
        context_data: Dict
    ) -> Dict:
        """
        Invoke Lambda to send emails asynchronously
        """
        try:
            payload = {
                "action": "send_email",
                "recipient": recipient_email,
                "email_type": email_type,
                "context": context_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.lambda_client.invoke(
                FunctionName='stressdetect-email-sender',
                InvocationType='Async',
                Payload=json.dumps(payload)
            )
            
            return {
                "status": "sent_to_queue",
                "email_type": email_type,
                "recipient": recipient_email,
                "request_id": response['ResponseMetadata']['RequestId']
            }
        except Exception as e:
            raise Exception(f"Error invoking email Lambda: {str(e)}")
    
    async def invoke_backup_lambda(
        self,
        user_id: str,
        user_data: Dict
    ) -> Dict:
        """
        Trigger Lambda for automated user data backup
        """
        try:
            payload = {
                "action": "backup_user_data",
                "user_id": user_id,
                "data": user_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.lambda_client.invoke(
                FunctionName='stressdetect-data-backup',
                InvocationType='Async',
                Payload=json.dumps(payload)
            )
            
            return {
                "status": "backup_initiated",
                "user_id": user_id,
                "request_id": response['ResponseMetadata']['RequestId'],
                "estimated_completion": "5-10 minutes"
            }
        except Exception as e:
            raise Exception(f"Error invoking backup Lambda: {str(e)}")
    
    async def create_scheduled_journal_reminder(
        self,
        user_id: str,
        email: str,
        cron_expression: str = "cron(0 20 * * ? *)"  # 8 PM daily
    ) -> Dict:
        """
        Create scheduled EventBridge rule to send journal reminders
        """
        try:
            rule_name = f"journal-reminder-{user_id}"
            
            # Create rule
            self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=cron_expression,
                State='ENABLED',
                Description=f'Daily journal reminder for {user_id}'
            )
            
            # Add Lambda as target
            self.events_client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': 'arn:aws:lambda:us-east-1:ACCOUNT_ID:function:stressdetect-email-sender',
                        'Input': json.dumps({
                            "action": "send_email",
                            "email_type": "journal_reminder",
                            "recipient": email,
                            "user_id": user_id
                        })
                    }
                ]
            )
            
            return {
                "status": "scheduled",
                "rule_name": rule_name,
                "user_id": user_id,
                "schedule": cron_expression,
                "description": "Daily journal reminder"
            }
        except Exception as e:
            raise Exception(f"Error creating scheduled reminder: {str(e)}")
    
    async def create_scheduled_weekly_summary(
        self,
        user_id: str,
        email: str,
        day_of_week: int = 0,
        hour: int = 9
    ) -> Dict:
        """
        Create scheduled rule for weekly summary reports
        day_of_week: 0=Monday, 6=Sunday
        """
        try:
            rule_name = f"weekly-summary-{user_id}"
            cron_expression = f"cron(0 {hour} ? * {day_of_week} *)"
            
            # Create rule
            self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=cron_expression,
                State='ENABLED',
                Description=f'Weekly summary for {user_id}'
            )
            
            # Add Lambda target
            self.events_client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': '1',
                        'Arn': 'arn:aws:lambda:us-east-1:ACCOUNT_ID:function:stressdetect-report-generator',
                        'Input': json.dumps({
                            "action": "generate_weekly_report",
                            "user_id": user_id,
                            "recipient": email
                        })
                    }
                ]
            )
            
            return {
                "status": "scheduled",
                "rule_name": rule_name,
                "user_id": user_id,
                "schedule": cron_expression,
                "description": "Weekly summary report"
            }
        except Exception as e:
            raise Exception(f"Error creating weekly summary: {str(e)}")
    
    async def get_lambda_function_info(
        self,
        function_name: str
    ) -> Dict:
        """
        Get information about Lambda function
        """
        try:
            response = self.lambda_client.get_function(
                FunctionName=function_name
            )
            
            config = response['Configuration']
            
            return {
                "function_name": config['FunctionName'],
                "runtime": config['Runtime'],
                "memory": config['MemorySize'],
                "timeout": config['Timeout'],
                "role": config['Role'],
                "handler": config['Handler'],
                "last_modified": config['LastModified'],
                "status": "active"
            }
        except Exception as e:
            raise Exception(f"Error getting Lambda info: {str(e)}")
    
    async def get_lambda_metrics(
        self,
        function_name: str,
        hours: int = 1
    ) -> Dict:
        """
        Get Lambda function metrics (invocations, errors, duration)
        """
        try:
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            from datetime import timedelta
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get invocations
            invocations = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            # Get errors
            errors = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            # Get duration
            duration = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum']
            )
            
            total_invocations = sum(dp['Sum'] for dp in invocations['Datapoints'])
            total_errors = sum(dp['Sum'] for dp in errors['Datapoints'])
            
            return {
                "function_name": function_name,
                "period_hours": hours,
                "total_invocations": total_invocations,
                "total_errors": total_errors,
                "error_rate": (total_errors / total_invocations * 100) if total_invocations > 0 else 0,
                "average_duration_ms": sum(dp['Average'] for dp in duration['Datapoints']) / len(duration['Datapoints']) if duration['Datapoints'] else 0,
                "max_duration_ms": max((dp['Maximum'] for dp in duration['Datapoints']), default=0),
                "metrics_collected_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error getting Lambda metrics: {str(e)}")
    
    async def list_scheduled_rules(self, user_id: str = None) -> Dict:
        """
        List all scheduled rules for user
        """
        try:
            response = self.events_client.list_rules()
            
            rules = []
            for rule in response.get('Rules', []):
                rule_name = rule['Name']
                
                if user_id and user_id not in rule_name:
                    continue
                
                # Get targets for this rule
                targets = self.events_client.list_targets_by_rule(Rule=rule_name)
                
                rules.append({
                    "rule_name": rule_name,
                    "schedule": rule.get('ScheduleExpression'),
                    "state": rule['State'],
                    "description": rule.get('Description'),
                    "targets_count": len(targets.get('Targets', []))
                })
            
            return {
                "user_id": user_id,
                "total_rules": len(rules),
                "rules": rules
            }
        except Exception as e:
            raise Exception(f"Error listing scheduled rules: {str(e)}")
    
    async def delete_scheduled_rule(self, rule_name: str) -> Dict:
        """
        Delete a scheduled rule
        """
        try:
            # Remove targets first
            targets = self.events_client.list_targets_by_rule(Rule=rule_name)
            if targets.get('Targets'):
                target_ids = [t['Id'] for t in targets['Targets']]
                self.events_client.remove_targets(Rule=rule_name, Ids=target_ids)
            
            # Delete rule
            self.events_client.delete_rule(Name=rule_name)
            
            return {
                "status": "deleted",
                "rule_name": rule_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error deleting rule: {str(e)}")

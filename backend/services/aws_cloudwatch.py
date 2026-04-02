"""
AWS CloudWatch Monitoring Service
Logs metrics, creates alarms, and monitors application health
Integrates with AWS CloudWatch for comprehensive monitoring
"""
import boto3
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class MetricType(str, Enum):
    API_CALLS = "api_calls"
    ERROR_RATE = "error_rate"
    STRESS_SCORE = "stress_score"
    DATABASE_LATENCY = "database_latency"
    USER_SESSIONS = "user_sessions"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"

class CloudWatchMonitoringService:
    """
    AWS CloudWatch monitoring and logging
    Tracks application metrics and creates alarms
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
        
        self.cloudwatch = boto3.client('cloudwatch', **client_kwargs)
        self.logs = boto3.client('logs', **client_kwargs)
        self.region = aws_region
        self.namespace = 'StressDetectApp'
    
    async def put_metric_data(
        self,
        metric_name: MetricType,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict] = None
    ) -> Dict:
        """
        Put custom metric data to CloudWatch
        """
        try:
            metric_dimensions = []
            if dimensions:
                for key, val in dimensions.items():
                    metric_dimensions.append({
                        'Name': key,
                        'Value': str(val)
                    })
            
            response = self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': metric_name.value,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': metric_dimensions
                    }
                ]
            )
            
            return {
                "status": "logged",
                "metric": metric_name.value,
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error putting metric data: {str(e)}")
    
    async def log_application_event(
        self,
        log_group: str,
        log_stream: str,
        event: Dict
    ) -> Dict:
        """
        Log application events to CloudWatch Logs
        """
        try:
            # Create log group if doesn't exist
            try:
                self.logs.create_log_group(logGroupName=log_group)
            except self.logs.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Create log stream if doesn't exist
            try:
                self.logs.create_log_stream(
                    logGroupName=log_group,
                    logStreamName=log_stream
                )
            except self.logs.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Put log event
            response = self.logs.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                logEvents=[
                    {
                        'timestamp': int(datetime.utcnow().timestamp() * 1000),
                        'message': json.dumps(event)
                    }
                ]
            )
            
            return {
                "status": "logged",
                "log_group": log_group,
                "log_stream": log_stream,
                "event_id": response.get('nextSequenceToken', 'unknown')
            }
        except Exception as e:
            raise Exception(f"Error logging event: {str(e)}")
    
    async def create_alarm(
        self,
        alarm_name: str,
        metric_name: MetricType,
        threshold: float,
        comparison_operator: str = "GreaterThanThreshold",
        evaluation_periods: int = 1,
        period: int = 60,
        alarm_actions: Optional[List[str]] = None
    ) -> Dict:
        """
        Create CloudWatch alarm for metric
        Triggers SNS notification when threshold exceeded
        """
        try:
            params = {
                'AlarmName': alarm_name,
                'MetricName': metric_name.value,
                'Namespace': self.namespace,
                'Statistic': 'Average',
                'Period': period,
                'EvaluationPeriods': evaluation_periods,
                'Threshold': threshold,
                'ComparisonOperator': comparison_operator,
                'AlarmDescription': f'Alarm for {metric_name.value}'
            }
            
            if alarm_actions:
                params['AlarmActions'] = alarm_actions
            
            response = self.cloudwatch.put_metric_alarm(**params)
            
            return {
                "status": "created",
                "alarm_name": alarm_name,
                "metric": metric_name.value,
                "threshold": threshold,
                "comparison": comparison_operator
            }
        except Exception as e:
            raise Exception(f"Error creating alarm: {str(e)}")
    
    async def get_metric_statistics(
        self,
        metric_name: MetricType,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistic: str = "Average"
    ) -> Dict:
        """
        Get metric statistics from CloudWatch
        """
        try:
            response = self.cloudwatch.get_metric_statistics(
                Namespace=self.namespace,
                MetricName=metric_name.value,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=[statistic]
            )
            
            datapoints = sorted(
                response.get('Datapoints', []),
                key=lambda x: x['Timestamp']
            )
            
            return {
                "metric": metric_name.value,
                "statistics": statistic,
                "datapoints": [
                    {
                        "timestamp": dp['Timestamp'].isoformat(),
                        "value": dp.get(statistic)
                    }
                    for dp in datapoints
                ],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "count": len(datapoints)
            }
        except Exception as e:
            raise Exception(f"Error getting metric statistics: {str(e)}")
    
    async def log_stress_detection_event(
        self,
        user_id: str,
        stress_score: float,
        emotion: str,
        session_duration: int
    ) -> Dict:
        """
        Log stress detection event with metrics
        """
        try:
            # Log to CloudWatch Logs
            event = {
                "event_type": "stress_detection",
                "user_id": user_id,
                "stress_score": stress_score,
                "emotion": emotion,
                "duration": session_duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.log_application_event(
                '/stressdetect/sessions',
                'stress-detections',
                event
            )
            
            # Put metrics to CloudWatch
            await self.put_metric_data(
                MetricType.STRESS_SCORE,
                stress_score,
                'None',
                {'User': user_id, 'Emotion': emotion}
            )
            
            # Track user sessions
            await self.put_metric_data(
                MetricType.USER_SESSIONS,
                1,
                'Count',
                {'User': user_id}
            )
            
            return {
                "status": "logged",
                "event_type": "stress_detection",
                "metrics_published": 2
            }
        except Exception as e:
            raise Exception(f"Error logging stress event: {str(e)}")
    
    async def log_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Log API request metrics
        """
        try:
            # Log event
            event = {
                "event_type": "api_request",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.log_application_event(
                '/stressdetect/api',
                'requests',
                event
            )
            
            # Track API calls
            await self.put_metric_data(
                MetricType.API_CALLS,
                1,
                'Count',
                {'Endpoint': endpoint, 'Method': method}
            )
            
            # Track errors
            if status_code >= 400:
                await self.put_metric_data(
                    MetricType.ERROR_RATE,
                    1,
                    'Count',
                    {'StatusCode': str(status_code)}
                )
            
            # Track response time
            await self.put_metric_data(
                MetricType.DATABASE_LATENCY,
                response_time_ms,
                'Milliseconds',
                {'Endpoint': endpoint}
            )
            
            return {
                "status": "logged",
                "endpoint": endpoint,
                "status_code": status_code,
                "response_time_ms": response_time_ms
            }
        except Exception as e:
            raise Exception(f"Error logging API request: {str(e)}")
    
    async def get_dashboard_data(
        self,
        hours: int = 24
    ) -> Dict:
        """
        Get dashboard data with key metrics
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            metrics_data = {}
            
            for metric in [
                MetricType.API_CALLS,
                MetricType.ERROR_RATE,
                MetricType.STRESS_SCORE
            ]:
                stats = await self.get_metric_statistics(
                    metric,
                    start_time,
                    end_time,
                    period=3600  # Hourly
                )
                metrics_data[metric.value] = stats
            
            return {
                "period": f"Last {hours} hours",
                "metrics": metrics_data,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error getting dashboard data: {str(e)}")
    
    async def list_application_logs(
        self,
        log_group: str,
        limit: int = 100,
        start_time_minutes_ago: int = 60
    ) -> Dict:
        """
        List recent application logs
        """
        try:
            start_time = int(
                (datetime.utcnow() - timedelta(minutes=start_time_minutes_ago))
                .timestamp() * 1000
            )
            end_time = int(datetime.utcnow().timestamp() * 1000)
            
            response = self.logs.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                endTime=end_time,
                limit=limit
            )
            
            events = []
            for event in response.get('events', []):
                try:
                    message = json.loads(event['message'])
                except:
                    message = event['message']
                
                events.append({
                    'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                    'message': message,
                    'log_stream': event.get('logStreamName', 'unknown')
                })
            
            return {
                "log_group": log_group,
                "events": events,
                "total_events": len(events),
                "time_range": f"Last {start_time_minutes_ago} minutes"
            }
        except Exception as e:
            raise Exception(f"Error listing logs: {str(e)}")

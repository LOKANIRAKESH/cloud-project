"""
AWS S3 Storage Service
Stores exported data, backups, and reports in AWS S3
Provides secure file management and retrieval
"""
import boto3
import json
import io
import os
from typing import Dict, Optional, BinaryIO
from datetime import datetime, timedelta
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class StorageType(str, Enum):
    EXPORT = "exports"
    BACKUP = "backups"
    REPORTS = "reports"
    ARCHIVE = "archive"

class S3StorageService:
    """
    AWS S3 based storage service for data persistence
    Handles file uploads, downloads, and management
    """
    
    def __init__(self, bucket_name: str, aws_region: str = "us-east-1"):
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
        
        self.s3_client = boto3.client('s3', **client_kwargs)
        self.bucket_name = bucket_name
        self.region = aws_region
    
    async def upload_file(
        self,
        user_id: str,
        file_name: str,
        file_content: bytes,
        storage_type: StorageType = StorageType.EXPORT,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Upload file to S3
        Files are organized by user and storage type
        """
        try:
            # Create hierarchical key: storage_type/user_id/timestamp-filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            s3_key = f"{storage_type.value}/{user_id}/{timestamp}_{file_name}"
            
            # Prepare metadata
            meta = {
                "user_id": user_id,
                "upload_date": datetime.utcnow().isoformat(),
                "file_type": storage_type.value,
                **(metadata or {})
            }
            
            # Upload to S3
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType='application/octet-stream',
                ServerSideEncryption='AES256',  # Encrypt at rest
                Metadata={k: str(v) for k, v in meta.items()}
            )
            
            return {
                "status": "uploaded",
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "file_size": len(file_content),
                "etag": response['ETag'],
                "upload_time": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error uploading to S3: {str(e)}")
    
    async def download_file(
        self,
        user_id: str,
        s3_key: str
    ) -> BinaryIO:
        """Download file from S3"""
        try:
            # Verify user owns this file
            if f"/{user_id}/" not in s3_key:
                raise Exception("Access denied - file not owned by user")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return response['Body'].read()
        except Exception as e:
            raise Exception(f"Error downloading from S3: {str(e)}")
    
    async def list_user_exports(
        self,
        user_id: str,
        storage_type: StorageType = StorageType.EXPORT,
        limit: int = 50
    ) -> Dict:
        """List all exports for a user"""
        try:
            prefix = f"{storage_type.value}/{user_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            exports = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    exports.append({
                        "key": obj['Key'],
                        "filename": obj['Key'].split('/')[-1],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "storage_class": obj['StorageClass']
                    })
            
            return {
                "user_id": user_id,
                "storage_type": storage_type.value,
                "exports": exports,
                "total_count": len(exports)
            }
        except Exception as e:
            raise Exception(f"Error listing exports: {str(e)}")
    
    async def delete_file(
        self,
        user_id: str,
        s3_key: str
    ) -> Dict:
        """Delete file from S3"""
        try:
            # Verify user owns this file
            if f"/{user_id}/" not in s3_key:
                raise Exception("Access denied - cannot delete")
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                "status": "deleted",
                "s3_key": s3_key,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error deleting from S3: {str(e)}")
    
    async def generate_download_url(
        self,
        user_id: str,
        s3_key: str,
        expiration_hours: int = 24
    ) -> Dict:
        """Generate pre-signed URL for file download"""
        try:
            # Verify user owns this file
            if f"/{user_id}/" not in s3_key:
                raise Exception("Access denied")
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration_hours * 3600
            )
            
            return {
                "download_url": url,
                "expires_in_hours": expiration_hours,
                "expires_at": (
                    datetime.utcnow() + timedelta(hours=expiration_hours)
                ).isoformat()
            }
        except Exception as e:
            raise Exception(f"Error generating download URL: {str(e)}")
    
    async def backup_user_data(
        self,
        user_id: str,
        data: Dict
    ) -> Dict:
        """Backup user data to S3"""
        try:
            # Convert data to JSON
            json_data = json.dumps(data, default=str).encode('utf-8')
            
            # Upload with backup metadata
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_key = f"backups/{user_id}/backup_{timestamp}.json"
            
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=backup_key,
                Body=json_data,
                ContentType='application/json',
                ServerSideEncryption='AES256',
                StorageClass='GLACIER',  # Cost-effective for backups
                Metadata={
                    'user_id': user_id,
                    'backup_date': datetime.utcnow().isoformat(),
                    'data_type': 'user_backup'
                }
            )
            
            return {
                "status": "backed_up",
                "backup_key": backup_key,
                "size": len(json_data),
                "storage_class": "GLACIER"
            }
        except Exception as e:
            raise Exception(f"Error backing up data: {str(e)}")
    
    async def restore_user_backup(
        self,
        user_id: str,
        backup_key: str
    ) -> Dict:
        """Restore user data from S3 backup"""
        try:
            # Verify user owns this backup
            if f"/{user_id}/" not in backup_key:
                raise Exception("Access denied")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=backup_key
            )
            
            backup_data = json.loads(response['Body'].read().decode('utf-8'))
            
            return {
                "status": "restored",
                "data": backup_data,
                "restore_time": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise Exception(f"Error restoring backup: {str(e)}")
    
    async def get_storage_stats(
        self,
        user_id: str
    ) -> Dict:
        """Get storage usage statistics for user"""
        try:
            prefix = f"{StorageType.EXPORT.value}/{user_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            total_size = 0
            total_files = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    total_size += obj['Size']
                    total_files += 1
            
            return {
                "user_id": user_id,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_limit_gb": 5,
                "percentage_used": round((total_size / (5 * 1024**3)) * 100, 2)
            }
        except Exception as e:
            raise Exception(f"Error getting storage stats: {str(e)}")
    
    async def create_bucket_if_not_exists(self) -> Dict:
        """Create S3 bucket if it doesn't exist"""
        try:
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                return {"status": "exists", "bucket": self.bucket_name}
            except:
                # Bucket doesn't exist, create it
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                
                # Enable versioning for data protection
                self.s3_client.put_bucket_versioning(
                    Bucket=self.bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
                # Set lifecycle policy (delete old backups after 90 days)
                lifecycle = {
                    'Rules': [
                        {
                            'Id': 'delete-old-backups',
                            'Status': 'Enabled',
                            'Prefix': 'backups/',
                            'Expiration': {'Days': 90}
                        }
                    ]
                }
                
                self.s3_client.put_bucket_lifecycle_configuration(
                    Bucket=self.bucket_name,
                    LifecycleConfiguration=lifecycle
                )
                
                return {
                    "status": "created",
                    "bucket": self.bucket_name,
                    "versioning": "enabled"
                }
        except Exception as e:
            raise Exception(f"Error managing S3 bucket: {str(e)}")

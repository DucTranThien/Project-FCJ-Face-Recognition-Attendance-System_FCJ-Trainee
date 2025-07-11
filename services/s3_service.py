import boto3
import os
from botocore.exceptions import ClientError

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'ap-southeast-1'))
        self.bucket_name = os.getenv('S3_BUCKET')
    
    def upload_image(self, file, username):
        try:
            key = f"faces/{username}.jpg"
            
            # Ensure file pointer is at the beginning
            if hasattr(file, 'seek'):
                file.seek(0)
            
            # Detect content type from file
            content_type = 'image/jpeg'  # Default
            if hasattr(file, 'content_type') and file.content_type:
                content_type = file.content_type
            elif hasattr(file, 'filename') and file.filename:
                if file.filename.lower().endswith('.png'):
                    content_type = 'image/png'
            
            # Upload to S3 with public-read ACL
            self.s3_client.upload_fileobj(
                file, 
                self.bucket_name, 
                key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'
                }
            )
            
            # Return the public URL
            url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION', 'ap-southeast-1')}.amazonaws.com/{key}"
            return url
            
        except (ClientError, Exception):
            return None
    
    def get_image_url(self, username):
        return f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION', 'ap-southeast-1')}.amazonaws.com/faces/{username}.jpg"
    
    def get_presigned_url(self, username, expiration=3600):
        """Generate a presigned URL for private image access"""
        try:
            key = f"faces/{username}.jpg"
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return response
        except ClientError:
            return None
    
    def validate_bucket_setup(self):
        """Validate S3 bucket configuration for public access"""
        try:
            # Check if bucket exists and is accessible
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            
            # Check public access block configuration
            try:
                response = self.s3_client.get_public_access_block(Bucket=self.bucket_name)
                config = response['PublicAccessBlockConfiguration']
                if any(config.values()):
                    return False
            except ClientError:
                pass
            
            return True
        except ClientError:
            return False
import boto3
import os
from botocore.exceptions import ClientError

class RekognitionService:
    def __init__(self):
        self.rekognition_client = boto3.client('rekognition', region_name=os.getenv('AWS_REGION', 'ap-southeast-1'))
        self.bucket_name = os.getenv('S3_BUCKET')
    
    def compare_faces(self, username, uploaded_image):
        try:
            # Handle both file objects and BytesIO objects
            if hasattr(uploaded_image, 'read'):
                image_bytes = uploaded_image.read()
            else:
                image_bytes = uploaded_image.getvalue()
                
            response = self.rekognition_client.compare_faces(
                SourceImage={'S3Object': {'Bucket': self.bucket_name, 'Name': f'faces/{username}.jpg'}},
                TargetImage={'Bytes': image_bytes},
                SimilarityThreshold=90
            )
            
            if response['FaceMatches']:
                return response['FaceMatches'][0]['Similarity']
            return 0
        except ClientError:
            return 0
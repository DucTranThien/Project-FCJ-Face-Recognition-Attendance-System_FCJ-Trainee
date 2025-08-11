---
title : "Set Up Amazon Rekognition Collection"
date : "" 
weight : 2
chapter : false
pre : " <b> 3.2. </b> "
---

1. **Create Amazon Rekognition Collection via AWS CLI**

   Amazon Rekognition collections are containers for face data that enable you to search for faces. We'll create a collection for the FCJ Face Recognition Attendance System.

   Open your terminal or command prompt and run the following AWS CLI command:

   {{< copycode >}}
   aws rekognition create-collection --collection-id fcj-faces --region ap-southeast-1
   {{< /copycode >}}

![Connect](/images/3.connect/01-3.2-setupcollection.png)

2. **Verify Collection Creation**

   To verify that your collection was created successfully, list all collections:

   {{< copycode >}}
   aws rekognition list-collections --region ap-southeast-1
   {{< /copycode >}}

   You should see output similar to:
   ```json
   {
       "CollectionIds": [
           "fcj-faces"
       ]
   }
   ```

![Connect](/images/3.connect/02-3.2-listcollection.png)

3. **Create DynamoDB Tables**

   Create the required DynamoDB tables for storing user data and attendance logs:

   **Users Table:**
   {{< copycode >}}
  self.dynamodb.create_table(
                TableName=os.getenv('USERS_TABLE'),
                KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
   {{< /copycode >}}

![Connect](/images/3.connect/03-3.2-tableuser.png)

   **Checkin Setting Table:**
   {{< copycode >}}
   def save_checkin(self, username, similarity, status):
        try:
            from datetime import datetime, time
            now = datetime.now()
            current_time = now.time()
            
            # Get dynamic similarity threshold
            threshold = self.settings_service.get_similarity_threshold()
            
            # Only save if similarity meets threshold and status is success
            if status != 'success' or similarity < threshold:
                return {
                    'error': 'recognition_failed',
                    'similarity': similarity,
                    'threshold': threshold,
                    'message': f'Face recognition failed. Similarity: {similarity:.1f}% (Required: ≥95%)',
                    'can_retry': True,
                    'session_type': 'unknown'
                }
   {{< /copycode >}}

![Connect](/images/3.connect/04-3.2-tablecheckinsetting.png)

   **Checkin History Table:**
   {{< copycode >}}
   self.dynamodb.create_table(
                TableName=os.getenv('CHECKIN_TABLE'),
                KeySchema=[
                    {'AttributeName': 'username', 'KeyType': 'HASH'},
                    {'AttributeName': 'checkin_time', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'username', 'AttributeType': 'S'},
                    {'AttributeName': 'checkin_time', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
   {{< /copycode >}}

![Connect](/images/3.connect/05-3.2-tablecheckinhistory.png)

4. **Create S3 Bucket for User Photos (Private with Presigned URLs)**

   Create a private S3 bucket to store user face photos securely:

   {{< copycode >}}
   # Create bucket with timestamp for uniqueness
   BUCKET_NAME="fcj-user-photos-$(date +%s)"
   aws s3 mb s3://fcj-face --region ap-southeast-1
   
   # Block public access for security
   aws s3api put-public-access-block \
       --bucket fcj-face \
       --public-access-block-configuration \
       "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
   {{< /copycode >}}

   > **Note**: The bucket is configured as private. The application will use presigned URLs for secure access to face images.

5. **Configure SES for Email OTP**

   Set up Amazon SES for sending OTP emails:

   **Verify your email address (for sandbox mode):**
   {{< copycode >}}
   aws ses verify-email-identity --email-address your-email@example.com --region ap-southeast-1
   {{< /copycode >}}

   **Check verification status:**
   {{< copycode >}}
   aws ses get-identity-verification-attributes --identities your-email@example.com --region ap-southeast-1
   {{< /copycode >}}

   {{% notice info %}}
   **SES Sandbox vs Production:**
   - **Sandbox mode**: Can only send emails to verified addresses (good for testing)
   - **Production mode**: Can send emails to any address (requires AWS support request)
   - For production deployment, request to move out of SES sandbox through AWS Support
   {{% /notice %}}

![Connect](/images/3.connect/06-3.2-verifyotp.png)

6. **Test Rekognition Collection**

   Test your Rekognition collection by indexing a sample face (optional):

   {{< copycode >}}
   # First, upload a test image to your S3 bucket
   aws s3 cp sample.jpg s3://$BUCKET_NAME/faces/test-user.jpg
   
   # Index the face in Rekognition collection
   aws rekognition index-faces \
       --collection-id fcj-faces \
       --image '{"S3Object":{"Bucket":"'$BUCKET_NAME'","Name":"faces/test-user.jpg"}}' \
       --external-image-id "test-user" \
       --region ap-southeast-1
   {{< /copycode >}}

![Connect](/images/3.connect/07-3.2-faceimagecheckin.png)

   The setup is now complete. You have:
   -  Rekognition collection `fcj-faces` for face indexing and searching
   -  DynamoDB tables for users, attendance logs, OTP codes, and settings
   -  Private S3 bucket for storing user photos securely
   -  SES configured for OTP email delivery
   -  All resources configured in the `ap-southeast-1` region

   {{% notice tip %}}
   **DynamoDB TTL Configuration:**
   - OTP codes automatically expire after 10 minutes using DynamoDB TTL
   - Account locking information is stored in the settings table
   - Failed login attempts are tracked per user email
   - Accounts are automatically unlocked after a configurable time period
   {{% /notice %}}
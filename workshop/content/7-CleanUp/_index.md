---
title: "Clean up Resources"
date: "" 
weight: 7
chapter: false
pre: " <b> 7. </b> "
---

We will follow the steps below to delete the resources created during this lab.

{{% notice warning %}}
**Important**: Follow the cleanup steps in the correct order to avoid dependency issues. Some resources must be deleted before others.
{{% /notice %}}

#### Step 1: Delete Zappa Deployment First

Delete the entire Zappa deployment (Lambda function, API Gateway, IAM roles):

{{< copycode >}}
# Navigate to backend directory
cd backend

# Undeploy Zappa application
zappa undeploy prod
{{< /copycode >}}

This command will remove:
- Lambda function
- API Gateway
- Associated IAM roles and policies (created by Zappa)
- CloudWatch log groups

![Cleanup](/images/7.cleanup/01-3.6-cleanup.png)

#### Step 2: Delete Rekognition Collection and Face Data

**Delete all faces from collection first:**
{{< copycode >}}
# List all faces in collection
aws rekognition list-faces --collection-id fcj-faces --region ap-southeast-1

# Delete collection (this removes all faces automatically)
aws rekognition delete-collection --collection-id fcj-faces --region ap-southeast-1
{{< /copycode >}}

#### Step 3: Delete DynamoDB Tables

**Delete all DynamoDB tables:**
{{< copycode >}}
aws dynamodb delete-table --table-name fcj-users --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-attendance-logs --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-otp-codes --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-settings --region ap-southeast-1
{{< /copycode >}}

**Verify tables are deleted:**
{{< copycode >}}
aws dynamodb list-tables --region ap-southeast-1
{{< /copycode >}}

![Cleanup](/images/7.cleanup/02-3.6-cleanup.png)

#### Step 4: Delete S3 Buckets

**Delete User Photos Bucket (with all face images):**
{{< copycode >}}
# Replace with your actual bucket name
BUCKET_NAME="fcj-user-photos-1234567890"

# Empty the bucket first (removes all objects and versions)
aws s3 rm s3://$BUCKET_NAME --recursive --region ap-southeast-1

# Delete the bucket
aws s3 rb s3://$BUCKET_NAME --region ap-southeast-1
{{< /copycode >}}

**Delete Zappa Deployment Bucket:**
{{< copycode >}}
# Empty the bucket first
aws s3 rm s3://fcj-zappa-deployments --recursive --region ap-southeast-1

# Delete the bucket
aws s3 rb s3://fcj-zappa-deployments --region ap-southeast-1
{{< /copycode >}}

**Delete Frontend Hosting Bucket (if created):**
{{< copycode >}}
# Replace with your frontend bucket name
FRONTEND_BUCKET="your-frontend-bucket-name"

# Empty and delete frontend bucket
aws s3 rm s3://$FRONTEND_BUCKET --recursive --region ap-southeast-1
aws s3 rb s3://$FRONTEND_BUCKET --region ap-southeast-1
{{< /copycode >}}

#### Step 5: Delete CloudFront Distribution

1. Go to the [CloudFront service management console](https://us-east-1.console.aws.amazon.com/cloudfront/v4/home)  
   + Click **Distributions**.  
   + Select the distribution you created during the lab, and click **Disable** to disable the domain before deletion.

![Cleanup](/images/7.cleanup/04-3.6-cleanup.png)

2. Wait for the distribution to be disabled (this may take 15-20 minutes).
   + Once the domain is successfully disabled, click **Delete** to remove it and confirm deletion.

![Cleanup](/images/7.cleanup/03-3.6-cleanup.png)

#### Step 6: Clean up SES Configuration

**Remove verified email addresses (if no longer needed):**
{{< copycode >}}
# List verified identities
aws ses list-identities --region ap-southeast-1

# Delete specific email identity
aws ses delete-identity --identity your-email@example.com --region ap-southeast-1
{{< /copycode >}}

#### Step 7: Delete Custom IAM Role and Policy

Go to the [IAM service management console](https://us-east-1.console.aws.amazon.com/iam/home)  

**Delete Custom Policy:**
1. Click the **Policies** tab.  
2. Click **Filter by Type** and select **Customer managed**.  
3. Search for the policy you created (e.g., `FCJ-FaceRecognition-Policy`) and click **Delete**, then confirm the deletion.

**Delete Custom Role:**
1. Click the **Roles** tab.  
2. Select the role you created during the lab (e.g., `FCJ-FaceRecognition-Role`). Click **Delete**.  
3. Enter the role name and confirm deletion.

#### Step 8: Verify Complete Cleanup

**Run verification commands to ensure all resources are deleted:**

{{< copycode >}}
# Verify Rekognition collections
aws rekognition list-collections --region ap-southeast-1

# Verify DynamoDB tables
aws dynamodb list-tables --region ap-southeast-1

# Verify S3 buckets (should not show FCJ-related buckets)
aws s3 ls

# Verify Lambda functions (should not show FCJ-related functions)
aws lambda list-functions --region ap-southeast-1
{{< /copycode >}}

#### Cost Verification

After cleanup, verify that no charges are being incurred:

1. **AWS Cost Explorer**: Check for any ongoing charges related to:
   - Lambda invocations
   - DynamoDB requests
   - S3 storage
   - Rekognition API calls
   - CloudFront data transfer

2. **CloudWatch Billing Alarms**: Set up billing alerts to monitor unexpected charges

{{% notice tip %}}
**Complete Cleanup Checklist:**
- Zappa deployment undeployed
- Rekognition collection deleted
- All DynamoDB tables deleted
- All S3 buckets emptied and deleted
- CloudFront distribution disabled and deleted
- SES verified identities removed (optional)
- Custom IAM role and policy deleted
- No ongoing AWS charges verified
{{% /notice %}}

{{% notice warning %}}
**Important Notes:**
- CloudFront distribution deletion can take up to 24 hours to complete
- DynamoDB tables with TTL may take additional time to fully clean up
- S3 buckets with versioning enabled may require additional cleanup steps
- Always verify billing after cleanup to ensure no unexpected charges
{{% /notice %}}
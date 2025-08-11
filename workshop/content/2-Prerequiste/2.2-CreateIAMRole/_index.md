---
title: "Create IAM Role"
date: "" 
weight: 3
chapter: false
pre: " <b> 2.3 </b> "
---

#### Access the **IAM** Service on AWS

1. From the IAM service console, select **Policies** from the left-hand navigation menu  
   + Click the **Create policy** button

2. In the **Create policy** dialog:  
   + Choose the **JSON** tab in the **Policy editor** section and paste the following content. Make sure to replace `<YourAccountID>` with your actual AWS account ID and `<YourS3BucketName>` with your S3 bucket name.

{{< copycode >}}
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:ap-southeast-1:<YourAccountID>:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:ap-southeast-1:<YourAccountID>:table/fcj-users",
                "arn:aws:dynamodb:ap-southeast-1:<YourAccountID>:table/fcj-attendance-logs",
                "arn:aws:dynamodb:ap-southeast-1:<YourAccountID>:table/fcj-otp-codes"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "rekognition:CreateCollection",
                "rekognition:DeleteCollection",
                "rekognition:ListCollections",
                "rekognition:IndexFaces",
                "rekognition:SearchFacesByImage",
                "rekognition:DeleteFaces",
                "rekognition:ListFaces",
                "rekognition:CompareFaces",
                "rekognition:DetectFaces"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectVersion"
            ],
            "Resource": "arn:aws:s3:::<YourS3BucketName>/faces/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail",
                "ses:GetSendQuota",
                "ses:GetSendStatistics"
            ],
            "Resource": "*"
        }
    ]
}
{{< /copycode >}}

+ Click **Next**, enter a name of your choice for the policy under **Policy name** (e.g., `FCJ-FaceRecognition-Policy`), scroll down and click **Create policy**  
+ Wait for the policy to be created successfully. Return to the IAM Policies main page to verify that your new policy appears in the list.

![IAMPolicy](/images/2.prerequisite/01-2.2-policysuccess.png)

{{% notice warning %}}
**Important Notes:**
- This IAM policy follows the principle of least privilege, granting only the necessary permissions for the FCJ Face Recognition system
- The Rekognition permissions allow collection management and face operations
- S3 permissions are restricted to the `/faces/` prefix for security
- SES permissions are required for OTP email functionality
- DynamoDB permissions are scoped to the three specific tables used by the application
{{% /notice %}}
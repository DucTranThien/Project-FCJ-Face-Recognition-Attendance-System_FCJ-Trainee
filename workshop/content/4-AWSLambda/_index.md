---
title : "Deploy Flask Backend with Zappa"
date : "" 
weight : 4
chapter : false
pre : " <b> 4. </b> "
---

## Overview

In this step, we will deploy the Flask backend to AWS Lambda using Zappa with production-ready configuration for the FCJ Face Recognition system.

## 1. Prepare Python Environment

Create and activate virtual environment:

{{< copycode >}}
python -m venv .venv
{{< /copycode >}}

**Windows:**
{{< copycode >}}
.venv\Scripts\activate
{{< /copycode >}}

**macOS/Linux:**
{{< copycode >}}
source .venv/bin/activate
{{< /copycode >}}

Update pip and install dependencies:

{{< copycode >}}
pip install --upgrade pip
pip install -r requirements.txt
{{< /copycode >}}

![Zappa Environment Setup](/images/4.lambda/01-3.3-configlambda.png)

## 2. Create S3 Bucket for Zappa Deployments

Create dedicated bucket for storing deployment packages:

{{< copycode >}}
aws s3 mb s3://fcj-checkin-zappa-deployments --region ap-southeast-1
{{< /copycode >}}

![S3 Bucket Creation](/images/4.lambda/02-3.3-s3bucket.png)

## 3. Initialize Zappa Configuration

Run Zappa initialization command:

{{< copycode >}}
zappa init
{{< /copycode >}}

When prompted, enter the following information:
- **App function**: `app.app`
- **AWS Region**: `ap-southeast-1`
- **S3 bucket**: `fcj-checkin-zappa-deployments`
- **Environment name**: `production`

![Zappa Init](/images/4.lambda/03-3.3-configzappa.png)

## 4. Configure zappa_settings.json for Production

Update `zappa_settings.json` file with production configuration:

{{< copycode >}}
{
  "production": {
    "app_function": "app.app",
    "aws_region": "ap-southeast-1",
    "project_name": "fcj-checkin",
    "runtime": "python3.9",
    "s3_bucket": "fcj-checkin-zappa-deployments",
    "memory_size": 1024,
    "timeout_seconds": 30,
    "keep_warm": false,
    "slim_handler": true,
    "exclude": [
      "*.pyc","__pycache__",".git",".env","*.md",
      "fresh_env","zappa_env","handler_venv","*.zip","*.rar"
    ]
  }
}
{{< /copycode >}}

![Zappa Settings](/images/4.lambda/04-3.3-zappasetting.png)

## 5. Deploy to AWS Lambda

Perform initial deployment:

{{< copycode >}}
zappa deploy production
{{< /copycode >}}

This command will:
- Create Lambda function with Flask app
- Create API Gateway endpoint
- Configure IAM execution role
- Set up CloudWatch logs

![Zappa Deploy](/images/4.lambda/05-3.3-deploylambda.png)

## 6. Configure Environment Variables

### Method 1: Via AWS Lambda Console

Access AWS Lambda Console → Function → Configuration → Environment variables:

- `AWS_REGION`: `ap-southeast-1`
- `USERS_TABLE`: `FCJ_Users`
- `CHECKIN_TABLE`: `FCJ_CheckinLogs`
- `SETTINGS_TABLE`: `FCJ_Settings`
- `S3_BUCKET`: `fcj-user-photos-[timestamp]`
- `REKOGNITION_COLLECTION_ID`: `FCJ_FaceCollection`
- `SECRET_KEY`: `[your-secret-key]`
- `FROM_EMAIL`: `noreply@yourdomain.com`
- `FRONTEND_ORIGIN`: `https://your-cloudfront-domain.cloudfront.net`

![Environment Variables](/images/4.lambda/06-3.3-settingenvironment.png)

### Method 2: Via Zappa CLI

{{< copycode >}}
zappa update production --env AWS_REGION=ap-southeast-1,USERS_TABLE=FCJ_Users
{{< /copycode >}}

**⚠️ Security Note**: Do not store secrets in repository. Use AWS Systems Manager Parameter Store or AWS Secrets Manager for production.

## 7. Configure Secure CORS

In `app.py` file, configure CORS with specific domain:

{{< copycode >}}
from flask_cors import CORS

# Production CORS - specify exact domain
CORS(app, resources={
    r"/*": {
        "origins": "https://your-cloudfront-domain.cloudfront.net",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
}, supports_credentials=True)
{{< /copycode >}}

## 8. Configure Minimal IAM Permissions

Create IAM policy with least privilege permissions:

{{< copycode >}}
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:CreateCollection",
        "rekognition:IndexFaces",
        "rekognition:SearchFacesByImage",
        "rekognition:DeleteFaces",
        "rekognition:ListCollections"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::fcj-user-photos-*/faces/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:ap-southeast-1:*:table/FCJ_Users",
        "arn:aws:dynamodb:ap-southeast-1:*:table/FCJ_CheckinLogs",
        "arn:aws:dynamodb:ap-southeast-1:*:table/FCJ_Settings"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-southeast-1:*:*"
    }
  ]
}
{{< /copycode >}}


## 9. Testing and Operations

### Check deployment status

{{< copycode >}}
zappa status production
{{< /copycode >}}

### Monitor real-time logs

{{< copycode >}}
zappa tail production
{{< /copycode >}}

### Update when changes are made

{{< copycode >}}
zappa update production
{{< /copycode >}}

## 10. Test API Endpoints

### User registration

{{< copycode >}}
curl -X POST https://your-api-id.execute-api.ap-southeast-1.amazonaws.com/production/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "name": "Test User"
  }'
{{< /copycode >}}

### User login

{{< copycode >}}
curl -X POST https://your-api-id.execute-api.ap-southeast-1.amazonaws.com/production/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
{{< /copycode >}}

## 11. Common Troubleshooting

### CORS 4xx errors
- **Cause**: Preflight OPTIONS request rejected
- **Solution**: Check CORS configuration in `app.py` and API Gateway

### SES sandbox limitations
- **Cause**: SES in sandbox mode, can only send to verified email addresses
- **Solution**: Request production access for SES or verify email addresses

### Lambda timeout
- **Cause**: Function runs longer than 30 seconds
- **Solution**: Increase `timeout_seconds` in `zappa_settings.json`

### AccessDenied errors
- **Cause**: IAM role missing permissions
- **Solution**: Check and update IAM policy

### Pillow binary issues
- **Cause**: Pillow version incompatible with Lambda runtime
- **Solution**: Use pinned version: `Pillow==10.2.0`

## Results

After completion, you will have:

- Flask backend running on AWS Lambda with Python 3.12
- API Gateway endpoint with securely configured CORS
- Minimal IAM permissions following least privilege principle
- Securely managed environment variables
- Monitoring and logging via CloudWatch
- Production-ready deployment with Zappa

In the next step, we will deploy the frontend and integrate it with the backend API.
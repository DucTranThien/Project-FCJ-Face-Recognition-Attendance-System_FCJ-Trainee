---
title : "Triển khai Flask Backend với Zappa"
date : "" 
weight : 4
chapter : false
pre : " <b> 4. </b> "
---

## Tổng quan

Trong bước này, chúng ta sẽ triển khai Flask backend lên AWS Lambda sử dụng Zappa với cấu hình production-ready cho hệ thống FCJ Face Recognition.

## 1. Chuẩn bị môi trường Python

Tạo và kích hoạt virtual environment:

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

Cập nhật pip và cài đặt dependencies:

{{< copycode >}}
pip install --upgrade pip
pip install -r requirements.txt
{{< /copycode >}}

![Zappa Environment Setup](/images/4.lambda/01-3.3-configlambda.png)

## 2. Tạo S3 Bucket cho Zappa Deployments

Tạo bucket chuyên dụng để lưu trữ deployment packages:

{{< copycode >}}
aws s3 mb s3://fcj-checkin-zappa-deployments --region ap-southeast-1
{{< /copycode >}}

![S3 Bucket Creation](/images/4.lambda/02-3.3-s3bucket.png)

## 3. Khởi tạo Zappa Configuration

Chạy lệnh khởi tạo Zappa:

{{< copycode >}}
zappa init
{{< /copycode >}}

Khi được hỏi, nhập các thông tin sau:
- **App function**: `app.app`
- **AWS Region**: `ap-southeast-1`
- **S3 bucket**: `fcj-checkin-zappa-deployments`
- **Environment name**: `production`

![Zappa Init](/images/4.lambda/03-3.3-configzappa.png)

## 4. Cấu hình zappa_settings.json Production

Cập nhật file `zappa_settings.json` với cấu hình production:

{{< copycode >}}
{
  "production": {
    "app_function": "app.app",
    "aws_region": "ap-southeast-1",
    "project_name": "fcj-checkin",
    "runtime": "python3.12",
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

## 5. Triển khai lên AWS Lambda

Thực hiện deployment đầu tiên:

{{< copycode >}}
zappa deploy production
{{< /copycode >}}

Lệnh này sẽ:
- ✅ Tạo Lambda function với Flask app
- ✅ Tạo API Gateway endpoint
- ✅ Cấu hình IAM execution role
- ✅ Thiết lập CloudWatch logs

![Zappa Deploy](/images/4.lambda/05-3.3-deploylambda.png)

## 6. Cấu hình biến môi trường

### Phương pháp 1: Qua AWS Lambda Console

Truy cập AWS Lambda Console → Function → Configuration → Environment variables:

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

### Phương pháp 2: Qua Zappa CLI

{{< copycode >}}
zappa update production --env AWS_REGION=ap-southeast-1,USERS_TABLE=FCJ_Users
{{< /copycode >}}

**⚠️ Lưu ý bảo mật**: Không lưu secrets trong repository. Sử dụng AWS Systems Manager Parameter Store hoặc AWS Secrets Manager cho production.

## 7. Cấu hình CORS an toàn

Trong file `app.py`, cấu hình CORS với domain cụ thể:

{{< copycode >}}
from flask_cors import CORS

# Production CORS - chỉ định domain cụ thể
CORS(app, resources={
    r"/*": {
        "origins": "https://your-cloudfront-domain.cloudfront.net",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
}, supports_credentials=True)
{{< /copycode >}}

## 8. Cấu hình IAM permissions tối thiểu

Tạo IAM policy với quyền tối thiểu cần thiết:

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

## 9. Kiểm tra và vận hành

### Kiểm tra trạng thái deployment

{{< copycode >}}
zappa status production
{{< /copycode >}}

### Theo dõi logs real-time

{{< copycode >}}
zappa tail production
{{< /copycode >}}

### Cập nhật khi có thay đổi

{{< copycode >}}
zappa update production
{{< /copycode >}}

## 10. Test API endpoints

### Health check

{{< copycode >}}
curl https://your-api-id.execute-api.ap-southeast-1.amazonaws.com/production/health
{{< /copycode >}}

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

## 11. Troubleshooting thường gặp

### CORS 4xx errors
- **Nguyên nhân**: Preflight OPTIONS request bị từ chối
- **Giải pháp**: Kiểm tra cấu hình CORS trong `app.py` và API Gateway

### SES sandbox limitations
- **Nguyên nhân**: SES đang ở chế độ sandbox, chỉ gửi được email đến địa chỉ đã verify
- **Giải pháp**: Request production access cho SES hoặc verify email addresses

### Lambda timeout
- **Nguyên nhân**: Function chạy quá 30 giây
- **Giải pháp**: Tăng `timeout_seconds` trong `zappa_settings.json`

### AccessDenied errors
- **Nguyên nhân**: IAM role thiếu permissions
- **Giải pháp**: Kiểm tra và cập nhật IAM policy

### Pillow binary issues
- **Nguyên nhân**: Pillow version không tương thích với Lambda runtime
- **Giải pháp**: Sử dụng version đã pin: `Pillow==10.2.0`

## Kết quả

Sau khi hoàn thành, bạn sẽ có:

- Flask backend chạy trên AWS Lambda với Python 3.12
- API Gateway endpoint với CORS được cấu hình an toàn
- IAM permissions tối thiểu theo nguyên tắc least privilege
- Environment variables được quản lý bảo mật
- Monitoring và logging qua CloudWatch
- Production-ready deployment với Zappa

Trong bước tiếp theo, chúng ta sẽ triển khai frontend và tích hợp với backend API.
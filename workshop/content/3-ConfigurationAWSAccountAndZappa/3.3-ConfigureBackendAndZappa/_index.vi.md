---
title: "Cấu hình Flask Backend và Zappa"
date: "" 
weight: 3
chapter: false
pre: " <b> 3.3. </b> "
---

1. **Thiết lập Python Virtual Environment và cài đặt Dependencies**

   Điều hướng đến thư mục **backend** và tạo Python virtual environment:

   {{< copycode >}}
   cd backend
   python -m venv venv
   
   # Trên Windows
   venv\Scripts\activate
   
   # Trên macOS/Linux
   source venv/bin/activate
   {{< /copycode >}}

   **Cập nhật requirements.txt với các phiên bản đã pin:**

   {{< copycode >}}
   Flask==2.3.3
   Werkzeug==2.3.7
   boto3==1.34.0
   python-dotenv==1.0.1
   Pillow==10.2.0
   zappa==0.58.0
   flask-cors==4.0.0
   bcrypt==4.1.2
   {{< /copycode >}}

   Cài đặt các Python packages cần thiết:

   {{< copycode >}}
   pip install -r requirements.txt
   {{< /copycode >}}

![Connect](/images/3.connect/08-3.3-downloadrequirements.png)

2. **Cấu hình Environment Variables (Cập nhật cho Production)**

   Tạo file `.env` trong thư mục **backend** với cấu hình AWS cụ thể của bạn:

   {{< copycode >}}
   # Sao chép từ .env.example và điền các giá trị của bạn
   cp .env.example .env
   {{< /copycode >}}

   Chỉnh sửa file `.env` với các giá trị thực tế của bạn:

   ```bash
   # Cấu hình AWS (không cần trên Lambda - sử dụng IAM roles)
   AWS_REGION=ap-southeast-1

   # DynamoDB Tables
   USERS_TABLE=fcj-users
   CHECKIN_TABLE=fcj-attendance-logs
   SETTINGS_TABLE=fcj-settings

   # Cấu hình S3
   S3_BUCKET=fcj-user-photos-1234567890

   # Cài đặt ứng dụng
   SECRET_KEY=your-secret-key-here
   FROM_EMAIL=your-verified-email@example.com
   FRONTEND_ORIGIN=https://your-cloudfront-domain.cloudfront.net

   # Chỉ dành cho development (xóa trong production)
   FLASK_ENV=development
   ```

   {{% notice warning %}}
   **Quan trọng**: Không bao gồm `AWS_ACCESS_KEY_ID` và `AWS_SECRET_ACCESS_KEY` trong production. Lambda functions nên sử dụng IAM roles để truy cập dịch vụ AWS.
   {{% /notice %}}

3. **Cấu hình CORS (Cross-Origin Resource Sharing)**

   Cập nhật ứng dụng Flask của bạn để xử lý CORS đúng cách:

   ```python
   from flask_cors import CORS
   import os

   app = Flask(__name__)
   
   # Cấu hình CORS
   frontend_origin = os.getenv('FRONTEND_ORIGIN', '*')
   CORS(app, origins=[frontend_origin], 
        methods=['GET', 'POST', 'PUT', 'DELETE'],
        allow_headers=['Content-Type', 'Authorization'])
   ```

   **Tùy chọn cấu hình CORS:**
   - **Development**: Sử dụng `*` cho tất cả origins
   - **Production**: Chỉ định domain CloudFront chính xác
   - **API Gateway**: Cấu hình CORS bổ sung trong cài đặt Zappa

4. **Khởi tạo Zappa cho Serverless Deployment (Python 3.12)**

   Khởi tạo cấu hình Zappa:

   {{< copycode >}}
   zappa init
   {{< /copycode >}}

   Khi được hỏi, sử dụng các cài đặt này:
   - **Environment name**: `prod`
   - **S3 bucket**: Tạo bucket mới hoặc sử dụng bucket hiện có (ví dụ: `fcj-zappa-deployments`)
   - **App function**: `app.app`
   - **AWS Region**: `ap-southeast-1`

   **Cập nhật `zappa_settings.json` với Python 3.12 và cấu hình toàn diện:**

   ```json
   {
       "prod": {
           "app_function": "app.app",
           "aws_region": "ap-southeast-1",
           "profile_name": "default",
           "project_name": "fcj-face-recognition",
           "runtime": "python3.12",
           "s3_bucket": "fcj-zappa-deployments",
           "timeout_seconds": 30,
           "memory_size": 512,
           "environment_variables": {
               "FLASK_ENV": "production",
               "USERS_TABLE": "fcj-users",
               "CHECKIN_TABLE": "fcj-attendance-logs",
               "SETTINGS_TABLE": "fcj-settings",
               "S3_BUCKET": "fcj-user-photos-1234567890",
               "SECRET_KEY": "your-secret-key-here",
               "FROM_EMAIL": "your-verified-email@example.com",
               "FRONTEND_ORIGIN": "https://your-cloudfront-domain.cloudfront.net"
           },
           "cors": true,
           "cors_origin": "https://your-cloudfront-domain.cloudfront.net",
           "cors_methods": "GET,POST,PUT,DELETE,OPTIONS",
           "cors_headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
           "exclude": [
               "*.pyc",
               "__pycache__/*",
               "*.zip",
               "*.rar",
               "venv/*",
               "fresh_env/*",
               "zappa_env/*",
               "handler_venv/*",
               ".git/*",
               ".env",
               "README.md"
           ]
       }
   }
   ```

5. **Triển khai Flask Backend lên AWS Lambda**

   Triển khai ứng dụng Flask của bạn lên AWS Lambda:

   {{< copycode >}}
   zappa deploy prod
   {{< /copycode >}}

   Điều này sẽ:
   - Đóng gói ứng dụng Flask của bạn với Python 3.12 runtime
   - Tạo Lambda function với cài đặt timeout và memory phù hợp
   - Thiết lập API Gateway với cấu hình CORS
   - Cấu hình environment variables một cách bảo mật
   - Trả về URL endpoint API Gateway

   Sau khi triển khai thành công, bạn sẽ thấy output như:
   ```
   Deploying API Gateway..
   Deployment complete!: https://abc123.execute-api.ap-southeast-1.amazonaws.com/prod
   ```

   **Troubleshooting các vấn đề thường gặp:**

   {{% notice tip %}}
   **Vấn đề CORS:**
   - Đảm bảo `cors_origin` khớp chính xác với domain frontend của bạn
   - Kiểm tra rằng preflight OPTIONS requests được xử lý
   - Xác minh cài đặt CORS API Gateway trong AWS Console
   - Test với browser developer tools network tab
   {{% /notice %}}

   {{% notice tip %}}
   **Vấn đề Lambda:**
   - Kiểm tra CloudWatch logs: `zappa tail prod`
   - Xác minh IAM role permissions cho DynamoDB, S3, Rekognition, SES
   - Đảm bảo tương thích Python 3.12 của tất cả dependencies
   - Giám sát Lambda timeout và memory usage
   {{% /notice %}}

   {{% notice tip %}}
   **Environment Variables:**
   - Không bao giờ bao gồm AWS credentials trong Lambda environment variables
   - Sử dụng IAM roles để truy cập dịch vụ AWS
   - Giữ dữ liệu nhạy cảm trong AWS Systems Manager Parameter Store cho production
   {{% /notice %}}
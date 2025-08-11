---
title: "Configure Flask Backend and Zappa"
date: "" 
weight: 3
chapter: false
pre: " <b> 3.3. </b> "
---

1. **Set up Python Virtual Environment and Install Dependencies**

   Navigate to the **backend** folder and create a Python virtual environment:

   {{< copycode >}}
   cd backend
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   {{< /copycode >}}

   **Update requirements.txt with pinned versions:**

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

   Install the required Python packages:

   {{< copycode >}}
   pip install -r requirements.txt
   {{< /copycode >}}

![Connect](/images/3.connect/08-3.3-downloadrequirements.png)

2. **Configure Environment Variables (Updated for Production)**

   Create a `.env` file in the **backend** folder with your specific AWS configuration:

   {{< copycode >}}
   # Copy from .env.example and fill in your values
   cp .env.example .env
   {{< /copycode >}}

   Edit the `.env` file with your actual values:

   ```bash
   # AWS Configuration (not needed on Lambda - use IAM roles)
   AWS_REGION=ap-southeast-1

   # DynamoDB Tables
   USERS_TABLE=fcj-users
   CHECKIN_TABLE=fcj-attendance-logs
   SETTINGS_TABLE=fcj-settings

   # S3 Configuration
   S3_BUCKET=fcj-user-photos-1234567890

   # Application Settings
   SECRET_KEY=your-secret-key-here
   FROM_EMAIL=your-verified-email@example.com
   FRONTEND_ORIGIN=https://your-cloudfront-domain.cloudfront.net

   # Development only (remove in production)
   FLASK_ENV=development
   ```

   {{% notice warning %}}
   **Important**: Do not include `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in production. Lambda functions should use IAM roles for AWS service access.
   {{% /notice %}}

3. **Configure CORS (Cross-Origin Resource Sharing)**

   Update your Flask application to handle CORS properly:

   ```python
   from flask_cors import CORS
   import os

   app = Flask(__name__)
   
   # Configure CORS
   frontend_origin = os.getenv('FRONTEND_ORIGIN', '*')
   CORS(app, origins=[frontend_origin], 
        methods=['GET', 'POST', 'PUT', 'DELETE'],
        allow_headers=['Content-Type', 'Authorization'])
   ```

   **CORS Configuration Options:**
   - **Development**: Use `*` for all origins
   - **Production**: Specify exact CloudFront domain
   - **API Gateway**: Additional CORS configuration in Zappa settings

4. **Initialize Zappa for Serverless Deployment (Python 3.12)**

   Initialize Zappa configuration:

   {{< copycode >}}
   zappa init
   {{< /copycode >}}

   When prompted, use these settings:
   - **Environment name**: `prod`
   - **S3 bucket**: Create a new bucket or use existing (e.g., `fcj-zappa-deployments`)
   - **App function**: `app.app`
   - **AWS Region**: `ap-southeast-1`

   **Update `zappa_settings.json` with Python 3.12 and comprehensive configuration:**

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

5. **Deploy Flask Backend to AWS Lambda**

   Deploy your Flask application to AWS Lambda:

   {{< copycode >}}
   zappa deploy prod
   {{< /copycode >}}

   This will:
   - Package your Flask application with Python 3.12 runtime
   - Create a Lambda function with proper timeout and memory settings
   - Set up API Gateway with CORS configuration
   - Configure environment variables securely
   - Return an API Gateway endpoint URL

   After successful deployment, you'll see output like:
   ```
   Deploying API Gateway..
   Deployment complete!: https://abc123.execute-api.ap-southeast-1.amazonaws.com/prod
   ```

   **Troubleshooting Common Issues:**

   {{% notice tip %}}
   **CORS Issues:**
   - Ensure `cors_origin` matches your frontend domain exactly
   - Check that preflight OPTIONS requests are handled
   - Verify API Gateway CORS settings in AWS Console
   - Test with browser developer tools network tab
   {{% /notice %}}

   {{% notice tip %}}
   **Lambda Issues:**
   - Check CloudWatch logs: `zappa tail prod`
   - Verify IAM role permissions for DynamoDB, S3, Rekognition, SES
   - Ensure Python 3.12 compatibility of all dependencies
   - Monitor Lambda timeout and memory usage
   {{% /notice %}}

   {{% notice tip %}}
   **Environment Variables:**
   - Never include AWS credentials in Lambda environment variables
   - Use IAM roles for AWS service access
   - Keep sensitive data in AWS Systems Manager Parameter Store for production
   {{% /notice %}}
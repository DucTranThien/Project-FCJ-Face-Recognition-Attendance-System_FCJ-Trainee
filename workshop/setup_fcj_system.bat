@echo off
echo ========================================
echo FCJ Face Recognition Attendance System
echo Setup and Deployment Script
echo ========================================
echo.

echo Step 1: Setting up Python Virtual Environment
cd backend
python -m venv venv
call venv\Scripts\activate

echo Step 2: Installing Python Dependencies
pip install -r requirements.txt

echo Step 3: Creating AWS Resources
echo Creating Rekognition Collection...
aws rekognition create-collection --collection-id fcj-faces --region ap-southeast-1

echo Creating DynamoDB Tables...
aws dynamodb create-table --table-name fcj-users --attribute-definitions AttributeName=email,AttributeType=S --key-schema AttributeName=email,KeyType=HASH --billing-mode PAY_PER_REQUEST --region ap-southeast-1

aws dynamodb create-table --table-name fcj-attendance-logs --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=timestamp,AttributeType=S --key-schema AttributeName=user_id,KeyType=HASH AttributeName=timestamp,KeyType=RANGE --billing-mode PAY_PER_REQUEST --region ap-southeast-1

aws dynamodb create-table --table-name fcj-otp-codes --attribute-definitions AttributeName=email,AttributeType=S --key-schema AttributeName=email,KeyType=HASH --billing-mode PAY_PER_REQUEST --region ap-southeast-1

echo Enabling TTL for OTP table...
aws dynamodb update-time-to-live --table-name fcj-otp-codes --time-to-live-specification Enabled=true,AttributeName=ttl --region ap-southeast-1

echo Creating S3 Bucket for User Photos...
for /f %%i in ('powershell -command "Get-Date -UFormat %%s"') do set timestamp=%%i
aws s3 mb s3://fcj-user-photos-%timestamp% --region ap-southeast-1

echo Step 4: Testing Flask Application Locally
echo Starting Flask app for testing...
start /B python app.py
timeout /t 5 /nobreak > nul

echo Testing health endpoint...
curl http://localhost:5000/health

echo Step 5: Deploying with Zappa
echo Initializing Zappa...
zappa init

echo Deploying to AWS Lambda...
zappa deploy prod

echo Step 6: Testing Deployed API
echo Please test your deployed API endpoints:
echo.
echo Health Check:
echo curl https://your-api-url.execute-api.ap-southeast-1.amazonaws.com/prod/health
echo.
echo User Registration:
echo curl -X POST https://your-api-url.execute-api.ap-southeast-1.amazonaws.com/prod/auth/register -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\",\"password\":\"password123\",\"name\":\"Test User\"}"
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next Steps:
echo 1. Update your .env file with actual SMTP credentials
echo 2. Update frontend/index.html with your API Gateway URL
echo 3. Deploy frontend to S3 and configure CloudFront
echo 4. Test the complete flow: Register -> Verify OTP -> Login -> Check-in
echo.
echo For logs: zappa tail prod
echo For updates: zappa update prod
echo For cleanup: zappa undeploy prod
echo.
pause
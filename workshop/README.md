# FCJ Face Recognition Attendance System Workshop

## Overview

This workshop has been completely refactored from an OpenSearch + Node.js movie search system to a comprehensive **FCJ Face Recognition Attendance System** using modern serverless architecture on AWS.

## Technology Stack

### Backend
- **Runtime**: Python 3.9
- **Framework**: Flask
- **Deployment**: Zappa (Flask to AWS Lambda)
- **Region**: ap-southeast-1 (Asia Pacific - Singapore)

### AWS Services
- **Face Recognition**: Amazon Rekognition (IndexFaces, SearchFacesByImage)
- **Data Storage**: DynamoDB (Users, AttendanceLogs, OTP codes)
- **File Storage**: S3 (User photos)
- **Compute**: AWS Lambda (via Zappa)
- **API**: API Gateway (auto-configured by Zappa)
- **CDN**: CloudFront (for frontend)
- **Monitoring**: CloudWatch Logs

### Authentication & Communication
- **Authentication**: Password hashing (bcrypt) + Email OTP
- **Email Service**: SMTP (Gmail/Custom) - **NOT Amazon SES**
- **Frontend**: Static HTML/CSS/JavaScript

## Project Structure

```
workshop/
├── backend/                    # Flask application
│   ├── app.py                 # Main Flask app with all routes
│   ├── requirements.txt       # Python dependencies
│   ├── zappa_settings.json    # Zappa deployment configuration
│   ├── .env.example          # Environment variables template
│   └── services/             # Modular services
│       ├── auth.py           # Authentication service
│       ├── face.py           # Rekognition service
│       ├── storage.py        # S3 storage service
│       ├── otp.py            # SMTP OTP service
│       └── db.py             # DynamoDB service
├── frontend/                  # Static website
│   └── index.html            # Complete frontend interface
├── content/                   # Hugo documentation (refactored)
├── static/images/            # Workshop screenshots (preserved)
├── setup_fcj_system.bat     # Windows setup script
├── setup_fcj_system.sh      # Unix/Linux setup script
├── VERIFICATION_CHECKLIST.md # Complete testing checklist
├── TECHNOLOGY_MAPPING.md     # Old vs New stack mapping
└── README.md                 # This file
```

## Key Features

### 1. User Management
- **Registration**: Email, password, name
- **Email Verification**: OTP via SMTP (10-minute expiry)
- **Authentication**: Secure password hashing with bcrypt
- **Login**: Email/password with OTP verification for unverified users

### 2. Face Recognition
- **Face Indexing**: Store user faces in Rekognition collection
- **Face Search**: Real-time face matching during check-in
- **Confidence Scoring**: Configurable threshold (default: 80%)
- **Photo Storage**: User photos stored in S3 with presigned URLs

### 3. Attendance Tracking
- **Real-time Check-in**: Camera capture and face recognition
- **Attendance Logs**: Timestamped records in DynamoDB
- **Match Results**: Confidence scores and face IDs
- **Historical Data**: Query attendance history per user

### 4. API Endpoints
- `GET /health` - System health check
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /auth/verify-otp` - Email OTP verification
- `POST /checkin` - Face recognition check-in

## Quick Start

### Prerequisites
- Python 3.9+
- AWS CLI configured
- AWS account with appropriate permissions
- SMTP email credentials (Gmail app password recommended)

### 1. Automated Setup (Recommended)
```bash
# Windows
setup_fcj_system.bat

# Unix/Linux/macOS
chmod +x setup_fcj_system.sh
./setup_fcj_system.sh
```

### 2. Manual Setup
```bash
# 1. Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your AWS and SMTP credentials

# 4. Create AWS resources
aws rekognition create-collection --collection-id fcj-faces --region ap-southeast-1
aws dynamodb create-table --table-name fcj-users --attribute-definitions AttributeName=email,AttributeType=S --key-schema AttributeName=email,KeyType=HASH --billing-mode PAY_PER_REQUEST --region ap-southeast-1
# ... (see setup script for complete commands)

# 5. Test locally
python app.py
curl http://localhost:5000/health

# 6. Deploy to AWS
zappa deploy prod
```

### 3. Frontend Deployment
```bash
# Update API URL in frontend/index.html
# Upload to S3 and configure CloudFront
aws s3 sync frontend/ s3://your-frontend-bucket/
```

## Workshop Content

The Hugo documentation has been completely refactored:

1. **Introduction** - Amazon Rekognition and serverless architecture
2. **Prerequisites** - Python, pip, Git, VS Code, IAM roles
3. **AWS Configuration** - Rekognition collection, DynamoDB tables, Zappa setup
4. **Backend Deployment** - Flask app deployment via Zappa
5. **Frontend Hosting** - Static website on S3 + CloudFront
6. **Monitoring** - CloudWatch logs and debugging
7. **Cleanup** - Resource removal and cost optimization

## Testing

### API Testing
```bash
# Health check
curl https://your-api-url.execute-api.ap-southeast-1.amazonaws.com/prod/health

# User registration
curl -X POST https://your-api-url.execute-api.ap-southeast-1.amazonaws.com/prod/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# Login
curl -X POST https://your-api-url.execute-api.ap-southeast-1.amazonaws.com/prod/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Complete Flow Testing
1. Register new user → Receive OTP email
2. Verify OTP → Account activated
3. Login → Authentication successful
4. Access frontend → Camera permissions
5. Capture face → Face indexed in Rekognition
6. Check-in → Face recognition and attendance logging

## Monitoring & Debugging

```bash
# View real-time logs
zappa tail prod

# Update deployment
zappa update prod

# Check deployment status
zappa status prod
```

## Security Features

- **Password Hashing**: bcrypt with salt
- **Environment Variables**: No hardcoded credentials
- **IAM Least Privilege**: Minimal required permissions
- **CORS Configuration**: Proper frontend integration
- **OTP Expiry**: 10-minute time-based expiration
- **Input Validation**: Request data validation

## Cost Optimization

- **Serverless Architecture**: Pay-per-use Lambda functions
- **DynamoDB On-Demand**: Pay-per-request pricing
- **S3 Standard**: Cost-effective photo storage
- **CloudWatch**: Basic monitoring included
- **Rekognition**: Pay-per-API-call pricing

## Troubleshooting

### Common Issues
1. **CORS Errors**: Check `zappa_settings.json` CORS configuration
2. **SMTP Failures**: Verify Gmail app passwords and SMTP settings
3. **Permission Errors**: Ensure IAM role has required permissions
4. **Face Recognition Issues**: Check image quality and collection setup
5. **DynamoDB Errors**: Verify table names and region configuration

### Debug Commands
```bash
# View logs
zappa tail prod

# Check AWS resources
aws rekognition list-collections --region ap-southeast-1
aws dynamodb list-tables --region ap-southeast-1

# Test local Flask app
python app.py
```

## Cleanup

```bash
# Remove all resources
zappa undeploy prod
aws rekognition delete-collection --collection-id fcj-faces --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-users --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-attendance-logs --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-otp-codes --region ap-southeast-1
aws s3 rb s3://fcj-user-photos-TIMESTAMP --force --region ap-southeast-1
```

## Workshop Deliverables

✅ **Complete Backend**: Flask app with all FCJ Face Recognition features  
✅ **Frontend Interface**: HTML/CSS/JS for user interaction  
✅ **AWS Integration**: Rekognition, DynamoDB, S3, Lambda, API Gateway  
✅ **Documentation**: Refactored Hugo content with step-by-step guides  
✅ **Automation Scripts**: Setup and deployment automation  
✅ **Testing Framework**: Comprehensive verification checklist  
✅ **Technology Mapping**: Complete transformation documentation  

## Support

For issues or questions:
1. Check `VERIFICATION_CHECKLIST.md` for testing procedures
2. Review `TECHNOLOGY_MAPPING.md` for architecture details
3. Use `zappa tail prod` for real-time debugging
4. Check CloudWatch logs for detailed error information

---

**Note**: This workshop demonstrates a production-ready face recognition attendance system using modern serverless architecture on AWS, completely replacing the original OpenSearch movie search system while maintaining the same educational structure and flow.
# FCJ Face Recognition Attendance System - Verification Checklist

## Pre-Deployment Verification

### 1. Environment Setup
- [ ] Python 3.9+ installed
- [ ] AWS CLI configured with appropriate credentials
- [ ] Virtual environment created and activated
- [ ] All dependencies installed from requirements.txt

### 2. AWS Resources Created
- [ ] Rekognition collection `fcj-faces` created
- [ ] DynamoDB table `fcj-users` created
- [ ] DynamoDB table `fcj-attendance-logs` created  
- [ ] DynamoDB table `fcj-otp-codes` created with TTL enabled
- [ ] S3 bucket for user photos created
- [ ] IAM role with appropriate permissions configured

### 3. Configuration Files
- [ ] `.env` file created with all required variables
- [ ] `zappa_settings.json` configured for ap-southeast-1 region
- [ ] SMTP credentials configured (NOT SES)
- [ ] All environment variables properly set

## Local Testing

### 4. Flask Application
- [ ] `python app.py` runs without errors
- [ ] Health endpoint returns `{"ok": true, "message": "FCJ Face Recognition API is running"}`
- [ ] All service modules import successfully
- [ ] No syntax errors in any Python files

### 5. API Endpoints (Local)
```bash
# Health check
curl http://localhost:5000/health

# Expected: {"ok": true, "message": "FCJ Face Recognition API is running"}
```

## Zappa Deployment

### 6. Deployment Process
- [ ] `zappa init` completed successfully
- [ ] `zappa deploy prod` completed without errors
- [ ] API Gateway endpoint URL generated
- [ ] Lambda function created in ap-southeast-1 region
- [ ] Environment variables properly set in Lambda

### 7. Deployed API Testing
```bash
# Replace YOUR_API_URL with actual API Gateway URL
export API_URL="https://YOUR_API_URL.execute-api.ap-southeast-1.amazonaws.com/prod"

# Health check
curl $API_URL/health

# User registration
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# Expected: {"message": "User registered. Please verify OTP sent to email."}
```

## End-to-End Flow Testing

### 8. Complete User Journey
- [ ] **Registration**: User can register with email/password/name
- [ ] **OTP Email**: OTP email sent via SMTP (check spam folder)
- [ ] **OTP Verification**: OTP code verification works
- [ ] **Login**: User can login after verification
- [ ] **Face Capture**: Camera access works in frontend
- [ ] **Face Recognition**: Face indexing and searching works
- [ ] **Attendance Logging**: Check-in records saved to DynamoDB

### 9. Data Verification
```bash
# Check DynamoDB tables have data
aws dynamodb scan --table-name fcj-users --region ap-southeast-1
aws dynamodb scan --table-name fcj-attendance-logs --region ap-southeast-1

# Check Rekognition collection
aws rekognition list-faces --collection-id fcj-faces --region ap-southeast-1
```

## Frontend Deployment

### 10. Static Website
- [ ] `frontend/index.html` updated with correct API Gateway URL
- [ ] Frontend uploaded to S3 bucket
- [ ] S3 bucket configured for static website hosting
- [ ] CloudFront distribution created and deployed
- [ ] Website accessible via CloudFront URL

## Monitoring and Logs

### 11. CloudWatch Integration
- [ ] Lambda logs visible in CloudWatch
- [ ] `zappa tail prod` shows real-time logs
- [ ] Error logs captured for debugging
- [ ] Attendance events logged with timestamps

### 12. Sample Log Verification
```bash
# View logs
zappa tail prod

# Expected log entries:
# - User registration attempts
# - OTP generation and sending
# - Face recognition results
# - Attendance logging
```

## Performance and Security

### 13. Security Checks
- [ ] Passwords properly hashed with bcrypt
- [ ] Environment variables not exposed in code
- [ ] IAM permissions follow least-privilege principle
- [ ] CORS properly configured for frontend domain
- [ ] No hardcoded credentials in any files

### 14. Performance Validation
- [ ] API response times under 5 seconds
- [ ] Face recognition confidence scores reasonable (>80%)
- [ ] SMTP email delivery within 1 minute
- [ ] DynamoDB operations complete successfully

## Error Handling

### 15. Common Issues Resolution
- [ ] **CORS errors**: Verify zappa_settings.json CORS configuration
- [ ] **SMTP failures**: Check SMTP credentials and app passwords
- [ ] **Permission errors**: Verify IAM role permissions
- [ ] **Rekognition errors**: Ensure collection exists and images are valid
- [ ] **DynamoDB errors**: Check table names and region configuration

## Final Acceptance Criteria

### 16. System Integration Test
1. **New User Registration**:
   ```bash
   curl -X POST $API_URL/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"newuser@test.com","password":"secure123","name":"New User"}'
   ```

2. **OTP Verification**:
   ```bash
   curl -X POST $API_URL/auth/verify-otp \
     -H "Content-Type: application/json" \
     -d '{"email":"newuser@test.com","otp":"123456"}'
   ```

3. **User Login**:
   ```bash
   curl -X POST $API_URL/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"newuser@test.com","password":"secure123"}'
   ```

4. **Face Check-in** (via frontend):
   - Camera captures face image
   - Image sent to `/checkin` endpoint
   - Face recognition returns match result
   - Attendance logged in DynamoDB

### 17. Success Criteria
- [ ] All API endpoints return expected responses
- [ ] Email OTP delivery works consistently
- [ ] Face recognition accuracy >80% for enrolled faces
- [ ] Attendance records properly stored with timestamps
- [ ] Frontend integrates seamlessly with backend API
- [ ] System handles errors gracefully
- [ ] CloudWatch logs provide adequate debugging information

## Cleanup Verification

### 18. Resource Cleanup (After Testing)
```bash
# Undeploy Zappa
zappa undeploy prod

# Delete AWS resources
aws rekognition delete-collection --collection-id fcj-faces --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-users --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-attendance-logs --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-otp-codes --region ap-southeast-1

# Delete S3 buckets
aws s3 rb s3://fcj-user-photos-TIMESTAMP --force --region ap-southeast-1
aws s3 rb s3://fcj-zappa-deployments --force --region ap-southeast-1
```

---

**Note**: This checklist ensures the complete FCJ Face Recognition Attendance System is properly deployed and functional. Each checkbox should be verified before proceeding to the next section.
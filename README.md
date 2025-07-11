# 🧠 FCJ Face Recognition Attendance System

![Powered by AWS](https://img.shields.io/badge/Built%20with-AWS-orange?logo=amazonaws)
![Serverless](https://img.shields.io/badge/Serverless-Lambda-blue?logo=awslambda)
![License: MIT](https://img.shields.io/badge/License-MIT-green)

> AI-powered, serverless facial recognition check-in system designed for enterprise-grade attendance management.

---
📌 Project Description
The FCJ Check-in System offers a complete, contactless attendance solution that leverages Amazon Rekognition for facial verification, DynamoDB for attendance tracking, and S3 + Lambda for seamless frontend-backend integration. Users authenticate via email OTP, register face data, and perform secure check-ins in real-time.

## 🚀 Live Demo

🌐 Frontend (S3 + CloudFront):  
[https://d3v2ldedbs76u2.cloudfront.net](https://d3v2ldedbs76u2.cloudfront.net)

🔐 Backend (API Gateway + Lambda):  
`https://go18cmoqsa.execute-api.ap-southeast-1.amazonaws.com/default`

> ⚠️ Note: Make sure the backend routes like `/register`, `/login`, `/checkin`, `/dashboard` are properly deployed via API Gateway.

---

## 📦 Features

- ✅ AI Face Recognition (Amazon Rekognition)
- 🔐 OTP-based email authentication (SMTP)
- 📊 Admin dashboard with session tracking & statistics
- 🗓️ Multi-session check-in support (e.g. morning/evening)
- 📱 Mobile responsive UI (Bootstrap 5)
- 🌍 100% serverless & cloud-native architecture
- 📈 Logs & monitoring via Amazon CloudWatch

---

## 🧩 Tech Stack

| Layer       | Technology             |
|-------------|------------------------|
| Frontend    | HTML5, CSS3, Bootstrap 5 |
| Backend     | Python Flask + Zappa (AWS Lambda) |
| AI Engine   | Amazon Rekognition     |
| Storage     | Amazon S3              |
| Database    | Amazon DynamoDB        |
| Auth/Email  | Gmail SMTP (or SES)    |
| Deployment  | S3 static hosting + API Gateway |

---

## 🗂️ Project Structure

fcj-checkin/
│
├── static_frontend/             # S3-hosted static files
│   ├── index.html, login.html, dashboard.html ...
│   └── static/
│       ├── css/
│       ├── images/
│       └── js/
│           └── camera.js, main.js, notifications.js
│
├── templates/                   # Flask server-rendered templates
│   ├── base.html, register.html, checkin.html ...
│
├── services/                    # Modular backend services
│   ├── dynamodb_service.py
│   ├── rekognition_service.py
│   ├── s3_service.py
│   ├── email_service.py
│   └── settings_service.py
│
├── app.py                       # Flask entry point
├── requirements.txt            # Python dependencies
├── zappa_settings.json         # Zappa deploy settings
└── .env / .env.example         # Environment variables

---

🚀 Deployment
✅ Already deployed at:

Frontend (CloudFront): https://d3v2ldedbs76u2.cloudfront.net

Backend (API Gateway): https://go18cmoqsa.execute-api.ap-southeast-1.amazonaws.com/default

1. 🛠️ Install Python & Zappa
bash
Copy
Edit
pip install zappa
2. ⚙️ Configure Deployment
Update zappa_settings.json:

json
Copy
Edit
{
  "production": {
    "app_function": "app.app",
    "aws_region": "ap-southeast-1",
    "profile_name": "default",
    "project_name": "fcj-checkin",
    "runtime": "python3.9",
    "s3_bucket": "fcj-checkin-zappa-deployments"
  }
}
3. 🚀 Deploy to AWS
bash
Copy
Edit
zappa deploy production
📈 Metrics Dashboard (Sample)
✅ Total Check-ins: 10

🔥 Day Streak: 5

📊 Success Rate: 80.0%

⏱️ Punctuality Tracking: Completed Late, On-time, etc.


🧠 Technologies Used
Layer	Stack
Frontend	HTML5, Bootstrap 5, JavaScript
Backend	Python, Flask, Zappa
Cloud Services	AWS S3, Lambda, API Gateway, Rekognition, DynamoDB
Email OTP	SMTP / Amazon SES

🛡️ Security
✅ IAM with least privilege

✅ CORS restrictions on S3/API

✅ Email-based MFA OTP

✅ Face-based verification (no password alone)

🧪 Testing
✔️ Postman API tests for /login, /register, /checkin

✔️ Lambda CloudWatch logs

✔️ Manual validation of check-in success/fail logic

💵 Cost Estimation
Service	Monthly Estimate
Lambda	Free (under 1M)
S3	~$0.05
Rekognition	~$1
DynamoDB	Free Tier
SES/SMTP	Free (Gmail)
Total	~$1.05/month

🧑‍💻 Author
Duc Tran Thien
@ducdeptrai
FCJ Trainee – AWS First Cloud Journey
Built with ❤️ on AWS


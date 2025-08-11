---
title : "Introduction"
date : "" 
weight : 1 
chapter : false
pre : " <b> 1. </b> "
---
**Amazon Rekognition** is an AI-powered image and video analysis service that provides highly accurate facial recognition capabilities. In this workshop, you will build a complete face recognition attendance system using a modern serverless stack: Flask backend deployed via Zappa to AWS Lambda, Amazon Rekognition for face processing, DynamoDB for data storage, and S3 with CloudFront for the frontend.

By using this serverless architecture, you gain several advantages:

- **Accurate facial recognition** with Amazon Rekognition's IndexFaces and SearchFacesByImage APIs
- **Serverless scalability** with Flask on AWS Lambda via Zappa deployment
- **Secure authentication** with password hashing and email OTP verification via SMTP
- **Real-time data storage** using DynamoDB for users and attendance logs
- **Cost-effective hosting** with S3 static website and CloudFront CDN
- **Comprehensive logging** with CloudWatch for monitoring and debugging
- **Infrastructure as Code** approach with minimal manual configuration

This workshop demonstrates a production-ready attendance system that can handle user registration, face enrollment, real-time check-ins, and attendance tracking. You'll learn to integrate multiple AWS services using Python and deploy everything using modern serverless practices.
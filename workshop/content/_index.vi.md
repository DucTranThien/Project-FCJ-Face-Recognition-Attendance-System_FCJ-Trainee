---
title: "FCJ Face Recognition Attendance System"
date: "" 
weight: 1
chapter: false
---
# FCJ Face Recognition Attendance System

### Tổng quan

Trong workshop này, bạn sẽ học cách xây dựng một hệ thống điểm danh nhận diện khuôn mặt hoàn chỉnh sử dụng Amazon Rekognition, backend Flask được triển khai qua Zappa lên AWS Lambda, và frontend tĩnh được lưu trữ trên S3 với CloudFront. Hệ thống bao gồm đăng ký người dùng với xác thực OTP qua email thông qua SMTP, lập chỉ mục khuôn mặt, và theo dõi điểm danh thời gian thực với lưu trữ DynamoDB.

![ConnectPrivate](/images/arcFCJCheckin.png) 

### Mục lục

1. [Giới thiệu](1-Introduce/)
2. [Các bước chuẩn bị](2-Prerequiste/)
3. [Cấu hình AWS Account và Zappa](3-ConfigurationAWSAccountAndZappa/)
4. [Triển khai Backend với AWS Lambda](4-AWSLambda/)
5. [Lưu trữ Website tĩnh với Amazon S3 và CloudFront](5-HostingStaticWebsite/)
6. [Xem Log ứng dụng với CloudWatch](6-ApplicationLogWithCloudWatch/)
7. [Dọn dẹp tài nguyên](7-CleanUp/)
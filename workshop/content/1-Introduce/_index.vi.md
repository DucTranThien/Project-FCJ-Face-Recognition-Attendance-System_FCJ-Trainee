---
title : "Giới thiệu"
date : "" 
weight : 1 
chapter : false
pre : " <b> 1. </b> "
---
**Amazon Rekognition** là dịch vụ phân tích hình ảnh và video được hỗ trợ bởi AI, cung cấp khả năng nhận diện khuôn mặt có độ chính xác cao. Trong workshop này, bạn sẽ xây dựng một hệ thống điểm danh nhận diện khuôn mặt hoàn chỉnh sử dụng stack serverless hiện đại: Flask backend được triển khai qua Zappa lên AWS Lambda, Amazon Rekognition để xử lý khuôn mặt, DynamoDB để lưu trữ dữ liệu, và S3 với CloudFront cho frontend.

Bằng cách sử dụng kiến trúc serverless này, bạn sẽ có được nhiều lợi ích:

- **Nhận diện khuôn mặt chính xác** với các API IndexFaces và SearchFacesByImage của Amazon Rekognition
- **Khả năng mở rộng serverless** với Flask trên AWS Lambda qua triển khai Zappa
- **Xác thực bảo mật** với mã hóa mật khẩu và xác minh OTP qua email thông qua SMTP
- **Lưu trữ dữ liệu thời gian thực** sử dụng DynamoDB cho người dùng và nhật ký điểm danh
- **Hosting tiết kiệm chi phí** với S3 static website và CloudFront CDN
- **Logging toàn diện** với CloudWatch để giám sát và debug
- **Phương pháp Infrastructure as Code** với cấu hình thủ công tối thiểu

Workshop này trình bày một hệ thống điểm danh production-ready có thể xử lý đăng ký người dùng, đăng ký khuôn mặt, check-in thời gian thực, và theo dõi điểm danh. Bạn sẽ học cách tích hợp nhiều dịch vụ AWS sử dụng Python và triển khai mọi thứ bằng các thực hành serverless hiện đại.
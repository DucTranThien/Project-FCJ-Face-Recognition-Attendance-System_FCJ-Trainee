---
title: "Kết nối AWS Account với Visual Studio Code"
date: "" 
weight: 1 
chapter: false
pre: " <b> 3.1. </b> "
---

1. Sau khi cài đặt **AWS Toolkit** và cấu hình tài khoản AWS của bạn, Visual Studio Code sẽ hiển thị danh sách các dịch vụ AWS có sẵn trong region đã chọn (**Asia Pacific - Singapore**).

Tài khoản được kết nối sử dụng profile `ductran63`. Từ đây, bạn có thể dễ dàng truy cập và quản lý các dịch vụ như:

- **Lambda**: triển khai Flask backend sử dụng Zappa
- **S3**: lưu trữ hình ảnh khuôn mặt
- **CloudWatch Logs**: theo dõi lịch sử check-in
- **API Gateway**: kết nối frontend với serverless backend

> Đây là bước thiết yếu để chuẩn bị triển khai hệ thống FCJ Face Check-in sử dụng kiến trúc serverless AWS.

2. Cấu hình Environment File (`.env`)

File `.env` này chứa các biến môi trường cần thiết để ứng dụng Flask hoạt động và kết nối với các dịch vụ AWS như S3 và DynamoDB.

3. Đây là danh sách các thư viện Python cần thiết cho dự án **Hệ thống FCJ Face Check-in**, cùng với các phiên bản cụ thể để đảm bảo tương thích khi triển khai lên AWS Lambda sử dụng Zappa:

| Thư viện | Phiên bản | 
|---------|---------| 
| `Flask==2.3.3` | Framework web nhẹ để xử lý routes và APIs. |
| `boto3==1.34.0` | AWS SDK để tương tác với các dịch vụ như Rekognition, S3, DynamoDB, v.v. |
| `python-dotenv==1.0.0` | Tải các biến môi trường từ file `.env`. |
| `Pillow>=9.0.0` | Thư viện xử lý hình ảnh (được sử dụng để xử lý hình ảnh khuôn mặt). |
| `zappa>=0.58.0` | Đơn giản hóa việc triển khai ứng dụng Flask lên AWS Lambda. |
| `Werkzeug==2.3.7` | Thư viện tiện ích được Flask sử dụng để xử lý requests và responses. |

#### Cách thiết lập môi trường với các phiên bản đúng:

{{< copycode >}}
# 1. Tạo môi trường ảo (nếu chưa tạo)
python -m venv venv
source venv/bin/activate  # Trên Windows sử dụng: venv\\Scripts\\activate

# 2. Cài đặt các packages cần thiết
pip install -r requirements.txt
{{< /copycode >}}



 
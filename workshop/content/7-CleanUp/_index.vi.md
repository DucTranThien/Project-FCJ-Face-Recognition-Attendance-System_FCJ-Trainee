---
title: "Dọn dẹp tài nguyên"
date: "" 
weight: 7
chapter: false
pre: " <b> 7. </b> "
---

Chúng ta sẽ thực hiện các bước sau để xóa các tài nguyên đã tạo trong bài lab này.

{{% notice warning %}}
**Quan trọng**: Thực hiện các bước dọn dẹp theo đúng thứ tự để tránh các vấn đề phụ thuộc. Một số tài nguyên phải được xóa trước các tài nguyên khác.
{{% /notice %}}

#### Bước 1: Xóa Zappa Deployment trước

Xóa toàn bộ Zappa deployment (Lambda function, API Gateway, IAM roles):

{{< copycode >}}
# Điều hướng đến thư mục backend
cd backend

# Undeploy ứng dụng Zappa
zappa undeploy prod
{{< /copycode >}}

Lệnh này sẽ xóa:
- Lambda function
- API Gateway
- Các IAM roles và policies liên quan (được tạo bởi Zappa)
- CloudWatch log groups

![Cleanup](/images/7.cleanup/01-3.6-cleanup.png)

#### Bước 2: Xóa Rekognition Collection và dữ liệu Face

**Xóa tất cả faces từ collection trước:**
{{< copycode >}}
# Liệt kê tất cả faces trong collection
aws rekognition list-faces --collection-id fcj-faces --region ap-southeast-1

# Xóa collection (điều này sẽ tự động xóa tất cả faces)
aws rekognition delete-collection --collection-id fcj-faces --region ap-southeast-1
{{< /copycode >}}

#### Bước 3: Xóa DynamoDB Tables

**Xóa tất cả DynamoDB tables:**
{{< copycode >}}
aws dynamodb delete-table --table-name fcj-users --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-attendance-logs --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-otp-codes --region ap-southeast-1
aws dynamodb delete-table --table-name fcj-settings --region ap-southeast-1
{{< /copycode >}}

**Xác minh các tables đã được xóa:**
{{< copycode >}}
aws dynamodb list-tables --region ap-southeast-1
{{< /copycode >}}

![Cleanup](/images/7.cleanup/02-3.6-cleanup.png)

#### Bước 4: Xóa S3 Buckets

**Xóa User Photos Bucket (với tất cả face images):**
{{< copycode >}}
# Thay thế bằng tên bucket thực tế của bạn
BUCKET_NAME="fcj-user-photos-1234567890"

# Làm trống bucket trước (xóa tất cả objects và versions)
aws s3 rm s3://$BUCKET_NAME --recursive --region ap-southeast-1

# Xóa bucket
aws s3 rb s3://$BUCKET_NAME --region ap-southeast-1
{{< /copycode >}}

**Xóa Zappa Deployment Bucket:**
{{< copycode >}}
# Làm trống bucket trước
aws s3 rm s3://fcj-zappa-deployments --recursive --region ap-southeast-1

# Xóa bucket
aws s3 rb s3://fcj-zappa-deployments --region ap-southeast-1
{{< /copycode >}}

**Xóa Frontend Hosting Bucket (nếu đã tạo):**
{{< copycode >}}
# Thay thế bằng tên frontend bucket của bạn
FRONTEND_BUCKET="your-frontend-bucket-name"

# Làm trống và xóa frontend bucket
aws s3 rm s3://$FRONTEND_BUCKET --recursive --region ap-southeast-1
aws s3 rb s3://$FRONTEND_BUCKET --region ap-southeast-1
{{< /copycode >}}

#### Bước 5: Xóa CloudFront Distribution

1. Truy cập [CloudFront service management console](https://us-east-1.console.aws.amazon.com/cloudfront/v4/home)  
   + Nhấp **Distributions**.  
   + Chọn distribution bạn đã tạo trong bài lab, và nhấp **Disable** để vô hiệu hóa domain trước khi xóa.

![Cleanup](/images/7.cleanup/04-3.6-cleanup.png)

2. Đợi distribution được vô hiệu hóa (có thể mất 15-20 phút).
   + Khi domain đã được vô hiệu hóa thành công, nhấp **Delete** để xóa và xác nhận việc xóa.

![Cleanup](/images/7.cleanup/03-3.6-cleanup.png)

#### Bước 6: Dọn dẹp cấu hình SES

**Xóa các địa chỉ email đã xác minh (nếu không còn cần thiết):**
{{< copycode >}}
# Liệt kê các identities đã xác minh
aws ses list-identities --region ap-southeast-1

# Xóa email identity cụ thể
aws ses delete-identity --identity your-email@example.com --region ap-southeast-1
{{< /copycode >}}

#### Bước 7: Xóa Custom IAM Role và Policy

Truy cập [IAM service management console](https://us-east-1.console.aws.amazon.com/iam/home)  

**Xóa Custom Policy:**
1. Nhấp tab **Policies**.  
2. Nhấp **Filter by Type** và chọn **Customer managed**.  
3. Tìm kiếm policy bạn đã tạo (ví dụ: `FCJ-FaceRecognition-Policy`) và nhấp **Delete**, sau đó xác nhận việc xóa.

**Xóa Custom Role:**
1. Nhấp tab **Roles**.  
2. Chọn role bạn đã tạo trong bài lab (ví dụ: `FCJ-FaceRecognition-Role`). Nhấp **Delete**.  
3. Nhập tên role và xác nhận việc xóa.

#### Bước 8: Xác minh việc dọn dẹp hoàn tất

**Chạy các lệnh xác minh để đảm bảo tất cả tài nguyên đã được xóa:**

{{< copycode >}}
# Xác minh Rekognition collections
aws rekognition list-collections --region ap-southeast-1

# Xác minh DynamoDB tables
aws dynamodb list-tables --region ap-southeast-1

# Xác minh S3 buckets (không nên hiển thị các buckets liên quan đến FCJ)
aws s3 ls

# Xác minh Lambda functions (không nên hiển thị các functions liên quan đến FCJ)
aws lambda list-functions --region ap-southeast-1
{{< /copycode >}}

#### Xác minh chi phí

Sau khi dọn dẹp, xác minh rằng không có phí nào đang phát sinh:

1. **AWS Cost Explorer**: Kiểm tra các khoản phí đang diễn ra liên quan đến:
   - Lambda invocations
   - DynamoDB requests
   - S3 storage
   - Rekognition API calls
   - CloudFront data transfer

2. **CloudWatch Billing Alarms**: Thiết lập cảnh báo billing để theo dõi các khoản phí bất ngờ

{{% notice tip %}}
**Danh sách kiểm tra dọn dẹp hoàn tất:**
- Zappa deployment đã được undeploy
- Rekognition collection đã được xóa
- Tất cả DynamoDB tables đã được xóa
- Tất cả S3 buckets đã được làm trống và xóa
- CloudFront distribution đã được vô hiệu hóa và xóa
- SES verified identities đã được xóa (tùy chọn)
- Custom IAM role và policy đã được xóa
- Không có phí AWS đang diễn ra đã được xác minh
{{% /notice %}}

{{% notice warning %}}
**Ghi chú quan trọng:**
- Việc xóa CloudFront distribution có thể mất đến 24 giờ để hoàn tất
- DynamoDB tables với TTL có thể cần thêm thời gian để dọn dẹp hoàn toàn
- S3 buckets có bật versioning có thể cần các bước dọn dẹp bổ sung
- Luôn xác minh billing sau khi dọn dẹp để đảm bảo không có phí bất ngờ
{{% /notice %}}
---
title: "Tạo IAM Role"
date: "" 
weight: 3
chapter: false
pre: " <b> 2.3 </b> "
---

#### Truy cập dịch vụ **IAM** trên AWS

1. Từ console dịch vụ IAM, chọn **Policies** từ menu điều hướng bên trái  
   + Nhấp nút **Create policy**

2. Trong hộp thoại **Create policy**:  
   + Chọn tab **JSON** trong phần **Policy editor** và dán nội dung sau. Đảm bảo thay thế `<YourAccountID>` bằng AWS account ID thực tế của bạn và `<YourS3BucketName>` bằng tên S3 bucket của bạn.

{{< copycode >}}
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams"
            ],
            "Resource": "arn:aws:logs:ap-southeast-1:<YourAccountID>:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": [
                "arn:aws:dynamodb:ap-southeast-1:<YourAccountID>:table/fcj-users",
                "arn:aws:dynamodb:ap-southeast-1:<YourAccountID>:table/fcj-attendance-logs",
                "arn:aws:dynamodb:ap-southeast-1:<YourAccountID>:table/fcj-otp-codes"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "rekognition:CreateCollection",
                "rekognition:DeleteCollection",
                "rekognition:ListCollections",
                "rekognition:IndexFaces",
                "rekognition:SearchFacesByImage",
                "rekognition:DeleteFaces",
                "rekognition:ListFaces",
                "rekognition:CompareFaces",
                "rekognition:DetectFaces"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectVersion"
            ],
            "Resource": "arn:aws:s3:::<YourS3BucketName>/faces/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail",
                "ses:GetSendQuota",
                "ses:GetSendStatistics"
            ],
            "Resource": "*"
        }
    ]
}
{{< /copycode >}}

![IAMPolicy](/images/2.prerequisite/001-2.3-setuppolicy.png)

+ Nhấp **Next**, nhập tên bạn chọn cho policy dưới **Policy name** (ví dụ: `FCJ-FaceRecognition-Policy`), cuộn xuống và nhấp **Create policy**  
+ Đợi policy được tạo thành công. Quay lại trang chính IAM Policies để xác minh rằng policy mới của bạn xuất hiện trong danh sách.

![IAMPolicy](/images/2.prerequisite/002-2.3-createpolicysuccess.png)

---

#### Gắn Policy đã tạo vào IAM Role

1. Từ console dịch vụ IAM, chọn **Roles** từ menu điều hướng bên trái  
   + Nhấp nút **Create role**

2. Trong hộp thoại **Create role**:  
   + Chọn **AWS Service** làm loại trusted entity, và chọn **Lambda** làm use case

![IAMPolicy](/images/2.prerequisite/003-2.3-createrolephase1.png)

+ Trong bước **Add permissions**, dưới **Filter by Type**, chọn **Customer managed**, chọn policy bạn vừa tạo, và nhấp **Next**

![IAMPolicy](/images/2.prerequisite/004-2.3-createrolephase2.png)

+ Xem lại cài đặt role của bạn, nhập tên bạn chọn cho role (ví dụ: `FCJ-FaceRecognition-Role` - bạn sẽ cần tên này sau), và nhấp **Create role**. Đảm bảo role được tạo thành công.

![IAMPolicy](/images/2.prerequisite/005-2.3-createrolesuccess.png)

{{% notice warning %}}
**Ghi chú quan trọng:**
- IAM policy này tuân theo nguyên tắc least privilege, chỉ cấp các quyền cần thiết cho hệ thống FCJ Face Recognition
- Các quyền Rekognition cho phép quản lý collection và các thao tác face
- Quyền S3 được giới hạn trong prefix `/faces/` để bảo mật
- Quyền SES cần thiết cho chức năng OTP email
- Quyền DynamoDB được giới hạn trong ba bảng cụ thể được sử dụng bởi ứng dụng
{{% /notice %}}
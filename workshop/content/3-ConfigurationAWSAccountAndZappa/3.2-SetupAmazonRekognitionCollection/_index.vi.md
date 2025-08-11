---
title : "Thiết lập Amazon Rekognition Collection"
date : "" 
weight : 2
chapter : false
pre : " <b> 3.2. </b> "
---

1. **Tạo Amazon Rekognition Collection qua AWS CLI**

   Amazon Rekognition collections là các container cho dữ liệu khuôn mặt cho phép bạn tìm kiếm khuôn mặt. Chúng ta sẽ tạo một collection cho Hệ thống Điểm danh Nhận diện Khuôn mặt FCJ.

   Mở terminal hoặc command prompt và chạy lệnh AWS CLI sau:

   {{< copycode >}}
   aws rekognition create-collection --collection-id fcj-faces --region ap-southeast-1
   {{< /copycode >}}

![Connect](/images/3.connect/01-3.2-setupcollection.png)

2. **Xác minh việc tạo Collection**

   Để xác minh rằng collection của bạn đã được tạo thành công, liệt kê tất cả collections:

   {{< copycode >}}
   aws rekognition list-collections --region ap-southeast-1
   {{< /copycode >}}

   Bạn sẽ thấy output tương tự như:
   ```json
   {
       "CollectionIds": [
           "fcj-faces"
       ]
   }
   ```

![Connect](/images/3.connect/02-3.2-listcollection.png)

3. **Tạo DynamoDB Tables**

   Tạo các bảng DynamoDB cần thiết để lưu trữ dữ liệu người dùng và nhật ký điểm danh:

   **Users Table:**
   {{< copycode >}}
  self.dynamodb.create_table(
                TableName=os.getenv('USERS_TABLE'),
                KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
   {{< /copycode >}}

![Connect](/images/3.connect/03-3.2-tableuser.png)

   **Checkin Setting Table:**
   {{< copycode >}}
   def save_checkin(self, username, similarity, status):
        try:
            from datetime import datetime, time
            now = datetime.now()
            current_time = now.time()
            
            # Get dynamic similarity threshold
            threshold = self.settings_service.get_similarity_threshold()
            
            # Only save if similarity meets threshold and status is success
            if status != 'success' or similarity < threshold:
                return {
                    'error': 'recognition_failed',
                    'similarity': similarity,
                    'threshold': threshold,
                    'message': f'Face recognition failed. Similarity: {similarity:.1f}% (Required: ≥95%)',
                    'can_retry': True,
                    'session_type': 'unknown'
                }
   {{< /copycode >}}

![Connect](/images/3.connect/04-3.2-tablecheckinsetting.png)

   **Checkin History Table:**
   {{< copycode >}}
   self.dynamodb.create_table(
                TableName=os.getenv('CHECKIN_TABLE'),
                KeySchema=[
                    {'AttributeName': 'username', 'KeyType': 'HASH'},
                    {'AttributeName': 'checkin_time', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'username', 'AttributeType': 'S'},
                    {'AttributeName': 'checkin_time', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
   {{< /copycode >}}

![Connect](/images/3.connect/05-3.2-tablecheckinhistory.png)

4. **Tạo S3 Bucket cho User Photos (Private với Presigned URLs)**

   Tạo một S3 bucket private để lưu trữ ảnh khuôn mặt người dùng một cách bảo mật:

   {{< copycode >}}
   # Tạo bucket với timestamp để đảm bảo tính duy nhất
   BUCKET_NAME="fcj-user-photos-$(date +%s)"
   aws s3 mb s3://fcj-face --region ap-southeast-1
   
   # Chặn public access để bảo mật
   aws s3api put-public-access-block \
       --bucket fcj-face \
       --public-access-block-configuration \
       "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
   {{< /copycode >}}

   > **Lưu ý**: Bucket được cấu hình là private. Ứng dụng sẽ sử dụng presigned URLs để truy cập bảo mật đến hình ảnh khuôn mặt.

5. **Cấu hình SES cho Email OTP**

   Thiết lập Amazon SES để gửi email OTP:

   **Xác minh địa chỉ email của bạn (cho chế độ sandbox):**
   {{< copycode >}}
   aws ses verify-email-identity --email-address your-email@example.com --region ap-southeast-1
   {{< /copycode >}}

   **Kiểm tra trạng thái xác minh:**
   {{< copycode >}}
   aws ses get-identity-verification-attributes --identities your-email@example.com --region ap-southeast-1
   {{< /copycode >}}

   {{% notice info %}}
   **SES Sandbox vs Production:**
   - **Chế độ Sandbox**: Chỉ có thể gửi email đến các địa chỉ đã xác minh (tốt cho testing)
   - **Chế độ Production**: Có thể gửi email đến bất kỳ địa chỉ nào (cần yêu cầu AWS support)
   - Để triển khai production, yêu cầu chuyển ra khỏi SES sandbox thông qua AWS Support
   {{% /notice %}}

![Connect](/images/3.connect/06-3.2-verifyotp.png)

6. **Test Rekognition Collection**

   Test Rekognition collection của bạn bằng cách index một khuôn mặt mẫu (tùy chọn):

   {{< copycode >}}
   # Đầu tiên, upload một hình ảnh test lên S3 bucket của bạn
   aws s3 cp sample.jpg s3://$BUCKET_NAME/faces/test-user.jpg
   
   # Index khuôn mặt trong Rekognition collection
   aws rekognition index-faces \
       --collection-id fcj-faces \
       --image '{"S3Object":{"Bucket":"'$BUCKET_NAME'","Name":"faces/test-user.jpg"}}' \
       --external-image-id "test-user" \
       --region ap-southeast-1
   {{< /copycode >}}

![Connect](/images/3.connect/07-3.2-faceimagecheckin.png)

   Việc thiết lập hiện đã hoàn tất. Bạn có:
   -  Rekognition collection `fcj-faces` để index và tìm kiếm khuôn mặt
   -  Các bảng DynamoDB cho users, attendance logs, OTP codes, và settings
   -  S3 bucket private để lưu trữ ảnh người dùng một cách bảo mật
   -  SES được cấu hình để gửi OTP email
   -  Tất cả tài nguyên được cấu hình trong region `ap-southeast-1`

   {{% notice tip %}}
   **Cấu hình DynamoDB TTL:**
   - Mã OTP tự động hết hạn sau 10 phút sử dụng DynamoDB TTL
   - Thông tin khóa tài khoản được lưu trữ trong bảng settings
   - Các lần đăng nhập thất bại được theo dõi theo email người dùng
   - Tài khoản được tự động mở khóa sau một khoảng thời gian có thể cấu hình
   {{% /notice %}}
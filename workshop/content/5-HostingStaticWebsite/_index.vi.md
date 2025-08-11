---
title: "Cấu hình Frontend với S3 và CloudFront"
date: ""
weight: 5
chapter: false
pre: " <b> 5. </b> "
---

1. Cấu hình và upload frontend tĩnh lên AWS S3
  + Tạo một frontend HTML đơn giản cho Hệ thống Điểm danh Nhận diện Khuôn mặt FCJ. Frontend sẽ là một website tĩnh giao tiếp với Flask API của bạn qua các AJAX calls.
  + Tạo file **index.html** với giao diện nhận diện khuôn mặt và cấu hình nó để sử dụng URL endpoint API Gateway của bạn.

![Connect](/images/5.cloudfronts3/01-3.4-apigateway.png)

  + Đăng nhập vào AWS Management Console, truy cập dịch vụ **S3**, và nhấp **Create bucket**.

![Connect](/images/5.cloudfronts3/02-3.4-creates3.png)

  + Trong cửa sổ tạo bucket, làm theo các hướng dẫn được đánh dấu. Để tất cả các trường không được chỉ định với cài đặt mặc định.

![Connect](/images/5.cloudfronts3/03-3.4-settings3.png)

![Connect](/images/5.cloudfronts3/04-3.4-settingcreates3.png)

  + Khi bucket được tạo thành công, mở nó và chọn **Upload**. Ở bước này, điều hướng đến thư mục **dist** đã được xây dựng trước đó và upload toàn bộ nội dung của nó lên bucket.

![Connect](/images/5.cloudfronts3/05-3.4-uploads3.png)

![Connect](/images/5.cloudfronts3/06-3.4-uploads3.png)

  + Sau khi upload thành công, xác minh các file đã upload và xác nhận việc upload.

![Connect](/images/5.cloudfronts3/07-3.4-uploads3.png)

  + Tiếp theo, từ giao diện chính của bucket mới tạo, truy cập tab **Permissions** và nhấp **Edit**. Trong cửa sổ **Edit bucket policy**, chỉnh sửa policy như hình dưới để cho phép CloudFront truy cập các frontend assets đã upload lên S3 bucket. Đảm bảo thay thế **YourBucketName** bằng tên thực tế của bucket của bạn.

{{< copycode >}}
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontAccess",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::<YourBucketName>/*"
        }
    ]
}
{{< /copycode >}}

![Connect](/images/5.cloudfronts3/08-3.4-settingpolicy.png)

2. Cấu hình CloudFront để phân phối nội dung website

  + Đăng nhập vào AWS Management Console và chọn dịch vụ **CloudFront**, sau đó chọn **Create distribution**.

![Connect](/images/5.cloudfronts3/09-3.4-createcloudfront.png)

  + Trong cửa sổ Create Distribution, điền các trường theo hướng dẫn. Để các trường không được chỉ định với cấu hình mặc định.

![Connect](/images/5.cloudfronts3/10-3.4-settingcloudfront.png)

  + Cho bước cấu hình Origin, chọn **S3** bucket bạn đã tạo trước đó.

![Connect](/images/5.cloudfronts3/11-3.4-chooses3.png)

![Connect](/images/5.cloudfronts3/12-3.4-chooses3bucket.png)

  + Cho các cài đặt còn lại của distribution, tiến hành như hình:

![Connect](/images/5.cloudfronts3/13-3.4-settingcloudfront.png)

![Connect](/images/5.cloudfronts3/14-3.4-reviewcloudfront.png)

  + Khi cấu hình được xác nhận, CloudFront sẽ tạo ra một **Distribution domain name** cho phép truy cập domain của bạn qua internet. Bạn phải đợi quá trình triển khai hoàn tất.

![Connect](/images/5.cloudfronts3/15-3.4-deploycloudfront.png)

  + Tiếp theo, cấu hình CloudFront để truy cập các tài nguyên website trong **S3** và định nghĩa điểm vào của website. Trong phần **Settings**, nhấp **Edit**. Trong cửa sổ chỉnh sửa cấu hình, chỉ định file vào của website dưới **Default root object**.

![Connect](/images/5.cloudfronts3/16-3.4-settingcloudfront.png)

![Connect](/images/5.cloudfronts3/17-3.4-editcloudfront.png)

  + Điều đó hoàn tất quá trình cấu hình để triển khai dự án của bạn trên các dịch vụ AWS. Bây giờ, đợi việc triển khai CloudFront domain hoàn tất, và sau đó bạn có thể trải nghiệm website của mình.

  + Khi việc triển khai hoàn tất, sử dụng **Distribution domain name** để truy cập website qua internet. Bạn sẽ có thể thấy giao diện frontend của dự án. Thử tìm kiếm phim bằng từ khóa. Bạn sẽ thấy công cụ tìm kiếm full-text của OpenSearch mạnh mẽ như thế nào trong việc trả về kết quả nhanh và liên quan ngay cả trên các tập dữ liệu lớn. Ngoài ra, tìm kiếm full-text hỗ trợ fuzzy matching và làm nổi bật các kết quả gần đúng bằng màu vàng.

![Connect](/images/5.cloudfronts3/18-3.4-modified.png)

![Connect](/images/5.cloudfronts3/19-3.4-indexweb.png)
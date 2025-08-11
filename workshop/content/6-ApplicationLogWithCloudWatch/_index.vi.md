---
title: "Xem Logs trong CloudWatch"
date: ""
weight: 6
chapter: false
pre: " <b> 6. </b> "
---

+ Đăng nhập vào AWS Console và chọn dịch vụ **CloudWatch**. Sau đó chọn **Logs**, và chọn **Log groups**. Bạn sẽ thấy các log groups cho ứng dụng Flask của bạn, thường được đặt tên **/aws/lambda/fcj-face-recognition-prod**. Log group này ghi lại tất cả logs của ứng dụng Flask bao gồm đăng ký người dùng, các lần thử đăng nhập, kết quả nhận diện khuôn mặt, và bản ghi điểm danh.

![Connect](/images/6.cloudwatch/01-3.5-viewlog.png)

+ Nhấp vào log group để xem các log streams. Mỗi log stream đại diện cho một lần thực thi Lambda khác nhau. Ở đây bạn sẽ thấy các logs chi tiết bao gồm:
  - Các lần thử đăng ký người dùng và xác minh OTP
  - Điểm số độ tin cậy nhận diện khuôn mặt
  - Kết quả check-in điểm danh
  - Trạng thái gửi email SMTP
  - Các thao tác DynamoDB
  - Bất kỳ lỗi hoặc ngoại lệ nào

![Connect](/images/6.cloudwatch/02-3.5-viewlog.png)

+ Bạn cũng có thể sử dụng CloudWatch Insights để truy vấn logs của mình. Ví dụ, để tìm tất cả các kết quả khớp khuôn mặt thành công:
  ```
  fields @timestamp, @message
  | filter @message like /matched.*true/
  | sort @timestamp desc
  ```
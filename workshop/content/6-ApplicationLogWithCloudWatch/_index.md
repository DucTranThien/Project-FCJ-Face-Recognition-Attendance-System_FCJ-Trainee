---
title: "View Logs in CloudWatch"
date: ""
weight: 6
chapter: false
pre: " <b> 6. </b> "
---

+ Log in to the AWS Console and select the **CloudWatch** service. Then choose **Logs**, and select **Log groups**. You will see log groups for your Flask application, typically named **/aws/lambda/fcj-face-recognition-prod**. This log group captures all Flask application logs including user registrations, login attempts, face recognition results, and attendance records.

![Connect](/images/6.cloudwatch/01-3.5-viewlog.png)

+ Click on the log group to view log streams. Each log stream represents a different Lambda execution. Here you will see detailed logs including:
  - User registration and OTP verification attempts
  - Face recognition confidence scores
  - Attendance check-in results
  - SMTP email sending status
  - DynamoDB operations
  - Any errors or exceptions

![Connect](/images/6.cloudwatch/02-3.5-viewlog.png)

+ You can also use CloudWatch Insights to query your logs. For example, to find all successful face matches:
  ```
  fields @timestamp, @message
  | filter @message like /matched.*true/
  | sort @timestamp desc
  ```

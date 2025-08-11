---
title: "Configure Frontend with S3 and CloudFront"
date: ""
weight: 5
chapter: false
pre: " <b> 5. </b> "
---

1. Configure and upload the static frontend to AWS S3
  + Create a simple HTML frontend for the FCJ Face Recognition Attendance System. The frontend will be a static website that communicates with your Flask API via AJAX calls.
  + Create an **index.html** file with the face recognition interface and configure it to use your API Gateway endpoint URL.

![Connect](/images/5.cloudfronts3/01-3.4-apigateway.png)

  + Log in to the AWS Management Console, go to the **S3** service, and click **Create bucket**.

![Connect](/images/5.cloudfronts3/02-3.4-creates3.png)

  + In the bucket creation window, follow the highlighted instructions. Leave all unspecified fields with their default settings.

![Connect](/images/5.cloudfronts3/03-3.4-settings3.png)

![Connect](/images/5.cloudfronts3/04-3.4-settingcreates3.png)

  + Once the bucket is successfully created, open it and select **Upload**. At this step, navigate to the previously built **dist** folder and upload all its contents to the bucket.

![Connect](/images/5.cloudfronts3/05-3.4-uploads3.png)

![Connect](/images/5.cloudfronts3/06-3.4-uploads3.png)

  + After a successful upload, verify the uploaded files and confirm the upload.

![Connect](/images/5.cloudfronts3/07-3.4-uploads3.png)

  + Next, from the main interface of the newly created bucket, go to the **Permissions** tab and click **Edit**. In the **Edit bucket policy** window, modify the policy as shown below to allow CloudFront to access the frontend assets uploaded to the S3 bucket. Be sure to replace **YourBucketName** with the actual name of your bucket.

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

2. Configure CloudFront to deliver website content

  + Log in to the AWS Management Console and select the **CloudFront** service, then choose **Create distribution**.

![Connect](/images/5.cloudfronts3/09-3.4-createcloudfront.png)

  + In the Create Distribution window, fill in the fields as instructed. Leave unspecified fields with their default configurations.

![Connect](/images/5.cloudfronts3/10-3.4-settingcloudfront.png)

  + For the Origin configuration step, select the **S3** bucket you created earlier.

![Connect](/images/5.cloudfronts3/11-3.4-chooses3.png)

![Connect](/images/5.cloudfronts3/12-3.4-chooses3bucket.png)

  + For the remaining settings of the distribution, proceed as shown:

![Connect](/images/5.cloudfronts3/13-3.4-settingcloudfront.png)

![Connect](/images/5.cloudfronts3/14-3.4-reviewcloudfront.png)

  + Once the configuration is confirmed, CloudFront will generate a **Distribution domain name** that allows access to your domain over the internet. You must wait for the deployment process to complete.

![Connect](/images/5.cloudfronts3/15-3.4-deploycloudfront.png)

  + Next, configure CloudFront to access the website resources in **S3** and define the website's entry point. In the **Settings** section, click **Edit**. In the configuration edit window, specify the entry file of your website under **Default root object**.

![Connect](/images/5.cloudfronts3/16-3.4-settingcloudfront.png)

![Connect](/images/5.cloudfronts3/17-3.4-editcloudfront.png)

  + That completes the configuration process to deploy your project on AWS services. Now, wait for the CloudFront domain deployment to finish, and then you can experience your website.

  + Once the deployment is complete, use the **Distribution domain name** to access the website via the internet. You should be able to see your project’s frontend interface. Try searching for movies using keywords. You'll see how powerful OpenSearch's full-text search engine is at returning fast and relevant results even over large datasets. Additionally, full-text search supports fuzzy matching and highlights approximate matches in yellow.

![Connect](/images/5.cloudfronts3/18-3.4-modified.png)

![Connect](/images/5.cloudfronts3/19-3.4-indexweb.png)

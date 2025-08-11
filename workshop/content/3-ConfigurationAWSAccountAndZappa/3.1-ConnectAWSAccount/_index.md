---
title: "Connect AWS Account to Visual Studio Code"
date: "" 
weight: 1 
chapter: false
pre: " <b> 3.1. </b> "
---

1. After installing the **AWS Toolkit** and configuring your AWS account, Visual Studio Code will display a list of AWS services available in the selected region (**Asia Pacific - Singapore**).

The account is connected using the profile `ductran63`. From here, you can easily access and manage services such as:

- **Lambda**: deploy Flask backend using Zappa
- **S3**: store face images
- **CloudWatch Logs**: track check-in history
- **API Gateway**: connect the frontend to serverless backend

> This is an essential step to prepare for deploying the FCJ Face Check-in system using AWS serverless architecture.

2. Environment File Configuration (`.env`)

This `.env` file contains the necessary environment variables for the Flask application to operate and connect to AWS services such as S3 and DynamoDB.

3. This is the list of required Python libraries for the **FCJ Face Check-in System** project, along with specific versions to ensure compatibility when deploying to AWS Lambda using Zappa:


| Library | Version | 
|---------|---------|
| `Flask==2.3.3` | Lightweight web framework for handling routes and APIs. |
| `boto3==1.34.0` | AWS SDK for interacting with services like Rekognition, S3, DynamoDB, etc. |
| `python-dotenv==1.0.0` | Loads environment variables from the `.env` file. |
| `Pillow>=9.0.0` | Image processing library (used for handling face images). |
| `zappa>=0.58.0` | Simplifies deployment of Flask apps to AWS Lambda. |
| `Werkzeug==2.3.7` | Utility library used by Flask to handle requests and responses. |

#### How to set up the environment with the correct versions:

{{< copycode >}}
# 1. Create a virtual environment (if not created yet)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\\Scripts\\activate

# 2. Install the required packages
pip install -r requirements.txt
{{< /copycode >}}



 

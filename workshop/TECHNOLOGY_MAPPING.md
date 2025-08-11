# Technology Stack Mapping: OpenSearch → FCJ Face Recognition

## Complete Technology Transformation

| **Component** | **Original (OpenSearch Stack)** | **New (FCJ Face Recognition Stack)** | **Purpose** |
|---------------|----------------------------------|---------------------------------------|-------------|
| **Search Engine** | Amazon OpenSearch Service | Amazon Rekognition | Face indexing and searching |
| **Data Storage** | OpenSearch Domain/Index | DynamoDB Tables | User data and attendance logs |
| **Backend Runtime** | Node.js | Python 3.9 | Server-side application logic |
| **Web Framework** | Express.js | Flask | HTTP API and routing |
| **Package Manager** | npm | pip | Dependency management |
| **Dependencies File** | package.json | requirements.txt | Project dependencies |
| **Deployment Tool** | Manual Lambda upload | Zappa | Serverless deployment automation |
| **Authentication** | Basic/JWT | Password + Email OTP | User verification system |
| **Email Service** | Amazon SES | SMTP (Gmail/Custom) | Email delivery for OTP |
| **Image Processing** | N/A | Amazon Rekognition + Pillow | Face detection and analysis |
| **Data Format** | JSON documents | DynamoDB items | Structured data storage |

## Service-Level Mapping

### Data Layer
| **Original** | **New** | **Migration Notes** |
|--------------|---------|-------------------|
| OpenSearch Domain | Rekognition Collection | Face data container |
| OpenSearch Index | DynamoDB Tables | Structured data storage |
| Document ID | User Email (Primary Key) | Unique identifier |
| Index Mapping | Table Schema | Data structure definition |
| Bulk Insert | Batch Operations | Data loading method |

### API Layer
| **Original Endpoint** | **New Endpoint** | **Functionality** |
|----------------------|------------------|-------------------|
| `/search` | `/checkin` | Face recognition check-in |
| `/index` | `/auth/register` | User registration |
| `/health` | `/health` | System health check |
| N/A | `/auth/login` | User authentication |
| N/A | `/auth/verify-otp` | Email verification |

### Configuration
| **Original Config** | **New Config** | **Purpose** |
|--------------------|----------------|-------------|
| `OPENSEARCH_URL` | `REKOGNITION_COLLECTION_ID` | Service endpoint |
| `OPENSEARCH_USERNAME` | `SMTP_USERNAME` | Authentication |
| `OPENSEARCH_PASSWORD` | `SMTP_PASSWORD` | Authentication |
| `INDEX_NAME` | `USERS_TABLE` | Data container name |

## Command Mapping

### Development Commands
| **Original (Node.js)** | **New (Python)** | **Purpose** |
|------------------------|------------------|-------------|
| `npm install` | `pip install -r requirements.txt` | Install dependencies |
| `npm start` | `python app.py` | Start development server |
| `npm run dev` | `flask run` | Development mode |
| `npm run build` | N/A (Static frontend) | Build process |
| `node index.js` | `python app.py` | Execute application |

### AWS CLI Commands
| **Original (OpenSearch)** | **New (Rekognition/DynamoDB)** | **Purpose** |
|---------------------------|--------------------------------|-------------|
| `aws opensearch create-domain` | `aws rekognition create-collection` | Create service |
| `aws opensearch describe-domain` | `aws rekognition list-collections` | Check status |
| `aws opensearch delete-domain` | `aws rekognition delete-collection` | Cleanup |
| N/A | `aws dynamodb create-table` | Create data tables |

### Deployment Commands
| **Original** | **New** | **Purpose** |
|--------------|---------|-------------|
| Manual zip upload | `zappa deploy prod` | Deploy to Lambda |
| AWS Console configuration | `zappa update prod` | Update deployment |
| Manual deletion | `zappa undeploy prod` | Remove deployment |

## Code Structure Mapping

### File Organization
| **Original Structure** | **New Structure** | **Purpose** |
|------------------------|-------------------|-------------|
| `index.js` | `app.py` | Main application file |
| `package.json` | `requirements.txt` | Dependencies |
| `node_modules/` | `venv/` | Dependencies folder |
| `src/` | `services/` | Business logic modules |
| `.env` | `.env` | Environment variables |

### Module Structure
| **Original (Node.js)** | **New (Python)** | **Functionality** |
|------------------------|------------------|-------------------|
| `const express = require('express')` | `from flask import Flask` | Web framework import |
| `const { Client } = require('@opensearch-project/opensearch')` | `import boto3` | AWS service client |
| `app.get('/search', ...)` | `@app.route('/checkin', methods=['POST'])` | Route definition |
| `client.search({...})` | `rekognition.search_faces_by_image({...})` | Service operation |

## Data Model Transformation

### Original OpenSearch Document
```json
{
  "_id": "movie123",
  "_source": {
    "title": "Movie Title",
    "genre": "Action",
    "year": 2023,
    "description": "Movie description"
  }
}
```

### New DynamoDB User Record
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "password": "hashed_password",
  "verified": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### New Attendance Log Record
```json
{
  "user_id": "user@example.com",
  "timestamp": "2024-01-01T09:00:00Z",
  "matched": true,
  "confidence": 95.5,
  "face_id": "rekognition-face-id",
  "check_in_time": "2024-01-01 09:00:00"
}
```

## Environment Variables Mapping

| **Original Variable** | **New Variable** | **Purpose** |
|----------------------|------------------|-------------|
| `OPENSEARCH_ENDPOINT` | `AWS_REGION` | Service region |
| `OPENSEARCH_USERNAME` | `SMTP_USERNAME` | Authentication |
| `OPENSEARCH_PASSWORD` | `SMTP_PASSWORD` | Authentication |
| `INDEX_NAME` | `REKOGNITION_COLLECTION_ID` | Data container |
| N/A | `USERS_TABLE` | User data table |
| N/A | `ATTENDANCE_LOGS_TABLE` | Attendance data table |
| N/A | `S3_BUCKET_PHOTOS` | Photo storage |

## Functional Mapping

### Original: Movie Search System
- **Input**: Search query text
- **Process**: Full-text search in OpenSearch
- **Output**: Matching movie documents
- **Use Case**: Content discovery

### New: Face Recognition Attendance
- **Input**: Face image (base64)
- **Process**: Face recognition via Rekognition
- **Output**: Match result with confidence
- **Use Case**: Attendance tracking

## Migration Benefits

| **Aspect** | **Improvement** | **Benefit** |
|------------|-----------------|-------------|
| **Accuracy** | Text search → Face recognition | Higher precision for attendance |
| **Security** | Basic auth → Password + OTP | Enhanced user verification |
| **Scalability** | Manual scaling → Serverless | Automatic scaling |
| **Cost** | Always-on OpenSearch → Pay-per-use | Cost optimization |
| **Maintenance** | Manual updates → Zappa automation | Reduced operational overhead |
| **Integration** | Single service → Multi-service | Comprehensive solution |

This mapping provides a complete transformation guide from the original OpenSearch-based movie search system to the new FCJ Face Recognition Attendance System, maintaining the same workshop structure while completely changing the underlying technology stack and use case.
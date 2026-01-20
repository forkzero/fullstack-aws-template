# Infrastructure

AWS CDK infrastructure for deploying a serverless full-stack application.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Route 53                                 │
│                  yourdomain.com                                  │
│         ┌──────────────┬──────────────┐                         │
│         │              │              │                         │
│         ▼              ▼              ▼                         │
│    app.yourdomain.com  api.yourdomain.com  auth.yourdomain.com │
│         │              │                                        │
│         ▼              ▼                                        │
│   ┌──────────┐   ┌──────────────┐   ┌──────────────┐          │
│   │CloudFront│   │  App Runner  │   │   Cognito    │          │
│   │  + S3    │   │  (Backend)   │   │  Hosted UI   │          │
│   │(Frontend)│   │              │   │              │          │
│   └──────────┘   └──────┬───────┘   └──────────────┘          │
│                         │                                       │
│                         ▼                                       │
│                  ┌──────────────┐                               │
│                  │ RDS Postgres │                               │
│                  │  (t4g.micro) │                               │
│                  └──────────────┘                               │
│                                                                 │
│   Secrets: AWS Secrets Manager (DB creds)                      │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. AWS CLI installed and configured
2. Node.js 20+ installed
3. AWS CDK CLI: `npm install -g aws-cdk`
4. AWS accounts set up (see [Control Tower Setup](docs/CONTROL_TOWER_SETUP.md))

## Setup

### 1. Install Dependencies

```bash
cd infrastructure
npm install
```

### 2. Configure Accounts

Edit `cdk.json` with your AWS account IDs:

```json
{
  "context": {
    "environments": {
      "preprod": {
        "account": "111111111111",
        "region": "us-east-1"
      },
      "prod": {
        "account": "222222222222",
        "region": "us-east-1"
      }
    }
  }
}
```

### 3. Bootstrap CDK

```bash
cdk bootstrap aws://111111111111/us-east-1 -c environment=preprod
cdk bootstrap aws://222222222222/us-east-1 -c environment=prod
```

### 4. Deploy

```bash
# Preview
AWS_PROFILE=app-preprod npx cdk diff --all -c environment=preprod

# Deploy
AWS_PROFILE=app-preprod npx cdk deploy --all -c environment=preprod
```

## Stacks

| Stack | Description |
|-------|-------------|
| `{prefix}-network` | VPC, subnets, security groups |
| `{prefix}-dns` | Route 53 hosted zone, ACM certificates |
| `{prefix}-auth` | Cognito User Pool, hosted UI |
| `{prefix}-database` | RDS PostgreSQL, credentials secret |
| `{prefix}-backend` | ECR repository, App Runner service |
| `{prefix}-frontend` | S3 bucket, CloudFront distribution |
| `{prefix}-cicd` | IAM user for GitHub Actions |

## Cost Estimate

| Service | Monthly Cost |
|---------|--------------|
| S3 | ~$1 |
| CloudFront | ~$1 |
| App Runner | ~$5-15 |
| RDS PostgreSQL (t4g.micro) | ~$12 |
| Route 53 | ~$0.50 |
| Secrets Manager | ~$1 |
| **Total** | **~$25-35/month** per environment |

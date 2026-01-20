# AWS Control Tower Setup Guide

AWS Control Tower provides a pre-configured landing zone with SSO, guardrails, and centralized logging.

**Two setup options:**
- [Option A: Console Setup](#option-a-console-setup-recommended) - Guided wizard, easier for first-time setup
- [Option B: CLI Setup](#option-b-cli-setup) - Scriptable, better for documentation/repeatability

## Prerequisites

- A fresh AWS account to serve as the **management account**
- AWS CLI v2 installed and configured with management account credentials
- An email address for AWS account root user
- Additional email addresses for:
  - Log Archive account (e.g., `aws-logs@yourcompany.com`)
  - Audit account (e.g., `aws-audit@yourcompany.com`)
  - Pre-prod account (e.g., `aws-preprod@yourcompany.com`)
  - Production account (e.g., `aws-prod@yourcompany.com`)

> **Tip**: Use email aliases like `aws+logs@yourcompany.com` if your email provider supports it.

---

## Option A: Console Setup (Recommended)

### Step 1: Set Up Control Tower (30-45 minutes)

1. **Sign in** to your management account as root user
2. Go to **AWS Control Tower** in the console (must be in a supported region, us-east-1 recommended)
3. Click **Set up landing zone**
4. Configure:
   - **Home Region**: `us-east-1`
   - **Region deny setting**: Enable (recommended)
   - **Additional regions**: None for now (can add later)
5. Configure **Foundational OU**:
   - Security OU name: `Security` (default)
6. Configure **Additional OU**:
   - Name: `Workloads`
7. Configure **shared accounts**:
   - Log Archive account email
   - Audit account email
8. Review and click **Set up landing zone**
9. Wait ~30-45 minutes for setup to complete

### Step 2: Create Workload Accounts via Account Factory

Once Control Tower is set up:

1. Go to **Control Tower** → **Account Factory**
2. Click **Create account**
3. For **Pre-prod account**:
   - Account email: `aws-preprod@yourcompany.com`
   - Display name: `teamofrivals-preprod`
   - SSO user email: Your admin email
   - SSO user name: Your name
   - Organizational unit: `Workloads`
4. Click **Create account** and wait (~10 minutes)
5. Repeat for **Production account**:
   - Account email: `aws-prod@yourcompany.com`
   - Display name: `teamofrivals-prod`
   - Same SSO user
   - Organizational unit: `Workloads`

### Step 3: Configure IAM Identity Center (SSO)

1. Go to **IAM Identity Center** (formerly AWS SSO)
2. Create **Permission Sets**:

### Admin Permission Set
- Name: `AdministratorAccess`
- Policy: `AdministratorAccess` (AWS managed)
- Session duration: 4 hours

### Developer Permission Set
- Name: `DeveloperAccess`
- Policies:
  - `PowerUserAccess`
  - `IAMReadOnlyAccess`
- Session duration: 8 hours

### ReadOnly Permission Set
- Name: `ReadOnlyAccess`
- Policy: `ReadOnlyAccess` (AWS managed)
- Session duration: 8 hours

3. **Assign permission sets to accounts**:
   - Go to **AWS accounts** in Identity Center
   - Select `teamofrivals-preprod`
   - Click **Assign users or groups**
   - Assign your user with `AdministratorAccess`
   - Repeat for `teamofrivals-prod`

### Step 4: Configure AWS CLI with SSO

1. Get your SSO start URL from IAM Identity Center → Settings → Identity source
   - It looks like: `https://d-xxxxxxxxxx.awsapps.com/start`

2. Configure AWS CLI:

```bash
# Configure SSO profile for pre-prod
aws configure sso
# SSO session name: teamofrivals
# SSO start URL: https://d-xxxxxxxxxx.awsapps.com/start
# SSO region: us-east-1
# Choose teamofrivals-preprod account
# Choose AdministratorAccess role
# CLI default region: us-east-1
# CLI default output: json
# Profile name: rivals-preprod

# Configure SSO profile for prod
aws configure sso --profile rivals-prod
# Same SSO session
# Choose teamofrivals-prod account
# Choose AdministratorAccess role
# Profile name: rivals-prod
```

3. Login and test:

```bash
# Login (opens browser)
aws sso login --profile rivals-preprod

# Test access
aws sts get-caller-identity --profile rivals-preprod

# Use profile for CDK
export AWS_PROFILE=rivals-preprod
cd infrastructure
cdk bootstrap
cdk deploy --all
```

### Step 5: Update CDK Configuration

After creating accounts, update `infrastructure/cdk.json` with account IDs:

```json
{
  "context": {
    "environments": {
      "preprod": {
        "account": "111111111111",  // Pre-prod account ID
        "region": "us-east-1"
      },
      "prod": {
        "account": "222222222222",  // Prod account ID
        "region": "us-east-1"
      }
    }
  }
}
```

Get account IDs from:
- IAM Identity Center → AWS accounts
- Or: `aws sts get-caller-identity --profile rivals-preprod`

### Step 6: Set Up GitHub Actions Credentials

For CI/CD, you need IAM credentials (not SSO). Create a dedicated IAM user in each account:

### In Pre-prod Account:

```bash
aws iam create-user --user-name github-actions --profile rivals-preprod

aws iam attach-user-policy \
  --user-name github-actions \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess \
  --profile rivals-preprod

aws iam create-access-key --user-name github-actions --profile rivals-preprod
# Save the AccessKeyId and SecretAccessKey
```

### In Prod Account:

```bash
aws iam create-user --user-name github-actions --profile rivals-prod

aws iam attach-user-policy \
  --user-name github-actions \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess \
  --profile rivals-prod

aws iam create-access-key --user-name github-actions --profile rivals-prod
# Save the AccessKeyId and SecretAccessKey
```

> **Security Note**: For production, create a custom IAM policy with least-privilege instead of `AdministratorAccess`.

### Add to GitHub Secrets:

Repository → Settings → Secrets and variables → Actions:

- `AWS_ACCESS_KEY_ID_PREPROD`
- `AWS_SECRET_ACCESS_KEY_PREPROD`
- `AWS_ACCOUNT_ID_PREPROD`
- `AWS_ACCESS_KEY_ID_PROD`
- `AWS_SECRET_ACCESS_KEY_PROD`
- `AWS_ACCOUNT_ID_PROD`

---

## Option B: CLI Setup

For scriptable/repeatable setup, use the AWS CLI. This approach is more complex but fully automatable.

### Step 1: Create Landing Zone via CLI

First, create a manifest file that defines your landing zone configuration:

```bash
# Create the manifest file
cat > landing-zone-manifest.json << 'EOF'
{
  "governedRegions": ["us-east-1"],
  "organizationStructure": {
    "security": {
      "name": "Security"
    },
    "sandbox": {
      "name": "Workloads"
    }
  },
  "centralizedLogging": {
    "accountId": "TO_BE_CREATED",
    "configurations": {
      "loggingBucket": {
        "retentionDays": 365
      },
      "accessLoggingBucket": {
        "retentionDays": 365
      }
    },
    "enabled": true
  },
  "securityRoles": {
    "accountId": "TO_BE_CREATED"
  },
  "accessManagement": {
    "enabled": true
  }
}
EOF
```

> **Note**: The `TO_BE_CREATED` values are placeholders. Control Tower will create the Log Archive and Audit accounts automatically.

```bash
# Create the landing zone (requires management account credentials)
aws controltower create-landing-zone \
  --manifest file://landing-zone-manifest.json \
  --version "3.3" \
  --region us-east-1

# This returns an operation ID - save it
# Example output: { "operationIdentifier": "abc123-def456-..." }
```

### Step 2: Monitor Landing Zone Creation

```bash
# Check status (takes 30-45 minutes)
aws controltower get-landing-zone-operation \
  --operation-identifier <operation-id-from-step-1> \
  --region us-east-1

# Or list all landing zones to get the ARN
aws controltower list-landing-zones --region us-east-1

# Get details
aws controltower get-landing-zone \
  --landing-zone-identifier <landing-zone-arn> \
  --region us-east-1
```

Wait until status is `SUCCEEDED` before proceeding.

### Step 3: Create Workload Accounts via Service Catalog

Control Tower uses AWS Service Catalog for Account Factory. First, find the Account Factory product:

```bash
# List Service Catalog products
aws servicecatalog search-products \
  --filters FullTextSearch="AWS Control Tower Account Factory" \
  --region us-east-1

# Get the product ID and provisioning artifact ID
PRODUCT_ID=$(aws servicecatalog search-products \
  --filters FullTextSearch="AWS Control Tower Account Factory" \
  --query 'ProductViewSummaries[0].ProductId' \
  --output text \
  --region us-east-1)

ARTIFACT_ID=$(aws servicecatalog list-provisioning-artifacts \
  --product-id $PRODUCT_ID \
  --query 'ProvisioningArtifactDetails[-1].Id' \
  --output text \
  --region us-east-1)

echo "Product ID: $PRODUCT_ID"
echo "Artifact ID: $ARTIFACT_ID"
```

Create the pre-prod account:

```bash
# Create pre-prod account
aws servicecatalog provision-product \
  --product-id $PRODUCT_ID \
  --provisioning-artifact-id $ARTIFACT_ID \
  --provisioned-product-name "teamofrivals-preprod" \
  --provisioning-parameters \
    Key=AccountName,Value=teamofrivals-preprod \
    Key=AccountEmail,Value=aws-preprod@yourcompany.com \
    Key=SSOUserFirstName,Value=Admin \
    Key=SSOUserLastName,Value=User \
    Key=SSOUserEmail,Value=admin@yourcompany.com \
    Key=ManagedOrganizationalUnit,Value=Workloads \
  --region us-east-1

# Check provisioning status
aws servicecatalog describe-provisioned-product \
  --name "teamofrivals-preprod" \
  --region us-east-1
```

Create the production account:

```bash
# Create prod account
aws servicecatalog provision-product \
  --product-id $PRODUCT_ID \
  --provisioning-artifact-id $ARTIFACT_ID \
  --provisioned-product-name "teamofrivals-prod" \
  --provisioning-parameters \
    Key=AccountName,Value=teamofrivals-prod \
    Key=AccountEmail,Value=aws-prod@yourcompany.com \
    Key=SSOUserFirstName,Value=Admin \
    Key=SSOUserLastName,Value=User \
    Key=SSOUserEmail,Value=admin@yourcompany.com \
    Key=ManagedOrganizationalUnit,Value=Workloads \
  --region us-east-1
```

### Step 4: Get Account IDs

```bash
# List all accounts in the organization
aws organizations list-accounts \
  --query 'Accounts[*].[Name,Id,Email]' \
  --output table

# Or get specific account by email
aws organizations list-accounts \
  --query "Accounts[?Email=='aws-preprod@yourcompany.com'].Id" \
  --output text
```

### Step 5: Configure IAM Identity Center via CLI

```bash
# Get Identity Center instance ARN
INSTANCE_ARN=$(aws sso-admin list-instances \
  --query 'Instances[0].InstanceArn' \
  --output text \
  --region us-east-1)

IDENTITY_STORE_ID=$(aws sso-admin list-instances \
  --query 'Instances[0].IdentityStoreId' \
  --output text \
  --region us-east-1)

echo "Instance ARN: $INSTANCE_ARN"
echo "Identity Store ID: $IDENTITY_STORE_ID"

# Create Administrator permission set
aws sso-admin create-permission-set \
  --instance-arn $INSTANCE_ARN \
  --name "AdministratorAccess" \
  --description "Full administrator access" \
  --session-duration "PT4H" \
  --region us-east-1

# Get the permission set ARN
ADMIN_PS_ARN=$(aws sso-admin list-permission-sets \
  --instance-arn $INSTANCE_ARN \
  --query "PermissionSets[0]" \
  --output text \
  --region us-east-1)

# Attach AWS managed policy to permission set
aws sso-admin attach-managed-policy-to-permission-set \
  --instance-arn $INSTANCE_ARN \
  --permission-set-arn $ADMIN_PS_ARN \
  --managed-policy-arn "arn:aws:iam::aws:policy/AdministratorAccess" \
  --region us-east-1
```

Assign the permission set to accounts:

```bash
# Get your user's principal ID from Identity Store
USER_ID=$(aws identitystore list-users \
  --identity-store-id $IDENTITY_STORE_ID \
  --query "Users[?UserName=='admin@yourcompany.com'].UserId" \
  --output text \
  --region us-east-1)

# Get account IDs
PREPROD_ACCOUNT_ID="111111111111"  # Replace with actual
PROD_ACCOUNT_ID="222222222222"      # Replace with actual

# Assign admin access to pre-prod
aws sso-admin create-account-assignment \
  --instance-arn $INSTANCE_ARN \
  --target-id $PREPROD_ACCOUNT_ID \
  --target-type AWS_ACCOUNT \
  --permission-set-arn $ADMIN_PS_ARN \
  --principal-type USER \
  --principal-id $USER_ID \
  --region us-east-1

# Assign admin access to prod
aws sso-admin create-account-assignment \
  --instance-arn $INSTANCE_ARN \
  --target-id $PROD_ACCOUNT_ID \
  --target-type AWS_ACCOUNT \
  --permission-set-arn $ADMIN_PS_ARN \
  --principal-type USER \
  --principal-id $USER_ID \
  --region us-east-1
```

### Step 6: Configure AWS CLI with SSO

```bash
# Get SSO start URL
SSO_START_URL=$(aws sso-admin list-instances \
  --query 'Instances[0].IdentityStoreId' \
  --output text \
  --region us-east-1)

# The SSO portal URL follows this pattern:
# https://d-xxxxxxxxxx.awsapps.com/start
# Get it from: IAM Identity Center → Settings → Identity source → AWS access portal URL

# Configure profiles (interactive)
aws configure sso
# Follow prompts for rivals-preprod profile

aws configure sso --profile rivals-prod
# Follow prompts for rivals-prod profile

# Or manually create ~/.aws/config entries:
cat >> ~/.aws/config << 'EOF'

[profile rivals-preprod]
sso_session = teamofrivals
sso_account_id = 111111111111
sso_role_name = AdministratorAccess
region = us-east-1
output = json

[profile rivals-prod]
sso_session = teamofrivals
sso_account_id = 222222222222
sso_role_name = AdministratorAccess
region = us-east-1
output = json

[sso-session teamofrivals]
sso_start_url = https://d-xxxxxxxxxx.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
EOF
```

### Step 7: Create GitHub Actions IAM Users

```bash
# Login to pre-prod
aws sso login --profile rivals-preprod

# Create IAM user for GitHub Actions
aws iam create-user --user-name github-actions --profile rivals-preprod

aws iam attach-user-policy \
  --user-name github-actions \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess \
  --profile rivals-preprod

# Create access keys (save the output!)
aws iam create-access-key --user-name github-actions --profile rivals-preprod

# Repeat for prod
aws sso login --profile rivals-prod

aws iam create-user --user-name github-actions --profile rivals-prod

aws iam attach-user-policy \
  --user-name github-actions \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess \
  --profile rivals-prod

aws iam create-access-key --user-name github-actions --profile rivals-prod
```

### CLI Setup Script (All-in-One)

For convenience, here's a script that combines the key steps:

```bash
#!/bin/bash
# control-tower-cli-setup.sh
# Run this after landing zone is created

set -e

REGION="us-east-1"
PREPROD_EMAIL="aws-preprod@yourcompany.com"
PROD_EMAIL="aws-prod@yourcompany.com"
ADMIN_EMAIL="admin@yourcompany.com"

echo "=== Finding Account Factory product ==="
PRODUCT_ID=$(aws servicecatalog search-products \
  --filters FullTextSearch="AWS Control Tower Account Factory" \
  --query 'ProductViewSummaries[0].ProductId' \
  --output text \
  --region $REGION)

ARTIFACT_ID=$(aws servicecatalog list-provisioning-artifacts \
  --product-id $PRODUCT_ID \
  --query 'ProvisioningArtifactDetails[-1].Id' \
  --output text \
  --region $REGION)

echo "Product ID: $PRODUCT_ID"
echo "Artifact ID: $ARTIFACT_ID"

echo "=== Creating pre-prod account ==="
aws servicecatalog provision-product \
  --product-id $PRODUCT_ID \
  --provisioning-artifact-id $ARTIFACT_ID \
  --provisioned-product-name "teamofrivals-preprod" \
  --provisioning-parameters \
    Key=AccountName,Value=teamofrivals-preprod \
    Key=AccountEmail,Value=$PREPROD_EMAIL \
    Key=SSOUserFirstName,Value=Admin \
    Key=SSOUserLastName,Value=User \
    Key=SSOUserEmail,Value=$ADMIN_EMAIL \
    Key=ManagedOrganizationalUnit,Value=Workloads \
  --region $REGION

echo "=== Creating prod account ==="
aws servicecatalog provision-product \
  --product-id $PRODUCT_ID \
  --provisioning-artifact-id $ARTIFACT_ID \
  --provisioned-product-name "teamofrivals-prod" \
  --provisioning-parameters \
    Key=AccountName,Value=teamofrivals-prod \
    Key=AccountEmail,Value=$PROD_EMAIL \
    Key=SSOUserFirstName,Value=Admin \
    Key=SSOUserLastName,Value=User \
    Key=SSOUserEmail,Value=$ADMIN_EMAIL \
    Key=ManagedOrganizationalUnit,Value=Workloads \
  --region $REGION

echo "=== Waiting for accounts to be created ==="
echo "Check status with:"
echo "  aws servicecatalog describe-provisioned-product --name teamofrivals-preprod --region $REGION"
echo "  aws servicecatalog describe-provisioned-product --name teamofrivals-prod --region $REGION"
```

---

## Common Configuration (Both Options)

After completing either Option A or Option B, continue with these shared steps.

## Control Tower Guardrails

Control Tower comes with default guardrails. Key ones enabled by default:

| Guardrail | Type | Effect |
|-----------|------|--------|
| Disallow public S3 buckets | Preventive | Blocks creation |
| Require MFA for root user | Detective | Alerts if not set |
| Disallow internet gateways | Preventive (optional) | Can enable per-OU |
| Enable CloudTrail | Preventive | Always on |
| Enable AWS Config | Detective | Compliance tracking |

You can enable additional guardrails in Control Tower → Guardrails.

## Architecture After Setup

```
Management Account (Control Tower)
├── IAM Identity Center (SSO)
├── AWS Organizations
└── Control Tower Dashboard

Security OU
├── Log Archive Account
│   └── Centralized CloudTrail logs
└── Audit Account
    └── AWS Config aggregator

Workloads OU
├── teamofrivals-preprod (111111111111)
│   ├── VPC, RDS, App Runner, S3, CloudFront
│   └── Secrets Manager
└── teamofrivals-prod (222222222222)
    ├── VPC, RDS, App Runner, S3, CloudFront
    └── Secrets Manager
```

## Alternative: Simple Organizations (No Control Tower)

If Control Tower feels like overkill, you can use simple AWS Organizations:

```bash
# In management account
aws organizations create-organization

# Create pre-prod account
aws organizations create-account \
  --email aws-preprod@yourcompany.com \
  --account-name teamofrivals-preprod

# Create prod account
aws organizations create-account \
  --email aws-prod@yourcompany.com \
  --account-name teamofrivals-prod

# Check status
aws organizations list-accounts
```

Then set up IAM users manually in each account for CLI/CI access.

**Trade-off**: No SSO, no guardrails, no centralized logging. But simpler and faster to set up.

## Costs

| Component | Monthly Cost |
|-----------|-------------|
| Control Tower | Free |
| AWS Organizations | Free |
| IAM Identity Center | Free |
| CloudTrail (centralized) | ~$2-5 |
| AWS Config | ~$1-3 per account |
| **Total overhead** | ~$5-10/month |

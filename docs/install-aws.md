# AWS Deployment Guide

This guide provides a practical path for deploying the Bank Offer Feed Ranking application to AWS. 

> **Scope Note:** Version 1 of this application is designed primarily for local execution and evaluation. There is currently no full Terraform stack or automated infrastructure-as-code deployment included in this repository. This document outlines a practical, Docker-free AWS EC2 pattern that mirrors the local architecture.

## 1. Prerequisites
- **AWS Account:** Active account with billing enabled.
- **IAM Basics:** An IAM user/role with permissions to provision EC2 instances, Security Groups, and (optionally) S3 buckets.
- **Region:** Select a region (e.g., `us-east-1`).

## 2. Infrastructure Setup (EC2 Single Instance Pattern)
Since this is a lightweight, Docker-free stack (Python/FastAPI + Node/React), a single EC2 instance is sufficient for a non-HA demo environment.

1. **Launch an EC2 Instance:**
   - Choose an Amazon Linux 2023 or Ubuntu 22.04 AMI.
   - Instance type: `t3.medium` or larger (ML training requires some memory).
   - Configure a Security Group to allow inbound traffic on:
     - Port `22` (SSH)
     - Port `8000` (FastAPI backend)
     - Port `5173` (Vite frontend - or build statically and serve via Nginx on port 80).

2. **Connect and Install Dependencies:**
   SSH into the instance and install Python 3.11+, Node 18+, and Git.
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv nodejs npm git
   ```

## 3. Clone and Build
Follow steps similar to the [Local Installation Guide](install-local.md):
```bash
git clone <your-repo-url>
cd BankOfferFeedRanking
```

**Set up Python and Node:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .

cd frontend
npm install
cd ..
```

## 4. ML Artifacts on AWS
You have two options for ML artifacts:
1. **Train on EC2:** Upload `data/raw/bank-additional-full.csv` to the EC2 instance and run the pipelines (`ml.data.preprocess`, `ml.data.run_synthetic`, `ml.training.train`).
2. **Use S3 (Optional):** Train locally, upload `ml/artifacts/` to an S3 bucket, and download them to the EC2 instance upon deployment. Ensure your EC2 instance has an IAM Role with `s3:GetObject` permissions.

## 5. Running the Application
**Backend:**
Use a process manager like `pm2` or `systemd` to keep the backend running.
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

**Frontend:**
For a demo, you can run the dev server, but a production build is recommended:
```bash
cd frontend
# Build static assets
VITE_API_BASE_URL=http://<EC2_PUBLIC_IP>:8000 npm run build
# Serve using a static server (e.g., serve or nginx)
npx serve -s dist -p 5173 &
```

## 6. Security and Environment Variables
- **No Secrets in Git:** Never commit AWS credentials. Use EC2 IAM roles instead of hardcoded keys.
- **Environment Variables:** Set `VITE_API_BASE_URL` to your EC2 public IP or domain name so the frontend can route to the backend properly.
- **Firewall Restrictions:** Limit IP ranges in the Security Group if this demo is meant to be private.

## 7. Verification and Smoke Tests
From your local machine, run health checks against the EC2 instance:
```bash
curl http://<EC2_PUBLIC_IP>:8000/health
curl http://<EC2_PUBLIC_IP>:8000/api/v1/sample-users
```
Open `http://<EC2_PUBLIC_IP>:5173` in your browser.

## 8. Cost and Scope Caveats
- **Not Production HA:** This guide does not deploy an Application Load Balancer (ALB), ECS/Fargate clusters, or an RDS database. 
- **Cost:** Running a `t3.medium` 24/7 will incur standard hourly rates. Terminate or stop the instance when the demo is not in use.

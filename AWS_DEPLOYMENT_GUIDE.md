# 🚀 FAM-FIOS: Production AWS Cloud Deployment Guide

This guide explains how to deploy **FAM-FIOS (Federated Adaptive Multi-Tenant Fitness OS)** to Amazon Web Services (AWS) to receive a **live, secure public HTTPS URL** accessible from any phone or computer worldwide.

---

## ⚡ Method 1: AWS App Runner (Fastest — No Local Docker Required!)

**AWS App Runner** is a fully managed container service that automatically builds, deploys, and scales web applications with automated SSL/TLS certificates and load balancing.

### Step-by-Step Instructions:

1. **Push your code to GitHub**:
   Ensure your repository has the newly created `Dockerfile` and `requirements.txt` at the root.

2. **Open AWS App Runner Console**:
   - Sign in to your [AWS Management Console](https://console.aws.amazon.com/).
   - Set your region to **Asia Pacific (Mumbai) `ap-south-1`** (top right dropdown).
   - In the search bar, type **App Runner** and click **Create service**.

3. **Configure Source**:
   - **Repository type**: Choose **Source code repository** (GitHub).
   - Connect your GitHub account and select your `fam-fios` repository and branch (e.g. `main`).
   - **Deployment trigger**: Select **Automatic** (deploys automatically whenever you push code).

4. **Configure Build Settings**:
   - **Build runtime**: Select **Use a Dockerfile** (uses our optimized `Dockerfile`).
   - Click **Next**.

5. **Configure Service**:
   - **Service name**: `fam-fios-production`
   - **Virtual CPU & Memory**: `1 vCPU` & `2 GB` (plenty for high-performance Streamlit + AI engines).
   - **Port**: `8501`
   - **Environment Variables**:
     ```ini
     STREAMLIT_SERVER_PORT = 8501
     STREAMLIT_SERVER_ADDRESS = 0.0.0.0
     STREAMLIT_SERVER_HEADLESS = true
     AWS_DEFAULT_REGION = ap-south-1
     AWS_S3_BUCKET_NAME = fam-fios-cloud-vault
     ```

6. **Deploy**:
   - Click **Next** $\rightarrow$ Review details $\rightarrow$ Click **Create & deploy**.
   - Within 3–5 minutes, AWS will provision your live service and grant you a public HTTPS URL:
     ```text
     https://fam-fios-abc123xyz.ap-south-1.awsapprunner.com
     ```

---

## 💻 Method 2: AWS CloudShell (100% In-Browser Terminal Build)

If you don't have Docker installed on your local computer, you can build and push the container using **AWS CloudShell** directly in your browser (Docker and AWS CLI are already pre-installed for free):

1. Click the **CloudShell icon** `(>_)` at the top right of the AWS Console.
2. Clone your repository:
   ```bash
   git clone https://github.com/your-username/fam-fios.git
   cd fam-fios
   ```
3. Authenticate with Amazon ECR:
   ```bash
   ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com
   aws ecr create-repository --repository-name fam-fios --region ap-south-1 || true
   ```
4. Build and push the container image:
   ```bash
   docker build -t fam-fios .
   docker tag fam-fios:latest ${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/fam-fios:latest
   docker push ${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/fam-fios:latest
   ```
5. In **AWS App Runner**, select **Container registry** $\rightarrow$ **Amazon ECR** $\rightarrow$ Choose your newly pushed image.

---

## 🖥️ Method 3: Local Docker Desktop & PowerShell

If you have Docker Desktop installed on your Windows machine:

1. Open PowerShell in this folder:
   ```powershell
   # Test locally with Docker Compose
   docker-compose up -d

   # Access at http://localhost:8501
   ```
2. Deploy to AWS ECR:
   ```powershell
   # Runs automated authentication, image build, tagging, and push
   .\deploy_aws.ps1 -Region "ap-south-1"
   ```

---

## 🔒 Security & Health Checks

* **Container Health Probe**:
  Configured to `http://localhost:8501/_stcore/health`.
* **Zero Root Execution**:
  The container runs as non-root user `appuser` (UID 1000) for strict multi-tenant container isolation.
* **Server-Side Encryption**:
  All files uploaded via the application automatically inherit AWS S3 and SNS cloud policies.

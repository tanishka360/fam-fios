# 🚀 FAM-FIOS: Production AWS Cloud Deployment Guide

This guide provides the complete, step-by-step instructions to deploy **FAM-FIOS (Federated Adaptive Multi-Tenant Fitness OS)** to Amazon Web Services (AWS) to get a **live, secure public URL** accessible worldwide from any mobile phone or computer.

---

## 🌟 Quick Comparison: Which Deployment Method Should You Choose?

| Deployment Method | Best For | Prerequisites | Free Tier? | Time to Deploy |
|---|---|---|---|---|
| **Option 1: AWS App Runner** *(Recommended)* | Direct GitHub deployment, automatic HTTPS & scaling | None (No Docker/CLI needed on laptop) | Paid as you go (~$5/mo active) | **3 - 5 mins** |
| **Option 2: Amazon EC2 (Ubuntu VM)** | Complete server control, lowest cost | AWS Account | **Yes (Free Tier t2.micro)** | **3 - 5 mins** |
| **Option 3: AWS CloudShell + ECR** | Containerized deployment via browser | None (uses in-browser AWS terminal) | Uses ECR/App Runner | **5 - 8 mins** |

---

## ⚡ Option 1: AWS App Runner (Fastest & Zero Setup — Recommended)

**AWS App Runner** connects directly to your GitHub repository, builds your Docker container automatically in the cloud, provisions load balancing, and assigns a **live public HTTPS URL** (with SSL/TLS certificates).

### Step-by-Step Instructions:

1. **Ensure Code is on GitHub**:
   Your repository is at [`https://github.com/tanishka360/fam-fios`](https://github.com/tanishka360/fam-fios) with the `Dockerfile` and `requirements.txt` ready.

2. **Open AWS App Runner Console**:
   * Sign in to the [AWS Management Console](https://console.aws.amazon.com/).
   * Select your preferred AWS Region (e.g. **Asia Pacific (Mumbai) `ap-south-1`** or **US East (N. Virginia) `us-east-1`**).
   * Search for **App Runner** in the top search bar and click **Create service**.

3. **Step 1: Configure Source & Deployment**:
   * **Source**: Select **Source code repository**.
   * **Connect to GitHub**: Click **Add new** to authorize AWS with your GitHub account.
   * **Repository**: Select `tanishka360/fam-fios`.
   * **Branch**: Select `main`.
   * **Deployment trigger**: Select **Automatic** (every time you push code to GitHub, AWS automatically redeploys!).

4. **Step 2: Configure Build Settings**:
   * **Build runtime**: Select **Use a Dockerfile**.
   * Click **Next**.

5. **Step 3: Configure Service**:
   * **Service name**: `fam-fios-live`
   * **Virtual CPU & Memory**: Select `1 vCPU` & `2 GB` (optimal performance).
   * **Port**: `8501`
   * **Environment Variables** (Optional — click *Add environment variable*):
     ```ini
     STREAMLIT_SERVER_PORT = 8501
     STREAMLIT_SERVER_ADDRESS = 0.0.0.0
     STREAMLIT_SERVER_HEADLESS = true
     AWS_DEFAULT_REGION = ap-south-1
     AWS_S3_BUCKET_NAME = fam-fios-cloud-vault
     ```

6. **Step 4: Review and Deploy**:
   * Click **Next** $\to$ **Create & deploy**.
   * AWS will pull your code, build the container, and start the service in ~3 minutes.
   * Your public URL will be ready at:
     ```text
     https://fam-fios-xxxxxx.ap-south-1.awsapprunner.com
     ```

---

## 🖥️ Option 2: Amazon EC2 (100% Free Tier Eligible VM)

If you want a dedicated Linux server or want to use the AWS Free Tier (750 hours/month free on `t2.micro` or `t3.micro`):

### Step 1: Launch an EC2 Instance
1. In the AWS Console, search for **EC2** and click **Launch Instance**.
2. **Name**: `FAM-FIOS-Server`
3. **OS Image**: Select **Ubuntu** (Ubuntu Server 22.04 LTS or 24.04 LTS — Free Tier eligible).
4. **Instance Type**: Select `t2.micro` (or `t3.micro` / `t3.small`).
5. **Key pair**: Select *Proceed without a key pair* (if using EC2 Instance Connect) or choose your existing `.pem` key.
6. **Network Settings (Security Group)**:
   * Check **Allow SSH traffic from anywhere**.
   * Check **Allow HTTP traffic from the internet**.
   * Click **Edit network settings** and add a custom rule:
     * **Type**: Custom TCP
     * **Port range**: `8501`
     * **Source**: `0.0.0.0/0` (Anywhere)
7. Click **Launch Instance**.

### Step 2: Connect to Your Instance
1. In the EC2 Instances list, select your new instance and click **Connect**.
2. Choose **EC2 Instance Connect** and click **Connect** (opens a browser-based Linux terminal immediately!).

### Step 3: Run the 1-Line Deployment Command
Paste and run this single command in the terminal:

```bash
curl -sSL https://raw.githubusercontent.com/tanishka360/fam-fios/main/deploy_aws_ec2.sh | bash
```

### What This Script Does Automatically:
1. Installs Docker and Docker Compose on the Ubuntu server.
2. Clones the latest `fam-fios` repository from GitHub.
3. Builds and starts the production container in detached mode (`docker-compose up -d --build`).
4. Verifies the health check probe.
5. Prints your **live public IP and port**:
   ```text
   http://<YOUR-EC2-PUBLIC-IP>:8501
   ```

*(Optional: To map to standard Port 80, simply run: `sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8501`)*

---

## 💻 Option 3: AWS CloudShell (In-Browser Terminal Container Build)

If you want to build and push container images to Amazon Elastic Container Registry (ECR) without installing Docker on your local laptop:

1. Click the **CloudShell icon** `(>_)` at the top right header of the AWS Console.
2. Clone your repository:
   ```bash
   git clone https://github.com/tanishka360/fam-fios.git
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
5. In **AWS App Runner** or **AWS ECS**, select **Container registry** $	o$ **Amazon ECR** $	o$ Select `fam-fios:latest`.

---

## 🔐 Environment Variables for Live Services

When deploying to production, you can configure these optional environment variables in AWS App Runner or your EC2 `.env` file for full cloud integration:

| Variable | Description | Example |
|---|---|---|
| `AWS_DEFAULT_REGION` | AWS Region for S3 and SNS | `ap-south-1` |
| `AWS_S3_BUCKET_NAME` | Dedicated S3 bucket for invoices/weights | `fam-fios-cloud-vault` |
| `SMTP_HOST` | Email SMTP host for real OTP emails | `smtp.gmail.com` |
| `SMTP_PORT` | Email SMTP port | `587` |
| `SMTP_USER` | Sending email address | `notifications@yourgym.com` |
| `SMTP_PASSWORD` | App Password for SMTP | `xxxx xxxx xxxx xxxx` |

---

## 🩺 Health Check & Monitoring

* **Health Probe URL**: `http://<domain-or-ip>:8501/_stcore/health`
* **Response**: Returns HTTP `200 OK` when the application is healthy and ready to serve traffic.
* **Security Model**: The container executes as an unprivileged non-root user (`appuser`, UID 1000) for strict multi-tenant container security.

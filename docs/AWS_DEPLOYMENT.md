# 🚀 AWS EC2 Production Deployment Guide

This document details the step-by-step procedure for deploying the **Autonomous Logistics Object Detection & Reasoning API** to an **Amazon Web Services (AWS) EC2** instance for 24/7 autonomous operation during the hackathon evaluation window (15–20 days).

---

## 1. Deployment Architecture

```
                               Internet / Client Requests
                                           │
                                  ┌────────┴────────┐
                                  ▼                 ▼
                           HTTP (:80)         HTTPS (:443)
                                  │                 │
                                  └────────┬────────┘
                                           │
                                  ┌────────▼────────┐
                                  │   Nginx Proxy   │ (Public Reverse Proxy)
                                  └────────┬────────┘
                                           │ (Internal Port :7860)
                                           ▼
                        ┌─────────────────────────────────────┐
                        │  logistics-app Docker Container     │
                        │  ┌───────────────────────────────┐  │
                        │  │  FastAPI Application Backend  │  │
                        │  ├───────────────────────────────┤  │
                        │  │  RT-DETR-L PyTorch Model      │  │
                        │  │  (weights/best.pt)            │  │
                        │  ├───────────────────────────────┤  │
                        │  │  Deterministic Reasoning Logic│  │
                        │  └───────────────────────────────┘  │
                        └─────────────────────────────────────┘
```

The application runs inside a Docker container with `restart: unless-stopped` bound internally to port `7860`. Nginx acts as the public-facing reverse proxy listening on ports `80` and `443`.

---

## 2. AWS Cost Safety & Billing Precautions

> [!CAUTION]
> **AWS Cost Safety Warning**:
> - Do **NOT** assume your AWS account is eligible for Free Tier until confirmed in the AWS Billing Console.
> - Do **NOT** create NAT Gateways, Application Load Balancers (ALBs), RDS databases, ECS/EKS clusters, or GPU instances (`g4dn`/`p3`). These incur significant hourly charges.
> - Deploy strictly on a single standalone **t3.small** EC2 instance with a single 20 GiB gp3 root volume.

---

## 3. Recommended EC2 Instance Specifications

| Parameter | Recommended Specification | Rationale |
| :--- | :--- | :--- |
| **Instance Type** | `t3.small` | **2 vCPU, 2 GiB RAM**. Required because RT-DETR-L model idle footprint is ~988 MiB and inference tensor allocation requires >1.2 GiB RAM. |
| **Architecture** | `x86_64` | Native PyTorch & OpenCV pre-built wheel compatibility. |
| **AMI / OS** | Ubuntu 24.04 LTS | Standard, lightweight, highly stable server Linux distribution. |
| **Storage** | 20 GiB gp3 EBS | Sufficient for Ubuntu OS, Docker runtime, PyTorch CPU wheels, and repository weights. |
| **Region** | `ap-south-1` (Mumbai) | Select region closest to your target latency requirements. |

> [!WARNING]
> **Why `t3.micro` (1 GiB RAM) is NOT recommended**:
> The RT-DETR-L model memory footprint consumes ~988 MiB of RAM when idle. Under image inference workloads (`POST /detect` or `POST /ask`), RAM consumption briefly spikes above 1.2 GiB. On a `t3.micro` (1 GiB RAM) instance without swap, this triggers Linux Out-Of-Memory (OOM) killer terminating the container.

---

## 4. EC2 Security Group Configuration

Create an EC2 Security Group (e.g., `logistics-api-sg`) with the following **minimum required inbound rules**:

| Type | Protocol | Port Range | Source | Purpose |
| :--- | :---: | :---: | :---: | :--- |
| **SSH** | TCP | 22 | `<MY_CURRENT_IP>/32` | Remote administration access (Restricted to developer IP only). |
| **HTTP** | TCP | 80 | `0.0.0.0/0` | Active public web traffic for Nginx reverse proxy. |
| **HTTPS** | TCP | 443 | `0.0.0.0/0` | Reserved for future SSL reverse proxy configuration (Certbot / Let's Encrypt). |

> [!IMPORTANT]
> **Port Security & HTTPS Clarification**:
> - **Port 443 Reservation**: Port 443 is allowed in the Security Group as a reservation for future HTTPS/TLS configuration. The default automated bootstrap configures HTTP on Port 80. Do **NOT** claim HTTPS is active until a real domain and TLS certificate (e.g., via Certbot) are explicitly configured.
> - **Port 7860 Isolation**: Port **7860 must NOT be exposed publicly** in the AWS Security Group. FastAPI runs internally on container port `7860` (`127.0.0.1:7860`) and is accessed publicly only via Nginx on port `80` (and `443` when SSL is enabled).
> - Do **NOT** expose Docker daemon ports (`2375`, `2376`), SSH (`22`) to `0.0.0.0/0`, or internal database ports.


---

## 5. Step-by-Step EC2 Deployment Guide

### Step 5.1: Launch EC2 Instance & Connect via SSH
Launch your `t3.small` Ubuntu instance in the AWS Console, download your keypair (`.pem`), and connect via terminal:
```bash
chmod 400 <SSH_KEY_PATH>.pem
ssh -i <SSH_KEY_PATH>.pem ubuntu@<EC2_PUBLIC_IP>
```

### Step 5.2: Update System, Install Docker & Nginx
Once logged into the EC2 instance:
```bash
# 1. Update package indices
sudo apt update && sudo apt upgrade -y

# 2. Install Docker, Docker Compose, Nginx, and git
sudo apt install -y docker.io docker-compose-v2 nginx curl git

# 3. Add ubuntu user to docker group
sudo usermod -aG docker ubuntu
newgrp docker
```

### Step 5.3: Optional EC2 Swap Space Configuration (Memory Safety Buffer)
To safeguard the `t3.small` (2 GiB RAM) instance against temporary Out-Of-Memory (OOM) spikes during heavy concurrent inference, configure a **2 GB to 4 GB swap space**:

```bash
# 1. Create a 2GB swap file (or 4G for additional headroom)
sudo fallocate -l 2G /swapfile

# 2. Restrict permissions
sudo chmod 600 /swapfile

# 3. Set up swap area
sudo mkswap /swapfile
sudo swapon /swapfile

# 4. Make swap permanent across reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 5. Verify swap space
sudo swapon --show
```

> [!NOTE]
> **Swap Safety Clarification**:
> Swap space acts as an emergency memory safety buffer to prevent kernel OOM killer crashes during temporary peak workload spikes. Swap is stored on disk (EBS) and is significantly slower than physical RAM; **swap does NOT replace physical RAM**, but provides critical runtime safety.

### Step 5.4: Clone Repository & Launch Docker Container
```bash
# 1. Clone official repository
git clone https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git
cd Logistics-Object-Detection-Model

# 2. Build and launch container in detached mode using Docker Compose
docker compose up -d --build

# 3. Verify container status and health check internally
docker compose ps
curl -f http://localhost:7860/health
```

---

## 6. Nginx Reverse Proxy Configuration & HTTPS Setup

Nginx acts as the public reverse proxy, receiving requests on ports `80` and `443` and forwarding them internally to FastAPI on port `7860`.

### Step 6.1: Configure Nginx Site
```bash
sudo nano /etc/nginx/sites-available/logistics-api
```

Paste the following configuration:
```nginx
server {
    listen 80;
    server_name <EC2_PUBLIC_IP> <DOMAIN_NAME>;

    # Allow larger image uploads for detection endpoints
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and test Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/logistics-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6.2: Enable Free SSL/TLS via Let's Encrypt (If Domain Available)
If you have pointed a custom domain name to your EC2 Public IP:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d <DOMAIN_NAME>
```

---

## 7. Public API Endpoint Verification

Once Nginx is configured, test all four core API endpoints over public HTTP (`:80`):

```bash
# 1. GET /health
curl -X GET "http://<EC2_PUBLIC_IP>/health"

# 2. GET /classes
curl -X GET "http://<EC2_PUBLIC_IP>/classes"

# 3. POST /detect (Image Detection)
curl -X POST "http://<EC2_PUBLIC_IP>/detect" \
  -F "file=@data/logistics_2500/test/images/-1-DRY-CONTAINER-_-_png_jpg.rf.af49c95763d7179243f25c6bb47f3050.jpg"

# 4. POST /ask (Visual Reasoning Question)
curl -X POST "http://<EC2_PUBLIC_IP>/ask" \
  -F "file=@data/logistics_2500/test/images/-1-DRY-CONTAINER-_-_png_jpg.rf.af49c95763d7179243f25c6bb47f3050.jpg" \
  -F "question=How many freight containers are visible?"
```

---

## 8. Process Persistence & 15–20 Day Reliability

The deployment guarantees long-term availability without human intervention:

- **Laptop Independence**: The backend runs inside AWS EC2 instance. Turning off your developer PC or closing terminals does **not** affect the API.
- **Automatic Container Restarts**: `restart: unless-stopped` in `docker-compose.yml` ensures the container automatically restarts if application memory spikes or a temporary crash occurs.
- **EC2 System Reboot Recovery**: If AWS performs system maintenance or the EC2 instance is rebooted, the Docker service automatically starts `logistics-app` upon system boot.
- **Storage Persistence**: Attached EBS volume stores container state, swap file, and weights across instance restarts.

---

## 9. Redeployment & Update Procedure

When pushing updates to GitHub (`origin/main`), apply them to the EC2 instance with these 4 commands:

```bash
# 1. Connect to EC2
ssh -i <SSH_KEY_PATH>.pem ubuntu@<EC2_PUBLIC_IP>

# 2. Navigate to project root
cd Logistics-Object-Detection-Model

# 3. Pull latest code and rebuild container
git pull origin main
docker compose up -d --build

# 4. Confirm health
curl -f http://localhost:7860/health
```

---

---

## 11. Infrastructure as Code (Terraform) Automated Deployment

As a production-ready alternative to manual AWS console setup, this repository includes complete **Terraform Infrastructure as Code (IaC)** templates under the [`terraform/`](file:///C:/Aadithya%20projects/logistics-object-detection/terraform) directory.

### Step 11.1: Prerequisites & AWS Authentication
- Install [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) (version `>= 1.5.0`).
- Install [AWS CLI](https://aws.amazon.com/cli/) and authenticate using standard environment credentials:
  ```bash
  aws configure
  ```
  *(Never hardcode AWS Access Keys or Secret Keys inside `.tf` files).*

### Step 11.2: Initialize & Validate Terraform Code
```bash
# 1. Navigate to terraform directory
cd terraform

# 2. Create custom tfvars file from example template
cp terraform.tfvars.example terraform.tfvars

# 3. Initialize Terraform working directory (downloads AWS provider)
terraform init

# 4. Validate syntax and configuration
terraform validate
```

### Step 11.3: Preview Infrastructure Plan
```bash
terraform plan
```
**Resources to be Created**:
- Security Group (`aws_security_group.logistics_api_sg`) with ingress on 22, 80, 443 (Port 7860 closed publicly).
- EC2 Instance (`aws_instance.logistics_api`) on `t3.small` with 20 GiB `gp3` encrypted root volume.
- Dynamic AMI lookup for Ubuntu 24.04 LTS x86_64 (`data.aws_ami.ubuntu_2404`).
- Automatic EC2 system bootstrap via `user-data.sh` (installs Docker, Compose, Nginx, sets 2GB swap, clones repo, starts container).
- (Optional) Elastic IP (`aws_eip.logistics_eip`) if `enable_elastic_ip = true`.

### Step 11.4: Apply Deployment
```bash
terraform apply
```
Type `yes` when prompted.

### Step 11.5: Inspect Outputs & Verify Health
Upon completion, Terraform will output:
```hcl
Outputs:

api_http_url = "http://<EC2_PUBLIC_IP>"
docs_url     = "http://<EC2_PUBLIC_IP>/docs"
health_url   = "http://<EC2_PUBLIC_IP>/health"
instance_id  = "i-0123456789abcdef0"
public_dns   = "ec2-xxx-xxx-xxx-xxx.ap-south-1.compute.amazonaws.com"
public_ip    = "<EC2_PUBLIC_IP>"
```

Verify deployment via `curl`:
```bash
curl -f http://<EC2_PUBLIC_IP>/health
```

### Step 11.6: Destroy Infrastructure (Teardown)
To tear down all provisioned AWS resources and avoid unwanted charges:
```bash
terraform destroy
```

> [!CAUTION]
> **Free Tier Disclaimer**:
> Running `terraform apply` provisions real AWS EC2/EBS infrastructure. Terraform does **NOT** guarantee Free Tier eligibility. Verify your account status in the AWS Billing Console prior to executing `terraform apply`.


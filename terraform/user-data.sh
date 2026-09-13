#!/bin/bash
set -e

# Log user data execution
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/null) 2>&1
echo "=== Beginning Logistics API Bootstrap ==="

# 1. System update & package dependencies
apt-get update && apt-get upgrade -y
apt-get install -y docker.io docker-compose-v2 nginx git curl

# 2. Enable services
systemctl enable --now docker
systemctl enable --now nginx

# 3. Configure 2GB Swap space as memory safety buffer for t3.small
if [ ! -f /swapfile ]; then
    echo "Creating 2GB swap space..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 4. Clone repository
APP_DIR="/opt/logistics-api"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
git clone "${repo_url}" "$APP_DIR"
cd "$APP_DIR"

# 5. Build and launch Docker Compose container
echo "Building and launching Docker container..."
docker compose up -d --build

# 6. Configure Nginx Reverse Proxy (Port 80/443 -> Internal Port 7860)
cat <<'EOF' > /etc/nginx/sites-available/logistics-api
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/logistics-api /etc/nginx/sites-enabled/logistics-api
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "=== Logistics API Bootstrap Complete ==="

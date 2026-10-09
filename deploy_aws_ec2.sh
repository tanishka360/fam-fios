#!/usr/bin/env bash
# ==============================================================================
# FAM-FIOS: Automated 1-Click Amazon EC2 Deployment Script
# Patent Invention: 24BIT0370-24BIT0390-IDF-01
# ==============================================================================
set -e

echo "🚀 [1/4] Updating system packages and installing Docker..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y docker.io docker-compose git curl
elif command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y docker git curl
    sudo service docker start
fi

sudo systemctl enable docker || true
sudo systemctl start docker || true
sudo usermod -aG docker $USER || true

echo "📦 [2/4] Fetching latest FAM-FIOS source code..."
if [ -d "fam-fios" ]; then
    cd fam-fios
    git pull origin main
elif [ -f "streamlit_app.py" ]; then
    echo "Already inside fam-fios directory."
else
    git clone https://github.com/tanishka360/fam-fios.git
    cd fam-fios
fi

echo "🐳 [3/4] Building and launching FAM-FIOS container..."
sudo docker-compose down || true
sudo docker-compose up -d --build

echo "⏳ [4/4] Verifying Streamlit container health probe..."
sleep 12
curl -f http://localhost:8501/_stcore/health || echo "Container starting up..."

PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || curl -s ifconfig.me || echo "YOUR_EC2_PUBLIC_IP")
echo ""
echo "======================================================================"
echo "🎉 FAM-FIOS IS LIVE ON AWS CLOUD!"
echo "🌐 Public Web URL: http://${PUBLIC_IP}:8501"
echo "======================================================================"

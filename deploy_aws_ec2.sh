#!/usr/bin/env bash
# ==============================================================================
# FAM-FIOS: Automated 1-Click Amazon EC2 Deployment Script
# Patent Invention: 24BIT0370-24BIT0390-IDF-01
#
# Tested targets: Ubuntu 22.04 / 24.04 LTS, Amazon Linux 2023
# Usage (from the instance's home directory):
#   curl -sSL https://raw.githubusercontent.com/tanishka360/fam-fios/main/deploy_aws_ec2.sh | bash
# Re-running the same command pulls the latest code and redeploys.
# ==============================================================================
set -euo pipefail

REPO_URL="https://github.com/tanishka360/fam-fios.git"
APP_DIR="$HOME/fam-fios"
APP_PORT=8501
COMPOSE_FALLBACK_VERSION="v2.29.7"

# Everything runs inside main() so bash parses the whole script before executing.
# This matters for `curl ... | bash`, where a command reading stdin could
# otherwise swallow the rest of the script.
main() {
echo "🚀 [1/5] Installing Docker, Docker Compose, git and curl..."
if command -v apt-get &> /dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    sudo apt-get update -y
    sudo apt-get install -y docker.io git curl
    # Compose v2 plugin ("docker compose"); package name differs across releases
    sudo apt-get install -y docker-compose-v2 \
        || sudo apt-get install -y docker-compose-plugin \
        || true
    sudo apt-get install -y docker-buildx || true
elif command -v dnf &> /dev/null; then
    sudo dnf install -y docker git
elif command -v yum &> /dev/null; then
    sudo yum install -y docker git
else
    echo "❌ Unsupported OS: no apt-get, dnf or yum found." >&2
    exit 1
fi

sudo systemctl enable --now docker
sudo usermod -aG docker "${USER:-$(id -un)}" || true

# Last resort: install the Compose v2 plugin binary directly from GitHub
if ! sudo docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "   Compose not available from the package manager; installing plugin ${COMPOSE_FALLBACK_VERSION}..."
    case "$(uname -m)" in
        x86_64)  COMPOSE_ARCH="x86_64" ;;
        aarch64) COMPOSE_ARCH="aarch64" ;;
        *) echo "❌ Unsupported CPU architecture: $(uname -m)" >&2; exit 1 ;;
    esac
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -fsSL \
        "https://github.com/docker/compose/releases/download/${COMPOSE_FALLBACK_VERSION}/docker-compose-linux-${COMPOSE_ARCH}" \
        -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

if sudo docker compose version &> /dev/null; then
    COMPOSE=(sudo docker compose)
else
    COMPOSE=(sudo docker-compose)
fi
echo "   ✅ Using: ${COMPOSE[*]} ($("${COMPOSE[@]}" version --short 2>/dev/null || echo unknown))"

echo "💾 [2/5] Ensuring swap space for small instances..."
MEM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
if [ "$(swapon --noheadings | wc -l)" -eq 0 ] && [ "$MEM_MB" -lt 3000 ]; then
    sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab > /dev/null
    echo "   ✅ Added 2 GB swap (RAM: ${MEM_MB} MB)."
else
    echo "   ✅ Swap not needed or already present (RAM: ${MEM_MB} MB)."
fi

echo "📦 [3/5] Fetching latest FAM-FIOS source code..."
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only origin main
else
    git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

echo "🐳 [4/5] Building and launching FAM-FIOS container (first build takes a few minutes)..."
"${COMPOSE[@]}" down || true
"${COMPOSE[@]}" up -d --build

echo "⏳ [5/5] Waiting for Streamlit health probe..."
HEALTHY=false
for _ in $(seq 1 30); do
    if curl -fs "http://localhost:${APP_PORT}/_stcore/health" > /dev/null; then
        HEALTHY=true
        break
    fi
    sleep 4
done

# Public IP via instance metadata (IMDSv2), falling back to an external lookup
IMDS_TOKEN=$(curl -fs -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60" || true)
PUBLIC_IP=$(curl -fs -H "X-aws-ec2-metadata-token: ${IMDS_TOKEN}" \
    http://169.254.169.254/latest/meta-data/public-ipv4 \
    || curl -fs http://checkip.amazonaws.com \
    || echo "YOUR_EC2_PUBLIC_IP")

echo ""
echo "======================================================================"
if [ "$HEALTHY" = true ]; then
    echo "🎉 FAM-FIOS IS LIVE ON AWS CLOUD!"
    echo "🌐 Public Web URL: http://${PUBLIC_IP}:${APP_PORT}"
    echo "   (If it doesn't load, check the security group allows TCP ${APP_PORT}.)"
else
    echo "⚠️  Container did not report healthy within 2 minutes. Recent logs:"
    "${COMPOSE[@]}" logs --tail 40 || true
    echo "   Expected URL once healthy: http://${PUBLIC_IP}:${APP_PORT}"
fi
echo "======================================================================"
}

main "$@" < /dev/null

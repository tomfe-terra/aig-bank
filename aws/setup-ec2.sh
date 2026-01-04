#!/bin/bash
# =============================================================================
# AIG Bank EC2 Setup Script
# =============================================================================
# This script runs on the EC2 instance to:
# 1. Install Docker and Docker Compose
# 2. Generate secure secrets
# 3. Create .env file
# 4. Install and configure Certbot for Let's Encrypt SSL
# 5. Start Docker Compose services
# 6. Configure automatic certificate renewal

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as ec2-user
if [ "$USER" != "ec2-user" ]; then
    log_error "This script must be run as ec2-user"
    exit 1
fi

# Get domain name from parameter or file
DOMAIN=${1:-$(cat /opt/aig-bank/.domain 2>/dev/null || echo "")}
if [ -z "$DOMAIN" ]; then
    log_error "Domain name not provided. Usage: $0 <domain.com>"
    exit 1
fi

log_info "Setting up AIG Bank on EC2 for domain: $DOMAIN"

# Change to app directory
cd /opt/aig-bank

# =============================================================================
# 1. Install Docker
# =============================================================================
log_info "Installing Docker CE with Buildx and Compose plugins..."

# Add Docker CE repository (CentOS compatible)
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Fix repository to use CentOS 9 (compatible with Amazon Linux 2023)
sudo sed -i 's/\$releasever/9/g' /etc/yum.repos.d/docker-ce.repo

# Install Docker CE with all plugins
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Verify installation
docker --version
docker buildx version
docker compose version

# =============================================================================
# 2. Generate Secure Secrets
# =============================================================================
log_info "Generating secure secrets..."

# Generate JWT secret (URL-safe base64, 32 bytes)
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Generate AES key (hex, 32 bytes = 64 chars)
AES_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Generate HMAC key (hex, 32 bytes = 64 chars)
HMAC_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Generate database password (URL-safe base64, 24 bytes)
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

log_info "Secrets generated successfully"

# =============================================================================
# 3. Create .env File
# =============================================================================
log_info "Creating .env file..."

cat > .env << EOF
# =============================================================================
# AIG Bank Production Environment Configuration
# =============================================================================
# Auto-generated on $(date)

# -----------------------------------------------------------------------------
# Domain Configuration
# -----------------------------------------------------------------------------
DOMAIN=${DOMAIN}

# -----------------------------------------------------------------------------
# PostgreSQL Database Configuration
# -----------------------------------------------------------------------------
POSTGRES_USER=bankuser
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=bankdb

# -----------------------------------------------------------------------------
# API Security Keys
# -----------------------------------------------------------------------------
JWT_SECRET_KEY=${JWT_SECRET}
AES_KEY=${AES_KEY}
HMAC_KEY=${HMAC_KEY}

# -----------------------------------------------------------------------------
# API Configuration
# -----------------------------------------------------------------------------
DEBUG=false
LOG_LEVEL=INFO

# -----------------------------------------------------------------------------
# JWT Token Configuration
# -----------------------------------------------------------------------------
JWT_EXPIRATION_MINUTES=60
JWT_REFRESH_EXPIRATION_DAYS=30
EOF

chmod 600 .env
log_info ".env file created with secure permissions"

# =============================================================================
# 4. Install and Configure Certbot
# =============================================================================
log_info "Installing Certbot..."
sudo yum install -y certbot

# Create certs directory if it doesn't exist
mkdir -p certs

# Check if certificates already exist
# Let's Encrypt creates directory named after the first domain (app.DOMAIN)
CERT_DIR="/etc/letsencrypt/live/app.${DOMAIN}"

if [ -d "$CERT_DIR" ]; then
    log_warn "Certificates already exist for ${DOMAIN}, skipping certificate generation"
else
    log_info "Obtaining Let's Encrypt certificates..."
    log_info "This requires DNS to be properly configured and pointing to this server"
    
    # Request certificate for all three subdomains
    # Note: We don't use pre/post hooks here because Docker isn't running yet
    sudo certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email admin@${DOMAIN} \
        --domains app.${DOMAIN},api.${DOMAIN},pay.${DOMAIN}
    
    if [ $? -eq 0 ]; then
        log_info "Certificates obtained successfully"
    else
        log_error "Failed to obtain certificates. Please check:"
        log_error "  1. DNS records are properly configured"
        log_error "  2. Ports 80 and 443 are accessible"
        log_error "  3. Domain names resolve to this server's IP"
        exit 1
    fi
fi

# Copy certificates to certs directory for nginx
# Let's Encrypt stores certs in a directory named after the first domain
log_info "Copying certificates to certs directory..."
log_info "Certificate directory: $CERT_DIR"

if [ ! -d "$CERT_DIR" ]; then
    log_error "Certificate directory not found: $CERT_DIR"
    log_error "Checking for alternative certificate locations..."
    
    # Try to find the certificate directory
    FOUND_CERT_DIR=$(sudo find /etc/letsencrypt/live -type d -name "*${DOMAIN}*" | head -1)
    if [ -n "$FOUND_CERT_DIR" ]; then
        log_warn "Found certificates at: $FOUND_CERT_DIR"
        CERT_DIR="$FOUND_CERT_DIR"
    else
        log_error "Could not locate certificate directory"
        exit 1
    fi
fi

sudo cp ${CERT_DIR}/fullchain.pem certs/cert.pem
sudo cp ${CERT_DIR}/privkey.pem certs/key.pem
sudo chown ec2-user:ec2-user certs/cert.pem certs/key.pem
sudo chmod 644 certs/cert.pem
sudo chmod 600 certs/key.pem

log_info "Certificates copied successfully"

# =============================================================================
# 5. Start Docker Compose Services
# =============================================================================
log_info "Starting Docker Compose services..."

# Use newgrp to apply docker group membership without logout
sg docker -c "docker compose up -d"

log_info "Waiting for services to start..."
sleep 10

# Check service status
log_info "Checking service status..."
sg docker -c "docker compose ps"

# =============================================================================
# 7. Display Summary
# =============================================================================
echo ""
echo "========================================================================="
echo "                    AIG Bank Setup Complete!"
echo "========================================================================="
echo ""
echo "Your application should be accessible at:"
echo "  - App:  https://app.${DOMAIN}"
echo "  - API:  https://api.${DOMAIN}"
echo "  - Pay:  https://pay.${DOMAIN}"
echo ""
echo "Important files:"
echo "  - Application:  /opt/aig-bank/"
echo "  - Environment:  /opt/aig-bank/.env"
echo "  - Certificates: /opt/aig-bank/certs/"
echo "  - Logs:         /opt/aig-bank/aig-bank-api/logs/"
echo ""
echo "Useful commands:"
echo "  - View logs:        cd /opt/aig-bank && docker compose logs -f"
echo "  - Restart services: cd /opt/aig-bank && docker compose restart"
echo "  - Stop services:    cd /opt/aig-bank && docker compose down"
echo "  - Start services:   cd /opt/aig-bank && docker compose up -d"
echo ""
echo "Certificates are valid for 90 days."
echo "========================================================================="
echo ""

log_info "Setup completed successfully!"


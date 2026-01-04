#!/bin/bash
# =============================================================================
# AIG Bank AWS Deployment Script
# =============================================================================
# This script orchestrates the complete deployment process:
# 1. Deploy CloudFormation stack (EC2, Security Groups, using default VPC)
# 2. Wait for stack creation to complete
# 3. Retrieve EC2 public IP
# 4. Configure Route53 DNS records (BEFORE certificates)
# 5. Wait for DNS propagation
# 6. Package and transfer source code via SCP
# 7. SSH into EC2 and run setup script (which obtains SSL certificates)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# =============================================================================
# Parse Command Line Arguments
# =============================================================================
ZONE=""
NAME=""
DOMAIN=""  # Computed from ZONE and NAME
SSH_KEY=""
YOUR_IP=""
STACK_NAME="aig-bank-stack"
INSTANCE_TYPE="t3.medium"
AWS_REGION="us-east-1"
AWS_PROFILE=""
DESTROY_MODE=false

usage() {
    cat << EOF
Usage: $0 [MODE] [OPTIONS]

Modes:
  (default)               Deploy the infrastructure
  --destroy               Destroy the infrastructure and cleanup

Required Arguments (for deployment):
  --zone <zone>           Route53 hosted zone (e.g., example.com)
  --ssh-key <key-name>    AWS SSH key pair name (must exist in region)
  --your-ip <ip/32>       Your IP address in CIDR notation (e.g., 1.2.3.4/32)

Optional Arguments:
  --name <name>           Environment/deployment name (e.g., prod, dev, staging)
                          If provided: app.NAME.ZONE, api.NAME.ZONE, pay.NAME.ZONE
                          If omitted: app.ZONE, api.ZONE, pay.ZONE
  --stack-name <name>     CloudFormation stack name (default: aig-bank-stack)
  --instance-type <type>  EC2 instance type (default: t3.medium)
  --region <region>       AWS region (default: us-east-1)
  --profile <profile>     AWS CLI profile to use (default: default profile)
  --help                  Show this help message

  DEPRECATED (still supported for backward compatibility):
  --domain <domain>       Use --zone instead (if used, --name is ignored)

Examples:
  # Deploy production environment
  $0 --zone example.com --name prod --ssh-key my-key --your-ip \$(curl -s ifconfig.me)/32
  # Results in: app.prod.example.com, api.prod.example.com, pay.prod.example.com

  # Deploy dev environment in same zone
  $0 --zone example.com --name dev --ssh-key my-key --your-ip \$(curl -s ifconfig.me)/32
  # Results in: app.dev.example.com, api.dev.example.com, pay.dev.example.com

  # Deploy without environment name (root of zone)
  $0 --zone example.com --ssh-key my-key --your-ip \$(curl -s ifconfig.me)/32
  # Results in: app.example.com, api.example.com, pay.example.com

  # With custom stack name and AWS profile
  $0 --profile production --stack-name bank-prod --zone example.com --name prod --ssh-key my-key --your-ip \$(curl -s ifconfig.me)/32

  # Destroy infrastructure
  $0 --destroy --stack-name aig-bank-stack --region us-east-1

  # Destroy with specific profile
  $0 --destroy --profile production --stack-name bank-prod
EOF
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --destroy)
            DESTROY_MODE=true
            shift
            ;;
        --zone)
            ZONE="$2"
            shift 2
            ;;
        --name)
            NAME="$2"
            shift 2
            ;;
        --domain)
            # Backward compatibility: --domain sets ZONE directly
            DOMAIN="$2"
            ZONE="$2"
            shift 2
            ;;
        --ssh-key)
            SSH_KEY="$2"
            shift 2
            ;;
        --your-ip)
            YOUR_IP="$2"
            shift 2
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --instance-type)
            INSTANCE_TYPE="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Compute DOMAIN from ZONE and NAME
if [ -z "$DOMAIN" ]; then
    if [ -n "$NAME" ]; then
        DOMAIN="${NAME}.${ZONE}"
    else
        DOMAIN="${ZONE}"
    fi
fi

# Set AWS profile if specified
if [ -n "$AWS_PROFILE" ]; then
    export AWS_PROFILE
    log_info "Using AWS profile: $AWS_PROFILE"
fi

# If destroy mode, run destroy and exit
if [ "$DESTROY_MODE" = true ]; then
    log_step "Running in DESTROY mode"
    log_warn "This will delete the CloudFormation stack: $STACK_NAME"
    log_warn "Region: $AWS_REGION"
    
    read -p "Are you sure you want to destroy this infrastructure? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Destroy cancelled"
        exit 0
    fi
    
    log_step "Destroying CloudFormation stack: $STACK_NAME"
    
    # Check if stack exists
    if ! aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" &> /dev/null; then
        log_error "Stack '$STACK_NAME' not found in region $AWS_REGION"
        exit 1
    fi
    
    # Delete the stack
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
    
    log_info "Stack deletion initiated. Waiting for completion..."
    
    # Wait for deletion to complete
    aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
    
    log_info "Stack '$STACK_NAME' deleted successfully"
    
    echo ""
    echo "========================================================================="
    echo "                    Cleanup Complete!"
    echo "========================================================================="
    echo ""
    echo "Stack '$STACK_NAME' has been deleted from region $AWS_REGION"
    echo ""
    echo "All resources deleted:"
    echo "  ✓ EC2 instance"
    echo "  ✓ Security groups"
    echo "  ✓ Route53 DNS records"
    echo ""
    echo "========================================================================="
    echo ""
    
    exit 0
fi

# Validate required arguments for deployment
if [ -z "$ZONE" ] || [ -z "$SSH_KEY" ] || [ -z "$YOUR_IP" ]; then
    log_error "Missing required arguments for deployment"
    log_error "Required: --zone, --ssh-key, --your-ip"
    usage
fi

# Display deployment configuration
log_info "Deployment Configuration:"
log_info "  Zone: $ZONE"
if [ -n "$NAME" ]; then
    log_info "  Name: $NAME"
    log_info "  Domain: $DOMAIN (computed as $NAME.$ZONE)"
else
    log_info "  Domain: $DOMAIN (using zone directly)"
fi
log_info "  Stack: $STACK_NAME"
log_info "  Region: $AWS_REGION"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# =============================================================================
# Pre-flight Checks
# =============================================================================
log_step "Running pre-flight checks..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

log_info "AWS CLI configured for account: $(aws sts get-caller-identity --query Account --output text)"

# Check if SSH key exists in AWS
if ! aws ec2 describe-key-pairs --key-names "$SSH_KEY" --region "$AWS_REGION" &> /dev/null; then
    log_error "SSH key pair '$SSH_KEY' not found in region $AWS_REGION"
    log_error "Create it with: aws ec2 create-key-pair --key-name $SSH_KEY --region $AWS_REGION"
    exit 1
fi

log_info "SSH key pair '$SSH_KEY' found in $AWS_REGION"

# Check if CloudFormation template exists
if [ ! -f "$SCRIPT_DIR/cloudformation-stack.yaml" ]; then
    log_error "CloudFormation template not found: $SCRIPT_DIR/cloudformation-stack.yaml"
    exit 1
fi

# =============================================================================
# Get Route53 Hosted Zone ID
# =============================================================================
log_step "Looking up Route53 Hosted Zone for: $ZONE"

HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
    --dns-name "$ZONE" \
    --query "HostedZones[?Name=='${ZONE}.'].Id" \
    --output text | cut -d'/' -f3)

if [ -z "$HOSTED_ZONE_ID" ]; then
    log_error "Hosted zone not found for: $ZONE"
    log_error "Please ensure the zone exists in Route53"
    log_error "You can create it with: aws route53 create-hosted-zone --name $ZONE --caller-reference $(date +%s)"
    exit 1
fi

log_info "Found Hosted Zone ID: $HOSTED_ZONE_ID"

# =============================================================================
# Get Default VPC and Subnet
# =============================================================================
log_step "Looking up default VPC and subnet in region: $AWS_REGION"

# Get default VPC ID
DEFAULT_VPC_ID=$(aws ec2 describe-vpcs \
    --region "$AWS_REGION" \
    --filters "Name=isDefault,Values=true" \
    --query "Vpcs[0].VpcId" \
    --output text)

if [ -z "$DEFAULT_VPC_ID" ] || [ "$DEFAULT_VPC_ID" = "None" ]; then
    log_error "No default VPC found in region $AWS_REGION"
    log_error "Please create a default VPC or specify a custom VPC"
    exit 1
fi

log_info "Found default VPC: $DEFAULT_VPC_ID"

# Get first available subnet in the default VPC
DEFAULT_SUBNET_ID=$(aws ec2 describe-subnets \
    --region "$AWS_REGION" \
    --filters "Name=vpc-id,Values=$DEFAULT_VPC_ID" \
    --query "Subnets[0].SubnetId" \
    --output text)

if [ -z "$DEFAULT_SUBNET_ID" ] || [ "$DEFAULT_SUBNET_ID" = "None" ]; then
    log_error "No subnets found in default VPC $DEFAULT_VPC_ID"
    exit 1
fi

log_info "Using subnet: $DEFAULT_SUBNET_ID"

# =============================================================================
# Deploy CloudFormation Stack
# =============================================================================
log_step "Deploying CloudFormation stack: $STACK_NAME"

aws cloudformation deploy \
    --template-file "$SCRIPT_DIR/cloudformation-stack.yaml" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        KeyPairName="$SSH_KEY" \
        VpcId="$DEFAULT_VPC_ID" \
        SubnetId="$DEFAULT_SUBNET_ID" \
        YourIPAddress="$YOUR_IP" \
        DomainName="$DOMAIN" \
        HostedZoneId="$HOSTED_ZONE_ID" \
        InstanceType="$INSTANCE_TYPE" \
    --capabilities CAPABILITY_IAM \
    --region "$AWS_REGION"

if [ $? -eq 0 ]; then
    log_info "CloudFormation stack deployed successfully"
else
    log_error "Failed to deploy CloudFormation stack"
    exit 1
fi

# =============================================================================
# Retrieve Stack Outputs
# =============================================================================
log_step "Retrieving stack outputs..."

EC2_PUBLIC_IP=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='EC2PublicIP'].OutputValue" \
    --output text)

EC2_INSTANCE_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='EC2InstanceId'].OutputValue" \
    --output text)

if [ -z "$EC2_PUBLIC_IP" ] || [ -z "$EC2_INSTANCE_ID" ]; then
    log_error "Failed to retrieve stack outputs"
    exit 1
fi

log_info "EC2 Public IP: $EC2_PUBLIC_IP"
log_info "EC2 Instance ID: $EC2_INSTANCE_ID"

# =============================================================================
# Wait for EC2 Instance to be Ready
# =============================================================================
log_step "Waiting for EC2 instance to be ready..."

aws ec2 wait instance-running \
    --instance-ids "$EC2_INSTANCE_ID" \
    --region "$AWS_REGION"

log_info "EC2 instance is running"

# Wait for status checks to pass
log_info "Waiting for status checks to pass (this may take a few minutes)..."
aws ec2 wait instance-status-ok \
    --instance-ids "$EC2_INSTANCE_ID" \
    --region "$AWS_REGION"

log_info "EC2 instance is ready"

# Additional wait for SSH to be available
log_info "Waiting for SSH to be available..."
sleep 30

# =============================================================================
# Wait for DNS Propagation
# =============================================================================
log_step "Waiting for DNS propagation..."

log_info "Route53 DNS records were created by CloudFormation"
log_info "Waiting 60 seconds for DNS propagation..."
log_info "This ensures Let's Encrypt can verify domain ownership"
sleep 60

# Verify DNS is resolving
log_info "Verifying DNS resolution..."
for SUBDOMAIN in app api pay; do
    FQDN="${SUBDOMAIN}.${DOMAIN}"
    if host "$FQDN" > /dev/null 2>&1; then
        RESOLVED_IP=$(host "$FQDN" | grep "has address" | awk '{print $4}' | head -1)
        if [ "$RESOLVED_IP" == "$EC2_PUBLIC_IP" ]; then
            log_info "✓ $FQDN → $EC2_PUBLIC_IP"
        else
            log_warn "⚠ $FQDN resolves to $RESOLVED_IP (expected: $EC2_PUBLIC_IP)"
            log_warn "DNS may not have fully propagated yet"
        fi
    else
        log_warn "⚠ $FQDN does not resolve yet"
        log_warn "You may need to wait longer for DNS propagation"
    fi
done

# =============================================================================
# Package Source Code
# =============================================================================
log_step "Packaging source code..."

cd "$PROJECT_ROOT"

# Create temporary archive excluding unnecessary files
TEMP_ARCHIVE="/tmp/aig-bank-deploy-$(date +%s).tar.gz"

log_info "Creating archive: $TEMP_ARCHIVE"

# Disable macOS extended attributes to avoid tar warnings
export COPYFILE_DISABLE=1

tar -czf "$TEMP_ARCHIVE" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='bank.db' \
    --exclude='logs' \
    --exclude='aig-bank-api/logs' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    --exclude='aws/.ssh' \
    .

ARCHIVE_SIZE=$(du -h "$TEMP_ARCHIVE" | cut -f1)
log_info "Archive created: $ARCHIVE_SIZE"

# =============================================================================
# Transfer Files via SCP
# =============================================================================
log_step "Transferring files to EC2 instance..."

SSH_KEY_PATH="$HOME/.ssh/${SSH_KEY}.pem"
if [ ! -f "$SSH_KEY_PATH" ]; then
    log_error "SSH key file not found: $SSH_KEY_PATH"
    log_error "Please ensure your SSH key is located at: $SSH_KEY_PATH"
    exit 1
fi

# Set correct permissions on SSH key
chmod 400 "$SSH_KEY_PATH"

# SSH options for non-interactive use
SSH_OPTS="-i $SSH_KEY_PATH -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

# Test SSH connectivity
log_info "Testing SSH connectivity..."
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if ssh $SSH_OPTS ec2-user@$EC2_PUBLIC_IP "echo 'SSH connection successful'" &> /dev/null; then
        log_info "SSH connection established"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_warn "SSH connection attempt $RETRY_COUNT/$MAX_RETRIES failed, retrying in 10 seconds..."
        sleep 10
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Failed to establish SSH connection after $MAX_RETRIES attempts"
    exit 1
fi

# Transfer archive
log_info "Uploading source code archive..."
scp $SSH_OPTS "$TEMP_ARCHIVE" ec2-user@$EC2_PUBLIC_IP:/tmp/aig-bank.tar.gz

# Extract archive on remote server
log_info "Extracting archive on EC2 instance..."
ssh $SSH_OPTS ec2-user@$EC2_PUBLIC_IP << 'ENDSSH'
    set -e
    sudo mkdir -p /opt/aig-bank
    sudo chown ec2-user:ec2-user /opt/aig-bank
    cd /opt/aig-bank
    tar -xzf /tmp/aig-bank.tar.gz
    rm /tmp/aig-bank.tar.gz
    echo "Files extracted successfully"
ENDSSH

# Clean up local archive
rm "$TEMP_ARCHIVE"
log_info "Source code transferred successfully"

# =============================================================================
# Transfer and Run Setup Script
# =============================================================================
log_step "Running EC2 setup script..."

# Make setup script executable
chmod +x "$SCRIPT_DIR/setup-ec2.sh"

# Transfer setup script
scp $SSH_OPTS "$SCRIPT_DIR/setup-ec2.sh" ec2-user@$EC2_PUBLIC_IP:/opt/aig-bank/setup-ec2.sh

# Run setup script on EC2
log_info "Executing setup script on EC2 instance..."
ssh $SSH_OPTS ec2-user@$EC2_PUBLIC_IP "cd /opt/aig-bank && bash setup-ec2.sh $DOMAIN"

if [ $? -eq 0 ]; then
    log_info "EC2 setup completed successfully"
else
    log_error "EC2 setup failed"
    exit 1
fi

# =============================================================================
# Remove Public HTTP/HTTPS Access After Certificate Setup
# =============================================================================
log_step "Securing HTTP/HTTPS access (removing public access)..."

# Get security group ID
SECURITY_GROUP_ID=$(aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`SecurityGroupId`].OutputValue' \
    --output text \
    $PROFILE_FLAG)

if [ -z "$SECURITY_GROUP_ID" ]; then
    log_error "Failed to retrieve security group ID"
    exit 1
fi

log_info "Security Group ID: $SECURITY_GROUP_ID"

# Remove the public HTTP rule (0.0.0.0/0)
log_info "Removing public HTTP access (0.0.0.0/0)..."
aws ec2 revoke-security-group-ingress \
    --region "$AWS_REGION" \
    --group-id "$SECURITY_GROUP_ID" \
    --ip-permissions IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges='[{CidrIp=0.0.0.0/0,Description="HTTP - Temporary for Lets Encrypt"}]' \
    $PROFILE_FLAG 2>/dev/null || log_info "Public HTTP rule already removed or not found"

# Remove the public HTTPS rule (0.0.0.0/0)
log_info "Removing public HTTPS access (0.0.0.0/0)..."
aws ec2 revoke-security-group-ingress \
    --region "$AWS_REGION" \
    --group-id "$SECURITY_GROUP_ID" \
    --ip-permissions IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges='[{CidrIp=0.0.0.0/0,Description="HTTPS - Temporary for Lets Encrypt"}]' \
    $PROFILE_FLAG 2>/dev/null || log_info "Public HTTPS rule already removed or not found"

log_info "HTTP/HTTPS access now restricted to Terra IPs and your IP only"

# =============================================================================
# Deployment Summary
# =============================================================================
echo ""
echo "========================================================================="
echo "                    Deployment Complete!"
echo "========================================================================="
echo ""
echo "Stack Information:"
echo "  Stack Name:      $STACK_NAME"
echo "  Region:          $AWS_REGION"
echo "  Instance ID:     $EC2_INSTANCE_ID"
echo "  Public IP:       $EC2_PUBLIC_IP"
echo ""
echo "Application URLs:"
echo "  App:  https://app.${DOMAIN}"
echo "  API:  https://api.${DOMAIN}/docs"
echo "  Pay:  https://pay.${DOMAIN}"
echo ""
echo "SSH Access:"
echo "  ssh -i ~/.ssh/${SSH_KEY}.pem ec2-user@${ELASTIC_IP}"
echo ""
echo "Important Notes:"
echo "  1. DNS propagation may take a few minutes"
echo "  2. SSL certificates are configured with Let's Encrypt"
echo "  3. Certificates will auto-renew every 90 days"
echo "  4. Application logs: /opt/aig-bank/aig-bank-api/logs/"
echo "  5. Environment file: /opt/aig-bank/.env"
echo "  6. ⚠️  Public IP is NOT static - it will change if you stop/start the instance"
echo ""
echo "Useful Commands:"
echo "  View logs:        ssh -i ~/.ssh/${SSH_KEY}.pem ec2-user@${ELASTIC_IP} 'cd /opt/aig-bank && docker compose logs -f'"
echo "  Restart services: ssh -i ~/.ssh/${SSH_KEY}.pem ec2-user@${ELASTIC_IP} 'cd /opt/aig-bank && docker compose restart'"
echo "  Check status:     ssh -i ~/.ssh/${SSH_KEY}.pem ec2-user@${ELASTIC_IP} 'cd /opt/aig-bank && docker compose ps'"
echo ""
echo "To delete the stack:"
echo "  aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION"
echo ""
echo "========================================================================="
echo ""

log_info "Deployment completed successfully!"


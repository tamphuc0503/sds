#!/bin/bash
# Quick setup script for environment variables

echo "Setting up environment variables for SDS Docker project..."
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo "✓ .env file already exists"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "Keeping existing .env file"
        exit 0
    fi
fi

# Copy from example
if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "✓ Created .env from .env.example"
else
    echo "✗ .env.example not found"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Environment Variables Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Prompt for SECRET_KEY
read -p "Enter SECRET_KEY (press Enter to generate random): " secret_key
if [ -z "$secret_key" ]; then
    secret_key=$(openssl rand -base64 32 | tr -d '\n')
    echo "Generated SECRET_KEY: $secret_key"
fi
sed -i "s|SECRET_KEY=.*|SECRET_KEY=$secret_key|" .env

# Prompt for DEBUG
read -p "Enable DEBUG mode? (Y/n): " debug_mode
if [ "$debug_mode" = "n" ] || [ "$debug_mode" = "N" ]; then
    sed -i "s|DEBUG=.*|DEBUG=False|" .env
else
    sed -i "s|DEBUG=.*|DEBUG=True|" .env
fi

# Prompt for ALLOWED_HOSTS
read -p "Enter ALLOWED_HOSTS (comma-separated, default: *): " allowed_hosts
if [ ! -z "$allowed_hosts" ]; then
    sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$allowed_hosts|" .env
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AWS S3 Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Current AWS settings are already configured in .env.example"
read -p "Do you want to update AWS credentials? (y/N): " update_aws
if [ "$update_aws" = "y" ] || [ "$update_aws" = "Y" ]; then
    read -p "AWS Access Key ID: " aws_key
    read -p "AWS Secret Access Key: " aws_secret
    read -p "AWS Region (default: usc1): " aws_region
    read -p "AWS Bucket Name (default: sds): " aws_bucket
    
    [ ! -z "$aws_key" ] && sed -i "s|AWS_ACCESS_KEY_ID=.*|AWS_ACCESS_KEY_ID=$aws_key|" .env
    [ ! -z "$aws_secret" ] && sed -i "s|AWS_SECRET_ACCESS_KEY=.*|AWS_SECRET_ACCESS_KEY=$aws_secret|" .env
    [ ! -z "$aws_region" ] && sed -i "s|AWS_REGION=.*|AWS_REGION=$aws_region|" .env
    [ ! -z "$aws_bucket" ] && sed -i "s|AWS_BUCKET_NAME=.*|AWS_BUCKET_NAME=$aws_bucket|" .env
fi

echo ""
echo "✓ Environment variables configured successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Review your .env file:"
echo "   cat .env"
echo ""
echo "2. Start Docker containers:"
echo "   docker-compose -f .docker/docker-compose.yml up -d"
echo ""
echo "3. Or use the setup script:"
echo "   ./docker-setup.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

#!/bin/bash
# Local Agent Setup Script
# Sets up the local agent on user's machine

set -e

echo "=== Local Agent Setup ==="
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)     PLATFORM=linux;;
    Darwin*)    PLATFORM=mac;;
    MINGW*|MSYS*|CYGWIN*)    PLATFORM=windows;;
    *)          PLATFORM=unknown;;
esac

echo "Detected platform: $PLATFORM"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_CMD="python3"
if [ "$PLATFORM" = "windows" ]; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if Python 3.9+
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "Error: Python 3.9+ required (found $PYTHON_VERSION)"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r local_agent/requirements.txt
$PYTHON_CMD -m pip install -r shared/requirements.txt

# Install Node.js dependencies for MCP servers
echo "Installing Node.js dependencies..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "Node.js version: $NODE_VERSION"

    cd mcp_servers/email_mcp && npm install && cd ../..
    cd mcp_servers/social_mcp && npm install && cd ../..

    echo "Node.js dependencies installed"
else
    echo "Warning: Node.js not found. MCP servers will not work."
    echo "Install Node.js 18+ from https://nodejs.org/"
fi

# Install Playwright for WhatsApp
echo "Installing Playwright..."
$PYTHON_CMD -m playwright install chromium

# Create vault directory
echo "Creating vault directory..."
mkdir -p vault/Needs_Action
mkdir -p vault/In_Progress/cloud
mkdir -p vault/In_Progress/local
mkdir -p vault/Pending_Approval/email
mkdir -p vault/Pending_Approval/social
mkdir -p vault/Pending_Approval/accounting
mkdir -p vault/Pending_Approval/whatsapp
mkdir -p vault/Approved
mkdir -p vault/Rejected
mkdir -p vault/Done
mkdir -p vault/Plans
mkdir -p vault/Logs
mkdir -p vault/Updates

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your credentials"
fi

# Create credentials directory
mkdir -p credentials

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Configure Gmail API credentials in credentials/"
echo "3. Configure vault sync (Git or Syncthing)"
echo "4. Run: python -m local_agent.src.agent"
echo ""

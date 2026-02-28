#!/bin/bash
# Cloud Agent Deployment Script
# Deploys the cloud agent to a cloud VM

set -e

echo "=== Cloud Agent Deployment ==="
echo ""

# Configuration
DEPLOY_USER="${DEPLOY_USER:-ubuntu}"
DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/ai-employee}"
PYTHON_VERSION="3.9"

# Check required variables
if [ -z "$DEPLOY_HOST" ]; then
    echo "Error: DEPLOY_HOST environment variable not set"
    echo "Usage: DEPLOY_HOST=your-vm-ip ./deploy_cloud_agent.sh"
    exit 1
fi

echo "Deploying to: $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH"
echo ""

# Create deployment directory
echo "Creating deployment directory..."
ssh "$DEPLOY_USER@$DEPLOY_HOST" "mkdir -p $DEPLOY_PATH"

# Copy files
echo "Copying files..."
rsync -avz --exclude='*.pyc' --exclude='__pycache__' \
    --exclude='.git' --exclude='vault' --exclude='credentials' \
    cloud_agent/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/cloud_agent/"

rsync -avz --exclude='*.pyc' --exclude='__pycache__' \
    shared/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/shared/"

rsync -avz --exclude='*.pyc' --exclude='__pycache__' \
    orchestration/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/orchestration/"

rsync -avz --exclude='node_modules' \
    mcp_servers/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/mcp_servers/"

rsync -avz \
    config/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/config/"

# Install dependencies
echo "Installing dependencies..."
ssh "$DEPLOY_USER@$DEPLOY_HOST" << 'EOF'
cd /opt/ai-employee

# Install Python dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r cloud_agent/requirements.txt
python3 -m pip install -r shared/requirements.txt 2>/dev/null || true

# Install Node.js dependencies for MCP servers
cd mcp_servers/email_mcp && npm install && cd ../..

echo "Dependencies installed"
EOF

# Setup systemd service
echo "Setting up systemd service..."
ssh "$DEPLOY_USER@$DEPLOY_HOST" "sudo tee /etc/systemd/system/cloud-agent.service" << 'EOF'
[Unit]
Description=AI Employee Cloud Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/ai-employee
Environment="PYTHONPATH=/opt/ai-employee"
Environment="AGENT_TYPE=cloud"
EnvironmentFile=/opt/ai-employee/.env
ExecStart=/usr/bin/python3 -m cloud_agent.src.agent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
ssh "$DEPLOY_USER@$DEPLOY_HOST" << 'EOF'
sudo systemctl daemon-reload
sudo systemctl enable cloud-agent
echo "Systemd service configured"
EOF

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Copy .env file to $DEPLOY_HOST:$DEPLOY_PATH/.env"
echo "2. Configure vault sync (Git or Syncthing)"
echo "3. Start the service: ssh $DEPLOY_USER@$DEPLOY_HOST 'sudo systemctl start cloud-agent'"
echo "4. Check status: ssh $DEPLOY_USER@$DEPLOY_HOST 'sudo systemctl status cloud-agent'"
echo ""

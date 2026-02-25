#!/bin/bash
# Installation script for Platinum Tier AI Employee
# Run this from the project root directory

set -e

echo "========================================"
echo "Platinum Tier AI Employee - Setup"
echo "========================================"
echo ""

echo "[1/4] Installing Python dependencies..."
echo ""

echo "Installing shared package..."
cd shared
pip install -r requirements.txt
cd ..

echo "Installing cloud agent..."
cd cloud_agent
pip install -r requirements.txt
cd ..

echo "Installing local agent..."
cd local_agent
pip install -r requirements.txt
cd ..

echo ""
echo "[2/4] Installing Node.js dependencies..."
echo ""

echo "Installing Email MCP server..."
cd mcp_servers/email_mcp
npm install
cd ../..

echo ""
echo "[3/4] Testing configuration..."
echo ""

python test_config.py
python test_local_agent.py

echo ""
echo "[4/4] Setup complete!"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. Set up Gmail API credentials:"
echo "   - Place gmail_credentials.json in credentials/ folder"
echo "   - Run authentication flow to generate gmail_token.json"
echo ""
echo "2. Configure environment variables:"
echo "   - Copy config/.env.example to .env"
echo "   - Edit .env with your credentials"
echo ""
echo "3. Start the system:"
echo "   Terminal 1: cd mcp_servers/email_mcp && npm start"
echo "   Terminal 2: cd cloud_agent && python src/agent.py"
echo "   Terminal 3: cd local_agent && python src/agent.py"
echo ""
echo "See QUICKSTART_FIXED.md for detailed instructions."
echo ""

# Quickstart Guide: Platinum Tier AI Employee

**Version**: 1.0.0
**Date**: 2026-02-25
**Estimated Setup Time**: 2-4 hours

## Overview

This guide walks you through setting up the Platinum Tier AI Employee system from scratch. By the end, you'll have a cloud agent running 24/7 on a cloud VM, a local agent on your machine, and Odoo Community Edition for accounting integration.

## Prerequisites

### Required
- Python 3.9+ installed on local machine
- Node.js 18+ installed on local machine
- Git installed and configured
- Gmail account with API access enabled
- Cloud VM account (Oracle Cloud Free Tier recommended)
- Basic understanding of command line and Git

### Optional
- Obsidian installed (for viewing vault)
- WhatsApp Web access
- Bank account with transaction export capability

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Cloud VM (24/7)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Cloud Agent  │  │ Gmail Watcher│  │ Odoo Server  │     │
│  │ (Drafting)   │  │ (Monitoring) │  │ (Accounting) │     │
│  └──────┬───────┘  └──────────────┘  └──────────────┘     │
│         │                                                    │
│         │ Writes drafts to vault                           │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Synced Vault (Git/Syncthing)               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ Sync
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Local Machine (User)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Synced Vault (Git/Syncthing)               │  │
│  └──────────────────────────────────────────────────────┘  │
│         │                                                    │
│         │ Reads approvals, executes actions                │
│         ▼                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Local Agent  │  │ WhatsApp     │  │ Finance      │     │
│  │ (Execution)  │  │ Watcher      │  │ Watcher      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Local Setup (30 minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/ai-employee.git
cd ai-employee
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install local agent dependencies
cd local_agent
pip install -r requirements.txt
cd ..

# Install shared dependencies
cd shared
pip install -r requirements.txt
cd ..

# Install MCP servers
cd mcp_servers/odoo_mcp
pip install -r requirements.txt
cd ../..
```

### Step 4: Initialize Vault

```bash
# Create vault directory structure
mkdir -p vault/{Needs_Action/{email,social,accounting,whatsapp},In_Progress/{cloud,local},Pending_Approval/{email,social,accounting,whatsapp},Approved,Rejected,Done,Plans,Logs,Updates}

# Create initial files
touch vault/Dashboard.md
touch vault/Company_Handbook.md
touch vault/Business_Goals.md

# Initialize Git repository in vault
cd vault
git init
git add .
git commit -m "Initial vault structure"
cd ..
```

### Step 5: Configure Environment Variables

```bash
# Copy example .env file
cp config/.env.example .env

# Edit .env file with your credentials
# IMPORTANT: Never commit .env to version control
```

**Required environment variables**:
```bash
# Gmail API (for cloud agent)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

# Odoo (for cloud agent)
ODOO_URL=https://your-odoo-instance.com
ODOO_DATABASE=your_database
ODOO_USERNAME=your_username
ODOO_API_KEY=your_api_key

# WhatsApp (for local agent)
WHATSAPP_SESSION_PATH=/path/to/whatsapp/session

# Banking (for local agent)
BANK_API_TOKEN=your_bank_api_token
```

### Step 6: Configure Git Sync

```bash
# Create remote repository for vault sync
# Option A: GitHub
gh repo create ai-employee-vault --private
cd vault
git remote add origin https://github.com/yourusername/ai-employee-vault.git
git push -u origin main
cd ..

# Option B: GitLab
# Similar process with GitLab CLI or web interface
```

### Step 7: Test Local Agent

```bash
# Run local agent in test mode
cd local_agent
python src/agent.py --test

# Expected output:
# ✓ Local agent started
# ✓ WhatsApp watcher initialized
# ✓ Finance watcher initialized
# ✓ Vault sync configured
# ✓ MCP servers connected
```

## Phase 2: Cloud VM Setup (60 minutes)

### Step 1: Provision Cloud VM

**Oracle Cloud Free Tier**:
1. Sign up at https://cloud.oracle.com/free
2. Create VM instance:
   - Shape: VM.Standard.A1.Flex (Arm-based, 1 OCPU, 6GB RAM)
   - OS: Ubuntu 22.04 LTS
   - Network: Allow HTTPS (443) and SSH (22)
3. Note the public IP address

**Alternative providers**:
- AWS: t2.micro (1 vCPU, 1GB RAM) - 12 months free
- Azure: B1s (1 vCPU, 1GB RAM) - 12 months free
- GCP: e2-micro (0.25 vCPU, 1GB RAM) - always free (too small for Odoo)

### Step 2: Connect to Cloud VM

```bash
# SSH into cloud VM
ssh ubuntu@<your-vm-ip>

# Update system
sudo apt update && sudo apt upgrade -y
```

### Step 3: Install Dependencies on Cloud VM

```bash
# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip -y

# Install Git
sudo apt install git -y

# Install PostgreSQL (for Odoo)
sudo apt install postgresql postgresql-contrib -y

# Install Node.js 18+ (for MCP servers)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

### Step 4: Clone Repository on Cloud VM

```bash
# Clone repository
git clone https://github.com/yourusername/ai-employee.git
cd ai-employee

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install cloud agent dependencies
cd cloud_agent
pip install -r requirements.txt
cd ..
```

### Step 5: Configure Vault Sync on Cloud VM

```bash
# Clone vault repository
git clone https://github.com/yourusername/ai-employee-vault.git vault

# Configure Git credentials
git config --global user.name "Cloud Agent"
git config --global user.email "cloud@ai-employee.local"

# Set up SSH key for passwordless push
ssh-keygen -t ed25519 -C "cloud@ai-employee.local"
cat ~/.ssh/id_ed25519.pub
# Add this public key to GitHub/GitLab deploy keys
```

### Step 6: Configure Environment Variables on Cloud VM

```bash
# Create .env file
nano .env

# Add cloud agent credentials (Gmail only, no sensitive credentials)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token

ODOO_URL=https://localhost:8069
ODOO_DATABASE=production
ODOO_USERNAME=admin@example.com
ODOO_API_KEY=your_api_key
```

### Step 7: Test Cloud Agent

```bash
# Run cloud agent in test mode
cd cloud_agent
python src/agent.py --test

# Expected output:
# ✓ Cloud agent started
# ✓ Gmail watcher initialized
# ✓ Vault sync configured
# ✓ Odoo connection verified
```

## Phase 3: Odoo Deployment (60 minutes)

### Step 1: Install Odoo Community Edition

```bash
# Add Odoo repository
wget -O - https://nightly.odoo.com/odoo.key | sudo gpg --dearmor -o /usr/share/keyrings/odoo-archive-keyring.gpg
echo 'deb [signed-by=/usr/share/keyrings/odoo-archive-keyring.gpg] https://nightly.odoo.com/19.0/nightly/deb/ ./' | sudo tee /etc/apt/sources.list.d/odoo.list

# Install Odoo
sudo apt update
sudo apt install odoo -y
```

### Step 2: Configure PostgreSQL

```bash
# Create Odoo database user
sudo -u postgres createuser -s odoo

# Create Odoo database
sudo -u postgres createdb production -O odoo
```

### Step 3: Configure Odoo

```bash
# Edit Odoo configuration
sudo nano /etc/odoo/odoo.conf

# Update configuration:
[options]
admin_passwd = your_master_password
db_host = localhost
db_port = 5432
db_user = odoo
db_password = False
addons_path = /usr/lib/python3/dist-packages/odoo/addons
```

### Step 4: Start Odoo Service

```bash
# Start Odoo
sudo systemctl start odoo

# Enable Odoo to start on boot
sudo systemctl enable odoo

# Check status
sudo systemctl status odoo
```

### Step 5: Configure HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Install Nginx
sudo apt install nginx -y

# Configure Nginx for Odoo
sudo nano /etc/nginx/sites-available/odoo

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### Step 6: Initialize Odoo Database

```bash
# Access Odoo web interface
# Navigate to https://your-domain.com

# Create database:
# - Database name: production
# - Email: admin@example.com
# - Password: your_password
# - Language: English
# - Country: Your country

# Install Accounting module
# Apps > Search "Accounting" > Install
```

### Step 7: Configure Odoo API Access

```bash
# In Odoo web interface:
# Settings > Users & Companies > Users
# Select admin user
# Generate API key
# Copy API key to .env file on cloud VM
```

## Phase 4: Process Management (30 minutes)

### Step 1: Configure Orchestrator

```bash
# On cloud VM
cd orchestration
cp config/cloud_processes.yaml.example config/cloud_processes.yaml

# Edit process configuration
nano config/cloud_processes.yaml
```

### Step 2: Configure Watchdog

```bash
# On cloud VM
nano orchestration/watchdog.py

# Configure processes to monitor:
# - cloud_agent
# - gmail_watcher
# - odoo
```

### Step 3: Start Orchestrator and Watchdog

```bash
# On cloud VM
cd orchestration

# Start orchestrator in background
nohup python orchestrator.py > orchestrator.log 2>&1 &

# Start watchdog in background
nohup python watchdog.py > watchdog.log 2>&1 &

# Verify processes are running
ps aux | grep -E "orchestrator|watchdog"
```

### Step 4: Configure Local Orchestrator

```bash
# On local machine
cd orchestration
cp config/local_processes.yaml.example config/local_processes.yaml

# Edit process configuration
nano config/local_processes.yaml

# Start orchestrator
python orchestrator.py
```

## Phase 5: Testing (30 minutes)

### Test 1: Email Detection and Drafting

```bash
# Send test email to your Gmail account
# Subject: "Test Invoice Request"
# Body: "Can you send me the invoice for January?"

# Wait 2 minutes for cloud agent to detect

# Check vault for action file
ls vault/Needs_Action/email/

# Check vault for draft approval
ls vault/Pending_Approval/email/

# Expected: Draft email reply in Pending_Approval/email/
```

### Test 2: Approval Workflow

```bash
# Move approval file to Approved folder
mv vault/Pending_Approval/email/email_send_*.md vault/Approved/

# Wait 1 minute for local agent to execute

# Check email was sent
# Check vault/Done/ for completed action
ls vault/Done/

# Check vault/Logs/ for audit entry
cat vault/Logs/$(date +%Y-%m-%d).md
```

### Test 3: Vault Sync

```bash
# On local machine
cd vault
git pull

# Verify cloud agent updates are synced
ls Updates/

# On cloud VM
cd vault
git pull

# Verify local agent actions are synced
ls Done/
```

### Test 4: Odoo Integration

```bash
# Create test transaction file
cat > vault/Needs_Action/accounting/transaction_test_$(date +%Y%m%dT%H%M%S)Z.md << EOF
---
id: test-001
type: transaction
source: Bank Account ****1234
priority: medium
status: pending
created: $(date -Iseconds)
domain: accounting
metadata:
  amount: 100.00
  account: "****1234"
  description: "Test Payment"
  date: $(date +%Y-%m-%d)
  category: income
---

## Transaction Details

Test payment of $100.

## Suggested Actions
- [ ] Draft Odoo entry
- [ ] Send for approval
EOF

# Wait for cloud agent to process
# Check Pending_Approval/accounting/ for draft entry
ls vault/Pending_Approval/accounting/

# Approve entry
mv vault/Pending_Approval/accounting/accounting_entry_*.md vault/Approved/

# Wait for local agent to post to Odoo
# Check Odoo web interface for new entry
```

## Phase 6: Production Configuration (30 minutes)

### Step 1: Configure Business Goals

```bash
# Edit Business_Goals.md
nano vault/Business_Goals.md

# Add your business goals, metrics, and targets
```

### Step 2: Configure Company Handbook

```bash
# Edit Company_Handbook.md
nano vault/Company_Handbook.md

# Add your business rules, tone guidelines, and context
```

### Step 3: Configure Rate Limiting

```bash
# Edit local agent config
nano local_agent/src/config.py

# Set rate limits:
# MAX_EMAILS_PER_HOUR = 10
# MAX_PAYMENTS_PER_HOUR = 3
```

### Step 4: Enable All Watchers

```bash
# On cloud VM
# Enable Gmail watcher
nano cloud_agent/src/config.py
# Set GMAIL_WATCHER_ENABLED = True

# On local machine
# Enable WhatsApp watcher
nano local_agent/src/config.py
# Set WHATSAPP_WATCHER_ENABLED = True

# Enable Finance watcher
# Set FINANCE_WATCHER_ENABLED = True
```

### Step 5: Configure Backup

```bash
# On cloud VM
# Configure Odoo database backup
sudo nano /etc/cron.daily/odoo-backup

# Add backup script:
#!/bin/bash
pg_dump production | gzip > /backup/odoo-$(date +%Y%m%d).sql.gz
find /backup -name "odoo-*.sql.gz" -mtime +30 -delete

# Make executable
sudo chmod +x /etc/cron.daily/odoo-backup
```

## Troubleshooting

### Cloud Agent Not Detecting Emails

**Check**:
1. Gmail API credentials are correct
2. Gmail watcher is running: `ps aux | grep gmail_watcher`
3. Check logs: `tail -f cloud_agent/logs/agent.log`

**Fix**:
```bash
# Restart cloud agent
pkill -f cloud_agent
cd cloud_agent && python src/agent.py &
```

### Vault Sync Failing

**Check**:
1. Git credentials are configured
2. SSH key is added to GitHub/GitLab
3. Check sync logs: `tail -f vault/.git/logs/HEAD`

**Fix**:
```bash
# Manual sync
cd vault
git pull --rebase
git push
```

### Odoo Connection Error

**Check**:
1. Odoo service is running: `sudo systemctl status odoo`
2. Odoo API key is correct
3. Check Odoo logs: `sudo tail -f /var/log/odoo/odoo-server.log`

**Fix**:
```bash
# Restart Odoo
sudo systemctl restart odoo
```

### Local Agent Not Executing Approvals

**Check**:
1. Local agent is running: `ps aux | grep local_agent`
2. Approved folder is being monitored
3. Check logs: `tail -f local_agent/logs/agent.log`

**Fix**:
```bash
# Restart local agent
pkill -f local_agent
cd local_agent && python src/agent.py &
```

## Next Steps

1. **Monitor System**: Check Dashboard.md daily for system health
2. **Review Approvals**: Review pending approvals daily (target: < 30 minutes)
3. **Audit Logs**: Review audit logs weekly for anomalies
4. **Optimize Drafts**: Provide feedback on rejected drafts to improve quality
5. **Scale Up**: Add more watchers and integrations as needed

## Support

- **Documentation**: See `/docs` folder for detailed guides
- **Issues**: Report issues at https://github.com/yourusername/ai-employee/issues
- **Community**: Join discussions at https://github.com/yourusername/ai-employee/discussions

## Security Checklist

- [ ] .env file is in .gitignore
- [ ] Vault sync excludes secrets (.env, *.session, *.credentials)
- [ ] Odoo is accessed via HTTPS only
- [ ] Cloud agent has no sensitive credentials
- [ ] Local agent credentials are stored securely
- [ ] Pre-commit hooks are configured for secret detection
- [ ] Audit logs are enabled and retained for 90 days
- [ ] Rate limiting is configured
- [ ] Approval workflow is enforced (no bypasses)

## Performance Checklist

- [ ] Cloud agent detects emails within 2 minutes
- [ ] Vault sync completes within 10 seconds
- [ ] Local agent executes approvals within 1 minute
- [ ] Dashboard updates within 60 seconds
- [ ] Watchdog restarts failed processes within 60 seconds
- [ ] Memory usage < 500MB per agent
- [ ] Disk usage < 1GB for vault

## Congratulations!

You now have a fully functional Platinum Tier AI Employee system running 24/7. The cloud agent monitors your email and drafts responses, while the local agent handles approvals and executes actions. Odoo integration provides accounting automation, and the approval workflow ensures safety and control.

**Estimated Time Savings**:
- Email response time: 80% reduction
- Social media content creation: 70% reduction
- Financial data entry: 90% reduction
- Daily approval time: < 30 minutes

**Next milestone**: Run the system for 7 days and review the weekly business briefing to see insights and recommendations.

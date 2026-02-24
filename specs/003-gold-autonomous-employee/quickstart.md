# Quickstart Guide: Gold Tier - Autonomous Employee

**Feature**: 003-gold-autonomous-employee
**Date**: 2026-02-23
**Prerequisites**: Bronze and Silver Tiers fully implemented and tested

## Overview

Gold Tier transforms your Personal AI Employee into an autonomous business intelligence advisor with:
- Odoo accounting integration for automated bookkeeping
- Multi-platform social media management (Facebook, Instagram, Twitter)
- Weekly business audits with CEO briefings
- Multiple MCP servers for domain separation
- Ralph Wiggum autonomous loop for multi-step workflows
- Comprehensive error recovery and graceful degradation

**Estimated Setup Time**: 4-6 hours
**Estimated Implementation Time**: 40+ hours

---

## Prerequisites Checklist

Before starting Gold Tier implementation, verify:

### Bronze Tier (Required)
- [ ] FileSystem watcher operational
- [ ] Inbox→Needs_Action→Done workflow functional
- [ ] Claude Code processes tasks
- [ ] Dashboard updates automatically
- [ ] No external APIs required

### Silver Tier (Required)
- [ ] Gmail watcher integrated
- [ ] WhatsApp integration working
- [ ] LinkedIn posting functional
- [ ] Email classification working
- [ ] Human approval flow for sends
- [ ] Scheduling system operational
- [ ] MCP server running (communications)

### System Requirements
- [ ] Python 3.9+ installed
- [ ] Obsidian vault configured
- [ ] Git repository initialized
- [ ] `.env` file for secrets (not in git)
- [ ] 1.5GB+ RAM available
- [ ] 10GB+ disk space available

---

## Phase 1: External Service Setup (2-3 hours)

### 1.1 Odoo Community Installation

**Install Odoo locally** (choose one method):

**Option A: Docker (Recommended)**
```bash
# Pull Odoo 19 image
docker pull odoo:19

# Create PostgreSQL container
docker run -d -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres --name db postgres:15

# Create Odoo container
docker run -d -p 8069:8069 --name odoo --link db:db -t odoo:19
```

**Option B: Native Installation**
- Follow official Odoo installation guide: https://www.odoo.com/documentation/19.0/administration/install.html
- Install PostgreSQL 15+
- Install Odoo 19 Community Edition
- Configure database

**Verify Installation**:
1. Open browser to http://localhost:8069
2. Create database named `business_db`
3. Install Accounting module
4. Create admin user

**Configure Accounting**:
1. Go to Accounting → Configuration → Settings
2. Enable "Invoicing" and "Expenses"
3. Configure chart of accounts (use default)
4. Create at least one customer and one vendor for testing

**Test JSON-RPC Access**:
```python
import odoorpc

odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('business_db', 'admin', 'admin')
print(f"Connected to Odoo: {odoo.env.uid}")
```

### 1.2 Facebook/Instagram Setup

**Create Facebook App**:
1. Go to https://developers.facebook.com/
2. Create new app → Business type
3. Add "Instagram Graph API" product
4. Add "Facebook Login" product

**Configure Permissions**:
- `pages_manage_posts` (Facebook posting)
- `pages_read_engagement` (Facebook metrics)
- `instagram_basic` (Instagram access)
- `instagram_content_publish` (Instagram posting)

**Get Access Tokens**:
1. Use Graph API Explorer to generate user access token
2. Exchange for long-lived token (60 days):
```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN"
```
3. Get page access token:
```bash
curl -X GET "https://graph.facebook.com/v18.0/me/accounts?access_token=LONG_LIVED_USER_TOKEN"
```

**Connect Instagram Business Account**:
1. Create Facebook Page (if not exists)
2. Convert Instagram account to Business account
3. Connect Instagram to Facebook Page
4. Get Instagram account ID:
```bash
curl -X GET "https://graph.facebook.com/v18.0/PAGE_ID?fields=instagram_business_account&access_token=PAGE_ACCESS_TOKEN"
```

**Test Access**:
```python
import requests

# Test Facebook
url = f"https://graph.facebook.com/v18.0/{page_id}"
params = {'fields': 'name,fan_count', 'access_token': access_token}
response = requests.get(url, params=params)
print(f"Facebook Page: {response.json()}")

# Test Instagram
url = f"https://graph.facebook.com/v18.0/{instagram_account_id}"
params = {'fields': 'username,followers_count', 'access_token': access_token}
response = requests.get(url, params=params)
print(f"Instagram Account: {response.json()}")
```

### 1.3 Twitter (X) Setup

**Create Twitter Developer Account**:
1. Go to https://developer.twitter.com/
2. Apply for Developer account (Elevated access recommended)
3. Create new app in Developer Portal

**Generate Credentials**:
1. Go to app settings → Keys and tokens
2. Generate API Key and Secret (Consumer Key/Secret)
3. Generate Access Token and Secret
4. Generate Bearer Token

**Test Access**:
```python
import tweepy

client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret
)

# Test authentication
user = client.get_user(username='your_username')
print(f"Twitter Account: {user.data.name} (@{user.data.username})")
```

### 1.4 Environment Variables

**Create/Update `.env` file**:
```bash
# Existing (Bronze/Silver)
GMAIL_CREDENTIALS_PATH=path/to/credentials.json
GMAIL_TOKEN_PATH=path/to/token.json
LINKEDIN_ACCESS_TOKEN=your_linkedin_token
WHATSAPP_PHONE_NUMBER=your_phone_number

# Gold Tier - Odoo
ODOO_HOST=localhost
ODOO_PORT=8069
ODOO_DB=business_db
ODOO_USER=admin
ODOO_PASSWORD=secure_password

# Gold Tier - Facebook/Instagram
FACEBOOK_ACCESS_TOKEN=your_long_lived_page_access_token
FACEBOOK_PAGE_ID=your_page_id
INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id

# Gold Tier - Twitter
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
```

**Security Check**:
```bash
# Verify .env is in .gitignore
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore

# Verify .env is not tracked
git status | grep -q ".env" && echo "WARNING: .env is tracked in git!" || echo "OK: .env not tracked"
```

---

## Phase 2: Install Dependencies (15 minutes)

### 2.1 Update requirements.txt

Add Gold Tier dependencies:
```bash
# Gold Tier - Odoo Integration
odoorpc>=0.10.1

# Gold Tier - Social Media
requests>=2.31.0
tweepy>=4.14.0

# Gold Tier - Error Recovery
tenacity>=8.2.0
pybreaker>=1.0.0

# Already present (verify versions)
APScheduler>=3.10.0
python-dotenv>=1.0.0
watchdog>=3.0.0
frontmatter>=1.0.0
markdown>=3.4.0
pytest>=7.4.0
```

### 2.2 Install Dependencies

```bash
# Activate virtual environment (if using)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installations
python -c "import odoorpc; print(f'odoorpc: {odoorpc.__version__}')"
python -c "import tweepy; print(f'tweepy: {tweepy.__version__}')"
python -c "import tenacity; print(f'tenacity: {tenacity.__version__}')"
python -c "import pybreaker; print(f'pybreaker: {pybreaker.__version__}')"
```

---

## Phase 3: Vault Structure Setup (10 minutes)

### 3.1 Create Gold Tier Folders

```bash
cd AI_Employee_Vault

# Create new folders for Gold Tier
mkdir -p Accounting/transactions
mkdir -p Social_Media/posts
mkdir -p Audits/weekly
mkdir -p Workflows/executions
mkdir -p Workflows/plans
mkdir -p System/mcp_servers
mkdir -p Logs/error_recovery
mkdir -p Action_Queue
mkdir -p Circuit_State

echo "Gold Tier vault structure created"
```

### 3.2 Verify Vault Structure

```bash
# Expected structure
tree -L 2 AI_Employee_Vault

# Should show:
# AI_Employee_Vault/
# ├── Inbox/
# ├── Needs_Action/
# ├── Done/
# ├── Dashboard.md
# ├── Logs/
# │   └── error_recovery/
# ├── Company_Handbook/
# ├── Accounting/
# │   └── transactions/
# ├── Social_Media/
# │   └── posts/
# ├── Audits/
# │   └── weekly/
# ├── Workflows/
# │   ├── executions/
# │   └── plans/
# ├── System/
# │   └── mcp_servers/
# ├── Action_Queue/
# └── Circuit_State/
```

---

## Phase 4: Implementation (40+ hours)

Follow the implementation plan in `specs/003-gold-autonomous-employee/plan.md`.

**Implementation order** (after running `/sp.tasks`):
1. MCP Server Infrastructure (8 hours)
   - MCPServerOrchestrator class
   - Process-based server management
   - Health checks and routing

2. Odoo Integration (10 hours)
   - Accounting MCP server
   - OdooClient with odoorpc
   - Transaction sync (bidirectional)
   - Conflict detection

3. Social Media Integration (12 hours)
   - Social MCP server
   - Facebook, Instagram, Twitter clients
   - Platform-specific content optimization
   - Metrics aggregation

4. Error Recovery System (6 hours)
   - Retry logic with tenacity
   - Circuit breakers with pybreaker
   - Action queuing (Markdown-based)
   - Graceful degradation

5. Weekly Audit System (6 hours)
   - Audit generator service
   - Financial, operational, social metrics
   - Trend analysis and anomaly detection
   - CEO briefing generation

6. Ralph Wiggum Autonomous Loop (8 hours)
   - Workflow execution engine
   - Multi-step plan generation
   - Automatic error recovery
   - Human escalation when needed

---

## Phase 5: Testing (8 hours)

### 5.1 Contract Tests

Test each API integration:
```bash
# Test Odoo connection
pytest tests/contract/test_odoo_contracts.py -v

# Test Facebook API
pytest tests/contract/test_facebook_contracts.py -v

# Test Instagram API
pytest tests/contract/test_instagram_contracts.py -v

# Test Twitter API
pytest tests/contract/test_twitter_contracts.py -v
```

### 5.2 Integration Tests

Test end-to-end workflows:
```bash
# Test Odoo sync
pytest tests/integration/test_odoo_sync.py -v

# Test social media posting
pytest tests/integration/test_social_posting.py -v

# Test audit generation
pytest tests/integration/test_audit_generation.py -v

# Test Ralph Wiggum loop
pytest tests/integration/test_ralph_wiggum_loop.py -v

# Test error recovery
pytest tests/integration/test_error_recovery.py -v
```

### 5.3 Manual Testing

**Test Odoo Sync**:
1. Create invoice in Odoo manually
2. Wait 5 minutes for sync
3. Verify transaction appears in `Accounting/transactions/`
4. Create expense in vault
5. Verify it syncs to Odoo

**Test Social Media Posting**:
1. Create task: "Post to all platforms: Test message"
2. Verify post appears in approval queue
3. Approve post
4. Verify post published to Facebook, Instagram, Twitter, LinkedIn
5. Wait 24 hours, check metrics

**Test Weekly Audit**:
1. Run system for one week with various activities
2. Trigger audit generation (Sunday 6 PM or manual)
3. Verify CEO briefing in `Audits/weekly/`
4. Check financial, operational, social metrics

**Test Ralph Wiggum Loop**:
1. Create complex task: "Process invoice for Acme Corp ($1500), sync to Odoo, post announcement on social media"
2. Verify system generates execution plan
3. Verify steps execute in order
4. Verify error recovery if step fails

**Test Error Recovery**:
1. Disconnect network during Odoo sync
2. Verify retry with exponential backoff
3. Verify action queued if retries fail
4. Reconnect network
5. Verify queued action processes automatically

---

## Phase 6: Configuration (1 hour)

### 6.1 MCP Server Configuration

Create `config/mcp_servers.yaml`:
```yaml
servers:
  accounting:
    script: src/mcp_servers/accounting_mcp/server.py
    enabled: true
    restart_on_failure: true
    max_restarts: 3
    rate_limits:
      calls_per_minute: 60
      calls_per_hour: 1000
      concurrent_requests: 5

  social:
    script: src/mcp_servers/social_mcp/server.py
    enabled: true
    restart_on_failure: true
    max_restarts: 3
    rate_limits:
      calls_per_minute: 50
      calls_per_hour: 800
      concurrent_requests: 3

  communications:
    script: src/mcp_servers/comms_mcp/server.py
    enabled: true
    restart_on_failure: true
    max_restarts: 3
    rate_limits:
      calls_per_minute: 60
      calls_per_hour: 1000
      concurrent_requests: 5
```

### 6.2 Scheduling Configuration

Update `config/schedules.yaml`:
```yaml
schedules:
  # Existing schedules (Bronze/Silver)
  - name: "Check Gmail"
    cron: "*/5 * * * *"
    action: "check_gmail"

  # Gold Tier schedules
  - name: "Sync Odoo Transactions"
    cron: "*/5 * * * *"
    action: "sync_odoo_transactions"

  - name: "Update Social Media Metrics"
    cron: "0 */6 * * *"  # Every 6 hours
    action: "update_social_metrics"

  - name: "Generate Weekly Audit"
    cron: "0 18 * * 0"  # Sunday 6 PM
    action: "generate_weekly_audit"

  - name: "Health Check MCP Servers"
    cron: "*/1 * * * *"  # Every minute
    action: "health_check_mcp_servers"
```

### 6.3 Circuit Breaker Configuration

Create `config/circuit_breakers.yaml`:
```yaml
circuit_breakers:
  odoo:
    fail_max: 10
    timeout_duration: 300  # 5 minutes

  facebook:
    fail_max: 10
    timeout_duration: 3600  # 1 hour (rate limits)

  instagram:
    fail_max: 10
    timeout_duration: 86400  # 24 hours (daily limits)

  twitter:
    fail_max: 10
    timeout_duration: 900  # 15 minutes (rate limit window)
```

---

## Phase 7: Deployment (30 minutes)

### 7.1 Start MCP Servers

```bash
# Start all MCP servers
python src/cli/start_mcp_servers.py --vault AI_Employee_Vault

# Expected output:
# Starting accounting MCP server...
# ✓ accounting server started
# Starting social MCP server...
# ✓ social server started
# Starting communications MCP server...
# ✓ communications server started
# ✓ All MCP servers started successfully
# Servers are running. Press Ctrl+C to stop.
```

### 7.2 Start Main System

In a separate terminal:
```bash
# Start orchestrator with Gold Tier enabled
python src/main.py --gold-tier

# Expected output:
# ============================================================
# AI Employee System - Gold Tier (Autonomous)
# ============================================================
# Gold Tier Features Enabled:
#   - Odoo Integration (bidirectional sync)
#   - Social Media Management (multi-platform)
#   - Weekly Business Intelligence Reports
#   - Autonomous Multi-Step Workflows (Ralph Wiggum)
#   - MCP Server Orchestration
#   - Advanced Error Recovery
# ============================================================
```

### 7.3 Verify Health

In a third terminal:
```bash
# Check MCP server status
python src/cli/gold_tier_cli.py --vault AI_Employee_Vault mcp-status

# Expected output:
# === MCP Server Status ===
#
# ✓ ACCOUNTING
#   Status: running
#   Domain: accounting
#   PID: 12345
#   Error Count: 0
#   Restart Count: 0
#   Available Tools: 4
#
# ✓ SOCIAL
#   Status: running
#   Domain: social
#   PID: 12346
#   Error Count: 0
#   Restart Count: 0
#   Available Tools: 5
#
# ✓ COMMUNICATIONS
#   Status: running
#   Domain: communications
#   PID: 12347
#   Error Count: 0
#   Restart Count: 0
#   Available Tools: 4
```

### 7.3 Monitor Logs

```bash
# Watch orchestrator logs
tail -f logs/orchestrator.log

# Watch MCP server logs
tail -f logs/accounting_mcp.log
tail -f logs/social_mcp.log
tail -f logs/comms_mcp.log

# Watch error recovery logs
tail -f AI_Employee_Vault/Logs/error_recovery/*.md
```

---

## Troubleshooting

### Odoo Connection Issues

**Problem**: `ConnectionError: Cannot connect to Odoo`

**Solutions**:
1. Verify Odoo is running: `curl http://localhost:8069`
2. Check credentials in `.env`
3. Test connection manually:
```python
import odoorpc
odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('business_db', 'admin', 'admin')
```

### Facebook/Instagram API Errors

**Problem**: `OAuthException: Access token expired`

**Solutions**:
1. Refresh long-lived token (expires after 60 days)
2. Check token permissions in Graph API Explorer
3. Verify page access token, not user token

**Problem**: `Instagram account not found`

**Solutions**:
1. Verify Instagram account is Business/Creator (not personal)
2. Verify Instagram connected to Facebook Page
3. Get Instagram account ID again

### Twitter API Errors

**Problem**: `Unauthorized: Authentication failed`

**Solutions**:
1. Verify all 5 credentials in `.env` (bearer token, API key/secret, access token/secret)
2. Check app permissions in Developer Portal
3. Regenerate tokens if needed

### MCP Server Crashes

**Problem**: MCP server keeps crashing

**Solutions**:
1. Check server logs: `tail -f logs/accounting_mcp.log`
2. Verify dependencies installed
3. Check for port conflicts
4. Increase `max_restarts` in config

### Rate Limit Issues

**Problem**: `TooManyRequests: Rate limit exceeded`

**Solutions**:
1. Check rate limit config in `config/mcp_servers.yaml`
2. Reduce posting frequency
3. Wait for rate limit window to reset
4. Verify circuit breaker is working

---

## Success Criteria

Gold Tier is successfully implemented when:

- [ ] All 3 MCP servers running concurrently
- [ ] Odoo transactions sync bidirectionally within 5 minutes
- [ ] Posts publish to Facebook, Instagram, Twitter with 95%+ success rate
- [ ] Weekly audit generates automatically every Sunday at 6 PM
- [ ] Ralph Wiggum loop completes 80%+ of multi-step workflows autonomously
- [ ] Error recovery succeeds in 90%+ of transient errors
- [ ] System handles 200+ tasks per day without degradation
- [ ] Memory usage stays under 1.5GB
- [ ] All Bronze and Silver features continue working

---

## Next Steps

After Gold Tier is complete:
1. Run system for 1 week to collect baseline metrics
2. Review first weekly audit report
3. Tune rate limits and circuit breaker thresholds
4. Optimize performance based on logs
5. Consider Platinum Tier (self-correction, multi-agent coordination)

---

## Support

**Documentation**:
- Spec: `specs/003-gold-autonomous-employee/spec.md`
- Plan: `specs/003-gold-autonomous-employee/plan.md`
- Data Model: `specs/003-gold-autonomous-employee/data-model.md`
- API Contracts: `specs/003-gold-autonomous-employee/contracts/`

**Logs**:
- Orchestrator: `logs/orchestrator.log`
- MCP Servers: `logs/*_mcp.log`
- Error Recovery: `AI_Employee_Vault/Logs/error_recovery/`

**Testing**:
- Contract Tests: `tests/contract/`
- Integration Tests: `tests/integration/`
- Run all tests: `pytest -v`

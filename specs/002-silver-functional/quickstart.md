# Quickstart Guide: Silver Tier - Functional Assistant

**Version**: 1.0 | **Date**: 2026-02-14 | **Feature**: 002-silver-functional

## Prerequisites

Before starting Silver Tier setup, ensure Bronze Phase is working:
- ✅ FileSystem watcher operational
- ✅ Obsidian vault structure in place
- ✅ Claude Code integration working
- ✅ Agent skills functional
- ✅ Dashboard updates automatically

**Estimated Setup Time**: 2-3 hours (excluding API approvals)

---

## Step 1: Install Dependencies

**Add Silver Tier dependencies to requirements.txt**:

```bash
# Gmail Integration
google-auth-oauthlib>=1.0.0
google-api-python-client>=2.0.0

# LinkedIn Integration
requests-oauthlib>=1.3.0
oauthlib>=3.2.0

# WhatsApp Integration
playwright>=1.40.0

# Token Storage
keyring>=24.0.0
cryptography>=41.0.0

# Scheduling
APScheduler>=3.10.0
pytz>=2023.3
```

**Install dependencies**:
```bash
pip install -r requirements.txt
```

**Install Playwright browsers** (for WhatsApp):
```bash
playwright install chromium
```

---

## Step 2: Gmail API Setup

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "AI Employee System"
3. Enable Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2.2 Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure consent screen:
   - User Type: External
   - App name: "AI Employee System"
   - Scopes: Add Gmail API scopes
4. Create OAuth client ID:
   - Application type: Desktop app
   - Name: "AI Employee Desktop"
5. Download credentials JSON file
6. Save as `credentials/gmail_credentials.json` (outside vault)

### 2.3 Authenticate Gmail

**Run authentication script**:
```bash
python src/watchers/auth/gmail_auth.py --authenticate
```

**Follow prompts**:
1. Browser will open with Google login
2. Sign in with your Google account
3. Grant permissions (read and send emails)
4. Token will be saved securely in OS keyring

**Verify authentication**:
```bash
python src/watchers/auth/gmail_auth.py --verify
```

Expected output: "✅ Gmail authentication successful"

---

## Step 3: LinkedIn API Setup

### 3.1 Create LinkedIn Developer Application

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Click "Create app"
3. Fill in application details:
   - App name: "AI Employee System"
   - LinkedIn Page: Your business page
   - Privacy policy URL: (required)
   - App logo: Upload logo
4. Submit for review

**⚠️ Note**: LinkedIn app approval can take 1-2 weeks

### 3.2 Configure OAuth2 Settings

1. Go to "Auth" tab in your LinkedIn app
2. Add redirect URL: `http://localhost:8080/callback`
3. Note your Client ID and Client Secret
4. Add to `.env` file:
   ```
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   ```

### 3.3 Request API Access

1. Go to "Products" tab
2. Request access to:
   - Sign In with LinkedIn
   - Share on LinkedIn
3. Wait for approval (1-2 weeks)

### 3.4 Authenticate LinkedIn

**After approval, run authentication**:
```bash
python src/watchers/auth/linkedin_auth.py --authenticate
```

**Follow prompts**:
1. Browser will open with LinkedIn login
2. Sign in with your LinkedIn account
3. Grant permissions
4. Token will be saved securely

**Verify authentication**:
```bash
python src/watchers/auth/linkedin_auth.py --verify
```

---

## Step 4: WhatsApp Setup (Web Automation)

### 4.1 Initial Setup

**Run WhatsApp setup**:
```bash
python src/watchers/whatsapp_watcher.py --setup
```

**QR Code Scan**:
1. Browser window will open with web.whatsapp.com
2. Scan QR code with your phone:
   - Open WhatsApp on phone
   - Go to Settings > Linked Devices
   - Tap "Link a Device"
   - Scan QR code displayed in browser
3. Wait for successful connection
4. Session will be saved for future use

**⚠️ Important**:
- Keep browser window open during setup
- Session may expire after inactivity (re-scan required)
- WhatsApp may detect automation (use conservatively)

### 4.2 Verify WhatsApp Connection

```bash
python src/watchers/whatsapp_watcher.py --verify
```

Expected output: "✅ WhatsApp connected and ready"

---

## Step 5: Configure Watchers

### 5.1 Create Watcher Configuration

**Create file**: `vault/Company_Handbook/watcher-config.md`

```yaml
---
version: 1.0
updated_at: 2026-02-14T10:00:00Z
---

# Watcher Configuration

## FileSystem Watcher (Bronze)
- **Enabled**: true
- **Poll Interval**: 2 seconds
- **Watch Path**: vault/Inbox/

## Gmail Watcher
- **Enabled**: true
- **Poll Interval**: 30 seconds
- **Labels to Monitor**: INBOX, IMPORTANT
- **Exclude Labels**: SPAM, TRASH
- **Max Results Per Poll**: 10

## WhatsApp Watcher
- **Enabled**: true
- **Poll Interval**: 30 seconds
- **Monitor Groups**: true
- **Group Whitelist**: ["Team Chat", "Project Alpha"]

## LinkedIn Watcher
- **Enabled**: false  # Enable after API approval
- **Poll Interval**: 60 seconds
- **Monitor Messages**: true
- **Monitor Mentions**: true
- **Monitor Comments**: false
```

### 5.2 Test Individual Watchers

**Test Gmail watcher**:
```bash
python -m pytest tests/integration/test_gmail_watcher.py -v
```

**Test WhatsApp watcher**:
```bash
python -m pytest tests/integration/test_whatsapp_watcher.py -v
```

**Test LinkedIn watcher** (after approval):
```bash
python -m pytest tests/integration/test_linkedin_watcher.py -v
```

---

## Step 6: Configure Approval Workflow

### 6.1 Create Needs_Approval Folder

```bash
mkdir -p vault/Needs_Approval
```

### 6.2 Test Approval CLI

**List pending approvals**:
```bash
python src/approval/cli.py list
```

**View approval details**:
```bash
python src/approval/cli.py view <approval_id>
```

**Approve action**:
```bash
python src/approval/cli.py approve <approval_id>
```

**Reject action**:
```bash
python src/approval/cli.py reject <approval_id> --reason "Not appropriate"
```

---

## Step 7: Configure Scheduling

### 7.1 Create Schedules Configuration

**Create file**: `vault/Company_Handbook/schedules.md`

```yaml
---
version: 1.0
updated_at: 2026-02-14T10:00:00Z
---

# Scheduled Tasks

## LinkedIn Business Updates
- **Schedule ID**: linkedin-posts
- **Cron Expression**: `0 10 * * 1,3,5`  # Mon, Wed, Fri at 10 AM
- **Action**: generate_linkedin_post
- **Enabled**: true

## Daily Dashboard Summary
- **Schedule ID**: daily-summary
- **Cron Expression**: `0 18 * * *`  # Every day at 6 PM
- **Action**: generate_daily_summary
- **Enabled**: true
```

### 7.2 Test Scheduler

**Start scheduler**:
```bash
python src/scheduling/scheduler.py --start
```

**List schedules**:
```bash
python src/scheduling/scheduler.py --list
```

**Run schedule manually** (for testing):
```bash
python src/scheduling/scheduler.py --run linkedin-posts
```

---

## Step 8: Configure LinkedIn Posting

### 8.1 Update Company Handbook

**Edit**: `vault/Company_Handbook/business-context.md`

Add business information for LinkedIn post generation:

```markdown
# Business Context

## Company Overview
- **Name**: [Your Company]
- **Industry**: [Your Industry]
- **Mission**: [Your Mission]
- **Target Audience**: [Your Audience]

## Products/Services
1. **Product 1**: [Description]
2. **Product 2**: [Description]

## Key Messages
- Message 1: [Value proposition]
- Message 2: [Differentiator]
- Message 3: [Customer success]

## Tone & Voice
- Professional yet approachable
- Focus on customer value
- Data-driven insights
- Industry thought leadership

## Hashtags
- Primary: #YourIndustry, #YourProduct
- Secondary: #Innovation, #BusinessGrowth
```

### 8.2 Test LinkedIn Post Generation

**Generate test post**:
```bash
python -c "from src.planning.plan_generator import generate_linkedin_post; print(generate_linkedin_post('business_update'))"
```

**Review generated post** in approval queue:
```bash
python src/approval/cli.py list
```

---

## Step 9: Start Multi-Watcher System

### 9.1 Update Orchestrator Configuration

**Edit**: `.env`

```bash
# Watcher Configuration
ENABLE_FILESYSTEM_WATCHER=true
ENABLE_GMAIL_WATCHER=true
ENABLE_WHATSAPP_WATCHER=true
ENABLE_LINKEDIN_WATCHER=false  # Enable after API approval

# Polling Intervals (seconds)
FILESYSTEM_POLL_INTERVAL=2
GMAIL_POLL_INTERVAL=30
WHATSAPP_POLL_INTERVAL=30
LINKEDIN_POLL_INTERVAL=60

# Approval Settings
APPROVAL_TIMEOUT_HOURS=24
AUTO_APPROVE_LOW_RISK=false

# Scheduling
ENABLE_SCHEDULER=true
SCHEDULER_TIMEZONE=America/New_York
```

### 9.2 Start System

**Run orchestrator with all watchers**:
```bash
python src/orchestrator.py --multi-watcher
```

**Expected output**:
```
🚀 AI Employee System - Silver Tier
✅ FileSystem watcher started
✅ Gmail watcher started (authenticated)
✅ WhatsApp watcher started (connected)
⏸️  LinkedIn watcher disabled (awaiting API approval)
✅ Scheduler started (2 schedules active)
✅ MCP server started
✅ Approval queue monitoring

📊 System Status:
- Watchers: 3/4 active
- Pending Approvals: 0
- Scheduled Tasks: 2
- Memory Usage: 245 MB

Monitoring for new tasks...
```

---

## Step 10: Test End-to-End Flow

### 10.1 Test Gmail Flow

1. **Send test email** to your Gmail account:
   - Subject: "Test task: Review pricing proposal"
   - Body: "Please review the pricing proposal for customer XYZ"

2. **Wait 30 seconds** for Gmail watcher to detect

3. **Check Inbox folder**:
   ```bash
   ls vault/Inbox/
   ```
   Expected: New task file created

4. **Check Dashboard**:
   ```bash
   cat vault/Dashboard.md
   ```
   Expected: Task count incremented

### 10.2 Test WhatsApp Flow

1. **Send test message** to your WhatsApp:
   - "Can you help me with the quarterly report?"

2. **Wait 30 seconds** for WhatsApp watcher to detect

3. **Check Inbox folder** for new task

### 10.3 Test Approval Flow

1. **Trigger action requiring approval**:
   ```bash
   python src/mcp/server.py --execute send_email \
     --to "test@example.com" \
     --subject "Test" \
     --body "Test email"
   ```

2. **Check approval queue**:
   ```bash
   python src/approval/cli.py list
   ```

3. **Review and approve**:
   ```bash
   python src/approval/cli.py view <approval_id>
   python src/approval/cli.py approve <approval_id>
   ```

4. **Verify email sent** (check Gmail Sent folder)

---

## Troubleshooting

### Gmail Authentication Issues

**Problem**: "Token expired" error

**Solution**:
```bash
python src/watchers/auth/gmail_auth.py --refresh
```

**Problem**: "Insufficient permissions" error

**Solution**:
1. Delete existing token
2. Re-authenticate with correct scopes
3. Ensure Gmail API is enabled in Google Cloud Console

### WhatsApp Connection Issues

**Problem**: QR code not appearing

**Solution**:
1. Ensure Playwright is installed: `playwright install chromium`
2. Run with visible browser: `--headless=false`
3. Check browser console for errors

**Problem**: Session expired

**Solution**:
1. Re-run setup: `python src/watchers/whatsapp_watcher.py --setup`
2. Scan QR code again
3. Keep browser window open during operation

### LinkedIn API Issues

**Problem**: "App not approved" error

**Solution**:
1. Check application status in LinkedIn Developer Portal
2. Wait for approval (1-2 weeks typical)
3. Use manual posting as fallback

### Approval Queue Issues

**Problem**: Approvals not appearing

**Solution**:
1. Check `vault/Needs_Approval/` folder exists
2. Verify MCP server is running
3. Check logs: `vault/Logs/mcp-executions-*.md`

---

## Verification Checklist

After setup, verify all components:

- [ ] Gmail watcher detects new emails within 30 seconds
- [ ] WhatsApp watcher detects new messages within 30 seconds
- [ ] LinkedIn watcher enabled (after API approval)
- [ ] Tasks created in Inbox from all channels
- [ ] Approval queue functional (list, view, approve, reject)
- [ ] Scheduled tasks execute at specified times
- [ ] LinkedIn posts generated and require approval
- [ ] MCP server executes approved actions
- [ ] All Bronze features still working (regression test)
- [ ] Dashboard updates with multi-channel metrics
- [ ] Audit logs comprehensive (all actions logged)

---

## Next Steps

After successful setup:

1. **Monitor for 24 hours**: Ensure stability and no errors
2. **Review approval queue daily**: Approve/reject pending actions
3. **Adjust schedules**: Optimize posting times based on engagement
4. **Fine-tune classification**: Improve agent skills based on accuracy
5. **Scale up**: Increase polling frequency if needed
6. **Migrate WhatsApp**: Switch to Business API when volume increases

---

## Support & Resources

**Documentation**:
- Bronze Phase: `specs/001-bronze-foundation/`
- Silver Phase: `specs/002-silver-functional/`
- API Contracts: `specs/002-silver-functional/contracts/`

**Logs**:
- System logs: `vault/Logs/`
- MCP executions: `vault/Logs/mcp-executions-*.md`
- Watcher errors: `vault/Logs/watcher-errors-*.md`

**Configuration**:
- Watcher config: `vault/Company_Handbook/watcher-config.md`
- Schedules: `vault/Company_Handbook/schedules.md`
- Business context: `vault/Company_Handbook/business-context.md`

**Testing**:
- Unit tests: `pytest tests/unit/`
- Integration tests: `pytest tests/integration/`
- End-to-end tests: `pytest tests/e2e/`

---

## Security Reminders

- ✅ Never commit credentials or tokens to git
- ✅ Store tokens in OS keyring or encrypted files
- ✅ Use `.env` for configuration (add to `.gitignore`)
- ✅ Review approval queue daily
- ✅ Monitor logs for suspicious activity
- ✅ Rotate tokens every 60-90 days
- ✅ Keep dependencies updated (security patches)

---

**Setup Complete!** 🎉

Your Silver Tier system is now operational with multi-channel input processing, approval workflow, and automated scheduling.

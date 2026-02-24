# AI Employee System - Testing Guide

**Date**: 2026-02-24
**Project**: b-ai-employee

---

## Quick Start Testing (5 minutes)

### Test 1: Basic System Startup (Bronze Tier)

```bash
# Run the system in basic mode (no external APIs needed)
python src/main.py

# Expected output:
# - System starts successfully
# - FileSystem watcher initializes
# - Dashboard updates
# - Detects test task in Inbox
```

**What to watch for**:
- No import errors
- Vault path detected correctly
- Watchers start successfully
- Console shows task detection

---

### Test 2: Task Processing Flow

**Step 1**: Check if test task was created
```bash
ls AI_Employee_Vault/Inbox/test-task-001.md
```

**Step 2**: Run system for 30 seconds
```bash
# In one terminal
python src/main.py

# Let it run for 30 seconds, then press Ctrl+C
```

**Step 3**: Verify task was processed
```bash
# Check if task moved to Needs_Action or Done
ls AI_Employee_Vault/Needs_Action/
ls AI_Employee_Vault/Done/

# Check Dashboard was updated
cat AI_Employee_Vault/Dashboard.md
```

**Expected Result**:
- Task detected in Inbox
- Task moved to Needs_Action (or Done if processed)
- Dashboard shows updated metrics
- Logs show processing activity

---

## Detailed Testing by Tier

### Bronze Tier Testing (No External APIs)

**Test 1: FileSystem Watcher**
```bash
# Terminal 1: Run system
python src/main.py

# Terminal 2: Create test tasks
echo "---
title: Test Task 2
---
# Task 2
Simple test" > AI_Employee_Vault/Inbox/test-002.md

# Watch Terminal 1 for detection
```

**Test 2: Dashboard Updates**
```bash
# Check Dashboard before
cat AI_Employee_Vault/Dashboard.md

# Run system for 1 minute
python src/main.py
# Press Ctrl+C after 1 minute

# Check Dashboard after
cat AI_Employee_Vault/Dashboard.md
```

**Test 3: Vault Structure**
```bash
# Verify all folders exist
ls -la AI_Employee_Vault/

# Should show:
# - Inbox/
# - Needs_Action/
# - Done/
# - Dashboard.md
# - Company_Handbook/
# - Logs/
```

---

### Silver Tier Testing (With External APIs)

**Prerequisites**:
- Gmail OAuth credentials configured
- LinkedIn access token available
- WhatsApp session authenticated

**Test 1: Gmail Watcher** (Requires Gmail API setup)
```bash
# Enable Gmail watcher in .env
ENABLE_GMAIL_WATCHER=true

# Run system
python src/main.py

# Send test email to your Gmail
# Watch for detection in logs
```

**Test 2: LinkedIn Posting** (Requires LinkedIn API)
```bash
# Create LinkedIn post task
echo "---
title: LinkedIn Post Test
action: linkedin_post
---
# Post Content
Test post from AI Employee system" > AI_Employee_Vault/Inbox/linkedin-test.md

# Run system
python src/main.py

# Check LinkedIn_Posts folder
ls AI_Employee_Vault/LinkedIn_Posts/
```

**Test 3: Approval Workflow**
```bash
# Create task requiring approval
echo "---
title: Send Email Test
action: send_email
risk: high
---
# Email Task
Send test email to test@example.com" > AI_Employee_Vault/Inbox/email-test.md

# Run system
python src/main.py

# Check approval queue
ls AI_Employee_Vault/Needs_Approval/

# Approve via CLI
python src/cli/approval_cli.py list
python src/cli/approval_cli.py approve <task-id>
```

---

### Gold Tier Testing (Full System)

**Prerequisites**:
- Odoo Community running locally (Docker or native)
- Facebook/Instagram API credentials
- Twitter API credentials
- All .env variables configured

**Test 1: MCP Server Startup**
```bash
# Terminal 1: Start MCP servers
python src/cli/start_mcp_servers.py --vault AI_Employee_Vault

# Expected output:
# Starting accounting MCP server...
# Starting social MCP server...
# Starting communications MCP server...
# All servers started successfully

# Terminal 2: Check server status
python src/cli/gold_tier_cli.py mcp-status
```

**Test 2: Odoo Integration** (Requires Odoo running)
```bash
# Verify Odoo is running
curl http://localhost:8069

# Start system with Gold Tier
python src/main.py --gold-tier

# Create test transaction in Odoo
# Wait 5 minutes for sync
# Check Accounting folder
ls AI_Employee_Vault/Accounting/transactions/
```

**Test 3: Social Media Posting** (Requires API credentials)
```bash
# Create multi-platform post task
echo "---
title: Social Media Test
action: social_post
platforms: facebook,instagram,twitter
---
# Post Content
Test post from AI Employee system" > AI_Employee_Vault/Inbox/social-test.md

# Run system
python src/main.py --gold-tier

# Check approval queue
python src/cli/gold_tier_cli.py approval-queue

# Approve and verify posting
```

**Test 4: Ralph Wiggum Autonomous Loop**
```bash
# Create complex multi-step task
echo "---
title: Complex Workflow Test
---
# Multi-Step Task
1. Create invoice for Test Client ($500)
2. Sync to Odoo
3. Post announcement on social media
4. Send confirmation email" > AI_Employee_Vault/Inbox/complex-test.md

# Run system
python src/main.py --gold-tier

# Monitor workflow execution
python src/cli/gold_tier_cli.py workflow-status

# Check execution logs
ls AI_Employee_Vault/Workflows/executions/
```

**Test 5: Weekly Audit Generation**
```bash
# Manually trigger audit (don't wait for Sunday)
python src/cli/gold_tier_cli.py generate-audit

# Check audit report
ls AI_Employee_Vault/Audits/weekly/
cat AI_Employee_Vault/Audits/weekly/audit-*.md
```

---

## Troubleshooting

### Common Issues

**Issue 1: Import Errors**
```bash
# Solution: Install missing dependencies
pip install -r requirements.txt

# Verify installations
pip list | grep -E "(watchdog|frontmatter|odoorpc|tweepy)"
```

**Issue 2: Vault Path Not Found**
```bash
# Solution: Check .env file
cat .env | grep VAULT_PATH

# Should show: VAULT_PATH=C:\Users\admin\Desktop\b-ai-employee\AI_Employee_Vault

# Or specify manually
python src/main.py --vault AI_Employee_Vault
```

**Issue 3: No Tasks Detected**
```bash
# Check if Inbox has tasks
ls AI_Employee_Vault/Inbox/

# Check watcher is enabled
cat .env | grep ENABLE_FILESYSTEM_WATCHER

# Check logs
tail -f logs/orchestrator.log
```

**Issue 4: MCP Servers Won't Start**
```bash
# Check if ports are available
netstat -an | grep 8080

# Check server logs
tail -f logs/accounting_mcp.log
tail -f logs/social_mcp.log
tail -f logs/comms_mcp.log

# Restart servers
python src/cli/stop_mcp_servers.py
python src/cli/start_mcp_servers.py --vault AI_Employee_Vault
```

**Issue 5: Odoo Connection Failed**
```bash
# Verify Odoo is running
curl http://localhost:8069

# Test connection manually
python -c "
import odoorpc
odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('business_db', 'admin', 'admin')
print(f'Connected: {odoo.env.uid}')
"

# Check .env credentials
cat .env | grep ODOO_
```

---

## Performance Testing

### Load Test
```bash
# Create 100 test tasks
for i in {1..100}; do
  echo "---
title: Load Test Task $i
---
# Task $i
Test task for load testing" > AI_Employee_Vault/Inbox/load-test-$i.md
done

# Run system and monitor
python src/main.py --verbose

# Check processing time
# Monitor memory usage
# Verify all tasks processed
```

### Stress Test
```bash
# Run system for 24 hours
nohup python src/main.py --gold-tier > system.log 2>&1 &

# Monitor logs
tail -f system.log

# Check memory usage
ps aux | grep python

# Check task completion rate
ls AI_Employee_Vault/Done/ | wc -l
```

---

## Success Criteria

### Bronze Tier
- [ ] System starts without errors
- [ ] FileSystem watcher detects new tasks
- [ ] Tasks move from Inbox → Needs_Action → Done
- [ ] Dashboard updates automatically
- [ ] Logs are created and rotated

### Silver Tier
- [ ] Multiple watchers run concurrently
- [ ] Gmail watcher detects emails (if configured)
- [ ] LinkedIn posting works (if configured)
- [ ] Approval workflow functions correctly
- [ ] Scheduling system works
- [ ] MCP server responds to requests

### Gold Tier
- [ ] All 3 MCP servers start successfully
- [ ] Odoo sync works bidirectionally
- [ ] Social media posts to all platforms
- [ ] Weekly audit generates automatically
- [ ] Ralph Wiggum completes multi-step workflows
- [ ] Error recovery handles failures gracefully
- [ ] System runs for 24+ hours without crashes

---

## Next Steps After Testing

1. **If Bronze Tier works**: Configure Gmail/LinkedIn for Silver Tier
2. **If Silver Tier works**: Setup Odoo and social media APIs for Gold Tier
3. **If Gold Tier works**: Run for 1 week to collect baseline metrics
4. **Production Deployment**: Move to production environment
5. **Monitoring**: Setup alerts and dashboards
6. **Optimization**: Tune based on performance data

---

## Support

**Logs Location**:
- Main logs: `logs/orchestrator.log`
- MCP logs: `logs/*_mcp.log`
- Error recovery: `AI_Employee_Vault/Logs/error_recovery/`

**Documentation**:
- Spec: `specs/003-gold-autonomous-employee/spec.md`
- Quickstart: `specs/003-gold-autonomous-employee/quickstart.md`
- Plan: `specs/003-gold-autonomous-employee/plan.md`

**CLI Commands**:
```bash
# Check system status
python src/cli/gold_tier_cli.py mcp-status

# View approval queue
python src/cli/gold_tier_cli.py approval-queue

# Check workflow status
python src/cli/gold_tier_cli.py workflow-status

# Generate audit manually
python src/cli/gold_tier_cli.py generate-audit
```

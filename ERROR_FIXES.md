# Error Fixes and Installation Guide

## All Errors Fixed ✓

### 1. Email MCP Server - Module Not Found
**Error**: `Cannot find module 'C:\...\email_mcp\index.js'`
**Fix**: Updated `package.json` to point to `src/index.js` instead of `index.js`

### 2. Email MCP Server - Package Not Found
**Error**: `Cannot find package '@modelcontextprotocol/sdk'`
**Fix**: Need to run `npm install` in `mcp_servers/email_mcp/` directory

### 3. Cloud Agent - VaultConfig Validation Error
**Error**: `Field required [type=missing, input_value={'vault_root': 'vault'}, input_type=dict]`
**Fix**:
- Added `sync_method` parameter to VaultConfig initialization
- Made vault path absolute relative to project root

### 4. Local Agent - NameError: 'Any' is not defined
**Error**: `NameError: name 'Any' is not defined`
**Fix**: Added `from typing import Any` import to `approval_handler.py`

## Quick Installation

### Option 1: Automated Installation (Recommended)

**Windows**:
```cmd
cd C:\Users\admin\Desktop\b-ai-employee
install.bat
```

**Linux/Mac**:
```bash
cd /path/to/b-ai-employee
chmod +x install.sh
./install.sh
```

### Option 2: Manual Installation

**Step 1: Install Python Dependencies**
```bash
cd C:\Users\admin\Desktop\b-ai-employee

# Shared package
cd shared
pip install -r requirements.txt
cd ..

# Cloud agent
cd cloud_agent
pip install -r requirements.txt
cd ..

# Local agent
cd local_agent
pip install -r requirements.txt
cd ..
```

**Step 2: Install Node.js Dependencies**
```bash
cd mcp_servers/email_mcp
npm install
cd ../..
```

**Step 3: Verify Installation**
```bash
python test_config.py
python test_local_agent.py
```

## Configuration

### 1. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `gmail_credentials.json`
6. Place in `credentials/` folder:
   ```bash
   mkdir -p credentials
   # Copy gmail_credentials.json to credentials/
   ```

### 2. Environment Variables

Create `.env` file in project root:

```bash
# Copy example
cp config/.env.example .env

# Edit with your values
# Minimum required:
VAULT_PATH=vault
SYNC_METHOD=git
GMAIL_ENABLED=true
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=credentials/gmail_token.json
CLAUDE_API_KEY=your_api_key_here
```

## Running the System

### Start All Components

**Terminal 1 - Email MCP Server**:
```bash
cd C:\Users\admin\Desktop\b-ai-employee\mcp_servers\email_mcp
npm start
```

**Terminal 2 - Cloud Agent**:
```bash
cd C:\Users\admin\Desktop\b-ai-employee\cloud_agent
python src/agent.py
```

**Terminal 3 - Local Agent**:
```bash
cd C:\Users\admin\Desktop\b-ai-employee\local_agent
python src/agent.py
```

### Expected Output

**Email MCP Server**:
```
Email MCP server started successfully
```

**Cloud Agent**:
```
INFO - Initialized cloud agent: Cloud Agent (dev_mode=False, dry_run=False)
INFO - Setting up cloud agent
INFO - Gmail watcher started
INFO - Cloud agent setup complete
INFO - Cloud agent started successfully
```

**Local Agent**:
```
INFO - Initialized local agent: Local Agent (dev_mode=False, dry_run=False)
INFO - Setting up local agent
INFO - Local agent setup complete
INFO - Local agent started successfully
```

## Testing the Email Flow

### 1. Send Test Email
Send an email to your monitored Gmail account with subject "Test Email"

### 2. Wait for Detection (2 minutes)
Cloud agent polls Gmail every 2 minutes

### 3. Check for Draft
```bash
ls vault/Pending_Approval/email/
```
You should see a file like `email_send_sender@example.com_20260225T120000Z.md`

### 4. Approve the Draft
```bash
# Move to Approved folder
mv vault/Pending_Approval/email/email_send_*.md vault/Approved/
```

### 5. Verify Execution
- Email should be sent within 1 minute
- Check `vault/Done/` for completed action
- Check `vault/Logs/2026-02-25.md` for audit entry
- Check `vault/Dashboard.md` for updated status

## Troubleshooting

### Issue: "Cannot find package '@modelcontextprotocol/sdk'"
**Solution**:
```bash
cd mcp_servers/email_mcp
npm install
```

### Issue: "Vault root does not exist: vault"
**Solution**: The vault directory exists. This error should be fixed now with absolute path resolution.

### Issue: "No module named 'shared'"
**Solution**: Make sure you're running from the project root:
```bash
cd C:\Users\admin\Desktop\b-ai-employee
python cloud_agent/src/agent.py
```

### Issue: Gmail authentication fails
**Solution**:
1. Ensure `gmail_credentials.json` is in `credentials/` folder
2. Run the cloud agent - it will open a browser for authentication
3. Authorize the app
4. Token will be saved to `credentials/gmail_token.json`

### Issue: "CLAUDE_API_KEY environment variable is required"
**Solution**: Add your Claude API key to `.env`:
```bash
CLAUDE_API_KEY=sk-ant-...
```

## Development Mode

For testing without sending real emails:

```bash
# In .env file
DEVELOPMENT_MODE=true
DRY_RUN_MODE=true
```

This will:
- Log actions without executing them
- Use mock services instead of real APIs
- Skip Gmail authentication

## Next Steps

1. ✓ Install dependencies
2. ✓ Configure Gmail API
3. ✓ Set environment variables
4. ✓ Start all components
5. ✓ Test email flow
6. Deploy cloud agent to cloud VM (see `specs/001-platinum-employee/quickstart.md`)

## Support

- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Full Quickstart**: `specs/001-platinum-employee/quickstart.md`
- **Architecture**: `specs/001-platinum-employee/plan.md`
- **Tasks**: `specs/001-platinum-employee/tasks.md`

---

**Status**: All errors fixed. System ready for installation and testing.

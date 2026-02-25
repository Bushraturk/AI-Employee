# Quick Start Guide - Fixed Errors

## Errors Fixed

### 1. Email MCP Server - Module Not Found
**Error**: `Cannot find module 'C:\...\email_mcp\index.js'`
**Fix**: Updated `package.json` to point to `src/index.js`

### 2. Cloud Agent - VaultConfig Validation Error
**Error**: `Field required [type=missing, input_value={'vault_root': 'vault'}, input_type=dict]`
**Fix**:
- Added `sync_method` parameter to VaultConfig initialization
- Made vault path absolute relative to project root

### 3. Local Agent - NameError: 'Any' is not defined
**Error**: `NameError: name 'Any' is not defined`
**Fix**: Added `from typing import Any` import

## Running the System

### Prerequisites

1. **Install Python dependencies**:
```bash
cd C:\Users\admin\Desktop\b-ai-employee

# Install shared dependencies
cd shared
pip install -r requirements.txt
cd ..

# Install cloud agent dependencies
cd cloud_agent
pip install -r requirements.txt
cd ..

# Install local agent dependencies
cd local_agent
pip install -r requirements.txt
cd ..
```

2. **Install Node.js dependencies**:
```bash
cd mcp_servers/email_mcp
npm install
cd ../..
```

3. **Set up Gmail API credentials**:
- Place `gmail_credentials.json` in `credentials/` folder
- Run authentication flow to generate `gmail_token.json`

### Start the System

**Terminal 1 - Email MCP Server**:
```bash
cd C:\Users\admin\Desktop\b-ai-employee\mcp_servers\email_mcp
npm start
```

**Terminal 2 - Cloud Agent** (or deploy to cloud VM):
```bash
cd C:\Users\admin\Desktop\b-ai-employee\cloud_agent
python src/agent.py
```

**Terminal 3 - Local Agent**:
```bash
cd C:\Users\admin\Desktop\b-ai-employee\local_agent
python src/agent.py
```

## Testing

### Test Configuration Loading

```bash
cd C:\Users\admin\Desktop\b-ai-employee
python test_config.py
python test_local_agent.py
```

### Test Email Flow

1. Send test email to monitored Gmail account
2. Wait 2 minutes for cloud agent to detect
3. Check `vault/Pending_Approval/email/` for draft
4. Move draft to `vault/Approved/`
5. Verify email is sent
6. Check `vault/Logs/` for audit entry

## Environment Variables

Create `.env` file in project root:

```bash
# Vault configuration
VAULT_PATH=vault
SYNC_METHOD=git
GIT_REMOTE=https://github.com/yourusername/ai-employee-vault.git
GIT_BRANCH=main

# Gmail configuration
GMAIL_ENABLED=true
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=credentials/gmail_token.json
GMAIL_CHECK_INTERVAL=120

# Claude API (for drafting)
CLAUDE_API_KEY=your_api_key_here

# Development mode
DEVELOPMENT_MODE=false
DRY_RUN_MODE=false

# Rate limiting
MAX_EMAILS_PER_HOUR=10
MAX_PAYMENTS_PER_HOUR=3
```

## Common Issues

### Issue: "Vault root does not exist"
**Solution**: The vault directory exists but the path resolution might be relative. The code now makes it absolute.

### Issue: "Cannot find module @modelcontextprotocol/sdk"
**Solution**: Run `npm install` in `mcp_servers/email_mcp/`

### Issue: "No module named 'shared'"
**Solution**: Make sure you're running from the project root and the shared package is in the Python path.

## Next Steps

1. Set up Gmail API credentials
2. Configure environment variables
3. Test each component individually
4. Test end-to-end email flow
5. Deploy cloud agent to cloud VM

## Support

See `IMPLEMENTATION_SUMMARY.md` for detailed implementation notes and architecture overview.

# Research: Silver Tier - Functional Assistant

**Date**: 2026-02-14 | **Feature**: 002-silver-functional | **Phase**: 0

## Purpose

This document captures research findings for technology choices, integration patterns, and best practices for implementing Silver Tier multi-channel functionality.

## Research Areas

### 1. Gmail API Integration

**Decision**: Use Google Gmail API with OAuth2 authentication

**Rationale**:
- Official Google API provides reliable, well-documented access to Gmail
- OAuth2 ensures secure authentication without storing passwords
- Supports both reading emails and sending via API
- Rate limits are reasonable (250 quota units per user per second)
- Python client library (google-api-python-client) is mature and maintained

**Alternatives Considered**:
- IMAP/SMTP: Rejected due to less secure app passwords, no structured metadata access
- Third-party services (Nylas, SendGrid): Rejected to maintain local-first architecture
- Web scraping: Rejected due to fragility and ToS violations

**Implementation Pattern**:
```python
# OAuth2 flow for Gmail
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send']

# Token storage: Use OS keyring or encrypted file outside vault
# Refresh tokens automatically when expired
# Handle rate limits with exponential backoff
```

**Best Practices**:
- Store tokens in OS keyring (keyring library) or encrypted file outside git
- Use incremental sync with historyId to avoid re-processing emails
- Implement exponential backoff for rate limit handling
- Cache email metadata locally to reduce API calls
- Use batch requests for efficiency when processing multiple emails

**References**:
- Gmail API Python Quickstart: https://developers.google.com/gmail/api/quickstart/python
- OAuth2 for Installed Apps: https://developers.google.com/identity/protocols/oauth2/native-app

---

### 2. LinkedIn API Integration

**Decision**: Use LinkedIn API v2 with OAuth2 authentication

**Rationale**:
- Official LinkedIn API provides access to profile, posts, and messaging
- OAuth2 ensures secure authentication
- Supports creating posts (UGC Posts API)
- Can retrieve post analytics (likes, comments, shares, impressions)
- Python requests library sufficient for REST API calls

**Alternatives Considered**:
- linkedin-api (unofficial): Rejected due to lack of official support, potential ToS issues
- Web scraping with Selenium: Rejected due to fragility, ToS violations, account ban risk
- Third-party services: Rejected to maintain control and avoid dependencies

**Implementation Pattern**:
```python
# OAuth2 flow for LinkedIn
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

# LinkedIn OAuth2 endpoints
AUTHORIZATION_URL = 'https://www.linkedin.com/oauth/v2/authorization'
TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
SCOPES = ['r_liteprofile', 'r_emailaddress', 'w_member_social']

# UGC Posts API for creating posts
POST_URL = 'https://api.linkedin.com/v2/ugcPosts'
```

**Best Practices**:
- Request minimal scopes needed (r_liteprofile, w_member_social)
- Store access tokens securely (60-day expiration)
- Implement retry logic for API failures
- Respect rate limits (throttling varies by endpoint)
- Use UGC Posts API for creating posts (not Share API - deprecated)
- Include rich media (images, links) for better engagement

**Constraints**:
- LinkedIn API access requires approved developer application
- Rate limits are not publicly documented (monitor 429 responses)
- Post analytics may have 24-48 hour delay

**References**:
- LinkedIn OAuth2: https://docs.microsoft.com/en-us/linkedin/shared/authentication/authentication
- UGC Posts API: https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api

---

### 3. WhatsApp Integration

**Decision**: Use WhatsApp Business API (if available) or Playwright for web.whatsapp.com automation as fallback

**Rationale**:
- WhatsApp Business API is official but requires business verification and hosting
- web.whatsapp.com automation with Playwright is more accessible for MVP
- Playwright more reliable than Selenium (better async support, auto-wait)
- Can monitor messages and send replies programmatically

**Alternatives Considered**:
- WhatsApp Business API (Cloud): Preferred but requires Meta Business verification (weeks)
- Twilio WhatsApp API: Rejected due to cost and external dependency
- Selenium: Rejected in favor of Playwright (better reliability, modern tooling)
- Unofficial libraries (yowsup): Rejected due to ban risk and maintenance issues

**Implementation Pattern (Playwright)**:
```python
# WhatsApp web automation with Playwright
from playwright.async_api import async_playwright

async def monitor_whatsapp():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Requires QR scan
        context = await browser.new_context(
            user_data_dir='./whatsapp_session'  # Persist session
        )
        page = await context.new_page()
        await page.goto('https://web.whatsapp.com')

        # Wait for QR scan on first run
        # Monitor for new messages via DOM observation
        # Extract message text, sender, timestamp
```

**Best Practices**:
- Persist browser session to avoid repeated QR scans
- Use headless=False initially for QR code scanning
- Implement DOM observers for real-time message detection
- Handle connection drops gracefully (reconnect logic)
- Respect WhatsApp rate limits (avoid spam detection)
- Store session data securely outside vault

**Constraints**:
- Requires manual QR code scan on first setup
- Session may expire after inactivity (re-scan needed)
- WhatsApp may detect automation and require verification
- Not suitable for high-volume messaging (use Business API for scale)

**Fallback Strategy**:
- Start with Playwright for MVP (faster setup)
- Migrate to WhatsApp Business API if volume increases or automation detected
- Document migration path in quickstart.md

**References**:
- WhatsApp Business API: https://developers.facebook.com/docs/whatsapp/cloud-api
- Playwright Python: https://playwright.dev/python/docs/intro

---

### 4. MCP (Model Context Protocol) Implementation

**Decision**: Implement custom MCP server using Python with tool registry pattern

**Rationale**:
- MCP protocol is relatively new (Anthropic, 2024) - limited production libraries
- Custom implementation provides full control over tool execution and validation
- Tool registry pattern enables whitelisting and permission management
- Can implement rollback capability for failed actions
- Aligns with constitution principle of explicit action execution

**Alternatives Considered**:
- mcp-server-python (if exists): Use if mature library available
- Direct API calls from orchestrator: Rejected due to lack of abstraction and validation layer
- Generic RPC framework (gRPC, JSON-RPC): Rejected as over-engineered for single-process use

**Implementation Pattern**:
```python
# MCP Server with Tool Registry
class MCPServer:
    def __init__(self):
        self.tools = {}  # Tool registry
        self.audit_log = []

    def register_tool(self, name: str, handler: callable,
                     risk_level: str, requires_approval: bool):
        """Register a tool with metadata"""
        self.tools[name] = {
            'handler': handler,
            'risk_level': risk_level,
            'requires_approval': requires_approval
        }

    async def execute_tool(self, tool_name: str, params: dict,
                          approval_id: str = None):
        """Execute tool with validation and logging"""
        # 1. Validate tool exists and is whitelisted
        # 2. Check approval if required
        # 3. Execute with error handling
        # 4. Log to audit trail
        # 5. Return result or error
```

**Best Practices**:
- Implement tool registry with explicit whitelisting
- Classify tools by risk level (low/medium/high)
- Require approval for medium/high risk tools
- Log all tool calls with input/output/timestamp
- Implement idempotency for safe retries
- Provide rollback capability where possible (e.g., delete sent email draft)
- Use async/await for non-blocking execution
- Implement timeout handling for long-running tools

**Tool Categories**:
- **Low Risk** (auto-execute): Read operations, local file operations within vault
- **Medium Risk** (approval required): Email sends, LinkedIn posts, WhatsApp messages
- **High Risk** (approval + confirmation): Bulk operations, destructive actions

**References**:
- MCP Protocol Spec: https://modelcontextprotocol.io/docs (if available)
- Tool Use Patterns: Anthropic Claude API documentation

---

### 5. OAuth2 Token Storage

**Decision**: Use OS keyring (keyring library) for token storage with encrypted file fallback

**Rationale**:
- OS keyring provides secure, encrypted storage (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- Tokens never stored in git or vault (constitution compliance)
- Automatic encryption at rest
- Cross-platform support via keyring library
- Fallback to encrypted file if keyring unavailable

**Alternatives Considered**:
- Environment variables: Rejected due to lack of persistence and security concerns
- Encrypted file only: Rejected as less secure than OS keyring
- Database: Rejected as over-engineered and violates local-first principle

**Implementation Pattern**:
```python
import keyring
from cryptography.fernet import Fernet

class TokenStorage:
    SERVICE_NAME = "ai-employee-system"

    def store_token(self, account: str, token: dict):
        """Store OAuth2 token securely"""
        try:
            # Try OS keyring first
            keyring.set_password(self.SERVICE_NAME, account,
                               json.dumps(token))
        except keyring.errors.KeyringError:
            # Fallback to encrypted file
            self._store_encrypted_file(account, token)

    def get_token(self, account: str) -> dict:
        """Retrieve OAuth2 token"""
        try:
            token_json = keyring.get_password(self.SERVICE_NAME, account)
            return json.loads(token_json) if token_json else None
        except keyring.errors.KeyringError:
            return self._get_encrypted_file(account)
```

**Best Practices**:
- Store refresh tokens, not just access tokens
- Implement automatic token refresh before expiration
- Handle token revocation gracefully (re-authenticate)
- Use separate keyring entries per service (gmail, linkedin)
- Document token setup in quickstart.md
- Never log tokens (even in debug mode)

**Security Considerations**:
- Tokens stored outside vault directory (not backed up to git)
- Encrypted file fallback uses Fernet (symmetric encryption)
- Encryption key derived from machine-specific data or user password
- Token expiration handled automatically

**References**:
- keyring library: https://pypi.org/project/keyring/
- OAuth2 Token Best Practices: https://oauth.net/2/

---

### 6. Scheduling System

**Decision**: Use APScheduler for Python-based scheduling with OS scheduler integration

**Rationale**:
- APScheduler provides cron-like syntax in Python
- Supports multiple job stores (memory, SQLite, Redis)
- Can integrate with Windows Task Scheduler or cron for persistence
- Handles timezone-aware scheduling
- Supports job persistence across restarts

**Alternatives Considered**:
- schedule library: Rejected due to lack of persistence and limited features
- Direct cron/Task Scheduler: Rejected due to platform-specific complexity
- Celery: Rejected as over-engineered (requires message broker)

**Implementation Pattern**:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///vault/schedules.db')
}

scheduler = BackgroundScheduler(jobstores=jobstores)

# Add recurring job
scheduler.add_job(
    func=generate_linkedin_post,
    trigger=CronTrigger(day_of_week='mon,wed,fri', hour=10),
    id='linkedin_posting',
    replace_existing=True
)

scheduler.start()
```

**Best Practices**:
- Store job definitions in vault as Markdown (human-readable)
- Use SQLite job store for persistence
- Implement job execution logging
- Handle job failures with retry logic
- Support pausing/resuming schedules
- Provide CLI commands for schedule management
- Use timezone-aware scheduling (pytz)

**Integration with OS Scheduler**:
- Windows: Generate Task Scheduler XML from APScheduler jobs
- Linux/Mac: Generate crontab entries from APScheduler jobs
- Fallback: APScheduler runs as background process

**References**:
- APScheduler Documentation: https://apscheduler.readthedocs.io/
- Cron Syntax: https://crontab.guru/

---

### 7. Agent Skills Architecture

**Decision**: Continue Bronze pattern - all AI functionality as .command.md files in .specify/commands/

**Rationale**:
- Proven pattern from Bronze phase (4 agent skills working)
- Maintains separation between orchestration (Python) and reasoning (Claude)
- Agent skills are version-controlled and human-readable
- Easy to test and modify without code changes
- Aligns with constitution principle of explicit reasoning

**Implementation Pattern**:
```markdown
# Agent Skill: classify-email.command.md

## Purpose
Classify incoming email as task, question, notification, spam, or other.

## Input Format
- Email subject
- Email body
- Sender information
- Timestamp

## Output Format (JSON)
{
  "classification": "task|question|notification|spam|other",
  "confidence": 0.95,
  "priority": "P1|P2|P3",
  "category": "support|sales|internal|...",
  "extracted_metadata": {
    "due_date": "2026-02-20",
    "action_required": "Reply with pricing"
  }
}

## Classification Rules
[Detailed rules for classification logic]
```

**Best Practices**:
- One agent skill per distinct AI task
- Clear input/output contracts in each skill file
- Include examples and edge cases in skill documentation
- Version control agent skills with git
- Test agent skills independently with sample inputs
- Use structured output (JSON) for programmatic processing

**New Agent Skills for Silver**:
1. classify-email.command.md - Email classification
2. classify-whatsapp.command.md - WhatsApp message classification
3. classify-linkedin.command.md - LinkedIn content classification
4. generate-linkedin-post.command.md - Post generation
5. create-plan.command.md - Plan.md generation
6. draft-email-reply.command.md - Email reply drafting
7. draft-whatsapp-reply.command.md - WhatsApp reply drafting
8. validate-action.command.md - Pre-execution validation

**References**:
- Bronze Phase Agent Skills: .specify/commands/*.command.md
- Claude Code CLI: https://docs.anthropic.com/claude/docs/claude-code

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Gmail | Google Gmail API | v1 | Official, reliable, OAuth2 |
| LinkedIn | LinkedIn API | v2 | Official, UGC Posts API |
| WhatsApp | Playwright | 1.40+ | Web automation (MVP), migrate to Business API later |
| MCP Server | Custom Python | - | Full control, tool registry pattern |
| Token Storage | keyring + cryptography | Latest | Secure, cross-platform |
| Scheduling | APScheduler | 3.10+ | Cron syntax, persistence, Python-native |
| OAuth2 | oauthlib + requests-oauthlib | Latest | Standard OAuth2 flows |
| Agent Skills | Claude Code CLI | - | Proven Bronze pattern |

## Dependencies to Add

```txt
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

# Existing from Bronze
watchdog>=3.0.0
python-frontmatter>=1.0.0
markdown>=3.4.0
python-dotenv>=1.0.0
pytest>=7.4.0
```

## Risk Mitigation

### Risk 1: WhatsApp Automation Detection
**Mitigation**:
- Start with conservative message frequency
- Implement human-like delays between actions
- Monitor for verification requests
- Document migration path to Business API
- Provide manual fallback option

### Risk 2: OAuth2 Token Expiration
**Mitigation**:
- Implement automatic token refresh
- Store refresh tokens securely
- Handle token revocation gracefully
- Provide clear re-authentication instructions
- Log token refresh events

### Risk 3: API Rate Limits
**Mitigation**:
- Implement exponential backoff for all APIs
- Cache data locally to reduce API calls
- Monitor rate limit headers
- Queue requests when approaching limits
- Provide user feedback on rate limit status

### Risk 4: LinkedIn API Access Approval
**Mitigation**:
- Apply for LinkedIn developer access early
- Document approval process in quickstart.md
- Provide fallback: manual posting with draft generation
- Consider alternative: LinkedIn unofficial API (with warnings)

## Next Steps

Phase 1 will use these research findings to:
1. Generate data-model.md (entities: Task, Watcher, Approval, Schedule, Plan, LinkedInPost)
2. Create API contracts in contracts/ directory
3. Generate quickstart.md with setup instructions
4. Update agent context with new technologies

**Research Complete**: All technology choices documented with rationale and implementation patterns.

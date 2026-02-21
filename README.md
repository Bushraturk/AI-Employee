# AI Employee System - Silver Tier

Local-first autonomous AI employee system with multi-channel integration (Gmail, WhatsApp, LinkedIn), human-in-the-loop approval workflow, intelligent planning, automated scheduling, and external action capabilities.

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Claude Code CLI installed and configured
- Git (optional)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd b-ai-employee

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright for WhatsApp automation (Silver Tier)
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env and configure paths and API credentials
```

### Silver Tier Setup

**Gmail Integration**:
1. Create OAuth2 credentials in Google Cloud Console
2. Download credentials JSON and save to `vault/.credentials/gmail_credentials.json`
3. First run will open browser for OAuth2 consent

**WhatsApp Integration**:
1. First run will open WhatsApp Web
2. Scan QR code with your phone
3. Session persists in `whatsapp_session/` directory

**LinkedIn Integration**:
1. Configure LinkedIn API credentials in `.env`
2. Set `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET`
3. Run authentication: `python linkedin_authenticate.py`
4. For personal profile posting: Use `linkedin_publish.py` (automatic)
5. For company page posting: Use `linkedin_quick_post.py` (semi-automated)
   - Note: LinkedIn restricts company page API access to verified partners
   - Semi-automated approach: content copied to clipboard, you paste and post

### Running the System

```bash
# Start the AI employee
python src/main.py

# The system will:
# 1. Initialize the vault structure (Inbox, Needs_Action, Done, Logs, Company_Handbook)
# 2. Start monitoring the Inbox folder
# 3. Automatically process any task files dropped in Inbox
# 4. Update Dashboard.md with real-time status
```

### Creating Your First Task

Create a file in `AI_Employee_Vault/Inbox/my-task.md`:

```markdown
---
task_id: 550e8400-e29b-41d4-a716-446655440000
title: My first task
priority: P1
status: inbox
created_at: 2026-02-14T10:00:00Z
---

# My First Task

Please help me with this task!
```

The system will automatically:
- Detect the file within 2 seconds
- Move it to Needs_Action
- Process it through Claude Code
- Move it to Done
- Update the Dashboard

## Project Structure

```
b-ai-employee/
├── src/
│   ├── watchers/
│   │   ├── base_watcher.py          # Abstract watcher interface
│   │   └── filesystem_watcher.py    # FileSystem monitoring
│   ├── orchestrator.py               # Main coordination logic
│   ├── task_processor.py             # Markdown parsing
│   ├── action_executor.py            # Safe file operations
│   ├── vault_manager.py              # Vault initialization
│   └── main.py                       # CLI entry point
├── tests/
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   └── fixtures/                     # Test data
├── AI_Employee_Vault/                # Task vault (auto-created)
│   ├── Inbox/                        # New tasks
│   ├── Needs_Action/                 # Processing
│   ├── Done/                         # Completed
│   ├── Logs/                         # Audit trail
│   ├── Company_Handbook/             # Knowledge base
│   └── Dashboard.md                  # System status
├── specs/                            # Design documentation
├── requirements.txt                  # Python dependencies
├── .env                              # Configuration
└── README.md                         # This file
```

## Features

### Bronze Phase (MVP) ✅
- ✅ **Automatic Task Detection** - Monitors Inbox folder for new Markdown task files
- ✅ **Task Processing** - Processes tasks through Claude Code for reasoning and action planning
- ✅ **Workflow Management** - Moves tasks through Inbox → Needs_Action → Done stages
- ✅ **Local-First** - All data stored as Markdown files
- ✅ **Modular Architecture** - Base watcher interface for extensibility

### Silver Phase (Current) ✅ **COMPLETE**
- ✅ **Multi-Channel Detection** - Gmail, WhatsApp, and LinkedIn watchers
  - Gmail: OAuth2 authentication, email classification, task creation
  - WhatsApp: Web automation, message parsing, contact management
  - LinkedIn: Feed monitoring, message tracking, mention detection
- ✅ **Human-in-the-Loop Approval** - Approval workflow for high-risk actions
  - Risk classification (low/medium/high)
  - Approval queue with timeout handling
  - Multi-channel notifications (console, file, email)
  - Complete audit trail
- ✅ **LinkedIn Auto-Posting** - Automated business development posts
  - Post generation from business context
  - Optimal time scheduling (2-3 posts per week)
  - Performance tracking (views, engagement)
  - Human approval before posting
  - Personal profile (automatic) & Company page (semi-automatic)
- ✅ **Intelligent Planning** - Automatic plan generation for complex tasks
  - Multi-step task analysis
  - Plan.md generation with approach options
  - Risk identification and mitigation
  - Success criteria definition
- ✅ **Task Scheduling** - Recurring task automation
  - Cron-based schedules (e.g., daily at 9 AM)
  - Interval schedules (e.g., every 2 hours)
  - One-time execution at specific time
  - Schedule management CLI
  - Execution history logging
- ✅ **MCP Tools** - External action capabilities
  - Gmail: Send emails, create drafts, rollback capability
  - WhatsApp: Send messages with rate limiting (5/minute)
  - Parameter sanitization for privacy
  - Approval integration for high-risk actions
- ✅ **Agent Skills Framework** - Modular AI capabilities
  - 5 registered skills (planning, approval, MCP, scheduling, LinkedIn)
  - Skill registry and discovery system
  - Consistent execution interface
  - Extensible architecture
- ✅ **Real-Time Dashboard** - Live metrics and status
  - Multi-channel task counts
  - Approval workflow metrics
  - Performance tracking
  - System health monitoring

**Status:** 100% Complete - All 7 requirements met and tested
**See:** `SILVER_TIER_COMPLETE.md` for detailed completion report

## Configuration

Edit `.env` file:

```bash
# Vault path (absolute path recommended)
VAULT_PATH=/path/to/AI_Employee_Vault

# Claude Code CLI path
CLAUDE_CODE_PATH=claude

# Task processing timeout (seconds)
TASK_TIMEOUT=60

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Silver Tier - Multi-Channel Watchers
ENABLE_GMAIL_WATCHER=true
ENABLE_WHATSAPP_WATCHER=true
ENABLE_LINKEDIN_WATCHER=true

# Silver Tier - Gmail Configuration
GMAIL_POLL_INTERVAL=30
GMAIL_LABELS=INBOX
GMAIL_EXCLUDE_LABELS=SPAM,TRASH

# Silver Tier - WhatsApp Configuration
WHATSAPP_POLL_INTERVAL=30
WHATSAPP_SESSION_PATH=whatsapp_session/

# Silver Tier - LinkedIn Configuration
LINKEDIN_POLL_INTERVAL=60
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret

# Silver Tier - Approval Workflow
NOTIFICATIONS_CONSOLE=true
NOTIFICATIONS_FILE=true
NOTIFICATIONS_EMAIL=false

# Silver Tier - LinkedIn Auto-Posting
ENABLE_LINKEDIN_POSTING=true
LINKEDIN_AUTO_POST=true
LINKEDIN_POST_FREQUENCY=2.5
LINKEDIN_TIMEZONE=UTC

# Silver Tier - Intelligent Planning
MIN_STEPS_FOR_PLAN=3

# Silver Tier - Task Scheduling
ENABLE_TASK_SCHEDULING=true
SCHEDULER_TIMEZONE=UTC
SCHEDULER_MAX_INSTANCES=3

# Silver Tier - MCP Tools
ENABLE_MCP_SERVER=true
MCP_ENABLED_TOOLS=send_email,send_whatsapp
```

## Task File Format

Tasks are Markdown files with YAML frontmatter:

```markdown
---
task_id: <UUID v4>
title: <Task title (max 200 chars)>
priority: P1|P2|P3
status: inbox|needs_action|done
created_at: <ISO 8601 timestamp>
tags: [optional, tags]
---

# Task Description

Markdown content describing the task...
```

## Monitoring

View real-time system status in `AI_Employee_Vault/Dashboard.md`:

- Task counts (Inbox, Needs Action, Done)
- Performance metrics (processing time, success rate)
- Recent activity
- System health

## Troubleshooting

**System doesn't detect files:**
- Check VAULT_PATH in .env is correct
- Verify file extension is .md
- Check file permissions

**Claude Code not found:**
- Verify Claude Code is installed: `claude --version`
- Set full path in .env: `CLAUDE_CODE_PATH=/full/path/to/claude`

**Tasks fail to process:**
- Check task file format (valid YAML frontmatter)
- Review logs in AI_Employee_Vault/Logs/
- Verify Claude Code is responding: `echo "test" | claude`

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_vault_manager.py -v

# Run with coverage
pytest --cov=src tests/
```

### Project Phases

- **Bronze (Current)**: Local task processing with FileSystem watcher
- **Silver (Future)**: Gmail integration, email classification
- **Gold (Future)**: MCP tool execution, action validation
- **Platinum (Future)**: Self-improvement loop, multi-agent coordination

## Architecture

The system follows a clear **Perception → Reasoning → Action** loop:

1. **Perception**: FileSystem watcher detects new task files
2. **Reasoning**: Claude Code processes task and generates response
3. **Action**: Action executor moves files and updates dashboard

All state is stored as Markdown files (no hidden databases).

## Contributing

See `specs/001-bronze-foundation/` for detailed specifications and implementation plan.

## License

[Your License Here]

## Support

For issues and questions, see the documentation in `specs/001-bronze-foundation/quickstart.md`.

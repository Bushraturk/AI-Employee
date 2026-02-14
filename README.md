# AI Employee System - Bronze Phase

Local-first autonomous AI employee system that automatically detects, processes, and manages tasks through an Obsidian vault workflow.

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

# Configure environment
cp .env.example .env
# Edit .env and set VAULT_PATH to your desired location
```

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

## Features (Bronze Phase - MVP)

✅ **Automatic Task Detection** - Monitors Inbox folder for new Markdown task files
✅ **Task Processing** - Processes tasks through Claude Code for reasoning and action planning
✅ **Workflow Management** - Moves tasks through Inbox → Needs_Action → Done stages
✅ **Local-First** - No external APIs required, all data stored as Markdown
✅ **Modular Architecture** - Base watcher interface for future extensions (Gmail, WhatsApp)

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

# Quickstart Guide: Bronze Phase - Local Foundation

**Feature**: 001-bronze-foundation
**Date**: 2026-02-14
**Version**: 1.0.0

## Overview

This guide will help you set up and run the Bronze phase autonomous AI employee system in under 10 minutes. The system monitors an Obsidian vault for new task files and automatically processes them through Claude Code.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- **Claude Code CLI** installed and configured ([Installation Guide](https://github.com/anthropics/claude-code))
- **Git** (optional, for cloning repository)
- **Text editor** (VS Code, Sublime, or any editor)
- **Operating System**: Windows, macOS, or Linux

### Verify Prerequisites

```bash
# Check Python version (should be 3.9 or higher)
python --version

# Check Claude Code CLI
claude --version

# Check Git (optional)
git --version
```

---

## Installation

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd b-ai-employee

# Or download and extract ZIP if not using Git
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages**:
- watchdog (3.0+)
- python-frontmatter (1.0+)
- markdown (3.4+)
- python-dotenv (1.0+)
- pytest (7.4+)
- pytest-asyncio (0.21+)
- pytest-timeout (2.1+)

---

## Configuration

### Step 1: Create Vault Directory

```bash
# Create vault directory (or use existing Obsidian vault)
mkdir AI_Employee_Vault
cd AI_Employee_Vault

# Create required folders
mkdir Inbox Needs_Action Done Logs Company_Handbook
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
```

**Required variables** (`.env`):

```bash
# Vault Configuration
VAULT_PATH=/absolute/path/to/AI_Employee_Vault

# Watcher Configuration
POLLING_INTERVAL=1.0  # seconds (fallback if events fail)
FILE_EXTENSIONS=.md

# Claude Code Configuration
CLAUDE_CODE_PATH=claude  # or full path if not in PATH

# Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE=true

# Performance Configuration
MAX_CONCURRENT_TASKS=1  # Bronze phase: sequential only
TASK_TIMEOUT=60  # seconds
```

### Step 3: Verify Configuration

```bash
# Run configuration check
python src/main.py check-config

# Expected output:
# ✅ Vault path exists: /path/to/AI_Employee_Vault
# ✅ All required folders present
# ✅ Claude Code CLI accessible
# ✅ Configuration valid
```

---

## Running the System

### Start the AI Employee

```bash
# Start the system (runs in foreground)
python src/main.py start

# Expected output:
# [2026-02-14 10:30:00] INFO: Initializing AI Employee System...
# [2026-02-14 10:30:01] INFO: Vault structure validated
# [2026-02-14 10:30:01] INFO: FileSystem watcher started
# [2026-02-14 10:30:01] INFO: System ready. Monitoring Inbox folder...
```

### Run in Background (Daemon Mode)

```bash
# Start as background process
python src/main.py start --daemon

# Check status
python src/main.py status

# Stop daemon
python src/main.py stop
```

### View Logs

```bash
# Tail system logs
tail -f logs/system.log

# View today's audit log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).md

# View dashboard
cat AI_Employee_Vault/Dashboard.md
```

---

## Creating Your First Task

### Step 1: Create Task File

Create a file `AI_Employee_Vault/Inbox/task-001.md`:

```markdown
---
task_id: 550e8400-e29b-41d4-a716-446655440000
title: Test task - Say hello
priority: P1
status: inbox
created_at: 2026-02-14T10:30:00Z
tags: [test, hello]
---

# Task: Say Hello

Please respond with a friendly greeting and confirm the system is working.
```

### Step 2: Watch the Magic

The system will automatically:

1. **Detect** the file within 2 seconds
2. **Move** it to `Needs_Action/` folder
3. **Process** it through Claude Code
4. **Move** it to `Done/` folder
5. **Update** Dashboard.md with results
6. **Log** all actions to `Logs/YYYY-MM-DD.md`

### Step 3: Check Results

```bash
# View dashboard
cat AI_Employee_Vault/Dashboard.md

# View processed task
cat AI_Employee_Vault/Done/task-001.md

# View audit log
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).md
```

---

## Dashboard Overview

The `Dashboard.md` file shows real-time system status:

```markdown
# AI Employee Dashboard

**Last Updated**: 2026-02-14 10:45:30
**System Status**: 🟢 Running
**Uptime**: 0.25 hours

## Task Counts

- 📥 **Inbox**: 0
- ⚙️ **Needs Action**: 0
- ✅ **Done**: 1

## Performance Metrics

- **Total Processed**: 1 task
- **Average Processing Time**: 15.2 seconds
- **Success Rate**: 100.0%
- **Errors (24h)**: 0

## Recent Activity

1. **10:45:15** - Processed task: "Test task - Say hello" (P1) ✅

## System Health

- Memory Usage: 87 MB / 500 MB (17%)
- Disk Space: 45 GB available
- Watcher Status: Active
- Last Error: None
```

---

## Common Tasks

### Add Multiple Tasks

```bash
# Create multiple task files
for i in {1..5}; do
  cat > AI_Employee_Vault/Inbox/task-00$i.md <<EOF
---
task_id: $(uuidgen)
title: Task $i
priority: P2
status: inbox
created_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---

# Task $i

This is task number $i.
EOF
done
```

### Monitor System Activity

```bash
# Watch dashboard updates in real-time
watch -n 1 cat AI_Employee_Vault/Dashboard.md

# Tail audit logs
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).md
```

### Graceful Shutdown

```bash
# Stop the system gracefully
# Press Ctrl+C in foreground mode, or:
python src/main.py stop

# Expected output:
# [2026-02-14 11:00:00] INFO: Shutdown signal received
# [2026-02-14 11:00:00] INFO: Stopping FileSystem watcher...
# [2026-02-14 11:00:01] INFO: Completing current task...
# [2026-02-14 11:00:02] INFO: System stopped gracefully
```

---

## Troubleshooting

### Issue: System doesn't detect files

**Symptoms**: Files stay in Inbox, no processing occurs

**Solutions**:
1. Check vault path in `.env` is correct and absolute
2. Verify file permissions (read/write access)
3. Check file extension is `.md`
4. Review logs: `tail -f logs/system.log`

### Issue: Claude Code not found

**Symptoms**: Error "Claude Code CLI not accessible"

**Solutions**:
1. Verify Claude Code is installed: `claude --version`
2. Add Claude Code to PATH, or set full path in `.env`
3. Check Claude Code configuration: `claude config`

### Issue: Tasks fail to process

**Symptoms**: Tasks move to Needs_Action but never to Done

**Solutions**:
1. Check task file format (valid YAML frontmatter)
2. Review error logs: `cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).md`
3. Verify Claude Code is responding: `echo "test" | claude`
4. Check task timeout setting in `.env`

### Issue: High memory usage

**Symptoms**: System uses >500MB memory

**Solutions**:
1. Reduce concurrent tasks (should be 1 in Bronze)
2. Check for memory leaks: `python src/main.py diagnose`
3. Restart system to clear memory
4. Review large task files (>1MB)

### Issue: Dashboard not updating

**Symptoms**: Dashboard shows stale data

**Solutions**:
1. Check file permissions on Dashboard.md
2. Verify atomic write operations (temp file + rename)
3. Review dashboard update logs
4. Manually trigger update: `python src/main.py update-dashboard`

---

## Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_filesystem_watcher.py

# Run with coverage
pytest --cov=src tests/
```

### Run Integration Tests

```bash
# Run end-to-end workflow test
pytest tests/integration/test_workflow.py -v

# Run concurrent tasks test
pytest tests/integration/test_concurrent_tasks.py -v
```

### Performance Testing

```bash
# Load test: 100 tasks
python tests/performance/load_test.py --tasks 100

# Memory profiling
python -m memory_profiler src/main.py start --duration 60
```

---

## Next Steps

### Explore Features

1. **Add more tasks** to Inbox and watch them process
2. **Monitor Dashboard** to see real-time metrics
3. **Review audit logs** to understand system behavior
4. **Experiment with priorities** (P1, P2, P3)

### Customize Configuration

1. Adjust polling interval for faster/slower detection
2. Configure log levels for more/less verbosity
3. Set task timeout based on your workload

### Prepare for Silver Phase

Bronze phase is complete when:
- ✅ System runs continuously for 24 hours
- ✅ 100 tasks processed successfully
- ✅ Dashboard updates in real-time
- ✅ All actions logged correctly
- ✅ Memory usage stays under 500MB

---

## Support

### Documentation

- [Full Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Data Model](./data-model.md)
- [Task Schema](./contracts/task-schema.yaml)

### Logs

- System logs: `logs/system.log`
- Audit logs: `AI_Employee_Vault/Logs/YYYY-MM-DD.md`
- Dashboard: `AI_Employee_Vault/Dashboard.md`

### Commands Reference

```bash
# Start system
python src/main.py start [--daemon]

# Stop system
python src/main.py stop

# Check status
python src/main.py status

# Verify configuration
python src/main.py check-config

# Update dashboard manually
python src/main.py update-dashboard

# Run diagnostics
python src/main.py diagnose

# View help
python src/main.py --help
```

---

## Success Criteria

Your Bronze phase is ready when:

- [x] System detects files within 2 seconds
- [x] Tasks process within 30 seconds
- [x] Dashboard updates within 1 second
- [x] System runs 24 hours without crashes
- [x] Memory usage stays under 500MB
- [x] All actions are logged
- [x] 100% of file operations stay within vault

**Congratulations!** You now have a working autonomous AI employee system. Ready for Silver phase (Gmail integration) when you are.

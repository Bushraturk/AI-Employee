# Agent Skills Documentation

This directory contains Agent Skills for the AI Employee system. Agent Skills are command definitions that Claude Code can invoke to perform specific tasks.

## Available Skills

### 1. process-task
**File**: `process-task.command.md`
**Purpose**: Process a task file using Claude Code reasoning
**Usage**: `/process-task <task_file_path>`

Analyzes task requirements, generates responses, and provides action plans.

### 2. validate-task
**File**: `validate-task.command.md`
**Purpose**: Validate task file structure and metadata
**Usage**: `/validate-task <task_file_path>`

Checks YAML frontmatter, validates fields, ensures compliance with task schema.

### 3. update-dashboard
**File**: `update-dashboard.command.md`
**Purpose**: Update Dashboard.md with current metrics
**Usage**: `/update-dashboard`

Counts tasks, calculates metrics, generates dashboard content.

### 4. log-action
**File**: `log-action.command.md`
**Purpose**: Log actions to audit trail
**Usage**: `/log-action --type <type> --result <result> [options]`

Creates timestamped log entries in Logs/YYYY-MM-DD.md files.

## Architecture

```
Python Orchestrator
    ↓
Claude Code CLI
    ↓
Agent Skills (.command.md)
    ↓
Vault Operations
```

## Bronze Phase Compliance

All AI functionality is implemented as Agent Skills per Bronze phase requirements:
- ✅ Task processing via agent skill
- ✅ Task validation via agent skill
- ✅ Dashboard updates via agent skill
- ✅ Audit logging via agent skill

## Usage in Code

The orchestrator invokes agent skills through Claude Code CLI:

```python
# Example: Process task using agent skill
prompt = f"Use the /process-task agent skill to process this task: ..."
result = subprocess.run([claude_path], input=prompt, ...)
```

## Future Skills (Silver/Gold Phase)

- `classify-email` - Classify incoming emails
- `draft-reply` - Generate email responses
- `execute-tool` - Execute MCP tools safely
- `validate-action` - Validate actions before execution

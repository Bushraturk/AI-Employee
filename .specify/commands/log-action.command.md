---
name: log-action
description: Log an action to the audit trail in Logs/YYYY-MM-DD.md
version: 1.0.0
author: AI Employee System
tags: [bronze, logging, agent-skill]
---

# Log Action Command

This agent skill logs actions to the audit trail for compliance and debugging.

## Usage

```bash
/log-action --type <action_type> --result <result> [--task-id <task_id>] [--details <details>]
```

## Parameters

- `--type`: Action type (FILE_DETECTED, TASK_PROCESSED, FILE_MOVED, etc.)
- `--result`: Result status (success/failure/partial)
- `--task-id`: Optional task reference UUID
- `--details`: Optional additional context

## Behavior

1. Generate unique action ID (UUID)
2. Get current timestamp (ISO 8601)
3. Format log entry as Markdown
4. Append to today's log file (Logs/YYYY-MM-DD.md)
5. Create log file with header if it doesn't exist

## Log Entry Format

```markdown
## 16:26:05 - TASK_PROCESSED

- **Action ID**: 7de74b81-8504-4264-9794-825e8f208fb1
- **Result**: success
- **Task Reference**: 550e8400-e29b-41d4-a716-446655440003
- **Details**: Processed task: System verification test (Priority: P1)
- **Duration**: 44ms

---
```

## Action Types

- `FILE_DETECTED` - New file found in Inbox
- `FILE_MOVED` - Task file moved between folders
- `TASK_PARSED` - Task file parsed successfully
- `TASK_PROCESSED` - Claude Code processing completed
- `DASHBOARD_UPDATED` - Dashboard.md updated
- `ERROR` - Error occurred during operation
- `SYSTEM_STARTED` - System initialization
- `SYSTEM_STOPPED` - System shutdown

## Example

```bash
/log-action --type TASK_PROCESSED --result success --task-id 550e8400-e29b-41d4-a716-446655440003 --details "Processed task: Test (Priority: P1)"
```

## Safety

- Append-only (never overwrites)
- Creates daily log files automatically
- All timestamps in ISO 8601 format

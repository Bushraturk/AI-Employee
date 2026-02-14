---
name: update-dashboard
description: Update the Dashboard.md with current system metrics and status
version: 1.0.0
author: AI Employee System
tags: [bronze, dashboard, agent-skill]
---

# Update Dashboard Command

This agent skill updates the Dashboard.md file with current system metrics and status.

## Usage

```bash
/update-dashboard
```

## Parameters

None - reads current state from vault folders

## Behavior

1. Count tasks in each folder (Inbox, Needs_Action, Done)
2. Calculate performance metrics (avg processing time, success rate)
3. Get recent activity from Done folder
4. Generate Dashboard.md content
5. Write atomically to Dashboard.md

## Output Format

Updates Dashboard.md with:
- Last updated timestamp
- System status (IDLE/ACTIVE/PROCESSING)
- Task counts by folder
- Performance metrics
- Recent activity (last 10 tasks)
- System health indicators

## Example Dashboard

```markdown
# AI Employee Dashboard

**Last Updated**: 2026-02-14 16:26:05
**System Status**: [IDLE]
**Uptime**: 2.5 hours

## Task Counts

- **Inbox**: 0
- **Needs Action**: 0
- **Done**: 5

## Performance Metrics

- **Total Processed**: 5 tasks
- **Average Processing Time**: 28.3 seconds
- **Success Rate**: 100.0%
- **Errors (24h)**: 0

## Recent Activity

1. **16:25:46** - Processed task: system-test
2. **09:45:21** - Processed task: verification-test
...
```

## Safety

- Uses atomic writes (temp file + rename)
- Only writes to Dashboard.md
- Preserves existing vault structure

# Data Model: Bronze Phase - Local Foundation

**Feature**: 001-bronze-foundation
**Date**: 2026-02-14
**Phase**: Phase 1 - Design

## Overview

This document defines the core entities and their relationships for the Bronze phase autonomous AI employee system. All entities are represented as Markdown files or in-memory Python objects that serialize to Markdown.

---

## Entity 1: Task

**Purpose**: Represents a work item to be processed by the AI employee.

**Storage**: Markdown file with YAML frontmatter

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| task_id | string | Yes | Unique identifier (UUID v4) | Must be valid UUID |
| title | string | Yes | Brief task description (max 200 chars) | Non-empty, max 200 chars |
| description | string | Yes | Full task details (Markdown body) | Non-empty |
| priority | enum | No | Task priority (P1/P2/P3) | Default: P2 |
| status | enum | Yes | Current workflow stage | inbox/needs_action/done |
| created_at | datetime | Yes | Task creation timestamp (ISO 8601) | Valid ISO 8601 |
| processed_at | datetime | No | Task processing completion timestamp | Valid ISO 8601 or null |
| file_path | string | Yes | Absolute path to task file | Within vault boundary |
| tags | list[string] | No | User-defined tags | Max 10 tags |
| assigned_to | string | No | Future: user assignment | Not used in Bronze |

**State Transitions**:

```
inbox → needs_action → done
  ↓          ↓
(error)   (error)
```

**Lifecycle**:
1. Created in Inbox folder (status: inbox)
2. Detected by FileSystem watcher
3. Moved to Needs_Action (status: needs_action)
4. Processed by Claude Code
5. Moved to Done (status: done, processed_at set)

**Example File** (Inbox/task-001.md):

```markdown
---
task_id: 550e8400-e29b-41d4-a716-446655440000
title: Review Q1 financial report
priority: P1
status: inbox
created_at: 2026-02-14T10:30:00Z
tags: [finance, quarterly, review]
---

# Task: Review Q1 Financial Report

Please review the Q1 2026 financial report and provide:
- Summary of key metrics
- Comparison to Q4 2025
- Recommendations for Q2

Report location: Company_Handbook/Finance/Q1-2026-Report.pdf
```

---

## Entity 2: Watcher

**Purpose**: Abstract interface for monitoring input sources (FileSystem, Gmail, WhatsApp).

**Storage**: In-memory Python object (no persistence needed)

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| watcher_id | string | Yes | Unique identifier | Non-empty |
| watcher_type | enum | Yes | Type of watcher | filesystem/gmail/whatsapp |
| status | enum | Yes | Current operational status | running/stopped/error |
| last_check_at | datetime | No | Last successful check timestamp | Valid ISO 8601 or null |
| error_count | int | Yes | Consecutive error count | >= 0 |
| config | dict | Yes | Watcher-specific configuration | Varies by type |

**Methods** (Abstract Interface):

```python
def start() -> None:
    """Begin monitoring input source"""

def stop() -> None:
    """Gracefully shutdown monitoring"""

def get_new_tasks() -> list[Task]:
    """Return list of newly detected tasks"""

def mark_processed(task_id: str) -> None:
    """Acknowledge task has been handled"""
```

**FileSystem Watcher Config**:

```python
{
    "vault_path": "/path/to/AI_Employee_Vault",
    "inbox_folder": "Inbox",
    "watch_recursive": False,
    "file_extensions": [".md"],
    "polling_interval": 1.0  # seconds (fallback if events fail)
}
```

**State Transitions**:

```
stopped → running → stopped
            ↓
          error → running (after recovery)
```

---

## Entity 3: Action

**Purpose**: Represents an operation performed by the system (for audit trail).

**Storage**: Markdown log entry in Logs/YYYY-MM-DD.md

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| action_id | string | Yes | Unique identifier (UUID v4) | Must be valid UUID |
| action_type | enum | Yes | Type of action performed | See action types below |
| timestamp | datetime | Yes | When action occurred (ISO 8601) | Valid ISO 8601 |
| task_reference | string | No | Related task_id (if applicable) | Valid UUID or null |
| result | string | Yes | Action outcome (success/failure) | success/failure/partial |
| details | string | No | Additional context or error message | Max 1000 chars |
| duration_ms | int | No | Action execution time in milliseconds | >= 0 |

**Action Types**:

- `FILE_DETECTED` - New file found in Inbox
- `FILE_MOVED` - Task file moved between folders
- `TASK_PARSED` - Task file parsed successfully
- `TASK_PROCESSED` - Claude Code processing completed
- `DASHBOARD_UPDATED` - Dashboard.md updated
- `LOG_WRITTEN` - Log entry created
- `ERROR` - Error occurred during operation
- `SYSTEM_STARTED` - System initialization
- `SYSTEM_STOPPED` - System shutdown

**Example Log Entry** (Logs/2026-02-14.md):

```markdown
## 10:30:15 - FILE_DETECTED

- **Action ID**: 7c9e6679-7425-40de-944b-e07fc1f90ae7
- **Task Reference**: 550e8400-e29b-41d4-a716-446655440000
- **Result**: success
- **Details**: Detected new task file: task-001.md
- **Duration**: 5ms

---

## 10:30:17 - TASK_PROCESSED

- **Action ID**: 3f2504e0-4f89-11d3-9a0c-0305e82c3301
- **Task Reference**: 550e8400-e29b-41d4-a716-446655440000
- **Result**: success
- **Details**: Claude Code processing completed. Priority: P1, Actions: 3
- **Duration**: 2847ms

---
```

---

## Entity 4: Dashboard Metrics

**Purpose**: System status and performance metrics displayed in Dashboard.md.

**Storage**: Markdown file (AI_Employee_Vault/Dashboard.md)

**Attributes**:

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| inbox_count | int | Yes | Number of tasks in Inbox | >= 0 |
| needs_action_count | int | Yes | Number of tasks in Needs_Action | >= 0 |
| done_count | int | Yes | Number of tasks in Done | >= 0 |
| total_processed | int | Yes | Lifetime task count | >= 0 |
| average_processing_time | float | No | Average task processing time (seconds) | >= 0 or null |
| success_rate | float | No | Percentage of successful tasks | 0.0-100.0 or null |
| system_status | enum | Yes | Current system state | running/idle/error |
| last_updated | datetime | Yes | Dashboard last update time | Valid ISO 8601 |
| uptime_hours | float | Yes | Hours since system start | >= 0 |
| error_count_24h | int | Yes | Errors in last 24 hours | >= 0 |

**Computed Metrics**:

- `average_processing_time` = sum(task durations) / total_processed
- `success_rate` = (successful_tasks / total_processed) × 100
- `uptime_hours` = (current_time - system_start_time) / 3600

**Example Dashboard.md**:

```markdown
# AI Employee Dashboard

**Last Updated**: 2026-02-14 10:45:30
**System Status**: 🟢 Running
**Uptime**: 2.5 hours

## Task Counts

- 📥 **Inbox**: 0
- ⚙️ **Needs Action**: 1
- ✅ **Done**: 12

## Performance Metrics

- **Total Processed**: 12 tasks
- **Average Processing Time**: 28.3 seconds
- **Success Rate**: 100.0%
- **Errors (24h)**: 0

## Recent Activity

1. **10:45:15** - Processed task: "Review Q1 financial report" (P1) ✅
2. **10:30:22** - Processed task: "Update team meeting notes" (P2) ✅
3. **10:15:08** - Processed task: "Draft email response" (P3) ✅

## System Health

- Memory Usage: 87 MB / 500 MB (17%)
- Disk Space: 45 GB available
- Watcher Status: Active
- Last Error: None
```

---

## Relationships

### Task ↔ Action
- One Task can have many Actions (1:N)
- Each Action may reference one Task (N:1)
- Relationship tracked via `task_reference` in Action

### Watcher → Task
- One Watcher detects many Tasks (1:N)
- Tasks don't reference their source Watcher in Bronze phase
- Relationship implicit through file detection

### Dashboard Metrics ← Task
- Dashboard aggregates data from all Tasks
- No direct reference, computed from Task files
- Real-time aggregation on each update

---

## Validation Rules

### Task Validation

1. **task_id**: Must be valid UUID v4 format
2. **title**: Non-empty, max 200 characters, no newlines
3. **priority**: Must be P1, P2, or P3 (default P2)
4. **status**: Must match current folder location
5. **created_at**: Must be valid ISO 8601, not in future
6. **file_path**: Must be within vault boundary, must exist

### File Path Validation

```python
def validate_vault_path(file_path: Path, vault_root: Path) -> bool:
    """Ensure file is within vault boundary"""
    resolved_path = file_path.resolve()
    resolved_vault = vault_root.resolve()
    return resolved_path.is_relative_to(resolved_vault)
```

### Timestamp Validation

All timestamps must be ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

Example: `2026-02-14T10:30:00Z`

---

## Error Handling

### Malformed Task Files

- Missing required fields → Log error, skip task
- Invalid YAML frontmatter → Log error, skip task
- Empty description → Log warning, process with default
- Invalid UUID → Generate new UUID, log warning

### File Operation Errors

- Permission denied → Log error, retry with backoff
- Disk full → Log critical error, pause processing
- File locked → Wait and retry (max 3 attempts)
- Path outside vault → Log security error, reject task

---

## Future Extensions (Silver/Gold/Platinum)

### Task Entity Extensions

- `assigned_to`: User assignment (multi-user support)
- `dependencies`: Task dependencies (workflow support)
- `scheduled_at`: Scheduled execution time
- `recurrence`: Recurring task pattern

### New Entities

- **User**: Multi-user support (Silver)
- **Tool**: MCP tool registry (Gold)
- **Metric**: Performance tracking (Platinum)
- **Improvement**: Self-improvement suggestions (Platinum)

---

## Data Integrity

### Atomic Operations

- File moves use `os.replace()` for atomicity
- Dashboard updates use temp file + rename
- Log writes are append-only (no overwrites)

### Consistency Checks

- Task status must match folder location
- Dashboard counts must match actual file counts
- Log entries must have unique action_ids

### Recovery Procedures

- On startup, scan all folders and reconcile state
- Orphaned files (wrong status) → Move to correct folder
- Missing task_id → Generate new UUID and log warning

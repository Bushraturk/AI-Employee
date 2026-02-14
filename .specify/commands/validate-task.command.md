---
name: validate-task
description: Validate a task file's structure and metadata
version: 1.0.0
author: AI Employee System
tags: [bronze, validation, agent-skill]
---

# Validate Task Command

This agent skill validates task files to ensure they meet requirements before processing.

## Usage

```bash
/validate-task <task_file_path>
```

## Parameters

- `task_file_path`: Absolute path to the task Markdown file

## Behavior

1. Check file exists and is readable
2. Parse YAML frontmatter
3. Validate required fields (task_id, title, status, created_at)
4. Validate field formats (UUID, ISO 8601, priority levels)
5. Check file path is within vault boundaries
6. Return validation result

## Validation Rules

### Required Fields
- `task_id`: Must be valid UUID v4
- `title`: Non-empty, max 200 characters, no newlines
- `status`: Must be inbox/needs_action/done
- `created_at`: Valid ISO 8601 timestamp, not in future

### Optional Fields
- `priority`: P1/P2/P3 (defaults to P2)
- `tags`: Array of strings (max 10 tags)
- `processed_at`: Valid ISO 8601 or null

### File Path
- Must be within vault directory
- Must be .md extension
- Must be readable

## Output Format

Returns JSON with:
- `valid`: boolean
- `errors`: array of error messages (if invalid)
- `warnings`: array of warning messages
- `task_data`: parsed task data (if valid)

## Example Success

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "task_data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440003",
    "title": "System verification test",
    "priority": "P1",
    "status": "inbox",
    "created_at": "2026-02-14T08:00:00Z"
  }
}
```

## Example Failure

```json
{
  "valid": false,
  "errors": [
    "Missing required field: task_id",
    "Invalid timestamp format: created_at"
  ],
  "warnings": [
    "Title exceeds recommended length (150 chars)"
  ],
  "task_data": null
}
```

## Safety

- Read-only operation
- Does not modify files
- Validates path boundaries

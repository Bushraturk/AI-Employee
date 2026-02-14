---
name: process-task
description: Process a task file from the AI Employee vault using Claude Code reasoning
version: 1.0.0
author: AI Employee System
tags: [bronze, task-processing, agent-skill]
---

# Process Task Command

This agent skill processes task files from the AI Employee vault, providing reasoning and action planning.

## Usage

```bash
/process-task <task_file_path>
```

## Parameters

- `task_file_path`: Absolute path to the task Markdown file

## Behavior

1. Read the task file from the vault
2. Parse YAML frontmatter (task_id, title, priority, status, created_at)
3. Extract task description from Markdown body
4. Analyze task requirements and priority
5. Generate appropriate response or action plan
6. Return structured output for orchestrator

## Input Format

Task files must be Markdown with YAML frontmatter:

```yaml
---
task_id: 550e8400-e29b-41d4-a716-446655440000
title: Task title here
priority: P1
status: inbox
created_at: 2026-02-14T10:00:00Z
tags: [tag1, tag2]
---

# Task Description

Task details go here...
```

## Output Format

Returns JSON with:
- `task_id`: Task identifier
- `status`: Processing status (success/failure)
- `response`: AI-generated response or action plan
- `processed_at`: ISO 8601 timestamp
- `actions`: List of recommended actions (if any)

## Example

```bash
/process-task /path/to/AI_Employee_Vault/Needs_Action/task-001.md
```

## Implementation

This skill should be invoked by the Python orchestrator when a task needs AI processing.

## Safety

- Only reads files within vault boundaries
- Does not execute external commands
- Logs all processing to audit trail

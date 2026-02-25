# Data Model: Platinum Tier AI Employee

**Date**: 2026-02-25
**Feature**: 001-platinum-employee
**Purpose**: Define data structures, relationships, and validation rules for the dual-agent system

## Overview

The Platinum Tier AI Employee uses markdown files as the primary data storage mechanism, following the "Markdown as System Memory" principle. This document defines the structure, validation rules, and relationships for all data entities in the system.

## Core Entities

### 1. Action File

**Purpose**: Represents a detected event requiring processing (email, WhatsApp message, transaction, file drop)

**Location**: `vault/Needs_Action/{domain}/`

**Frontmatter Schema**:
```yaml
---
id: string                    # Unique identifier (UUID)
type: enum                    # email | whatsapp | transaction | file_drop
source: string                # Source identifier (email address, phone number, account)
priority: enum                # high | medium | low
status: enum                  # pending | processing | completed | failed
created: datetime             # ISO 8601 timestamp
domain: enum                  # email | social | accounting | whatsapp
metadata:                     # Type-specific metadata
  # For email:
  from: string
  subject: string
  message_id: string
  # For whatsapp:
  sender: string
  keywords: array[string]
  # For transaction:
  amount: number
  account: string
  description: string
---
```

**Body Content**:
- Human-readable description of the event
- Suggested actions (checklist format)
- Relevant context for processing

**Validation Rules**:
- `id` must be unique across all action files
- `type` must be one of the defined enum values
- `created` must be valid ISO 8601 timestamp
- `status` must progress: pending → processing → completed/failed
- `metadata` must contain required fields for the specified type

**State Transitions**:
```
pending → processing (when agent claims task)
processing → completed (when action executed successfully)
processing → failed (when action execution fails)
```

**Relationships**:
- One Action File → Zero or One Approval Request (if requires approval)
- One Action File → One or More Audit Log Entries (for all state changes)

### 2. Approval Request

**Purpose**: Represents a draft action requiring human approval before execution

**Location**: `vault/Pending_Approval/{domain}/`

**Frontmatter Schema**:
```yaml
---
id: string                    # Unique identifier (UUID)
action_type: enum             # email_send | social_post | accounting_entry | whatsapp_send | payment
target: string                # Target identifier (email address, platform, account)
created: datetime             # ISO 8601 timestamp
expires: datetime             # ISO 8601 timestamp (24 hours from created)
status: enum                  # pending | approved | rejected | expired
action_file_id: string        # Reference to originating action file
parameters:                   # Action-specific parameters
  # For email_send:
  to: string
  subject: string
  body: string
  attachments: array[string]
  # For social_post:
  platform: enum              # facebook | instagram | twitter | linkedin
  content: string
  media: array[string]
  scheduled_time: datetime
  # For accounting_entry:
  entry_type: enum            # invoice | payment | expense
  amount: number
  account_code: string
  description: string
  # For whatsapp_send:
  recipient: string
  message: string
  # For payment:
  recipient: string
  amount: number
  reference: string
---
```

**Body Content**:
- Detailed description of the proposed action
- Context and rationale for the action
- Instructions for approval/rejection

**Validation Rules**:
- `id` must be unique across all approval requests
- `expires` must be after `created`
- `action_file_id` must reference a valid action file
- `parameters` must contain required fields for the specified action_type
- `status` must be pending when created

**State Transitions**:
```
pending → approved (when moved to Approved folder)
pending → rejected (when moved to Rejected folder)
pending → expired (when current time > expires)
```

**Relationships**:
- One Approval Request → One Action File (originating event)
- One Approval Request → One Audit Log Entry (when approved/rejected/expired)

### 3. Agent State

**Purpose**: Represents the current state of an agent (cloud or local)

**Location**: `vault/In_Progress/{agent}/agent_state.md`

**Frontmatter Schema**:
```yaml
---
agent_id: enum                # cloud | local
status: enum                  # running | stopped | error
last_heartbeat: datetime      # ISO 8601 timestamp
capabilities: array[string]   # List of agent capabilities
claimed_tasks: array[string]  # List of action file IDs currently being processed
version: string               # Agent version
---
```

**Body Content**:
- Current agent status description
- Recent activities
- Error messages (if status is error)

**Validation Rules**:
- `agent_id` must be either "cloud" or "local"
- `last_heartbeat` must be updated every 60 seconds
- `claimed_tasks` must reference valid action file IDs
- Agent is considered dead if `last_heartbeat` is older than 5 minutes

**Relationships**:
- One Agent State → Many Action Files (claimed tasks)

### 4. Audit Log Entry

**Purpose**: Represents a completed action with full audit trail

**Location**: `vault/Logs/{YYYY-MM-DD}.md`

**Format**: Append-only markdown file with entries in JSON format

**Entry Schema**:
```json
{
  "timestamp": "2026-02-25T10:30:00Z",
  "action_type": "email_send",
  "actor": "local",
  "target": "client@example.com",
  "parameters": {
    "subject": "Invoice #123",
    "body_preview": "Please find attached..."
  },
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success",
  "error": null,
  "action_file_id": "uuid-123",
  "approval_request_id": "uuid-456"
}
```

**Validation Rules**:
- `timestamp` must be valid ISO 8601 timestamp
- `actor` must be either "cloud" or "local"
- `result` must be either "success" or "failure"
- If `result` is "failure", `error` must be non-null
- Entries must be appended only (no modifications or deletions)

**Relationships**:
- One Audit Log Entry → One Action File (originating event)
- One Audit Log Entry → Zero or One Approval Request (if approval required)

### 5. Dashboard State

**Purpose**: Represents current system status and metrics

**Location**: `vault/Dashboard.md`

**Frontmatter Schema**:
```yaml
---
last_updated: datetime        # ISO 8601 timestamp
updated_by: enum              # local (only local agent can write)
system_health:
  cloud_agent: enum           # running | stopped | error
  local_agent: enum           # running | stopped | error
  vault_sync: enum            # synced | syncing | error
  odoo: enum                  # available | unavailable
pending_approvals:
  email: number
  social: number
  accounting: number
  whatsapp: number
  total: number
---
```

**Body Content**:
- Recent activities (last 10 actions)
- System health status
- Pending approvals summary
- Upcoming deadlines
- Alerts and notifications

**Validation Rules**:
- `updated_by` must always be "local" (single-writer rule)
- `last_updated` must be current timestamp
- `pending_approvals.total` must equal sum of domain counts

**Relationships**:
- Dashboard State → Many Action Files (recent activities)
- Dashboard State → Many Approval Requests (pending approvals)

### 6. Business Goal

**Purpose**: Represents strategic objectives and metrics for business intelligence

**Location**: `vault/Business_Goals.md`

**Frontmatter Schema**:
```yaml
---
last_updated: datetime        # ISO 8601 timestamp
review_frequency: enum        # daily | weekly | monthly
---
```

**Body Content**:
- Revenue targets
- Key metrics to track
- Active projects
- Subscription audit rules
- Alert thresholds

**Validation Rules**:
- Must contain at least one revenue target
- Metrics must have both target and alert threshold
- Projects must have due date and budget

**Relationships**:
- Business Goal → Many Audit Log Entries (for metrics calculation)

### 7. Watcher State

**Purpose**: Represents the state of a monitoring process

**Location**: `vault/In_Progress/{agent}/watcher_{source}.md`

**Frontmatter Schema**:
```yaml
---
watcher_id: string            # Unique identifier
source: enum                  # gmail | whatsapp | bank
agent: enum                   # cloud | local
status: enum                  # running | stopped | error
check_interval: number        # Seconds between checks
last_check: datetime          # ISO 8601 timestamp
processed_ids: array[string]  # List of processed item IDs (for deduplication)
---
```

**Body Content**:
- Watcher configuration
- Recent detections
- Error messages (if status is error)

**Validation Rules**:
- `source` must match agent capabilities (gmail on cloud, whatsapp/bank on local)
- `last_check` must be updated after each check
- `processed_ids` must be maintained to prevent duplicate action files
- Watcher is considered stale if `last_check` is older than 2 * `check_interval`

**Relationships**:
- One Watcher State → Many Action Files (detected events)

### 8. Odoo Entry Draft

**Purpose**: Represents a draft accounting entry for Odoo

**Location**: `vault/Pending_Approval/accounting/`

**Frontmatter Schema**:
```yaml
---
id: string                    # Unique identifier (UUID)
entry_type: enum              # invoice | payment | expense
amount: number                # Transaction amount
currency: string              # ISO 4217 currency code (default: USD)
account_code: string          # Odoo account code
partner_id: string            # Odoo partner ID (customer/vendor)
date: date                    # Transaction date (YYYY-MM-DD)
description: string           # Transaction description
created: datetime             # ISO 8601 timestamp
status: enum                  # draft | pending_approval | approved | posted
transaction_id: string        # Reference to bank transaction (if applicable)
---
```

**Body Content**:
- Detailed transaction description
- Supporting documentation references
- Account code justification

**Validation Rules**:
- `amount` must be positive number
- `currency` must be valid ISO 4217 code
- `account_code` must exist in Odoo chart of accounts
- `partner_id` must exist in Odoo partners
- `date` must not be in the future

**State Transitions**:
```
draft → pending_approval (when cloud agent creates draft)
pending_approval → approved (when moved to Approved folder)
approved → posted (when local agent posts to Odoo)
```

**Relationships**:
- One Odoo Entry Draft → Zero or One Action File (originating transaction)
- One Odoo Entry Draft → One Approval Request (for posting)

## Vault Folder Structure

```
vault/
├── Needs_Action/           # New events detected by watchers
│   ├── email/              # Email events
│   ├── social/             # Social media events (future)
│   ├── accounting/         # Financial transaction events
│   └── whatsapp/           # WhatsApp message events
├── In_Progress/            # Tasks currently being processed
│   ├── cloud/              # Cloud agent claimed tasks
│   │   ├── agent_state.md
│   │   └── watcher_gmail.md
│   └── local/              # Local agent claimed tasks
│       ├── agent_state.md
│       ├── watcher_whatsapp.md
│       └── watcher_finance.md
├── Pending_Approval/       # Draft actions requiring approval
│   ├── email/              # Email send approvals
│   ├── social/             # Social post approvals
│   ├── accounting/         # Accounting entry approvals
│   └── whatsapp/           # WhatsApp send approvals
├── Approved/               # Approved actions ready for execution
├── Rejected/               # Rejected actions (for learning)
├── Done/                   # Completed actions (archived)
├── Plans/                  # Generated plans and strategies
├── Logs/                   # Audit logs (one file per day)
├── Updates/                # Cloud agent updates (for Dashboard merge)
├── Dashboard.md            # System status (local agent only)
├── Company_Handbook.md     # Business rules and context
└── Business_Goals.md       # Strategic objectives and metrics
```

## File Naming Conventions

### Action Files
Format: `{type}_{source_id}_{timestamp}.md`
Example: `email_msg123_20260225T103000Z.md`

### Approval Requests
Format: `{action_type}_{target_id}_{timestamp}.md`
Example: `email_send_client@example.com_20260225T103000Z.md`

### Audit Logs
Format: `{YYYY-MM-DD}.md`
Example: `2026-02-25.md`

### Watcher State
Format: `watcher_{source}.md`
Example: `watcher_gmail.md`

## Data Validation

### Frontmatter Validation
- All frontmatter must be valid YAML
- Required fields must be present
- Enum fields must have valid values
- Datetime fields must be ISO 8601 format
- Number fields must be valid numbers

### File Validation
- Files must have .md extension
- Files must have frontmatter section (between --- markers)
- Files must have body content (after frontmatter)
- File names must follow naming conventions

### Referential Integrity
- `action_file_id` references must point to existing action files
- `approval_request_id` references must point to existing approval requests
- `claimed_tasks` must reference existing action files
- `processed_ids` must be maintained for deduplication

## Concurrency Control

### Claim-by-Move Rule
- First agent to move file from Needs_Action to In_Progress/{agent}/ owns the task
- Other agents must skip the task if file is already moved
- Atomic file operations (rename, not copy+delete) ensure consistency

### Single-Writer Rule
- Dashboard.md can only be written by local agent
- Cloud agent writes to Updates/ folder
- Local agent merges Updates/ into Dashboard.md

### File Locking
- Use atomic file operations (rename) for moves
- Check file existence before claiming
- Implement retry logic for race conditions

## Data Retention

### Action Files
- Completed action files moved to Done/ folder
- Retained for 90 days
- Archived to compressed format after 90 days

### Approval Requests
- Approved requests moved to Done/ folder
- Rejected requests moved to Rejected/ folder
- Expired requests moved to Expired/ folder
- Retained for 90 days

### Audit Logs
- Retained for minimum 90 days
- Compressed after 30 days
- Archived to long-term storage after 90 days

### Watcher State
- Maintained while watcher is running
- Deleted when watcher stops
- `processed_ids` persisted to prevent duplicates after restart

## Migration Strategy

### From Gold Tier
- Existing vault structure compatible
- Add new folders: Updates/, Pending_Approval/{domain}/
- Add agent_state.md files for cloud and local agents
- Add watcher state files
- No data migration required for existing files

### Version Compatibility
- Frontmatter schema versioned (v1.0.0)
- Backward compatible: new fields optional
- Forward compatible: unknown fields ignored
- Schema version in frontmatter for validation

## Performance Considerations

### File System Operations
- Use buffered I/O for large files
- Implement file caching for frequently accessed files
- Use directory watching (watchdog) instead of polling
- Batch file operations when possible

### Vault Sync
- Sync only changed files (not entire vault)
- Use .gitignore to exclude large files
- Implement sync throttling (max 1 sync per 10 seconds)
- Cache vault state to reduce file system reads

### Deduplication
- Maintain `processed_ids` in watcher state
- Use set data structure for O(1) lookup
- Persist `processed_ids` to disk for restart recovery
- Implement LRU cache for `processed_ids` (max 10,000 items)

## Error Handling

### Invalid Files
- Quarantine invalid files to separate folder
- Log validation errors with file path and reason
- Alert user to manual review
- Provide validation report

### Missing References
- Log warning for missing references
- Continue processing (don't block on missing references)
- Implement reference cleanup job (remove dangling references)

### Corrupted Files
- Detect corrupted files during read
- Quarantine corrupted files
- Attempt recovery from Git history
- Alert user to data loss

## Security Considerations

### Sensitive Data
- Never store credentials in vault files
- Sanitize email content before logging (remove sensitive data)
- Redact financial details in logs (show last 4 digits only)
- Encrypt vault at rest (optional, user-configured)

### Access Control
- Vault files readable by user only (chmod 600)
- Agent processes run as user (not root)
- MCP servers use local sockets (not network)
- Odoo credentials stored on cloud VM only (not in vault)

### Audit Trail
- All file operations logged
- All state changes logged
- All approval decisions logged
- Git history provides version control

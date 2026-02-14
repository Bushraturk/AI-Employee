# Data Model: Silver Tier - Functional Assistant

**Date**: 2026-02-14 | **Feature**: 002-silver-functional | **Phase**: 1

## Purpose

This document defines the core entities, their attributes, relationships, and validation rules for Silver Tier functionality. All entities are stored as Markdown files in the Obsidian vault following the local-first architecture principle.

---

## Entity: Task (Extended from Bronze)

**Description**: Work item detected from any input channel (FileSystem, Gmail, WhatsApp, LinkedIn)

**Storage Location**: `vault/Inbox/*.md` (new), `vault/Needs_Action/*.md` (processing), `vault/Done/*.md` (completed)

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| task_id | string | Yes | Unique identifier (UUID) | UUID v4 format |
| title | string | Yes | Brief task description | 1-200 characters |
| description | string | Yes | Full task details | 1-5000 characters |
| priority | enum | Yes | Task priority level | P1, P2, P3 |
| status | enum | Yes | Current task state | inbox, needs_action, done |
| channel | enum | Yes | Source channel | filesystem, gmail, whatsapp, linkedin |
| channel_metadata | object | Yes | Channel-specific data | See Channel Metadata below |
| category | string | No | Task classification | support, sales, internal, etc. |
| created_at | datetime | Yes | Task creation timestamp | ISO 8601 format |
| processed_at | datetime | No | Processing completion time | ISO 8601 format |
| due_date | datetime | No | Task deadline | ISO 8601 format |
| assigned_to | string | No | Assignee name | 1-100 characters |
| tags | array[string] | No | Task tags | Max 10 tags |

**Channel Metadata** (varies by channel):

```yaml
# Gmail
channel_metadata:
  sender: "user@example.com"
  subject: "Email subject"
  message_id: "<unique-message-id>"
  thread_id: "thread-123"
  labels: ["INBOX", "IMPORTANT"]

# WhatsApp
channel_metadata:
  sender: "+1234567890"
  sender_name: "John Doe"
  message_id: "msg-456"
  chat_type: "direct|group"
  group_name: "Team Chat"  # if group

# LinkedIn
channel_metadata:
  sender_profile: "https://linkedin.com/in/johndoe"
  sender_name: "John Doe"
  post_url: "https://linkedin.com/posts/..."  # if from post
  message_id: "msg-789"  # if from message
  content_type: "message|mention|comment"

# FileSystem (from Bronze)
channel_metadata:
  file_path: "/path/to/file.md"
  file_size: 1024
```

**Validation Rules**:
- task_id must be unique across all tasks
- created_at must be in the past or present
- due_date (if present) must be in the future
- priority must be one of: P1, P2, P3
- channel must be one of: filesystem, gmail, whatsapp, linkedin
- channel_metadata must contain required fields for the channel type

**State Transitions**:
```
inbox → needs_action → done
       ↓
    (rejected/cancelled)
```

**Relationships**:
- Task → Plan (one-to-one, optional): Complex tasks may have associated Plan.md
- Task → Approval (one-to-many): Task may generate multiple approval requests

**Markdown Format**:
```markdown
---
task_id: "550e8400-e29b-41d4-a716-446655440000"
title: "Reply to customer inquiry about pricing"
priority: P1
status: needs_action
channel: gmail
channel_metadata:
  sender: "customer@example.com"
  subject: "Pricing question"
  message_id: "<abc123@mail.gmail.com>"
  thread_id: "thread-456"
created_at: 2026-02-14T10:30:00Z
category: sales
tags: [pricing, customer-inquiry]
---

# Reply to customer inquiry about pricing

Customer is asking about enterprise pricing for 100+ users.

**Context**: Existing customer, currently on Pro plan (20 users)

**Action Required**: Provide enterprise pricing quote and schedule demo call
```

---

## Entity: Watcher

**Description**: Input channel monitor that detects new content and creates tasks

**Storage Location**: In-memory state (Python objects), configuration in `vault/Company_Handbook/watcher-config.md`

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| watcher_id | string | Yes | Unique identifier | filesystem, gmail, whatsapp, linkedin |
| watcher_type | enum | Yes | Channel type | filesystem, gmail, whatsapp, linkedin |
| status | enum | Yes | Current state | running, stopped, error, authenticating |
| enabled | boolean | Yes | Whether watcher is active | true/false |
| last_check_at | datetime | No | Last polling time | ISO 8601 format |
| last_success_at | datetime | No | Last successful check | ISO 8601 format |
| error_count | integer | Yes | Consecutive errors | >= 0 |
| authentication_status | enum | Yes | Auth state | authenticated, expired, missing, invalid |
| config | object | Yes | Watcher-specific config | See Watcher Config below |

**Watcher Config** (varies by type):

```yaml
# Gmail Watcher
config:
  poll_interval_seconds: 30
  labels_to_monitor: ["INBOX", "IMPORTANT"]
  exclude_labels: ["SPAM", "TRASH"]
  max_results_per_poll: 10

# WhatsApp Watcher
config:
  poll_interval_seconds: 30
  monitor_groups: true
  group_whitelist: ["Team Chat", "Project Alpha"]

# LinkedIn Watcher
config:
  poll_interval_seconds: 60
  monitor_messages: true
  monitor_mentions: true
  monitor_comments: false
```

**Validation Rules**:
- watcher_id must match watcher_type
- poll_interval_seconds must be >= 10 (avoid rate limits)
- error_count resets to 0 on successful check
- status transitions to 'error' after 5 consecutive failures

**State Transitions**:
```
stopped → authenticating → running → error
   ↑                          ↓
   └──────────────────────────┘
```

**Relationships**:
- Watcher → Task (one-to-many): Watcher creates multiple tasks

---

## Entity: Approval

**Description**: Pending action requiring human review before execution

**Storage Location**: `vault/Needs_Approval/*.md`

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| approval_id | string | Yes | Unique identifier (UUID) | UUID v4 format |
| action_type | enum | Yes | Type of action | send_email, post_linkedin, send_whatsapp |
| action_details | object | Yes | Action-specific data | See Action Details below |
| risk_level | enum | Yes | Risk classification | low, medium, high |
| task_reference | string | No | Related task ID | Valid task_id |
| created_at | datetime | Yes | Approval request time | ISO 8601 format |
| timeout_at | datetime | Yes | Auto-reject deadline | created_at + 24 hours |
| status | enum | Yes | Approval state | pending, approved, rejected, expired, executed |
| reviewer | string | No | Who approved/rejected | 1-100 characters |
| reviewed_at | datetime | No | Review timestamp | ISO 8601 format |
| decision_notes | string | No | Reviewer comments | 0-1000 characters |
| execution_result | object | No | Result after execution | See Execution Result below |

**Action Details** (varies by action_type):

```yaml
# send_email
action_details:
  to: ["recipient@example.com"]
  cc: ["cc@example.com"]
  subject: "Email subject"
  body: "Email body content"
  reply_to_message_id: "<original-msg-id>"  # if reply

# post_linkedin
action_details:
  content: "Post content"
  hashtags: ["#business", "#ai"]
  mentions: ["@company"]
  media_url: "https://..."  # optional

# send_whatsapp
action_details:
  to: "+1234567890"
  message: "Message content"
  reply_to_message_id: "msg-123"  # if reply
```

**Execution Result**:

```yaml
execution_result:
  success: true
  executed_at: "2026-02-14T11:00:00Z"
  external_id: "sent-email-id-123"  # API response ID
  error_message: null  # if success=false
```

**Validation Rules**:
- approval_id must be unique
- timeout_at must be exactly 24 hours after created_at
- status transitions: pending → (approved|rejected|expired) → executed
- risk_level determined by action_type and content analysis
- reviewer required when status is approved or rejected

**Risk Classification Rules**:
- **Low**: Read operations, internal notifications
- **Medium**: Single email sends, single LinkedIn posts, single WhatsApp messages
- **High**: Bulk operations (>5 recipients), external API calls, destructive actions

**State Transitions**:
```
pending → approved → executed
       ↓
       rejected
       ↓
       expired (after 24h)
```

**Relationships**:
- Approval → Task (many-to-one, optional): Approval may reference originating task

**Markdown Format**:
```markdown
---
approval_id: "660e8400-e29b-41d4-a716-446655440001"
action_type: send_email
risk_level: medium
task_reference: "550e8400-e29b-41d4-a716-446655440000"
created_at: 2026-02-14T10:45:00Z
timeout_at: 2026-02-15T10:45:00Z
status: pending
---

# Approval Required: Send Email Reply

**Action**: Send email to customer@example.com

**Subject**: Re: Pricing question

**Body**:
```
Hi [Customer],

Thank you for your inquiry about enterprise pricing...

[Full email body]
```

**Why**: Customer inquiry requires response with pricing information

**Impact**: Customer will receive pricing quote and demo invitation

**Risk Level**: Medium (external communication, customer-facing)

---
**Review Actions**:
- Approve: Email will be sent immediately
- Reject: Email will not be sent, task marked as rejected
- Edit: Modify email content before approval
```

---

## Entity: Schedule

**Description**: Recurring task definition for automated execution

**Storage Location**: `vault/Company_Handbook/schedules.md` (human-readable), SQLite database (APScheduler persistence)

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| schedule_id | string | Yes | Unique identifier (UUID) | UUID v4 format |
| name | string | Yes | Schedule name | 1-100 characters |
| cron_expression | string | Yes | Cron syntax schedule | Valid cron format |
| task_template | object | Yes | Task to create | See Task Template below |
| enabled | boolean | Yes | Whether schedule is active | true/false |
| created_at | datetime | Yes | Schedule creation time | ISO 8601 format |
| last_run_at | datetime | No | Last execution time | ISO 8601 format |
| next_run_at | datetime | No | Next scheduled execution | ISO 8601 format |
| execution_count | integer | Yes | Total executions | >= 0 |
| failure_count | integer | Yes | Failed executions | >= 0 |
| retry_policy | object | Yes | Failure handling | See Retry Policy below |

**Task Template**:

```yaml
task_template:
  title: "Weekly LinkedIn post"
  description: "Generate and post LinkedIn content"
  priority: P2
  category: marketing
  action: "generate_linkedin_post"  # Agent skill to invoke
  params:
    topic: "business_update"
```

**Retry Policy**:

```yaml
retry_policy:
  max_retries: 3
  retry_delay_seconds: 300  # 5 minutes
  exponential_backoff: true
```

**Validation Rules**:
- cron_expression must be valid cron syntax (5 or 6 fields)
- next_run_at calculated from cron_expression
- enabled schedules must have valid next_run_at
- failure_count resets after successful execution

**Cron Expression Format**:
```
# Standard cron: minute hour day month day_of_week
0 10 * * 1,3,5  # 10:00 AM on Mon, Wed, Fri

# Extended cron: second minute hour day month day_of_week
0 0 10 * * 1,3,5  # 10:00:00 AM on Mon, Wed, Fri
```

**State Transitions**:
```
enabled=true → executing → success → enabled=true
                         ↓
                       failure → retry → success/failure
                         ↓
                    (after max_retries) → enabled=false
```

**Relationships**:
- Schedule → Task (one-to-many): Schedule creates tasks on each execution

**Markdown Format**:
```markdown
---
schedule_id: "770e8400-e29b-41d4-a716-446655440002"
name: "LinkedIn Business Updates"
cron_expression: "0 10 * * 1,3,5"
enabled: true
created_at: 2026-02-14T09:00:00Z
last_run_at: 2026-02-14T10:00:00Z
next_run_at: 2026-02-17T10:00:00Z
execution_count: 5
failure_count: 0
---

# Schedule: LinkedIn Business Updates

**Frequency**: Every Monday, Wednesday, Friday at 10:00 AM

**Action**: Generate and post LinkedIn content about business updates

**Task Template**:
- Priority: P2
- Category: marketing
- Agent Skill: /generate-linkedin-post
- Topic: business_update

**Retry Policy**:
- Max Retries: 3
- Retry Delay: 5 minutes
- Exponential Backoff: Yes

**Execution History**: See logs in vault/Logs/schedule-executions.md
```

---

## Entity: Plan

**Description**: Multi-step execution plan for complex tasks

**Storage Location**: `vault/Plans/{task_id}-plan.md`

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| plan_id | string | Yes | Unique identifier (UUID) | UUID v4 format |
| task_reference | string | Yes | Related task ID | Valid task_id |
| version | integer | Yes | Plan version number | >= 1 |
| created_at | datetime | Yes | Plan creation time | ISO 8601 format |
| updated_at | datetime | No | Last modification time | ISO 8601 format |
| status | enum | Yes | Plan state | draft, approved, executing, completed, failed |
| problem_analysis | string | Yes | Problem description | 100-2000 characters |
| approach_options | array[object] | Yes | Alternative approaches | 2-4 options |
| recommended_solution | string | Yes | Chosen approach | 100-1000 characters |
| execution_steps | array[object] | Yes | Step-by-step plan | 3-20 steps |
| success_criteria | array[string] | Yes | Completion criteria | 1-10 criteria |
| risk_mitigation | array[object] | Yes | Risk handling | 1-10 risks |

**Approach Option**:

```yaml
approach_options:
  - name: "Option A: Direct API Integration"
    description: "Use Gmail API directly"
    pros: ["Official API", "Reliable", "Well-documented"]
    cons: ["Requires OAuth2", "Rate limits"]
    estimated_effort: "4 hours"

  - name: "Option B: IMAP/SMTP"
    description: "Use email protocols"
    pros: ["Simple", "No OAuth2"]
    cons: ["Less secure", "Limited metadata"]
    estimated_effort: "2 hours"
```

**Execution Step**:

```yaml
execution_steps:
  - step_number: 1
    title: "Set up Gmail OAuth2"
    description: "Configure OAuth2 credentials and test authentication"
    estimated_duration: "1 hour"
    dependencies: []
    success_criteria: "OAuth2 token obtained and stored securely"
    status: "pending|in_progress|completed|failed"
```

**Risk Mitigation**:

```yaml
risk_mitigation:
  - risk: "OAuth2 token expiration"
    likelihood: "medium"
    impact: "high"
    mitigation: "Implement automatic token refresh"
    contingency: "Manual re-authentication with clear instructions"
```

**Validation Rules**:
- plan_id must be unique
- task_reference must point to existing task
- version increments on each update
- approach_options must have 2-4 options
- execution_steps must have 3-20 steps
- Each step must have unique step_number

**State Transitions**:
```
draft → approved → executing → completed
                            ↓
                          failed
```

**Relationships**:
- Plan → Task (one-to-one): Plan references single task
- Plan versions: Multiple versions for same task (version field)

**Markdown Format**:
```markdown
---
plan_id: "880e8400-e29b-41d4-a716-446655440003"
task_reference: "550e8400-e29b-41d4-a716-446655440000"
version: 1
created_at: 2026-02-14T11:00:00Z
status: approved
---

# Plan: Implement Gmail Watcher Integration

## Problem Analysis

Need to monitor Gmail inbox for new emails and classify them as tasks...

## Approach Options

### Option A: Gmail API with OAuth2 (Recommended)
**Pros**: Official API, reliable, well-documented
**Cons**: Requires OAuth2 setup, rate limits
**Effort**: 4 hours

### Option B: IMAP/SMTP
**Pros**: Simple, no OAuth2
**Cons**: Less secure, limited metadata
**Effort**: 2 hours

## Recommended Solution

Use Gmail API with OAuth2 (Option A) because...

## Execution Steps

1. **Set up Gmail OAuth2** (1 hour)
   - Configure OAuth2 credentials
   - Test authentication
   - Success: Token obtained and stored

2. **Implement GmailWatcher class** (2 hours)
   - Inherit from BaseWatcher
   - Implement polling logic
   - Success: Watcher detects new emails

[... more steps ...]

## Success Criteria

- [ ] Gmail watcher detects new emails within 30 seconds
- [ ] Email classification achieves 90%+ accuracy
- [ ] OAuth2 tokens refresh automatically

## Risk Mitigation

**Risk**: OAuth2 token expiration
**Likelihood**: Medium | **Impact**: High
**Mitigation**: Implement automatic token refresh
**Contingency**: Manual re-authentication with clear instructions
```

---

## Entity: LinkedInPost

**Description**: Published social media content with performance metrics

**Storage Location**: `vault/LinkedIn_Posts/{post_id}.md`

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| post_id | string | Yes | Unique identifier (UUID) | UUID v4 format |
| external_id | string | No | LinkedIn post ID | From API response |
| content | string | Yes | Post text content | 1-3000 characters |
| hashtags | array[string] | No | Post hashtags | Max 10 hashtags |
| mentions | array[string] | No | Mentioned profiles | Max 10 mentions |
| media_url | string | No | Attached media | Valid URL |
| posted_at | datetime | No | Publication time | ISO 8601 format |
| scheduled_for | datetime | No | Scheduled post time | ISO 8601 format |
| status | enum | Yes | Post state | draft, pending_approval, approved, posted, failed |
| approval_id | string | No | Related approval | Valid approval_id |
| performance_metrics | object | No | Post analytics | See Performance Metrics below |
| generated_by | string | Yes | Creation method | agent_skill, manual, scheduled |

**Performance Metrics**:

```yaml
performance_metrics:
  views: 1250
  likes: 45
  comments: 8
  shares: 12
  click_through_rate: 0.035  # 3.5%
  engagement_rate: 0.052  # 5.2%
  last_updated_at: "2026-02-15T10:00:00Z"
```

**Validation Rules**:
- post_id must be unique
- content must be 1-3000 characters (LinkedIn limit)
- hashtags must start with # and contain no spaces
- posted_at required when status is 'posted'
- approval_id required when status is 'pending_approval' or 'approved'
- performance_metrics only present when status is 'posted'

**State Transitions**:
```
draft → pending_approval → approved → posted
                         ↓
                       rejected
       ↓
     failed
```

**Relationships**:
- LinkedInPost → Approval (one-to-one, optional): Post may require approval
- LinkedInPost → Schedule (many-to-one, optional): Post may be generated by schedule

**Markdown Format**:
```markdown
---
post_id: "990e8400-e29b-41d4-a716-446655440004"
external_id: "urn:li:share:7034567890"
status: posted
posted_at: 2026-02-14T10:00:00Z
generated_by: scheduled
approval_id: "660e8400-e29b-41d4-a716-446655440001"
---

# LinkedIn Post: Business Update - Q1 2026

**Content**:
```
Excited to share our Q1 2026 progress! 🚀

We've helped 50+ businesses automate their workflows with AI...

#AI #Automation #BusinessGrowth
```

**Hashtags**: #AI, #Automation, #BusinessGrowth

**Performance** (as of 2026-02-15):
- Views: 1,250
- Likes: 45
- Comments: 8
- Shares: 12
- Engagement Rate: 5.2%

**Post URL**: https://linkedin.com/posts/...
```

---

## Entity Relationships Summary

```
Task (1) ←→ (0..1) Plan
Task (1) ←→ (0..*) Approval
Watcher (1) ←→ (*) Task
Schedule (1) ←→ (*) Task
Approval (1) ←→ (0..1) LinkedInPost
Schedule (1) ←→ (*) LinkedInPost
```

## Storage Summary

| Entity | Storage Location | Format | Persistence |
|--------|-----------------|--------|-------------|
| Task | vault/Inbox, Needs_Action, Done | Markdown | Permanent |
| Watcher | In-memory + config file | Python object + Markdown | Config permanent, state ephemeral |
| Approval | vault/Needs_Approval | Markdown | Permanent |
| Schedule | vault/Company_Handbook/schedules.md + SQLite | Markdown + Database | Permanent |
| Plan | vault/Plans | Markdown | Permanent |
| LinkedInPost | vault/LinkedIn_Posts | Markdown | Permanent |

## Validation Summary

All entities follow these common validation rules:
- IDs are UUID v4 format
- Timestamps are ISO 8601 format
- Enums have predefined allowed values
- Required fields must be present
- String lengths within specified limits
- Relationships reference valid entity IDs

**Data Model Complete**: All entities defined with attributes, relationships, and validation rules.

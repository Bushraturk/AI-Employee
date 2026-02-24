# Data Model: Gold Tier - Autonomous Employee

**Feature**: 003-gold-autonomous-employee
**Date**: 2026-02-23
**Phase**: Phase 1 - Design

## Overview

This document defines the data entities for Gold Tier features. All entities are stored as Markdown files in the Obsidian vault, following Principle III (Markdown as System Memory).

---

## 1. OdooTransaction

**Purpose**: Financial record synced bidirectionally with Odoo accounting system.

**Storage Location**: `AI_Employee_Vault/Accounting/transactions/{transaction_id}.md`

### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| transaction_id | string | Yes | Unique identifier (UUID) | UUID format |
| type | enum | Yes | Transaction type | One of: invoice, expense, payment, journal_entry |
| amount | decimal | Yes | Transaction amount | Positive number, 2 decimal places |
| currency | string | Yes | Currency code | ISO 4217 (USD, EUR, etc.) |
| date | date | Yes | Transaction date | ISO 8601 date |
| customer_vendor | string | No | Customer or vendor name | Max 200 chars |
| category | string | Yes | Accounting category | From Company_Handbook categories |
| odoo_id | integer | No | Odoo record ID | Positive integer |
| sync_status | enum | Yes | Sync state | One of: pending, synced, conflict, failed |
| last_synced_at | datetime | No | Last sync timestamp | ISO 8601 datetime |
| conflict_flag | boolean | Yes | Conflict detected | Default: false |
| conflict_details | string | No | Conflict description | Max 500 chars |
| created_at | datetime | Yes | Creation timestamp | ISO 8601 datetime |
| updated_at | datetime | Yes | Last update timestamp | ISO 8601 datetime |

### Relationships
- **References**: Task file that created this transaction (if applicable)
- **Linked To**: Odoo record via `odoo_id`
- **Appears In**: Weekly audit reports

### State Transitions

```
pending → synced (successful sync to Odoo)
pending → failed (sync error, retry later)
synced → conflict (modification detected in both systems)
conflict → synced (human resolved conflict)
failed → synced (retry succeeded)
```

### Validation Rules
- Amount must be positive
- Date cannot be in future
- If `odoo_id` is set, `sync_status` cannot be `pending`
- If `conflict_flag` is true, `conflict_details` must be set
- Category must exist in Company_Handbook

### Markdown Format

```markdown
---
transaction_id: "550e8400-e29b-41d4-a716-446655440000"
type: "invoice"
amount: 1500.00
currency: "USD"
date: "2026-02-20"
customer_vendor: "Acme Corp"
category: "Revenue - Consulting"
odoo_id: 12345
sync_status: "synced"
last_synced_at: "2026-02-20T14:30:00Z"
conflict_flag: false
created_at: "2026-02-20T10:00:00Z"
updated_at: "2026-02-20T14:30:00Z"
---

# Invoice: Acme Corp - Consulting Services

**Amount**: $1,500.00
**Date**: 2026-02-20
**Status**: Synced to Odoo (ID: 12345)

## Description
Consulting services for Q1 2026 project.

## Sync History
- 2026-02-20 14:30:00 - Synced to Odoo successfully
- 2026-02-20 10:00:00 - Created in vault
```

---

## 2. SocialMediaPost

**Purpose**: Content published across social media platforms with performance tracking.

**Storage Location**: `AI_Employee_Vault/Social_Media/posts/{post_id}.md`

### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| post_id | string | Yes | Unique identifier (UUID) | UUID format |
| platforms | array[string] | Yes | Target platforms | One or more of: facebook, instagram, twitter, linkedin |
| content | string | Yes | Post text content | Max 280 chars for Twitter, 2200 for others |
| media_urls | array[string] | No | Media file URLs | Valid URLs or local paths |
| posted_at | datetime | No | Publication timestamp | ISO 8601 datetime |
| performance_metrics | object | No | Engagement metrics | See Performance Metrics structure |
| approval_metadata | object | Yes | Approval tracking | See Approval Metadata structure |
| cross_post_group_id | string | No | Cross-post group identifier | UUID format |
| status | enum | Yes | Post status | One of: draft, pending_approval, approved, posted, failed |
| created_at | datetime | Yes | Creation timestamp | ISO 8601 datetime |
| updated_at | datetime | Yes | Last update timestamp | ISO 8601 datetime |

### Performance Metrics Structure

```yaml
performance_metrics:
  facebook:
    reach: 1250
    impressions: 1800
    engagement: 95
    clicks: 42
    last_updated: "2026-02-21T10:00:00Z"
  instagram:
    reach: 890
    impressions: 1200
    engagement: 67
    clicks: 28
    last_updated: "2026-02-21T10:00:00Z"
  twitter:
    reach: 450
    impressions: 620
    engagement: 34
    clicks: 15
    last_updated: "2026-02-21T10:00:00Z"
  linkedin:
    reach: 320
    impressions: 480
    engagement: 28
    clicks: 12
    last_updated: "2026-02-21T10:00:00Z"
```

### Approval Metadata Structure

```yaml
approval_metadata:
  requested_at: "2026-02-20T09:00:00Z"
  approved_at: "2026-02-20T09:15:00Z"
  approved_by: "user"
  approval_method: "manual"  # manual, auto, scheduled
```

### Relationships
- **Part Of**: Cross-post group (if `cross_post_group_id` is set)
- **References**: Task file that requested this post
- **Appears In**: Weekly audit reports (social media metrics)

### State Transitions

```
draft → pending_approval (post generated, awaiting approval)
pending_approval → approved (user approved)
pending_approval → draft (user rejected, needs revision)
approved → posted (successfully published to all platforms)
approved → failed (posting error, retry or escalate)
failed → posted (retry succeeded)
```

### Validation Rules
- Content length must respect platform limits (280 chars for Twitter)
- At least one platform must be specified
- If status is `posted`, `posted_at` must be set
- Media URLs must be accessible or valid local paths
- Cross-posted posts must share same `cross_post_group_id`

### Markdown Format

```markdown
---
post_id: "660e8400-e29b-41d4-a716-446655440001"
platforms: ["facebook", "instagram", "twitter", "linkedin"]
status: "posted"
posted_at: "2026-02-20T12:00:00Z"
cross_post_group_id: "770e8400-e29b-41d4-a716-446655440002"
created_at: "2026-02-20T09:00:00Z"
updated_at: "2026-02-20T12:00:00Z"
approval_metadata:
  requested_at: "2026-02-20T09:00:00Z"
  approved_at: "2026-02-20T09:15:00Z"
  approved_by: "user"
  approval_method: "manual"
performance_metrics:
  facebook:
    reach: 1250
    impressions: 1800
    engagement: 95
    clicks: 42
  instagram:
    reach: 890
    impressions: 1200
    engagement: 67
    clicks: 28
  twitter:
    reach: 450
    impressions: 620
    engagement: 34
    clicks: 15
  linkedin:
    reach: 320
    impressions: 480
    engagement: 28
    clicks: 12
---

# Social Media Post: Product Launch Announcement

**Platforms**: Facebook, Instagram, Twitter, LinkedIn
**Status**: Posted
**Posted**: 2026-02-20 12:00:00

## Content

Excited to announce our new product launch! 🚀 Learn more at our website. #ProductLaunch #Innovation

## Media
- ![Product Image](./media/product-launch.jpg)

## Performance Summary
- **Total Reach**: 2,910
- **Total Engagement**: 224
- **Total Clicks**: 97
- **Engagement Rate**: 7.7%

## Platform-Specific Performance
- **Facebook**: 1,250 reach, 95 engagement (7.6% rate)
- **Instagram**: 890 reach, 67 engagement (7.5% rate)
- **Twitter**: 450 reach, 34 engagement (7.6% rate)
- **LinkedIn**: 320 reach, 28 engagement (8.8% rate)
```

---

## 3. MCPServer

**Purpose**: Metadata for independent MCP server instances.

**Storage Location**: `AI_Employee_Vault/System/mcp_servers/{server_id}.md`

### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| server_id | string | Yes | Server identifier | One of: accounting, social, communications |
| domain | enum | Yes | Action domain | One of: accounting, social, communications |
| status | enum | Yes | Server status | One of: running, stopped, error, crashed |
| available_tools | array[string] | Yes | Tool names | Non-empty array |
| rate_limits | object | Yes | Rate limit config | See Rate Limits structure |
| last_health_check | datetime | No | Last health check timestamp | ISO 8601 datetime |
| error_count | integer | Yes | Consecutive error count | Non-negative integer |
| restart_count | integer | Yes | Restart count | Non-negative integer |
| process_id | integer | No | OS process ID | Positive integer |
| started_at | datetime | No | Server start timestamp | ISO 8601 datetime |
| updated_at | datetime | Yes | Last update timestamp | ISO 8601 datetime |

### Rate Limits Structure

```yaml
rate_limits:
  calls_per_minute: 60
  calls_per_hour: 1000
  concurrent_requests: 5
```

### Relationships
- **Executes**: Actions routed to this server
- **Logs To**: Domain-specific log files

### State Transitions

```
stopped → running (server started successfully)
running → stopped (graceful shutdown)
running → error (recoverable error, retry)
running → crashed (unrecoverable error, restart)
error → running (recovery succeeded)
crashed → running (restart succeeded)
```

### Validation Rules
- If status is `running`, `process_id` and `started_at` must be set
- If status is `stopped`, `process_id` should be null
- `error_count` resets to 0 when status becomes `running`
- `available_tools` must not be empty

### Markdown Format

```markdown
---
server_id: "accounting"
domain: "accounting"
status: "running"
process_id: 12345
error_count: 0
restart_count: 1
started_at: "2026-02-20T08:00:00Z"
last_health_check: "2026-02-20T14:30:00Z"
updated_at: "2026-02-20T14:30:00Z"
available_tools:
  - "sync_odoo_transaction"
  - "create_odoo_invoice"
  - "create_odoo_expense"
  - "create_odoo_customer"
rate_limits:
  calls_per_minute: 60
  calls_per_hour: 1000
  concurrent_requests: 5
---

# MCP Server: Accounting

**Domain**: Accounting (Odoo Integration)
**Status**: Running (PID: 12345)
**Uptime**: 6 hours 30 minutes

## Available Tools
- sync_odoo_transaction
- create_odoo_invoice
- create_odoo_expense
- create_odoo_customer

## Health Status
- Last Health Check: 2026-02-20 14:30:00
- Error Count: 0
- Restart Count: 1

## Rate Limits
- 60 calls/minute
- 1000 calls/hour
- 5 concurrent requests
```

---

## 4. AuditReport

**Purpose**: Weekly business intelligence report with financial, operational, and social metrics.

**Storage Location**: `AI_Employee_Vault/Audits/weekly/{report_id}.md`

### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| report_id | string | Yes | Unique identifier (UUID) | UUID format |
| week_start_date | date | Yes | Week start date (Monday) | ISO 8601 date |
| week_end_date | date | Yes | Week end date (Sunday) | ISO 8601 date |
| financial_summary | object | Yes | Financial metrics | See Financial Summary structure |
| operational_metrics | object | Yes | Task/system metrics | See Operational Metrics structure |
| social_metrics | object | Yes | Social media metrics | See Social Metrics structure |
| trends | array[object] | Yes | Trend analysis | See Trends structure |
| anomalies | array[object] | Yes | Detected anomalies | See Anomalies structure |
| recommendations | array[string] | Yes | Actionable recommendations | Max 10 recommendations |
| generated_at | datetime | Yes | Generation timestamp | ISO 8601 datetime |

### Financial Summary Structure

```yaml
financial_summary:
  revenue: 15000.00
  expenses: 8500.00
  profit_loss: 6500.00
  cash_flow: 12000.00
  outstanding_invoices: 3
  outstanding_amount: 4500.00
  expense_categories:
    - category: "Software Subscriptions"
      amount: 2500.00
    - category: "Marketing"
      amount: 3000.00
```

### Operational Metrics Structure

```yaml
operational_metrics:
  tasks_completed: 45
  tasks_pending: 12
  average_response_time: 120  # seconds
  approval_rate: 0.92
  system_uptime: 0.998
```

### Social Metrics Structure

```yaml
social_metrics:
  total_posts: 8
  total_reach: 12500
  total_engagement: 850
  engagement_rate: 0.068
  follower_growth:
    facebook: 25
    instagram: 18
    twitter: 12
    linkedin: 8
  top_performing_post: "660e8400-e29b-41d4-a716-446655440001"
```

### Trends Structure

```yaml
trends:
  - metric: "revenue"
    direction: "up"
    change_percent: 12.5
    comparison: "vs_previous_week"
  - metric: "engagement_rate"
    direction: "down"
    change_percent: -5.2
    comparison: "vs_previous_week"
```

### Anomalies Structure

```yaml
anomalies:
  - type: "financial"
    severity: "high"
    description: "Expenses increased 30% compared to previous week"
    recommendation: "Review marketing spend and software subscriptions"
  - type: "operational"
    severity: "medium"
    description: "Approval rate dropped from 95% to 92%"
    recommendation: "Review rejected tasks for quality issues"
```

### Relationships
- **References**: OdooTransactions, SocialMediaPosts, Tasks from the reporting period
- **Part Of**: Historical audit series

### Validation Rules
- `week_end_date` must be 6 days after `week_start_date`
- `week_start_date` must be a Monday
- Financial amounts must be accurate (sum of transactions)
- Trends must reference valid metrics
- Anomalies must have severity level (low/medium/high)

### Markdown Format

```markdown
---
report_id: "880e8400-e29b-41d4-a716-446655440003"
week_start_date: "2026-02-17"
week_end_date: "2026-02-23"
generated_at: "2026-02-23T18:00:00Z"
---

# Weekly Business Audit: Feb 17-23, 2026

**Generated**: 2026-02-23 18:00:00

## Executive Summary

Strong week with 12.5% revenue growth and solid operational performance. Marketing expenses increased significantly (30%) - review recommended. Social media engagement declined slightly (-5.2%) - content strategy adjustment needed.

## Financial Performance

- **Revenue**: $15,000.00 (+12.5% vs last week)
- **Expenses**: $8,500.00 (+30% vs last week)
- **Profit/Loss**: $6,500.00 (+2.3% vs last week)
- **Cash Flow**: $12,000.00
- **Outstanding Invoices**: 3 ($4,500.00)

### Expense Breakdown
- Software Subscriptions: $2,500.00
- Marketing: $3,000.00
- Operations: $3,000.00

## Operational Metrics

- **Tasks Completed**: 45 (vs 42 last week)
- **Tasks Pending**: 12
- **Average Response Time**: 2 minutes
- **Approval Rate**: 92% (down from 95%)
- **System Uptime**: 99.8%

## Social Media Performance

- **Total Posts**: 8
- **Total Reach**: 12,500 (+8% vs last week)
- **Total Engagement**: 850 (-5.2% vs last week)
- **Engagement Rate**: 6.8%
- **Follower Growth**: +63 total (FB: +25, IG: +18, X: +12, LI: +8)

### Top Performing Post
Product Launch Announcement (2,910 reach, 224 engagement, 7.7% rate)

## Trends

📈 **Positive Trends**
- Revenue up 12.5%
- Tasks completed up 7.1%
- Follower growth steady

📉 **Concerning Trends**
- Expenses up 30% (marketing spend)
- Engagement rate down 5.2%
- Approval rate down 3%

## Anomalies Detected

🔴 **High Severity**
- Expenses increased 30% compared to previous week
  - **Recommendation**: Review marketing spend and software subscriptions

🟡 **Medium Severity**
- Approval rate dropped from 95% to 92%
  - **Recommendation**: Review rejected tasks for quality issues

## Recommendations

1. **Review Marketing ROI**: Expenses increased 30% but engagement declined. Analyze campaign effectiveness.
2. **Improve Content Strategy**: Engagement rate down 5.2%. Test new content formats and posting times.
3. **Investigate Approval Rejections**: 3% drop in approval rate. Review rejected tasks for patterns.
4. **Follow Up on Outstanding Invoices**: $4,500 outstanding. Send payment reminders.
5. **Maintain Operational Excellence**: 99.8% uptime and 2-minute response time are excellent.

## Next Week Focus

- Optimize marketing spend
- Refresh social media content strategy
- Improve task quality to increase approval rate
- Collect outstanding payments
```

---

## 5. WorkflowExecution

**Purpose**: Ralph Wiggum autonomous loop execution state and progress tracking.

**Storage Location**: `AI_Employee_Vault/Workflows/executions/{execution_id}.md`

### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| execution_id | string | Yes | Unique identifier (UUID) | UUID format |
| task_reference | string | Yes | Original task file path | Valid vault path |
| plan_reference | string | Yes | Execution plan file path | Valid vault path |
| steps | array[object] | Yes | Execution steps | See Step structure |
| current_step_index | integer | Yes | Current step (0-indexed) | 0 to steps.length-1 |
| status | enum | Yes | Execution status | One of: running, paused, completed, failed |
| execution_context | object | Yes | Data passed between steps | Key-value pairs |
| started_at | datetime | Yes | Execution start timestamp | ISO 8601 datetime |
| completed_at | datetime | No | Execution completion timestamp | ISO 8601 datetime |
| lessons_learned | array[string] | No | Process improvements | Max 5 lessons |
| created_at | datetime | Yes | Creation timestamp | ISO 8601 datetime |
| updated_at | datetime | Yes | Last update timestamp | ISO 8601 datetime |

### Step Structure

```yaml
steps:
  - step_id: "step_1"
    description: "Sync invoice to Odoo"
    action_type: "sync_odoo_transaction"
    parameters:
      transaction_id: "550e8400-e29b-41d4-a716-446655440000"
    status: "completed"
    started_at: "2026-02-20T10:00:00Z"
    completed_at: "2026-02-20T10:00:15Z"
    result:
      success: true
      odoo_id: 12345
    dependencies: []
  - step_id: "step_2"
    description: "Post about invoice on social media"
    action_type: "post_facebook"
    parameters:
      content: "Invoice processed successfully"
    status: "in_progress"
    started_at: "2026-02-20T10:00:20Z"
    dependencies: ["step_1"]
```

### Relationships
- **Executes**: Original task from `task_reference`
- **Follows**: Execution plan from `plan_reference`
- **Logs To**: Workflow execution logs

### State Transitions

```
running → completed (all steps succeeded)
running → failed (step failed, recovery exhausted)
running → paused (human intervention required)
paused → running (human provided guidance)
failed → running (manual recovery initiated)
```

### Validation Rules
- `current_step_index` must be valid index in `steps` array
- If status is `completed`, all steps must have status `completed`
- If status is `failed`, at least one step must have status `failed`
- Step dependencies must reference valid step IDs
- Execution context keys must be valid identifiers

### Markdown Format

```markdown
---
execution_id: "990e8400-e29b-41d4-a716-446655440004"
task_reference: "Inbox/process-invoice-and-announce.md"
plan_reference: "Workflows/plans/invoice-workflow-plan.md"
status: "running"
current_step_index: 1
started_at: "2026-02-20T10:00:00Z"
updated_at: "2026-02-20T10:00:20Z"
execution_context:
  invoice_id: "550e8400-e29b-41d4-a716-446655440000"
  odoo_id: 12345
  customer_name: "Acme Corp"
---

# Workflow Execution: Process Invoice and Announce

**Task**: [process-invoice-and-announce.md](../Inbox/process-invoice-and-announce.md)
**Plan**: [invoice-workflow-plan.md](plans/invoice-workflow-plan.md)
**Status**: Running (Step 2 of 3)
**Started**: 2026-02-20 10:00:00

## Execution Steps

### ✅ Step 1: Sync invoice to Odoo
**Status**: Completed
**Duration**: 15 seconds
**Result**: Successfully synced (Odoo ID: 12345)

### 🔄 Step 2: Post about invoice on social media
**Status**: In Progress
**Started**: 2026-02-20 10:00:20

### ⏳ Step 3: Update CEO briefing
**Status**: Pending
**Dependencies**: Step 2

## Execution Context

```yaml
invoice_id: "550e8400-e29b-41d4-a716-446655440000"
odoo_id: 12345
customer_name: "Acme Corp"
```

## Progress
- Steps Completed: 1/3 (33%)
- Estimated Time Remaining: 30 seconds
```

---

## 6. ErrorRecoveryLog

**Purpose**: Comprehensive logging of error handling and recovery attempts.

**Storage Location**: `AI_Employee_Vault/Logs/error_recovery/{error_id}.md`

### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| error_id | string | Yes | Unique identifier (UUID) | UUID format |
| error_type | enum | Yes | Error category | One of: network, authentication, rate_limit, validation, system |
| service | enum | Yes | Affected service | One of: odoo, facebook, instagram, twitter, linkedin, gmail, whatsapp |
| error_message | string | Yes | Error description | Max 500 chars |
| retry_count | integer | Yes | Number of retry attempts | Non-negative integer |
| recovery_strategy | enum | Yes | Strategy used | One of: retry, queue, escalate, degrade |
| outcome | enum | Yes | Recovery result | One of: recovered, escalated, queued |
| timestamp | datetime | Yes | Error occurrence timestamp | ISO 8601 datetime |
| context | object | No | Additional context | Key-value pairs |

### Relationships
- **Related To**: Action that failed
- **Part Of**: Daily error logs

### Validation Rules
- `retry_count` must be 0-3 (max 3 retries per FR-051)
- If `outcome` is `recovered`, `retry_count` must be > 0
- If `outcome` is `escalated`, `retry_count` must be 3
- Service must be valid integration name

### Markdown Format

```markdown
---
error_id: "aa0e8400-e29b-41d4-a716-446655440005"
error_type: "network"
service: "odoo"
error_message: "Connection timeout after 30 seconds"
retry_count: 2
recovery_strategy: "retry"
outcome: "recovered"
timestamp: "2026-02-20T14:30:00Z"
context:
  action: "sync_odoo_transaction"
  transaction_id: "550e8400-e29b-41d4-a716-446655440000"
  attempt_timestamps:
    - "2026-02-20T14:30:00Z"
    - "2026-02-20T14:30:04Z"
    - "2026-02-20T14:30:12Z"
---

# Error Recovery: Odoo Connection Timeout

**Service**: Odoo
**Error Type**: Network
**Timestamp**: 2026-02-20 14:30:00
**Outcome**: Recovered (after 2 retries)

## Error Details

Connection timeout after 30 seconds while attempting to sync transaction.

## Recovery Strategy

Exponential backoff retry:
1. Attempt 1: Failed (14:30:00)
2. Attempt 2: Failed (14:30:04, waited 4s)
3. Attempt 3: Success (14:30:12, waited 8s)

## Context

- **Action**: sync_odoo_transaction
- **Transaction ID**: 550e8400-e29b-41d4-a716-446655440000
- **Total Recovery Time**: 12 seconds

## Lessons Learned

Network transient errors are common during peak hours. Exponential backoff with 3 retries is effective for recovery.
```

---

## Entity Relationships Diagram

```
Task (Bronze/Silver)
  ↓ creates
OdooTransaction ←→ Odoo System (external)
  ↓ appears in
AuditReport

Task (Bronze/Silver)
  ↓ creates
SocialMediaPost ←→ Social Media APIs (external)
  ↓ appears in
AuditReport

Task (Bronze/Silver)
  ↓ triggers
WorkflowExecution
  ↓ executes steps via
MCPServer
  ↓ logs errors to
ErrorRecoveryLog

AuditReport
  ↓ references
OdooTransaction, SocialMediaPost, Task, WorkflowExecution
```

---

## Storage Summary

All entities stored as Markdown files in vault:

```
AI_Employee_Vault/
├── Accounting/
│   └── transactions/
│       └── {transaction_id}.md
├── Social_Media/
│   └── posts/
│       └── {post_id}.md
├── System/
│   └── mcp_servers/
│       └── {server_id}.md
├── Audits/
│   └── weekly/
│       └── {report_id}.md
├── Workflows/
│   └── executions/
│       └── {execution_id}.md
└── Logs/
    └── error_recovery/
        └── {error_id}.md
```

This structure maintains Principle III (Markdown as System Memory) and enables human inspection, version control, and debugging.

# Platinum Tier AI Employee - Architecture

## Overview

The Platinum Tier AI Employee is a dual-agent distributed system that provides 24/7 autonomous business operations with human-in-the-loop approval workflows.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Cloud VM                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Cloud Agent                                           │ │
│  │  - Gmail Watcher (24/7 monitoring)                     │ │
│  │  - Email Drafter                                       │ │
│  │  - Social Media Drafter                                │ │
│  │  - Accounting Drafter                                  │ │
│  │  - WhatsApp Drafter                                    │ │
│  │  - Business Auditor                                    │ │
│  │  - Orchestrator                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MCP Servers                                           │ │
│  │  - Email MCP (Node.js)                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Vault Sync (Git/Syncthing)
                            │
┌─────────────────────────────────────────────────────────────┐
│                     Local Machine                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Local Agent                                           │ │
│  │  - WhatsApp Watcher                                    │ │
│  │  - Finance Watcher                                     │ │
│  │  - Email Executor                                      │ │
│  │  - Social Executor                                     │ │
│  │  - Accounting Executor                                 │ │
│  │  - WhatsApp Executor                                   │ │
│  │  - Approval Handler                                    │ │
│  │  - Dashboard Updater                                   │ │
│  │  - Orchestrator                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  MCP Servers                                           │ │
│  │  - Email MCP (Node.js)                                 │ │
│  │  - Social MCP (Node.js)                                │ │
│  │  - Odoo MCP (Python)                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Cloud Agent
- **Purpose**: 24/7 monitoring and draft generation
- **Capabilities**: Read-only access to external services, write drafts to vault
- **Security**: Cannot execute sensitive actions, no access to credentials

### Local Agent
- **Purpose**: Approval handling and action execution
- **Capabilities**: Full access to all services and credentials
- **Security**: Owns all sensitive operations (email sends, payments, etc.)

### Shared Vault
- **Purpose**: State synchronization between agents
- **Technology**: Git or Syncthing
- **Structure**: Markdown files with YAML frontmatter
- **Security**: Excludes all secrets and credentials

### MCP Servers
- **Purpose**: External service integration
- **Architecture**: Independent processes with JSON-RPC communication
- **Isolation**: Process-based for fault tolerance

## Data Flow

### Email Handling Flow
```
Gmail → Cloud Agent (GmailWatcher) → ActionFile →
Cloud Agent (EmailDrafter) → ApprovalRequest →
Vault Sync → Local Agent → Human Approval →
Local Agent (EmailExecutor) → Email MCP → Gmail → Done
```

### Social Media Flow
```
Schedule → Cloud Agent (SocialDrafter) → ApprovalRequest →
Vault Sync → Local Agent → Human Approval →
Local Agent (SocialExecutor) → Social MCP → Platform → Done
```

### Financial Flow
```
Bank Transaction → Local Agent (FinanceWatcher) → ActionFile →
Vault Sync → Cloud Agent (AccountingDrafter) → ApprovalRequest →
Vault Sync → Local Agent → Human Approval →
Local Agent (AccountingExecutor) → Odoo MCP → Odoo → Done
```

## Security Architecture

### Principle: Defense in Depth

1. **Agent Separation**: Cloud agent can only draft, local agent executes
2. **Credential Isolation**: All secrets remain local-only
3. **Approval Workflow**: 100% of sensitive actions require approval
4. **Audit Logging**: Complete traceability of all actions
5. **Rate Limiting**: Prevents abuse (10 emails/hour, 3 payments/hour)
6. **Circuit Breakers**: Prevents cascading failures
7. **Secret Detection**: Pre-commit hooks prevent credential leaks

### Security Boundaries

- **Cloud Agent**: Read Gmail, write drafts (no execution)
- **Local Agent**: Full execution authority (with approval)
- **Vault Sync**: Markdown files only (no secrets)
- **MCP Servers**: Isolated processes (fault containment)

## Fault Tolerance

### Error Recovery
- **Retry Logic**: Exponential backoff (max 3 attempts)
- **Circuit Breakers**: Per-service failure protection
- **Action Queuing**: Graceful degradation when services unavailable
- **Watchdog**: Automatic process restart

### High Availability
- **Cloud Agent**: 99.9% uptime target
- **Local Agent**: Operates independently when cloud unavailable
- **Vault Sync**: Conflict resolution with last-write-wins
- **MCP Servers**: Auto-restart on failure

## Scalability

### Current Limits
- 500 emails/day
- 10 social posts/day
- 100 financial transactions/day
- 10 concurrent watchers

### Scaling Strategy
- Horizontal: Multiple cloud agents (future)
- Vertical: Increase VM resources
- Caching: Reduce API calls
- Batching: Group similar operations

## Technology Stack

### Languages
- Python 3.9+ (agents, shared, Odoo MCP)
- Node.js 18+ (Email MCP, Social MCP)
- Bash (deployment scripts)

### Key Libraries
- **watchdog**: File system monitoring
- **APScheduler**: Task scheduling
- **odoorpc**: Odoo integration
- **googleapis**: Gmail API
- **playwright**: WhatsApp automation
- **tenacity**: Retry logic
- **pybreaker**: Circuit breakers

### Infrastructure
- **Cloud VM**: Oracle Cloud Free Tier (or equivalent)
- **Vault Sync**: Git or Syncthing
- **Process Management**: systemd (cloud), manual (local)
- **Monitoring**: Watchdog + health checks

## Design Patterns

### Watcher-Drafter-Executor Pattern
- **Watcher**: Detects events, creates ActionFiles
- **Drafter**: Analyzes context, creates ApprovalRequests
- **Executor**: Executes approved actions, logs results

### Claim-by-Move Rule
- First agent to move file from Needs_Action to In_Progress owns it
- Prevents duplicate work between agents
- Atomic file operations ensure consistency

### Single-Writer Pattern
- Dashboard.md: Local agent only
- Updates folder: Cloud agent writes, local agent merges
- Prevents write conflicts

### Circuit Breaker Pattern
- Per-service breakers (Gmail, Odoo, Social platforms)
- Fail-fast to prevent cascading failures
- Automatic recovery after timeout

## Deployment Architecture

### Cloud Deployment
- Ubuntu 22.04 LTS on cloud VM
- systemd service for cloud agent
- Automated deployment via rsync
- Health monitoring via watchdog

### Local Deployment
- Windows/macOS/Linux support
- Manual start or system service
- Vault sync via Git or Syncthing
- WhatsApp session on local machine

## Monitoring & Observability

### Metrics
- Actions processed per hour
- Success rate percentage
- Approval queue depth
- MCP server health
- Error rate by category

### Logging
- Structured JSON logs
- Daily rotation with 30-day retention
- Audit trail for all actions
- Error tracking with stack traces

### Dashboards
- Dashboard.md: Real-time system status
- Weekly briefings: Business intelligence
- Cost optimization reports: Savings opportunities

## Future Enhancements

### Phase 2 (Future)
- Agent-to-Agent direct messaging
- Multi-user support
- Mobile app interface
- Voice/audio message handling
- Real-time chat integration
- Custom AI model fine-tuning
- Additional ERP integrations

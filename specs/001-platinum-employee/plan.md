# Implementation Plan: Platinum Tier AI Employee

**Branch**: `001-platinum-employee` | **Date**: 2026-02-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-platinum-employee/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The Platinum Tier AI Employee extends the Gold Tier with always-on cloud monitoring and a dual-agent architecture. A cloud agent runs 24/7 on a cloud VM, monitoring Gmail and drafting responses/social posts/accounting entries. A local agent handles approvals and executes sensitive actions (email sends, WhatsApp, payments). Agents communicate via a synced vault (Git or Syncthing) using a claim-by-move rule to prevent duplicate work. Odoo Community Edition is deployed on the cloud VM for accounting integration. The system maintains strict security boundaries: cloud agent can only draft, local agent owns all secrets and final actions.

## Technical Context

**Language/Version**: Python 3.9+
**Primary Dependencies**: watchdog (file monitoring), APScheduler (scheduling), odoorpc (Odoo integration), google-auth + googleapiclient (Gmail API), playwright (WhatsApp Web automation), tenacity (retry logic), pybreaker (circuit breaker), frontmatter + markdown (markdown processing), python-dotenv (environment variables)
**Storage**: Markdown files in synced vault (Obsidian-compatible), SQLite job store for APScheduler (job persistence), Odoo PostgreSQL database (accounting data)
**Testing**: pytest (unit/integration tests), contract tests for MCP servers
**Target Platform**: Cloud VM (Linux, Oracle Cloud Free Tier or equivalent) for cloud agent + Odoo, Windows/macOS/Linux for local agent
**Project Type**: Dual-agent distributed system with shared vault synchronization
**Performance Goals**: 2-minute email detection, 5-minute draft generation, 10-second vault sync (under 100 files), 99.9% cloud agent uptime, 60-second watchdog restart
**Constraints**: <5 minute end-to-end email response (detection to draft), <30 seconds approval review UI, <1 minute action execution post-approval, <30 minutes daily approval time, 100% approval compliance (zero unauthorized actions)
**Scale/Scope**: 500 emails/day, 10 social posts/day, 100 financial transactions/day, 10 concurrent watchers, 2 agents (cloud + local), 1 Odoo instance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance Analysis

✅ **II. Human-in-the-Loop for Risk Actions**: COMPLIANT
- All email sends, social posts, payments, and accounting entries require explicit approval
- Approval workflow implemented via file movement (Pending_Approval → Approved)
- Cloud agent can only draft, never execute sensitive actions

✅ **III. Markdown as System Memory**: COMPLIANT
- All state stored in markdown files within vault
- Action files, approval requests, logs, dashboard all use markdown format
- No hidden databases or binary state (except SQLite for APScheduler job persistence, which is acceptable for scheduling metadata)

✅ **IV. Modular Watcher Architecture**: COMPLIANT
- Gmail, WhatsApp, and Finance watchers inherit from BaseWatcher
- Each watcher operates independently
- Watchers can be added/removed without affecting core system

✅ **V. Clear Perception → Reasoning → Action Loop**: COMPLIANT
- Perception: Watchers detect events and create action files
- Reasoning: Agents (cloud/local) process action files and draft responses
- Action: Local agent executes approved actions with logging

✅ **VI. No Hidden State**: COMPLIANT
- All system behavior traceable through markdown files in vault
- Every action produces log entry
- Dashboard and audit logs provide complete visibility

✅ **VII. Phased Development with Independent Functionality**: COMPLIANT
- Platinum tier builds on Bronze (local foundation), Silver (scheduled operations), and Gold (autonomous operations with error recovery)
- Each tier is independently functional and deployable
- Platinum adds cloud agent and Odoo integration without breaking previous tiers

✅ **VIII. Safety-First Constraints**: COMPLIANT
- No destructive operations outside vault without approval
- All actions logged before execution
- Email sending requires approval
- Secrets use environment variables only
- Rate limiting enforced (10 emails/hour, 3 payments/hour)

⚠️ **I. Local-First Architecture**: PARTIAL VIOLATION
- **Violation**: Cloud agent runs 24/7 on cloud VM, not local machine
- **Justification**: Platinum tier's core value proposition is always-on availability that extends beyond local machine uptime. The specification explicitly requires 24/7 monitoring even when local machine is offline (FR-006, FR-007, FR-015, SC-001, SC-004). This is the defining feature that differentiates Platinum from Gold tier.
- **Mitigation**:
  - Local agent maintains full functionality independently
  - Cloud agent can only draft, never execute sensitive actions
  - All sensitive credentials and sessions remain local-only
  - System degrades gracefully when cloud agent is unavailable
  - User can operate entirely locally if cloud agent is disabled

### Gate Decision

**PASS WITH JUSTIFICATION**: The Local-First Architecture violation is justified by the explicit Platinum tier requirement for always-on cloud monitoring. The violation is minimal and well-mitigated: the cloud agent is read-only for external services (Gmail) and write-only for vault drafts. All execution authority remains with the local agent. The architecture maintains the spirit of local-first by ensuring the local agent can operate independently and retains all sensitive credentials.

## Project Structure

### Documentation (this feature)

```text
specs/001-platinum-employee/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── vault-structure.md
│   ├── action-file-schema.json
│   ├── approval-request-schema.json
│   ├── agent-api.md
│   └── mcp-odoo-spec.md
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Dual-agent distributed system structure

# Cloud Agent (deployed to cloud VM)
cloud_agent/
├── src/
│   ├── agent.py              # Main cloud agent orchestrator
│   ├── watchers/
│   │   ├── base_watcher.py   # Abstract base class
│   │   └── gmail_watcher.py  # Gmail monitoring
│   ├── drafters/
│   │   ├── email_drafter.py  # Email response generation
│   │   ├── social_drafter.py # Social media post generation
│   │   └── accounting_drafter.py # Odoo entry generation
│   ├── vault_sync.py         # Git/Syncthing sync handler
│   └── config.py             # Cloud agent configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md

# Local Agent (runs on user machine)
local_agent/
├── src/
│   ├── agent.py              # Main local agent orchestrator
│   ├── watchers/
│   │   ├── whatsapp_watcher.py # WhatsApp monitoring
│   │   └── finance_watcher.py  # Bank transaction monitoring
│   ├── executors/
│   │   ├── email_executor.py   # Email sending via MCP
│   │   ├── social_executor.py  # Social media posting via MCP
│   │   └── accounting_executor.py # Odoo posting via MCP
│   ├── approval_handler.py   # Approval workflow management
│   ├── dashboard_updater.py  # Dashboard.md writer
│   ├── vault_sync.py         # Git/Syncthing sync handler
│   └── config.py             # Local agent configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md

# Shared Components
shared/
├── models/
│   ├── action_file.py        # Action file data model
│   ├── approval_request.py   # Approval request data model
│   ├── audit_log.py          # Audit log entry model
│   └── vault_structure.py    # Vault folder structure
├── utils/
│   ├── markdown_parser.py    # Markdown frontmatter parsing
│   ├── file_operations.py    # Safe file operations
│   └── logging_utils.py      # Structured logging
└── constants.py              # Shared constants

# MCP Servers
mcp_servers/
├── email_mcp/                # Email MCP server (Node.js)
│   ├── src/
│   │   ├── index.js
│   │   └── gmail_client.js
│   ├── package.json
│   └── README.md
├── social_mcp/               # Social media MCP server (Node.js)
│   ├── src/
│   │   ├── index.js
│   │   ├── facebook_client.js
│   │   ├── instagram_client.js
│   │   ├── twitter_client.js
│   │   └── linkedin_client.js
│   ├── package.json
│   └── README.md
└── odoo_mcp/                 # Odoo accounting MCP server (Python)
    ├── src/
    │   ├── server.py
    │   └── odoo_client.py
    ├── requirements.txt
    └── README.md

# Orchestration
orchestration/
├── orchestrator.py           # Master process for scheduling and folder watching
├── watchdog.py               # Health monitor and process restarter
└── config/
    ├── cloud_processes.yaml  # Cloud agent process definitions
    └── local_processes.yaml  # Local agent process definitions

# Deployment
deployment/
├── cloud/
│   ├── terraform/            # Cloud VM provisioning
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ansible/              # Configuration management
│   │   ├── playbook.yml
│   │   └── roles/
│   │       ├── cloud_agent/
│   │       ├── odoo/
│   │       └── monitoring/
│   └── scripts/
│       ├── setup_cloud_vm.sh
│       └── deploy_cloud_agent.sh
└── local/
    └── scripts/
        ├── setup_local_agent.sh
        └── configure_vault_sync.sh

# Vault Structure (synced between agents)
vault/
├── Needs_Action/
│   ├── email/
│   ├── social/
│   ├── accounting/
│   └── whatsapp/
├── In_Progress/
│   ├── cloud/
│   └── local/
├── Pending_Approval/
│   ├── email/
│   ├── social/
│   ├── accounting/
│   └── whatsapp/
├── Approved/
├── Rejected/
├── Done/
├── Plans/
├── Logs/
├── Updates/                  # Cloud agent writes here
├── Dashboard.md              # Local agent writes here
├── Company_Handbook.md
└── Business_Goals.md

# Tests
tests/
├── e2e/
│   ├── test_email_flow.py    # End-to-end email handling
│   ├── test_social_flow.py   # End-to-end social media
│   └── test_accounting_flow.py # End-to-end accounting
├── contract/
│   ├── test_vault_structure.py
│   ├── test_action_file_schema.py
│   └── test_mcp_contracts.py
└── integration/
    ├── test_agent_coordination.py
    ├── test_vault_sync.py
    └── test_approval_workflow.py

# Configuration
config/
├── .env.example              # Example environment variables
├── .gitignore                # Vault sync exclusions
├── pre-commit-config.yaml    # Pre-commit hooks for secret detection
└── mcp_config.json           # MCP server configuration

# Documentation
docs/
├── architecture.md           # System architecture overview
├── deployment.md             # Deployment guide
├── security.md               # Security best practices
└── troubleshooting.md        # Common issues and solutions
```

**Structure Decision**: Dual-agent distributed system with shared components. Cloud agent and local agent are separate Python projects with their own dependencies and tests. Shared models and utilities are in a common package. MCP servers are independent Node.js/Python projects. Orchestration components manage process lifecycle. Deployment scripts handle cloud VM provisioning and configuration. The vault is a separate directory that syncs between agents via Git or Syncthing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Cloud agent (violates Local-First Architecture) | Platinum tier's core value proposition is 24/7 monitoring even when local machine is offline. Specification explicitly requires always-on availability (FR-006, FR-007, FR-015, SC-001, SC-004). | Running agent only on local machine would miss emails/events when machine is off, defeating the primary purpose of Platinum tier. Scheduled wake-up is insufficient for 2-minute email detection requirement. |
| Dual-agent coordination (adds complexity) | Required to maintain security boundaries: cloud agent can only draft (no secrets), local agent executes (has secrets). This separation prevents cloud compromise from accessing sensitive credentials. | Single cloud agent with all credentials would violate security principle of local-only secrets. Single local agent would not provide 24/7 monitoring. |
| Vault synchronization (Git/Syncthing) | Required for agent coordination without direct network communication. File-based coordination provides audit trail and allows offline operation. | Direct agent-to-agent messaging (A2A) is Phase 2 optional upgrade. File-based approach is simpler, more debuggable, and provides natural audit trail. |

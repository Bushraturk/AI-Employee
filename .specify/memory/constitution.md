<!--
Sync Impact Report:
Version: 2.0.0 (Platinum Tier Amendment)
Modified Principles: Principle I (Local-First Architecture) - Added exception clause for justified violations
Added Sections: Platinum Tier vault structure, Principle I exception clause
Removed Sections: None
Templates Status:
  ✅ plan-template.md - reviewed, aligned with principles
  ✅ spec-template.md - reviewed, aligned with principles
  ✅ tasks-template.md - reviewed, aligned with principles
Amendment Rationale:
  - Platinum tier requires sophisticated approval workflow with dual-agent architecture
  - New vault structure supports 24/7 cloud monitoring while maintaining security boundaries
  - Principle I violation justified by explicit requirement for always-on availability
  - Backward compatible: Bronze/Silver/Gold tiers continue using original structure
Follow-up TODOs: None
-->

# Personal AI Employee System Constitution

## Core Principles

### I. Local-First Architecture
The system MUST operate locally by default without requiring external APIs or cloud dependencies. All core functionality (file watching, task processing, vault management) MUST work offline. External integrations (Gmail, WhatsApp) are additive features, not foundational requirements.

**Exception for Platinum Tier**: The Platinum tier MAY deploy a cloud agent for 24/7 monitoring when:
1. The requirement for always-on availability is explicitly specified
2. The cloud agent has read-only access to external services (monitoring only)
3. The cloud agent can only draft actions, never execute them
4. All sensitive credentials remain local-only
5. The local agent maintains full independent functionality
6. The system degrades gracefully when cloud agent is unavailable
7. The violation is documented with detailed justification in the implementation plan

**Rationale**: Local-first ensures reliability, privacy, data sovereignty, and eliminates external service dependencies that could cause system failures. The Platinum tier exception allows always-on availability while maintaining security boundaries and local control.

### II. Human-in-the-Loop for Risk Actions
The system MUST require explicit human approval before executing any action with potential negative consequences. Risk actions include: sending emails, executing external tool calls, modifying files outside the vault, and any destructive operations.

**Rationale**: Autonomous systems must maintain human oversight for safety, accountability, and trust. The system augments human decision-making rather than replacing it.

### III. Markdown as System Memory
All system state, tasks, logs, and knowledge MUST be stored as human-readable Markdown files within the Obsidian vault. No hidden databases or binary state files. The vault structure serves as the single source of truth.

**Rationale**: Markdown ensures transparency, debuggability, version control compatibility, and human inspectability. Users can understand and modify system state directly.

### IV. Modular Watcher Architecture
The perception layer MUST be implemented as independent, pluggable watcher modules. Each watcher (FileSystem, Gmail, WhatsApp) MUST inherit from a common base interface and operate independently. Adding or removing watchers MUST NOT affect core system functionality.

**Rationale**: Modularity enables phased development, independent testing, and extensibility. New input channels can be added without system redesign.

### V. Clear Perception → Reasoning → Action Loop
Every system operation MUST follow the explicit three-stage pipeline: (1) Perception - detect input, (2) Reasoning - process with Claude Code, (3) Action - execute with logging. No stage may be bypassed or hidden.

**Rationale**: Explicit flow ensures predictability, debuggability, and auditability. Each stage can be monitored, tested, and improved independently.

### VI. No Hidden State
All system behavior MUST be deterministic and traceable through Markdown files. No in-memory caches, temporary databases, or ephemeral state that isn't persisted to the vault. Every action MUST produce a log entry.

**Rationale**: Hidden state creates debugging nightmares and unpredictable behavior. Full transparency enables trust and troubleshooting.

### VII. Phased Development with Independent Functionality
The system MUST be developed in phases (Bronze → Silver → Gold → Platinum) where each phase is independently functional and deployable. No phase may depend on incomplete future phases. Each phase MUST deliver standalone value.

**Rationale**: Phased development enables incremental validation, early feedback, and risk mitigation. Each phase serves as a checkpoint for hackathon progress.

### VIII. Safety-First Constraints
The system MUST enforce strict safety boundaries: (1) No destructive file operations outside vault, (2) All actions logged before execution, (3) Email sending requires approval, (4) External tool calls must be whitelisted, (5) Secrets must use environment variables only.

**Rationale**: Safety constraints prevent accidental damage, data loss, and security breaches. The system must be safe to run continuously without supervision.

## Vault Structure Requirements

The Obsidian vault structure varies by tier to support increasing sophistication:

### Bronze/Silver/Gold Tiers (Local-Only Architecture)

```
AI_Employee_Vault/
├── Inbox/              # New tasks arrive here
├── Needs_Action/       # Tasks being processed
├── Done/               # Completed tasks
├── Dashboard.md        # System status and metrics
├── Logs/               # Action audit trail
└── Company_Handbook/   # Knowledge base
```

**Workflow**: Watchers place new tasks in `Inbox/`. The orchestrator moves tasks through `Inbox/ → Needs_Action/ → Done/`. The dashboard auto-updates after each action.

### Platinum Tier (Dual-Agent with Approval Workflow)

```
AI_Employee_Vault/
├── Needs_Action/       # New events detected by watchers
│   ├── email/          # Email events
│   ├── social/         # Social media events
│   ├── accounting/     # Financial transaction events
│   └── whatsapp/       # WhatsApp message events
├── In_Progress/        # Tasks currently being processed
│   ├── cloud/          # Cloud agent claimed tasks
│   │   ├── agent_state.md
│   │   └── watcher_gmail.md
│   └── local/          # Local agent claimed tasks
│       ├── agent_state.md
│       ├── watcher_whatsapp.md
│       └── watcher_finance.md
├── Pending_Approval/   # Draft actions requiring approval
│   ├── email/          # Email send approvals
│   ├── social/         # Social post approvals
│   ├── accounting/     # Accounting entry approvals
│   └── whatsapp/       # WhatsApp send approvals
├── Approved/           # Approved actions ready for execution
├── Rejected/           # Rejected actions (for learning)
├── Done/               # Completed actions (archived)
├── Plans/              # Generated plans and strategies
├── Logs/               # Audit logs (one file per day)
├── Updates/            # Cloud agent updates (for Dashboard merge)
├── Dashboard.md        # System status (local agent only)
├── Company_Handbook.md # Business rules and context
└── Business_Goals.md   # Strategic objectives and metrics
```

**Workflow**: Watchers create action files in `Needs_Action/{domain}/`. Agents claim tasks by moving to `In_Progress/{agent}/` (claim-by-move rule). Cloud agent drafts responses and writes to `Pending_Approval/{domain}/`. User approves by moving to `Approved/`. Local agent executes and moves to `Done/`. Dashboard is single-writer (local agent only), cloud agent writes to `Updates/` for merge.

**Rationale**: Platinum tier requires sophisticated approval workflow to support 24/7 cloud monitoring while maintaining security boundaries. Domain-specific folders enable routing, agent-specific folders prevent duplicate work, and the approval workflow ensures human oversight for all sensitive actions.

## Watcher Interface Contract

Every watcher MUST implement:
- `start()` - Begin monitoring input source
- `stop()` - Gracefully shutdown
- `get_new_tasks()` - Return list of task objects
- `mark_processed(task_id)` - Acknowledge task handling

Watchers MUST NOT directly modify vault files. All vault writes go through the orchestrator.

## Claude Code Integration

The reasoning layer MUST use Claude Code to:
- Parse task Markdown into structured data
- Classify task priority and type
- Generate action plans
- Draft responses (emails, documents)
- Update dashboard metrics

Claude Code MUST receive tasks as Markdown input and return structured JSON output with: task_id, priority, action_type, proposed_actions, requires_approval.

## Action Execution Policy

Actions are categorized:
- **Safe** (auto-execute): File reads, dashboard updates, log writes within vault
- **Approval Required**: Email sends, external API calls, file operations outside vault
- **Forbidden**: Destructive operations without explicit user command, plaintext secret storage

The orchestrator MUST check action category before execution and enforce approval gates.

## Logging and Audit Requirements

Every action MUST generate a log entry with:
- Timestamp (ISO 8601)
- Action type
- Input task reference
- Output/result
- Approval status (if applicable)
- Error details (if failed)

Logs MUST be append-only Markdown files in `Logs/YYYY-MM-DD.md` format.

## Phase Completion Criteria

**Bronze**: FileSystem watcher operational, Inbox→Needs_Action→Done workflow functional, Claude processes tasks, Dashboard updates automatically, No external APIs.

**Silver**: Gmail watcher integrated, Email classification working, Draft replies generated, Human approval flow for sends, Bronze stability maintained.

**Gold**: MCP server integration complete, Tool registry operational, Safe tool execution working, Audit logs comprehensive, Rollback capability implemented.

**Platinum**: Dual-agent architecture operational (cloud + local), 24/7 monitoring functional, Approval workflow enforced (100% compliance), Vault synchronization working (Git or Syncthing), Odoo integration complete, Multi-agent coordination via claim-by-move rule, Dashboard single-writer pattern enforced, End-to-end demo under 5 minutes.

## Testing Requirements

Each phase MUST include:
- Unit tests for new components
- Integration tests for watcher→orchestrator→action flow
- End-to-end test demonstrating phase completion criteria
- Regression tests ensuring previous phases still work

Tests MUST be automated and runnable via single command.

## Security Requirements

- Credentials MUST use environment variables (`.env` file, never committed)
- API keys MUST NOT appear in code or logs
- Email content MUST be sanitized before logging
- File operations MUST validate paths are within vault
- External tool calls MUST be whitelisted by name
- **Platinum Tier**: Cloud agent MUST NOT have access to sensitive credentials (WhatsApp session, banking, payment)
- **Platinum Tier**: Vault sync MUST exclude secrets (.env, *.session, *.credentials)

## Performance Standards

- FileSystem watcher MUST detect new files within 2 seconds
- Task processing MUST complete within 30 seconds for simple tasks
- Dashboard updates MUST be atomic (no partial writes)
- System MUST handle 100 tasks/day without degradation
- Memory usage MUST stay under 500MB during normal operation
- **Platinum Tier**: Cloud agent MUST detect emails within 2 minutes
- **Platinum Tier**: Vault sync MUST complete within 10 seconds for typical updates (under 100 files)

## Governance

This constitution supersedes all other development practices. All code, architecture decisions, and feature implementations MUST comply with these principles.

**Amendment Process**: Constitution changes require:
1. Documented rationale for change
2. Impact analysis on existing phases
3. Migration plan if breaking changes
4. Approval before implementation

**Compliance Verification**: Every PR and design review MUST verify:
- Principles not violated (or violations properly justified)
- Safety constraints enforced
- Logging requirements met
- Phase independence maintained

**Version Control**: Constitution follows semantic versioning:
- MAJOR: Principle removal or incompatible changes
- MINOR: New principle or section added
- PATCH: Clarifications or wording improvements

**Version**: 2.0.0 | **Ratified**: 2026-02-14 | **Last Amended**: 2026-02-25

## Amendment History

### v2.0.0 (2026-02-25) - Platinum Tier Amendment
**Changes**:
- Added Platinum tier vault structure with approval workflow folders
- Added exception clause to Principle I (Local-First Architecture) for justified cloud agent deployment
- Updated Phase Completion Criteria for Platinum tier
- Added Platinum-specific security and performance requirements

**Rationale**: Platinum tier requires 24/7 monitoring capability that extends beyond local machine uptime. The dual-agent architecture with approval workflow maintains security boundaries while enabling always-on availability. This is a MAJOR version change because the vault structure is fundamentally different for Platinum tier.

**Impact**: Bronze/Silver/Gold tiers continue using original vault structure. Platinum tier uses new structure. No breaking changes to existing tiers.

**Migration**: New Platinum tier projects use new structure from start. Existing projects upgrading to Platinum must migrate vault structure and implement dual-agent coordination.

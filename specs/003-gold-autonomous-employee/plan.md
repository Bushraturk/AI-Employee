# Implementation Plan: Gold Tier - Autonomous Employee

**Branch**: `003-gold-autonomous-employee` | **Date**: 2026-02-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-gold-autonomous-employee/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Gold Tier extends the Personal AI Employee system with full cross-domain integration (Personal + Business), adding: (1) Odoo Community accounting integration via JSON-RPC MCP server for automated bookkeeping, (2) Multi-platform social media management (Facebook, Instagram, Twitter) with platform-specific optimization, (3) Weekly business and accounting audits with CEO briefing generation, (4) Multiple independent MCP servers for domain separation (accounting, social, communications), (5) Ralph Wiggum autonomous loop for multi-step workflow execution with error recovery, (6) Comprehensive error recovery and graceful degradation, and (7) Enhanced audit logging across all domains. This tier transforms the system from a task executor into an autonomous business intelligence advisor capable of handling complex workflows end-to-end.

## Technical Context

**Language/Version**: Python 3.9+
**Primary Dependencies**:
- Core: watchdog, frontmatter, markdown, python-dotenv, pytest (from Bronze/Silver)
- Odoo: NEEDS CLARIFICATION (odoorpc vs requests for JSON-RPC)
- Social Media: NEEDS CLARIFICATION (facebook-sdk vs requests, tweepy vs twitter-api-v2, instagram-private-api vs facebook graph API)
- MCP: NEEDS CLARIFICATION (multiple MCP server orchestration patterns, server lifecycle management)
- Scheduling: NEEDS CLARIFICATION (APScheduler vs cron-like for weekly audits)
- Error Recovery: NEEDS CLARIFICATION (tenacity vs custom retry logic, circuit breaker patterns)

**Storage**: Markdown files in Obsidian vault (per constitution), no databases
**Testing**: pytest with contract/integration/unit test structure
**Target Platform**: Windows, macOS, Linux (cross-platform CLI)
**Project Type**: Single project (CLI-based autonomous system)
**Performance Goals**:
- Handle 200+ tasks/day across all channels
- Memory usage <1.5GB during normal operation
- Transaction sync within 5 minutes
- Audit log queries <2 seconds
- 30-day continuous operation without crashes

**Constraints**:
- Local-first architecture (Odoo runs locally)
- Human-in-the-loop for risk actions (approval workflow)
- Markdown as single source of truth (no hidden state)
- Rate limits for all external APIs (Facebook, Instagram, Twitter, Odoo)
- Backward compatibility with Bronze/Silver Tiers
- Domain separation via multiple MCP servers
- Safety boundaries for autonomous execution

**Scale/Scope**:
- 3+ independent MCP servers (accounting, social, communications)
- 4 social media platforms (LinkedIn, Facebook, Instagram, Twitter)
- 70+ functional requirements across 7 major feature areas
- Multi-step autonomous workflows with error recovery
- Weekly audit generation with business intelligence

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Local-First Architecture
**Status**: COMPLIANT with clarification
- Odoo Community runs locally (JSON-RPC on local network) ✓
- Social media APIs (Facebook, Instagram, Twitter) are external but additive features ✓
- Core Bronze/Silver functionality remains offline-capable ✓
- **Clarification**: External social media APIs are additive, not foundational. System must work offline for local tasks.

### ⚠️ Principle II: Human-in-the-Loop for Risk Actions
**Status**: REQUIRES JUSTIFICATION
- Ralph Wiggum autonomous loop executes multi-step workflows automatically
- **Concern**: FR-043 states "execute plan steps automatically in order" - could bypass approval for risk actions
- **Mitigation Required**: Ralph Wiggum loop MUST check each step against risk action policy before execution
- **Justification**: Autonomy is valuable for multi-step workflows, but FR-050 explicitly states "no autonomous execution of high-risk actions without approval"
- **Gate**: Ralph Wiggum implementation MUST enforce approval gates for risk actions (email sends, external API calls, destructive operations)

### ✅ Principle III: Markdown as System Memory
**Status**: COMPLIANT
- All new entities (OdooTransaction, SocialMediaPost, AuditReport, WorkflowExecution, ErrorRecoveryLog) stored as Markdown ✓
- CEO briefings generated as Markdown (FR-028) ✓
- Execution plans stored as Plan.md (FR-042) ✓
- No hidden databases or binary state ✓

### ✅ Principle IV: Modular Watcher Architecture
**Status**: COMPLIANT
- Multiple independent MCP servers (FR-031) align with modular architecture ✓
- Domain separation (accounting, social, communications) follows watcher pattern ✓
- Independent failure handling (FR-037) maintains modularity ✓

### ✅ Principle V: Clear Perception → Reasoning → Action Loop
**Status**: COMPLIANT
- Ralph Wiggum loop follows explicit stages: analyze task → generate plan → execute steps → log outcomes ✓
- Each MCP server action goes through perception (detect task) → reasoning (Claude processes) → action (MCP executes) ✓
- Audit logging (FR-061-070) ensures traceability ✓

### ✅ Principle VI: No Hidden State
**Status**: COMPLIANT
- WorkflowExecution entity tracks execution state in Markdown (FR-044) ✓
- ErrorRecoveryLog persists all recovery attempts (FR-064) ✓
- Audit logs are append-only Markdown (FR-067) ✓
- No in-memory caches or ephemeral state ✓

### ✅ Principle VII: Phased Development with Independent Functionality
**Status**: COMPLIANT
- Gold Tier builds on Bronze/Silver without breaking changes (FR-072) ✓
- Silver Tier features continue working (FR-071) ✓
- Each Gold feature (Odoo, social media, audits, Ralph Wiggum) can be tested independently ✓

### ✅ Principle VIII: Safety-First Constraints
**Status**: COMPLIANT with enforcement required
- All actions logged before execution (FR-061) ✓
- Error recovery maintains data integrity (FR-058) ✓
- Secrets use environment variables (FR-002, constraint) ✓
- **Enforcement Required**: Ralph Wiggum loop must respect safety boundaries (FR-050, FR-190)
- **Gate**: No autonomous execution of destructive operations, email sends, or external tool calls without approval

### Summary
**Overall Status**: COMPLIANT with 1 area requiring careful implementation

**Critical Gate**: Ralph Wiggum autonomous loop (Principle II) MUST enforce approval gates for risk actions. Implementation must verify each step against action execution policy before proceeding. This is the primary architectural risk for Gold Tier.

**Re-check After Phase 1**: Verify that data-model.md and contracts/ maintain Markdown-first approach and that Ralph Wiggum execution plan includes approval checkpoints.

---

## Phase 1 Re-Evaluation (Post-Design)

**Date**: 2026-02-23
**Status**: ✅ COMPLIANT - All design artifacts maintain constitution principles

### Verification Results

#### ✅ Principle III: Markdown as System Memory
**Verified**: data-model.md defines all 6 entities as Markdown files
- OdooTransaction: `Accounting/transactions/{transaction_id}.md`
- SocialMediaPost: `Social_Media/posts/{post_id}.md`
- MCPServer: `System/mcp_servers/{server_id}.md`
- AuditReport: `Audits/weekly/{report_id}.md`
- WorkflowExecution: `Workflows/executions/{execution_id}.md`
- ErrorRecoveryLog: `Logs/error_recovery/{error_id}.md`

All entities use frontmatter for structured data and Markdown body for human-readable content. No hidden databases or binary state.

#### ✅ Principle II: Human-in-the-Loop for Risk Actions
**Verified**: WorkflowExecution entity includes approval checkpoints
- Each step in `steps` array has `status` field (pending/in_progress/completed/failed)
- Step dependencies tracked via `dependencies` array
- Execution can be `paused` for human intervention
- FR-050 explicitly states "no autonomous execution of high-risk actions without approval"

**Implementation Requirement**: Ralph Wiggum loop MUST check each step's `action_type` against risk action policy before execution. If step is a risk action (send_email, external API call, destructive operation), set status to `pending` and request approval before proceeding.

#### ✅ API Contracts Maintain Safety
**Verified**: All 4 API contracts include error handling and rate limiting
- Odoo: Retry with backoff, conflict detection, no automatic overwrites
- Facebook: Rate limiting, circuit breaker, policy violation handling
- Instagram: Two-step publishing with status checks, daily limits enforced
- Twitter: Automatic rate limit handling via tweepy, error recovery

#### ✅ Quickstart Guide Emphasizes Security
**Verified**: quickstart.md includes security checks
- Environment variables for all credentials
- `.env` not tracked in git
- Token rotation guidance
- HTTPS for all external APIs

### Conclusion
Phase 1 design artifacts are **COMPLIANT** with all constitution principles. The critical implementation requirement is that Ralph Wiggum loop must enforce approval gates for risk actions at runtime, which will be verified during Phase 2 (tasks generation) and implementation.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
src/
├── watchers/                    # Perception layer (Bronze/Silver)
│   ├── base_watcher.py
│   ├── filesystem_watcher.py
│   ├── gmail_watcher.py
│   └── whatsapp_watcher.py
├── mcp_servers/                 # NEW: Multiple MCP servers (Gold)
│   ├── accounting_mcp/          # Odoo integration
│   │   ├── server.py
│   │   ├── odoo_client.py
│   │   └── tools/
│   ├── social_mcp/              # Facebook, Instagram, Twitter
│   │   ├── server.py
│   │   ├── facebook_client.py
│   │   ├── instagram_client.py
│   │   ├── twitter_client.py
│   │   └── tools/
│   └── comms_mcp/               # Gmail, WhatsApp (from Silver)
│       ├── server.py
│       └── tools/
├── orchestrator/                # Reasoning layer
│   ├── task_processor.py
│   ├── action_executor.py
│   ├── approval_manager.py
│   └── ralph_wiggum.py          # NEW: Autonomous loop (Gold)
├── models/                      # Data entities
│   ├── task.py
│   ├── odoo_transaction.py      # NEW: Gold entities
│   ├── social_media_post.py     # NEW: Gold entities
│   ├── audit_report.py          # NEW: Gold entities
│   ├── workflow_execution.py    # NEW: Gold entities
│   └── error_recovery_log.py    # NEW: Gold entities
├── services/                    # Business logic
│   ├── vault_manager.py
│   ├── dashboard_updater.py
│   ├── audit_generator.py       # NEW: Weekly audits (Gold)
│   └── error_recovery.py        # NEW: Error handling (Gold)
└── cli/
    └── main.py

tests/
├── contract/                    # API contract tests
│   ├── test_odoo_contracts.py
│   ├── test_facebook_contracts.py
│   ├── test_instagram_contracts.py
│   └── test_twitter_contracts.py
├── integration/                 # End-to-end tests
│   ├── test_odoo_sync.py
│   ├── test_social_posting.py
│   ├── test_audit_generation.py
│   ├── test_ralph_wiggum_loop.py
│   └── test_error_recovery.py
└── unit/                        # Component tests
    ├── test_watchers/
    ├── test_mcp_servers/
    ├── test_orchestrator/
    ├── test_models/
    └── test_services/

AI_Employee_Vault/               # Obsidian vault (unchanged structure)
├── Inbox/
├── Needs_Action/
├── Done/
├── Dashboard.md
├── Logs/
│   └── YYYY-MM-DD.md
├── Company_Handbook/
├── Accounting/                  # NEW: Odoo sync data (Gold)
│   └── transactions/
├── Social_Media/                # NEW: Post history (Gold)
│   └── posts/
├── Audits/                      # NEW: CEO briefings (Gold)
│   └── weekly/
└── Workflows/                   # NEW: Ralph Wiggum executions (Gold)
    └── executions/
```

**Structure Decision**: Single project structure (Option 1) is appropriate because this is a CLI-based autonomous system, not a web or mobile application. The modular watcher architecture from Bronze/Silver is extended with multiple MCP servers for domain separation. New Gold Tier components (mcp_servers/, ralph_wiggum.py, audit_generator.py, error_recovery.py) integrate cleanly without breaking existing structure. Vault structure expands with new folders for accounting, social media, audits, and workflows while maintaining Markdown-first approach.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Ralph Wiggum autonomous loop (Principle II concern) | Gold Tier requires multi-step workflow automation without micromanagement (FR-041-050, User Story 5). Business value: enables true workflow automation and transforms system from task executor to autonomous advisor. | Manual step-by-step execution rejected because: (1) defeats purpose of "autonomous employee", (2) user explicitly requested "autonomous multi-step task completion", (3) 40+ hour Gold Tier scope requires automation to be feasible. Mitigation: FR-050 enforces safety boundaries, implementation MUST check each step against risk action policy before execution. |

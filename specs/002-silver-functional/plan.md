# Implementation Plan: Silver Tier - Functional Assistant

**Branch**: `002-silver-functional` | **Date**: 2026-02-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-silver-functional/spec.md`

## Summary

Silver Tier extends the Bronze Phase local foundation with multi-channel input processing (Gmail, WhatsApp, LinkedIn), automated LinkedIn posting for business development, intelligent planning with Plan.md generation, MCP server for external actions, human-in-the-loop approval workflow, and basic scheduling capabilities. The system maintains local-first architecture while adding external integrations as optional, additive features.

**Technical Approach**: Implement three new watchers (GmailWatcher, WhatsAppWatcher, LinkedInWatcher) inheriting from BaseWatcher interface. Add MCP server layer for external actions with approval queue system. Implement agent skills for classification, planning, and content generation. Use OAuth2 for Gmail/LinkedIn authentication and scheduling system for automation.

## Technical Context

**Language/Version**: Python 3.9+
**Primary Dependencies**:
- Core: watchdog, python-frontmatter, markdown, python-dotenv, pytest (from Bronze)
- Gmail: google-auth-oauthlib, google-api-python-client
- LinkedIn: linkedin-api or requests + OAuth2
- WhatsApp: selenium or playwright (web automation)
- MCP: mcp-server-python or custom implementation
- Scheduling: APScheduler or schedule
- Authentication: oauthlib, requests-oauthlib

**Storage**: Markdown files in Obsidian vault (Inbox, Needs_Action, Done, Needs_Approval, Logs, Company_Handbook)
**Testing**: pytest with fixtures for watcher testing, mock external APIs
**Target Platform**: Windows (Task Scheduler), macOS/Linux (cron)
**Project Type**: Single project (extends existing Bronze codebase)
**Performance Goals**:
- Detect new content within 30 seconds across all channels
- Process 100+ tasks/day without degradation
- 90%+ classification accuracy
- 99%+ scheduled task reliability

**Constraints**:
- Must maintain local-first architecture (Bronze features work offline)
- Memory usage <1GB during normal operation
- Human approval required for all external actions (emails, posts, messages)
- OAuth2 tokens stored securely (not in vault, not in git)
- Rate limits respected for all external APIs
- Must inherit from BaseWatcher interface
- All AI functionality as agent skills (no direct AI calls in Python)

**Scale/Scope**:
- 3 concurrent watchers (FileSystem, Gmail, WhatsApp, LinkedIn)
- 50+ pending approvals in queue
- 2-3 LinkedIn posts per week
- 10+ agent skills total
- Support for multi-language content (English, Urdu)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Local-First Architecture ✅ PASS
**Requirement**: System must operate locally by default without requiring external APIs.
**Compliance**: Bronze phase (FileSystem watcher, vault management, task processing) continues to work offline. Gmail, WhatsApp, LinkedIn watchers are additive features that can be disabled. Core orchestrator and vault operations remain local-first.
**Evidence**: FR-061 "All Bronze phase features MUST continue working", FR-062 "System MUST maintain local-first architecture"

### II. Human-in-the-Loop for Risk Actions ✅ PASS
**Requirement**: System must require explicit human approval before executing actions with potential negative consequences.
**Compliance**: FR-035 to FR-044 define comprehensive approval workflow. All email sends, LinkedIn posts, and WhatsApp messages require approval. Approval queue in Needs_Approval folder with CLI interface for review.
**Evidence**: FR-036 "System MUST store pending actions in Needs_Approval folder", FR-039 "System MUST support approve, reject, and edit operations"

### III. Markdown as System Memory ✅ PASS
**Requirement**: All system state must be stored as human-readable Markdown files.
**Compliance**: Tasks from all channels stored as Markdown in Inbox. Approval queue in Needs_Approval folder. Plans stored as Plan.md files. LinkedIn post history in vault. No hidden databases.
**Evidence**: FR-006 "System MUST preserve channel-specific metadata in task files", FR-019 "System MUST store post history in vault"

### IV. Modular Watcher Architecture ✅ PASS
**Requirement**: Perception layer must be implemented as independent, pluggable watcher modules inheriting from common base interface.
**Compliance**: FR-001 to FR-003 define three new watchers. FR-004 "All watchers MUST run concurrently and independently". All inherit from BaseWatcher interface from Bronze phase.
**Evidence**: Constraint "Must inherit from BaseWatcher interface for all watchers"

### V. Clear Perception → Reasoning → Action Loop ✅ PASS
**Requirement**: Every operation must follow explicit three-stage pipeline.
**Compliance**: Watchers detect content (Perception) → Agent skills classify and plan (Reasoning) → MCP server executes with approval (Action). FR-009 to FR-013 define classification. FR-026 to FR-034 define MCP execution.
**Evidence**: FR-052 "All AI functionality MUST be implemented as agent skills", FR-027 to FR-029 define MCP actions

### VI. No Hidden State ✅ PASS
**Requirement**: All system behavior must be deterministic and traceable through Markdown files.
**Compliance**: All tasks, approvals, plans, and post history stored in vault. FR-044 "System MUST log all approval decisions to audit trail". FR-033 "System MUST log all MCP calls comprehensively".
**Evidence**: SC-007 "Approval decisions are logged with complete audit trail", SC-022 "Complete audit trail exists for all actions"

### VII. Phased Development with Independent Functionality ✅ PASS
**Requirement**: Each phase must be independently functional and deployable.
**Compliance**: FR-061 "All Bronze phase features MUST continue working". Silver adds features without breaking Bronze. Each watcher can be enabled/disabled independently.
**Evidence**: Constraint "Must be compatible with existing Bronze phase code without breaking changes"

### VIII. Safety-First Constraints ✅ PASS
**Requirement**: System must enforce strict safety boundaries.
**Compliance**: FR-035 "System MUST create approval queue for sensitive actions". FR-042 "System MUST auto-reject actions after 24-hour timeout". FR-031 "System MUST validate actions before execution". Secrets in environment variables only.
**Evidence**: Constraint "OAuth2 tokens must be stored securely (not in vault, not in git)", FR-043 "System MUST classify actions by risk level"

**Constitution Check Result**: ✅ ALL GATES PASSED - No violations, proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/002-silver-functional/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (in progress)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   ├── gmail-api.md
│   ├── linkedin-api.md
│   ├── whatsapp-api.md
│   └── mcp-protocol.md
├── checklists/
│   └── requirements.md  # Validation checklist (complete)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
src/
├── watchers/
│   ├── base_watcher.py          # Existing from Bronze
│   ├── filesystem_watcher.py    # Existing from Bronze
│   ├── gmail_watcher.py         # NEW - Gmail monitoring
│   ├── whatsapp_watcher.py      # NEW - WhatsApp monitoring
│   ├── linkedin_watcher.py      # NEW - LinkedIn monitoring
│   └── auth/
│       ├── gmail_auth.py        # NEW - Gmail OAuth2
│       ├── linkedin_auth.py     # NEW - LinkedIn OAuth2
│       └── token_storage.py     # NEW - Secure token management
├── mcp/
│   ├── server.py                # NEW - MCP server implementation
│   ├── tools/
│   │   ├── gmail_tool.py        # NEW - Email sending
│   │   ├── linkedin_tool.py     # NEW - LinkedIn posting
│   │   └── whatsapp_tool.py     # NEW - WhatsApp messaging
│   └── registry.py              # NEW - Tool registry and validation
├── approval/
│   ├── queue.py                 # NEW - Approval queue management
│   ├── cli.py                   # NEW - CLI interface for approvals
│   └── risk_classifier.py       # NEW - Risk level classification
├── scheduling/
│   ├── scheduler.py             # NEW - Task scheduling
│   └── cron_parser.py           # NEW - Cron syntax parsing
├── planning/
│   └── plan_generator.py        # NEW - Plan.md generation logic
├── orchestrator.py              # MODIFY - Add multi-watcher coordination
├── task_processor.py            # Existing from Bronze
└── vault_manager.py             # Existing from Bronze

.specify/commands/
├── process-task.command.md      # Existing from Bronze
├── validate-task.command.md     # Existing from Bronze
├── update-dashboard.command.md  # Existing from Bronze
├── log-action.command.md        # Existing from Bronze
├── classify-email.command.md    # NEW - Email classification
├── classify-whatsapp.command.md # NEW - WhatsApp classification
├── classify-linkedin.command.md # NEW - LinkedIn classification
├── generate-linkedin-post.command.md  # NEW - Post generation
├── create-plan.command.md       # NEW - Plan.md generation
├── draft-email-reply.command.md # NEW - Email reply drafting
├── draft-whatsapp-reply.command.md    # NEW - WhatsApp reply drafting
└── validate-action.command.md   # NEW - Pre-execution validation

tests/
├── unit/
│   ├── test_gmail_watcher.py    # NEW
│   ├── test_whatsapp_watcher.py # NEW
│   ├── test_linkedin_watcher.py # NEW
│   ├── test_mcp_server.py       # NEW
│   ├── test_approval_queue.py   # NEW
│   └── test_scheduler.py        # NEW
├── integration/
│   ├── test_multi_watcher.py    # NEW - Test concurrent watchers
│   ├── test_approval_flow.py    # NEW - End-to-end approval
│   └── test_bronze_compatibility.py  # NEW - Regression tests
└── fixtures/
    ├── mock_gmail_api.py        # NEW
    ├── mock_linkedin_api.py     # NEW
    └── mock_whatsapp_api.py     # NEW
```

**Structure Decision**: Single project structure extending Bronze codebase. New modules organized by functional area (watchers, mcp, approval, scheduling, planning). Agent skills in `.specify/commands/` following Bronze pattern. Tests mirror source structure with unit, integration, and fixture separation.

## Complexity Tracking

> **No violations detected - this section intentionally left empty**

All constitution principles are satisfied without requiring complexity justifications.

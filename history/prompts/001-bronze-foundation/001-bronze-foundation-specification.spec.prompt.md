---
id: 001
title: Bronze Foundation Specification
stage: spec
date: 2026-02-14
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-bronze-foundation
branch: 001-bronze-foundation
user: admin
command: /sp.specify
labels: ["spec", "bronze-phase", "local-first", "filesystem-watcher", "autonomous-ai"]
links:
  spec: specs/001-bronze-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-foundation/spec.md
  - specs/001-bronze-foundation/checklists/requirements.md
tests:
  - N/A (specification document)
---

## Prompt

Bronze Phase - Local Foundation

Build the foundational local-first autonomous AI employee system with:

Core Workflow:
- Obsidian vault with Inbox/Needs_Action/Done folder structure
- FileSystem watcher that detects new Markdown task files in Inbox
- Orchestrator that processes tasks through perception → reasoning → action loop
- Claude Code integration for task parsing, classification, and action planning
- Automatic Dashboard.md updates showing system status and metrics
- Comprehensive logging system for all actions

Key Components:
1. Base Watcher (abstract interface for all future watchers)
2. FileSystem Watcher (monitors Inbox folder for new .md files)
3. Orchestrator (coordinates watcher → Claude → action execution)
4. Task Processor (parses Markdown tasks into structured data)
5. Action Executor (performs safe file operations within vault)
6. Dashboard Manager (updates system metrics and status)
7. Logger (append-only audit trail)

Success Criteria:
- Drop a task file in Inbox → automatically moves to Needs_Action → Claude processes → moves to Done
- Dashboard updates in real-time
- All actions logged with timestamps
- System runs continuously without external dependencies
- No external APIs or cloud services required

Constraints:
- Local-first only (no Gmail, WhatsApp, or external integrations)
- All state stored as Markdown files
- No hidden databases or binary state
- File operations restricted to vault directory
- Must be production-ready and stable for Silver phase to build upon

## Response snapshot

Created comprehensive Bronze Phase specification with 3 prioritized user stories:

**User Story 1 (P1) - Automatic Task Detection and Processing**: Core autonomous workflow where users drop task files in Inbox and system automatically detects, processes via Claude Code, and moves through workflow stages. 3 acceptance scenarios covering single file, successful processing, and concurrent tasks.

**User Story 2 (P2) - Real-Time Dashboard Visibility**: Dashboard.md provides system status, task counts, recent activity, and metrics for monitoring AI employee work. 3 acceptance scenarios covering idle state, active processing, and completed tasks.

**User Story 3 (P3) - Comprehensive Audit Trail**: Every action logged with timestamps, task references, and outcomes in Logs/YYYY-MM-DD.md files. 3 acceptance scenarios covering detection logs, processing logs, and error logs.

**18 Functional Requirements** defined (FR-001 to FR-018) covering:
- Continuous Inbox monitoring with 2-second detection
- Automatic file movement through workflow stages
- Markdown task parsing and Claude Code integration
- Safe action execution within vault boundaries
- Dashboard and logging requirements
- Vault structure initialization
- Error handling and graceful shutdown
- Base watcher interface for future extensibility

**10 Success Criteria** with measurable metrics:
- 30-second processing time for simple tasks
- 2-second file detection
- 1-second dashboard updates
- 100 tasks/day capacity
- 500MB memory limit
- 24-hour continuous operation
- 100% vault boundary enforcement
- 95% error recovery rate

**Key Entities**: Task, Watcher, Action, Dashboard Metrics with attributes and relationships defined.

**Edge Cases**: 7 scenarios identified (malformed files, deleted folders, name conflicts, crashes, disk space, concurrent modification, vault relocation).

**Scope Management**: Clear Out of Scope section deferring Gmail/WhatsApp (Silver), MCP tools (Gold), self-improvement (Platinum), and 5 other features.

**Validation**: Created requirements.md checklist - all items passed. Zero [NEEDS CLARIFICATION] markers. Spec is testable, unambiguous, technology-agnostic, and ready for planning phase.

## Outcome

- ✅ Impact: Complete Bronze phase specification created, defining foundational autonomous AI employee system with clear user stories, requirements, and success criteria
- 🧪 Tests: Specification includes 9 acceptance scenarios across 3 user stories, all independently testable
- 📁 Files: Created specs/001-bronze-foundation/spec.md and specs/001-bronze-foundation/checklists/requirements.md
- 🔁 Next prompts: /sp.plan to create technical architecture and implementation plan for Bronze phase
- 🧠 Reflection: Specification successfully balances clarity with flexibility. All constitution principles (local-first, Markdown memory, modular watchers, perception→reasoning→action loop) are reflected in requirements. No implementation details leaked while maintaining testability.

## Evaluation notes (flywheel)

- Failure modes observed: None - specification creation successful with full validation
- Graders run and results (PASS/FAIL): Requirements checklist - PASS (all 14 items validated)
- Prompt variant (if applicable): N/A (initial specification)
- Next experiment (smallest change to try): Validate that /sp.plan correctly interprets these requirements and generates appropriate technical architecture without over-engineering

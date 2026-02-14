---
id: 002
title: Bronze Foundation Implementation Plan
stage: plan
date: 2026-02-14
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-bronze-foundation
branch: 001-bronze-foundation
user: admin
command: /sp.plan
labels: ["plan", "bronze-phase", "architecture", "python", "watchdog", "local-first"]
links:
  spec: specs/001-bronze-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-bronze-foundation/plan.md
  - specs/001-bronze-foundation/research.md
  - specs/001-bronze-foundation/data-model.md
  - specs/001-bronze-foundation/contracts/task-schema.yaml
  - specs/001-bronze-foundation/quickstart.md
  - CLAUDE.md (updated with Bronze phase technologies)
tests:
  - N/A (planning artifacts)
---

## Prompt

(Empty user input - /sp.plan command executed without additional arguments)

## Response snapshot

Created comprehensive implementation plan for Bronze phase with complete Phase 0 (Research) and Phase 1 (Design) artifacts.

**Technical Context Defined**:
- Language: Python 3.11 (minimum 3.9)
- Dependencies: watchdog, python-frontmatter, pyyaml, subprocess, pathlib
- Storage: Markdown files only (no database)
- Testing: pytest, pytest-asyncio, pytest-timeout
- Platform: Cross-platform (Windows, macOS, Linux)
- Project Type: Single project (CLI tool with daemon mode)
- Performance: 2s detection, 30s processing, 100 tasks/day, <500MB memory

**Constitution Check**: ✅ PASSED
- All 8 core principles satisfied
- Vault structure compliance verified
- Watcher interface compliance confirmed
- Performance standards aligned
- No violations to justify

**Project Structure**:
- Single project layout (src/ and tests/)
- 9 core modules: base_watcher, filesystem_watcher, orchestrator, task_processor, action_executor, dashboard_manager, logger, vault_manager, main
- Test structure: unit/, integration/, fixtures/
- Vault structure: Inbox/, Needs_Action/, Done/, Dashboard.md, Logs/, Company_Handbook/

**Phase 0 - Research (research.md)**:
8 technology decisions documented with rationale:
1. File watching: watchdog (event-driven, cross-platform)
2. Markdown parsing: python-frontmatter (YAML frontmatter extraction)
3. Claude Code integration: subprocess with JSON I/O (local-first)
4. Concurrency: Synchronous with threading (simpler for Bronze)
5. Configuration: Environment variables + .env file (12-factor app)
6. Error handling: Try-catch with logging + retry (graceful recovery)
7. Dashboard updates: Temp file + atomic rename (constitution requirement)
8. Logging format: Markdown with structured sections (aligns with principles)

**Phase 1 - Design Artifacts**:

1. **data-model.md**: 4 core entities defined
   - Task: 11 attributes with validation rules, state transitions (inbox→needs_action→done)
   - Watcher: Abstract interface with 4 methods (start, stop, get_new_tasks, mark_processed)
   - Action: 7 attributes for audit trail, 9 action types defined
   - Dashboard Metrics: 10 attributes with computed metrics formulas

2. **contracts/task-schema.yaml**: Complete task file format specification
   - YAML frontmatter schema (4 required fields, 4 optional fields)
   - Markdown body requirements
   - Validation rules with Python code examples
   - Error handling behaviors
   - File naming conventions
   - Status transition rules
   - 3 complete examples (minimal, complete, with result)

3. **quickstart.md**: End-to-end setup guide
   - Prerequisites verification
   - Installation steps (clone, venv, dependencies)
   - Configuration (.env file setup)
   - Running the system (foreground, daemon, logs)
   - Creating first task walkthrough
   - Dashboard overview
   - Common tasks and troubleshooting
   - Testing instructions
   - Success criteria checklist

**Agent Context Updated**: CLAUDE.md updated with Python 3.11, watchdog, pyyaml, subprocess, pathlib, and Markdown storage.

**Implementation Notes**:
- Critical path: 9 modules in dependency order
- Risk mitigation: Atomic operations, retry logic, path validation
- Testing strategy: Unit, integration, contract, performance tests

## Outcome

- ✅ Impact: Complete implementation plan created with all Phase 0 and Phase 1 artifacts. Bronze phase architecture fully defined and ready for task generation.
- 🧪 Tests: Testing strategy defined (unit, integration, contract, performance). Test structure documented in plan.md.
- 📁 Files: Created 5 planning artifacts (plan.md, research.md, data-model.md, task-schema.yaml, quickstart.md) + updated CLAUDE.md
- 🔁 Next prompts: /sp.tasks to generate actionable task list from plan and spec
- 🧠 Reflection: Plan successfully balances technical detail with implementation flexibility. All constitution principles verified. Technology choices prioritize simplicity and local-first operation. Single project structure appropriate for CLI tool. Phase 0 research provides clear rationale for all decisions. Phase 1 design artifacts are comprehensive and implementation-ready.

## Evaluation notes (flywheel)

- Failure modes observed: None - planning phase completed successfully
- Graders run and results (PASS/FAIL): Constitution Check - PASS (all 8 principles satisfied, no violations)
- Prompt variant (if applicable): N/A (standard planning workflow)
- Next experiment (smallest change to try): Validate that /sp.tasks correctly interprets plan.md structure and generates appropriate task breakdown with proper dependencies

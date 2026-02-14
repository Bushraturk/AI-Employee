# Implementation Plan: Bronze Phase - Local Foundation

**Branch**: `001-bronze-foundation` | **Date**: 2026-02-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-bronze-foundation/spec.md`

## Summary

Build the foundational local-first autonomous AI employee system with automatic task detection, processing, and workflow management. The system monitors an Obsidian vault's Inbox folder for new Markdown task files, processes them through Claude Code for reasoning and action planning, and moves them through workflow stages (Inbox → Needs_Action → Done) while maintaining real-time dashboard updates and comprehensive audit logs. This Bronze phase establishes the core perception → reasoning → action loop and modular watcher architecture that Silver, Gold, and Platinum phases will build upon.

## Technical Context

**Language/Version**: Python 3.11 (minimum 3.9 for type hints and asyncio features)
**Primary Dependencies**: watchdog (filesystem monitoring), pyyaml (Markdown frontmatter), subprocess (Claude Code CLI integration), pathlib (path operations)
**Storage**: Markdown files only (no database) - all state persisted in vault structure
**Testing**: pytest (unit tests), pytest-asyncio (async tests), pytest-timeout (test timeouts)
**Target Platform**: Cross-platform (Windows, macOS, Linux) - Python standard library only
**Project Type**: Single project (CLI tool with daemon mode)
**Performance Goals**: 2-second file detection, 30-second task processing, 100 tasks/day capacity
**Constraints**: <500MB memory usage, local-first (no external APIs), vault-only file operations, graceful error handling
**Scale/Scope**: Single user, single vault, ~100 tasks/day, 24-hour continuous operation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance

✅ **I. Local-First Architecture**: System operates entirely locally with no external API dependencies. Claude Code CLI runs locally. All data stored in vault.

✅ **II. Human-in-the-Loop for Risk Actions**: Bronze phase has no risk actions (email sends, external tools). All operations are safe file moves within vault.

✅ **III. Markdown as System Memory**: All state stored as Markdown files (tasks, logs, dashboard). No hidden databases or binary state.

✅ **IV. Modular Watcher Architecture**: Base watcher abstract class defined with start(), stop(), get_new_tasks(), mark_processed(). FileSystem watcher is concrete implementation.

✅ **V. Clear Perception → Reasoning → Action Loop**: Explicit three-stage pipeline: FileSystem watcher (perception) → Claude Code (reasoning) → Action executor (action).

✅ **VI. No Hidden State**: All behavior traceable through Markdown files. Dashboard shows current state. Logs show all actions.

✅ **VII. Phased Development**: Bronze phase is independently functional and deployable. No dependencies on Silver/Gold/Platinum features.

✅ **VIII. Safety-First Constraints**: All file operations validated to stay within vault. No destructive operations. All actions logged before execution.

### Vault Structure Compliance

✅ Required structure implemented:
- AI_Employee_Vault/Inbox/ (new tasks)
- AI_Employee_Vault/Needs_Action/ (processing)
- AI_Employee_Vault/Done/ (completed)
- AI_Employee_Vault/Dashboard.md (system status)
- AI_Employee_Vault/Logs/ (audit trail)
- AI_Employee_Vault/Company_Handbook/ (knowledge base)

### Watcher Interface Compliance

✅ Base watcher interface implements required methods:
- start() - Begin monitoring
- stop() - Graceful shutdown
- get_new_tasks() - Return task list
- mark_processed(task_id) - Acknowledge handling

### Performance Standards Compliance

✅ **File detection**: 2-second target (constitution requires 2 seconds)
✅ **Task processing**: 30-second target (constitution requires 30 seconds)
✅ **Dashboard updates**: Atomic writes (constitution requires atomic)
✅ **Daily capacity**: 100 tasks/day (constitution requires 100 tasks/day)
✅ **Memory usage**: <500MB target (constitution requires <500MB)

### Gate Result: ✅ PASSED

All constitution principles satisfied. No violations to justify. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-foundation/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── task-schema.yaml # Task file format specification
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
src/
├── watchers/
│   ├── base_watcher.py          # Abstract watcher interface
│   └── filesystem_watcher.py    # Concrete FileSystem implementation
├── orchestrator.py               # Main coordination logic
├── task_processor.py             # Markdown parsing and task extraction
├── action_executor.py            # Safe file operations within vault
├── dashboard_manager.py          # Dashboard.md updates
├── logger.py                     # Append-only audit logging
├── vault_manager.py              # Vault structure initialization
└── main.py                       # CLI entry point

tests/
├── unit/
│   ├── test_base_watcher.py
│   ├── test_filesystem_watcher.py
│   ├── test_task_processor.py
│   ├── test_action_executor.py
│   ├── test_dashboard_manager.py
│   └── test_logger.py
├── integration/
│   ├── test_workflow.py          # End-to-end Inbox→Done flow
│   └── test_concurrent_tasks.py  # Multiple simultaneous tasks
└── fixtures/
    └── sample_tasks/             # Test task files

AI_Employee_Vault/               # Created by vault_manager.py
├── Inbox/
├── Needs_Action/
├── Done/
├── Dashboard.md
├── Logs/
└── Company_Handbook/
```

**Structure Decision**: Single project structure selected. This is a CLI tool with daemon mode, not a web application or mobile app. All components are Python modules in src/ with corresponding tests in tests/. The vault structure is created and managed by the system but lives outside the source tree.

## Complexity Tracking

> No constitution violations - this section is empty.

---

## Phase 0: Research & Technology Decisions

See [research.md](./research.md) for detailed research findings.

### Key Decisions

1. **File Watching Library**: watchdog (cross-platform, mature, event-driven)
2. **Markdown Parsing**: python-frontmatter + markdown library (YAML frontmatter + content)
3. **Claude Code Integration**: subprocess with JSON I/O (CLI invocation)
4. **Async vs Sync**: Sync with threading (simpler, sufficient for Bronze phase)
5. **Configuration**: Environment variables + .env file (vault path, polling interval)

---

## Phase 1: Design Artifacts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions.

**Key Entities**:
- Task (task_id, title, description, priority, status, timestamps, file_path)
- Watcher (watcher_type, status, last_check_timestamp)
- Action (action_id, action_type, timestamp, task_reference, result)
- Dashboard Metrics (counts, processing stats, system status)

### Contracts

See [contracts/](./contracts/) for schema definitions.

**Task File Format** (contracts/task-schema.yaml):
- YAML frontmatter with task metadata
- Markdown body with task description
- Validation rules for required fields

### Quickstart

See [quickstart.md](./quickstart.md) for setup and usage instructions.

**Quick Start Steps**:
1. Install Python 3.9+
2. Install Claude Code CLI
3. Clone repository and install dependencies
4. Configure vault path in .env
5. Run `python src/main.py start`
6. Drop task file in Inbox
7. Monitor Dashboard.md

---

## Implementation Notes

### Critical Path

1. Vault structure initialization (vault_manager.py)
2. Base watcher interface (base_watcher.py)
3. FileSystem watcher (filesystem_watcher.py)
4. Task processor (task_processor.py)
5. Orchestrator coordination (orchestrator.py)
6. Action executor (action_executor.py)
7. Dashboard manager (dashboard_manager.py)
8. Logger (logger.py)
9. CLI entry point (main.py)

### Risk Mitigation

- **File conflicts**: Use atomic file operations (write to temp, then move)
- **Concurrent tasks**: Process tasks sequentially in Bronze phase (parallel in Gold)
- **Claude Code failures**: Retry logic with exponential backoff
- **Disk space**: Check available space before file operations
- **Vault path validation**: Verify path exists and is writable on startup

### Testing Strategy

- **Unit tests**: Each module tested independently with mocks
- **Integration tests**: End-to-end workflow with real vault structure
- **Contract tests**: Task file format validation
- **Performance tests**: 100 tasks/day load test, memory profiling

### Next Steps

1. Run `/sp.tasks` to generate actionable task list
2. Implement tasks in priority order (Setup → Foundational → User Stories)
3. Run tests after each task completion
4. Validate against success criteria from spec.md

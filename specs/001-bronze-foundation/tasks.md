---

description: "Task list for Bronze Phase - Local Foundation implementation"
---

# Tasks: Bronze Phase - Local Foundation

**Input**: Design documents from `/specs/001-bronze-foundation/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Tests**: Tests are NOT included in this task list as they were not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below use single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure (src/, src/watchers/, tests/unit/, tests/integration/, tests/fixtures/)
- [ ] T002 Create requirements.txt with dependencies (watchdog>=3.0, python-frontmatter>=1.0, markdown>=3.4, python-dotenv>=1.0, pytest>=7.4, pytest-asyncio>=0.21, pytest-timeout>=2.1)
- [ ] T003 [P] Create .env.example with configuration template (VAULT_PATH, POLLING_INTERVAL, FILE_EXTENSIONS, CLAUDE_CODE_PATH, LOG_LEVEL, LOG_TO_FILE, MAX_CONCURRENT_TASKS, TASK_TIMEOUT)
- [ ] T004 [P] Create .gitignore file (venv/, __pycache__/, *.pyc, .env, .pytest_cache/, logs/, AI_Employee_Vault/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create vault_manager.py in src/ with VaultManager class that initializes vault structure (Inbox/, Needs_Action/, Done/, Logs/, Company_Handbook/, Dashboard.md)
- [ ] T006 [P] Create base_watcher.py in src/watchers/ with BaseWatcher abstract class defining interface (start, stop, get_new_tasks, mark_processed methods)
- [ ] T007 [P] Create task_processor.py in src/ with TaskProcessor class for parsing Markdown files with YAML frontmatter (task_id, title, description, priority, status, created_at validation)
- [ ] T008 [P] Create action_executor.py in src/ with ActionExecutor class for safe file operations (move_file, validate_vault_path, atomic_write methods)
- [ ] T009 Add path validation to action_executor.py ensuring all file operations stay within vault boundary using pathlib.resolve()

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automatic Task Detection and Processing (Priority: P1) 🎯 MVP

**Goal**: Drop task file in Inbox → automatically detect → process via Claude Code → move through workflow stages (Inbox → Needs_Action → Done)

**Independent Test**: Create task file in Inbox, observe it move to Needs_Action, then to Done, verify Dashboard updates with task status

### Implementation for User Story 1

- [ ] T010 [P] [US1] Create filesystem_watcher.py in src/watchers/ implementing BaseWatcher with watchdog library for monitoring Inbox folder
- [ ] T011 [P] [US1] Add event handlers to filesystem_watcher.py for on_created events detecting .md files within 2 seconds
- [ ] T012 [US1] Create orchestrator.py in src/ with Orchestrator class coordinating watcher → task processor → Claude Code → action executor pipeline
- [ ] T013 [US1] Add Claude Code integration to orchestrator.py using subprocess with JSON I/O (stdin for task data, stdout for response)
- [ ] T014 [US1] Implement task workflow in orchestrator.py (detect file → move to Needs_Action → process → move to Done)
- [ ] T015 [US1] Add error handling to orchestrator.py with try-catch blocks, logging, and exponential backoff retry for Claude Code failures
- [ ] T016 [US1] Add graceful shutdown support to orchestrator.py (stop watcher, complete current task, save state)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Tasks can be dropped in Inbox and automatically processed to Done.

---

## Phase 4: User Story 2 - Real-Time Dashboard Visibility (Priority: P2)

**Goal**: View Dashboard.md showing system status, task counts, recent activity, and processing metrics in real-time

**Independent Test**: Drop tasks in Inbox and observe Dashboard.md update automatically with task counts, status changes, and recent activity log

### Implementation for User Story 2

- [ ] T017 [P] [US2] Create dashboard_manager.py in src/ with DashboardManager class for generating Dashboard.md content
- [ ] T018 [US2] Add metrics calculation to dashboard_manager.py (inbox_count, needs_action_count, done_count, total_processed, average_processing_time, success_rate)
- [ ] T019 [US2] Implement atomic dashboard updates in dashboard_manager.py using temp file + os.replace() pattern
- [ ] T020 [US2] Add dashboard update calls to orchestrator.py after every task state change (file detected, moved to Needs_Action, moved to Done)
- [ ] T021 [US2] Add recent activity tracking to dashboard_manager.py (last 10 tasks with timestamps and status)
- [ ] T022 [US2] Add system health metrics to dashboard_manager.py (memory usage, disk space, watcher status, uptime, error count)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Dashboard provides real-time visibility into task processing.

---

## Phase 5: User Story 3 - Comprehensive Audit Trail (Priority: P3)

**Goal**: Every action logged with timestamps, task references, and outcomes in Logs/YYYY-MM-DD.md files

**Independent Test**: Process tasks and verify Logs/YYYY-MM-DD.md contains timestamped entries for each action (file detected, task processed, file moved, dashboard updated)

### Implementation for User Story 3

- [ ] T023 [P] [US3] Create logger.py in src/ with Logger class for append-only Markdown log entries
- [ ] T024 [US3] Add action type definitions to logger.py (FILE_DETECTED, FILE_MOVED, TASK_PARSED, TASK_PROCESSED, DASHBOARD_UPDATED, LOG_WRITTEN, ERROR, SYSTEM_STARTED, SYSTEM_STOPPED)
- [ ] T025 [US3] Implement log entry formatting in logger.py with ISO 8601 timestamps, action_id (UUID), task_reference, result, details, duration_ms
- [ ] T026 [US3] Add logging calls to orchestrator.py for all major actions (file detection, task processing, file moves, errors)
- [ ] T027 [US3] Add logging calls to action_executor.py for all file operations
- [ ] T028 [US3] Add logging calls to dashboard_manager.py for dashboard updates

**Checkpoint**: All user stories should now be independently functional. Complete audit trail available for debugging and compliance.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Create main.py in src/ with CLI entry point supporting commands (start, stop, status, check-config, update-dashboard, diagnose)
- [ ] T030 [P] Add command-line argument parsing to main.py using argparse (--daemon flag for background mode)
- [ ] T031 [P] Add configuration loading to main.py using python-dotenv to read .env file
- [ ] T032 Add startup validation to main.py (check vault path exists, Claude Code accessible, all folders present)
- [ ] T033 [P] Create README.md in repository root with project overview, installation instructions, and quickstart guide
- [ ] T034 Add signal handlers to main.py for graceful shutdown on SIGINT/SIGTERM
- [ ] T035 [P] Add memory profiling and performance monitoring to orchestrator.py
- [ ] T036 Create sample task files in tests/fixtures/sample_tasks/ for testing (minimal-task.md, complete-task.md, malformed-task.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 orchestrator but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1 orchestrator and US2 dashboard but independently testable

### Within Each User Story

- Foundational modules (vault_manager, base_watcher, task_processor, action_executor) before any user story
- FileSystem watcher (US1) before orchestrator (US1)
- Orchestrator (US1) before dashboard integration (US2) and logging integration (US3)
- All core functionality before CLI entry point (Polish)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Tasks within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch foundational modules together (after Setup):
Task: "Create base_watcher.py in src/watchers/"
Task: "Create task_processor.py in src/"
Task: "Create action_executor.py in src/"

# Launch US1 parallel tasks together:
Task: "Create filesystem_watcher.py in src/watchers/"
Task: "Add event handlers to filesystem_watcher.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Drop task file in Inbox
   - Verify automatic detection within 2 seconds
   - Verify processing through Claude Code
   - Verify file moves to Done
   - Verify no crashes or errors
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Dashboard visibility added)
4. Add User Story 3 → Test independently → Deploy/Demo (Audit trail added)
5. Add Polish → Final production-ready system
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T010-T016)
   - Developer B: User Story 2 (T017-T022)
   - Developer C: User Story 3 (T023-T028)
3. Stories complete and integrate independently
4. Team completes Polish together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are NOT included as they were not explicitly requested in the specification

---

## Task Count Summary

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 5 tasks (BLOCKING)
- **Phase 3 (User Story 1 - P1)**: 7 tasks
- **Phase 4 (User Story 2 - P2)**: 6 tasks
- **Phase 5 (User Story 3 - P3)**: 6 tasks
- **Phase 6 (Polish)**: 8 tasks

**Total**: 36 tasks

**Parallel Opportunities**: 15 tasks marked [P] can run in parallel within their phase

**MVP Scope**: Phases 1-3 (16 tasks) deliver core autonomous task processing

**Independent Test Criteria**:
- US1: Drop task in Inbox → automatically processed → moved to Done
- US2: Dashboard.md updates in real-time with task counts and metrics
- US3: Logs/YYYY-MM-DD.md contains all actions with timestamps

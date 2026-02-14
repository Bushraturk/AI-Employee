# Feature Specification: Bronze Phase - Local Foundation

**Feature Branch**: `001-bronze-foundation`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "Bronze Phase - Local Foundation: Build foundational local-first autonomous AI employee system with FileSystem watcher, Obsidian vault workflow, Claude Code integration, and comprehensive logging"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Task Detection and Processing (Priority: P1)

As a user, I want to drop a Markdown task file into the Inbox folder and have the system automatically detect it, process it through Claude Code, and move it through the workflow stages (Inbox → Needs_Action → Done) without any manual intervention.

**Why this priority**: This is the core value proposition of the autonomous AI employee - automatic task detection and processing. Without this, there is no autonomous system.

**Independent Test**: Can be fully tested by creating a task file in Inbox, observing it move to Needs_Action, then to Done, and verifying the Dashboard updates with the task status.

**Acceptance Scenarios**:

1. **Given** the system is running and Inbox folder is empty, **When** I create a new task file `task-001.md` in Inbox, **Then** the system detects the file within 2 seconds and moves it to Needs_Action folder
2. **Given** a task file is in Needs_Action folder, **When** Claude Code processes the task successfully, **Then** the task file moves to Done folder with processing timestamp
3. **Given** multiple task files are dropped in Inbox simultaneously, **When** the system processes them, **Then** each task is processed independently without conflicts or data loss

---

### User Story 2 - Real-Time Dashboard Visibility (Priority: P2)

As a user, I want to view a Dashboard.md file that shows me the current system status, task counts, recent activity, and processing metrics in real-time so I can monitor the AI employee's work without checking individual folders.

**Why this priority**: Visibility into system operations is critical for trust and debugging. Users need to see what the AI employee is doing.

**Independent Test**: Can be tested by dropping tasks in Inbox and observing Dashboard.md update automatically with task counts, status changes, and recent activity log.

**Acceptance Scenarios**:

1. **Given** the system is idle, **When** I open Dashboard.md, **Then** I see current task counts (Inbox: 0, Needs_Action: 0, Done: 0) and system status (Running/Idle)
2. **Given** a task is being processed, **When** I refresh Dashboard.md, **Then** I see the task count updated and the task listed in "Recent Activity" section
3. **Given** tasks have been completed, **When** I view Dashboard.md, **Then** I see processing metrics including total tasks processed, average processing time, and success rate

---

### User Story 3 - Comprehensive Audit Trail (Priority: P3)

As a user, I want every action the system takes to be logged with timestamps, task references, and outcomes so I can audit what happened, troubleshoot issues, and maintain accountability.

**Why this priority**: Audit logs are essential for production systems but not required for initial MVP validation. They become critical when debugging issues or ensuring compliance.

**Independent Test**: Can be tested by processing tasks and verifying that Logs/YYYY-MM-DD.md files contain timestamped entries for each action (file detected, task processed, file moved, dashboard updated).

**Acceptance Scenarios**:

1. **Given** a task file is dropped in Inbox, **When** the system processes it, **Then** a log entry is created with ISO 8601 timestamp, action type "FILE_DETECTED", and task file path
2. **Given** Claude Code processes a task, **When** processing completes, **Then** a log entry is created with action type "TASK_PROCESSED", task ID, and processing result
3. **Given** an error occurs during processing, **When** the error is caught, **Then** a log entry is created with action type "ERROR", error details, and task context

---

### Edge Cases

- What happens when a task file is malformed or empty?
- What happens when the Needs_Action or Done folders are manually deleted?
- What happens when two task files have the same name?
- What happens when the system crashes mid-processing?
- What happens when disk space runs out?
- What happens when a task file is modified while being processed?
- What happens when the vault directory is moved or renamed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST monitor the Inbox folder continuously for new Markdown (.md) files
- **FR-002**: System MUST detect new files in Inbox within 2 seconds of creation
- **FR-003**: System MUST move detected files from Inbox to Needs_Action folder automatically
- **FR-004**: System MUST parse Markdown task files into structured data (task ID, title, description, priority)
- **FR-005**: System MUST send parsed task data to Claude Code for reasoning and action planning
- **FR-006**: System MUST receive structured output from Claude Code (task classification, priority, proposed actions)
- **FR-007**: System MUST execute safe actions within the vault (file moves, dashboard updates, log writes)
- **FR-008**: System MUST move processed tasks from Needs_Action to Done folder
- **FR-009**: System MUST update Dashboard.md after every task state change
- **FR-010**: System MUST write log entries to Logs/YYYY-MM-DD.md for every action
- **FR-011**: System MUST create vault folder structure (Inbox, Needs_Action, Done, Logs, Company_Handbook) on first run if missing
- **FR-012**: System MUST validate that all file operations stay within the vault directory boundary
- **FR-013**: System MUST handle file operation errors gracefully without crashing
- **FR-014**: System MUST support graceful shutdown (stop watching, complete current task, save state)
- **FR-015**: System MUST persist no state outside of Markdown files in the vault
- **FR-016**: System MUST run continuously without requiring external APIs or internet connectivity
- **FR-017**: System MUST provide a base watcher interface that future watchers (Gmail, WhatsApp) can inherit from
- **FR-018**: System MUST implement FileSystem watcher as a concrete implementation of base watcher interface

### Key Entities

- **Task**: Represents a work item to be processed. Attributes: task_id (unique identifier), title (brief description), description (full details), priority (P1/P2/P3), status (inbox/needs_action/done), created_timestamp, processed_timestamp, file_path
- **Watcher**: Abstract interface for input monitoring. Attributes: watcher_type (filesystem/gmail/whatsapp), status (running/stopped), last_check_timestamp. Methods: start(), stop(), get_new_tasks(), mark_processed()
- **Action**: Represents an operation performed by the system. Attributes: action_id, action_type (file_detected/task_processed/file_moved/dashboard_updated/error), timestamp, task_reference, result, error_details
- **Dashboard Metrics**: System status information. Attributes: inbox_count, needs_action_count, done_count, total_processed, average_processing_time, success_rate, system_status (running/idle/error), last_updated

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can drop a task file in Inbox and see it automatically processed and moved to Done within 30 seconds for simple tasks
- **SC-002**: System detects new files in Inbox within 2 seconds of creation
- **SC-003**: Dashboard.md updates within 1 second of any task state change
- **SC-004**: System processes 100 tasks per day without performance degradation
- **SC-005**: System memory usage stays under 500MB during normal operation
- **SC-006**: System runs continuously for 24 hours without crashes or manual intervention
- **SC-007**: All actions are logged with timestamps accurate to the second
- **SC-008**: 100% of file operations stay within vault directory boundaries (no files created/modified outside vault)
- **SC-009**: System recovers gracefully from 95% of common errors (missing folders, malformed files, permission issues)
- **SC-010**: Users can understand system status by reading Dashboard.md without technical knowledge

### Assumptions

- Users have Python 3.9+ installed on their system
- Users have Claude Code CLI installed and configured
- Users have read/write permissions to the vault directory
- The vault directory is on a local filesystem (not network drive)
- Task files are UTF-8 encoded Markdown
- System runs on Windows, macOS, or Linux
- Users will manually start the system (no auto-start on boot required for Bronze phase)

### Out of Scope

- Email integration (Gmail watcher) - deferred to Silver phase
- WhatsApp integration - deferred to Silver phase
- External tool execution via MCP - deferred to Gold phase
- Self-improvement loop - deferred to Platinum phase
- Multi-agent coordination - deferred to Platinum phase
- Web UI or GUI - command-line only for Bronze phase
- Task scheduling or recurring tasks
- Task dependencies or workflows
- User authentication or multi-user support
- Cloud sync or backup
- Task templates or automation rules

### Dependencies

- Python 3.9+ runtime environment
- Claude Code CLI (must be installed and accessible via PATH)
- Local filesystem with read/write permissions
- Obsidian (optional - vault is compatible but system doesn't require Obsidian to be running)

### Constraints

- All operations must be local-first (no external APIs)
- All state must be stored as Markdown files
- No hidden databases or binary state files
- File operations restricted to vault directory only
- Must be production-ready and stable for Silver phase to build upon
- Must follow all principles defined in project constitution

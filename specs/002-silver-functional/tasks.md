# Tasks: Silver Tier - Functional Assistant

**Input**: Design documents from `/specs/002-silver-functional/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are excluded. Focus on implementation tasks only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- All paths relative to repository root: `C:\Users\admin\Desktop\b-ai-employee\`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency installation

- [ ] T001 Update requirements.txt with Silver Tier dependencies (google-auth-oauthlib, google-api-python-client, requests-oauthlib, oauthlib, playwright, keyring, cryptography, APScheduler, pytz)
- [ ] T002 Install Python dependencies via pip install -r requirements.txt
- [ ] T003 [P] Install Playwright browsers via playwright install chromium
- [ ] T004 [P] Create vault/Needs_Approval/ folder for approval queue
- [ ] T005 [P] Create vault/Plans/ folder for Plan.md files
- [ ] T006 [P] Create vault/LinkedIn_Posts/ folder for post history
- [ ] T007 [P] Create credentials/ folder (outside vault) for OAuth2 credentials
- [ ] T008 [P] Update .gitignore to exclude credentials/, whatsapp_session/, and token storage files
- [ ] T009 Create .env.example with Silver Tier configuration variables (watcher settings, approval timeout, scheduler timezone)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 Create src/watchers/auth/ directory for authentication modules
- [ ] T011 [P] Implement TokenStorage class in src/watchers/auth/token_storage.py (OS keyring with encrypted file fallback)
- [ ] T012 [P] Create src/mcp/ directory for MCP server modules
- [ ] T013 [P] Create src/approval/ directory for approval workflow modules
- [ ] T014 [P] Create src/scheduling/ directory for scheduler modules
- [ ] T015 [P] Create src/planning/ directory for Plan.md generation
- [ ] T016 Implement MCPServer base class in src/mcp/server.py (tool registry, validation, approval check, audit logging)
- [ ] T017 Implement ApprovalQueue class in src/approval/queue.py (create, list, get, update approval requests)
- [ ] T018 [P] Implement RiskClassifier in src/approval/risk_classifier.py (classify actions as low/medium/high risk)
- [ ] T019 [P] Create src/mcp/tools/ directory for MCP tool implementations
- [ ] T020 Update src/orchestrator.py to support multi-watcher coordination (add watcher registry, concurrent execution)
- [ ] T021 [P] Create 8 new agent skill files in .specify/commands/ directory (classify-email, classify-whatsapp, classify-linkedin, generate-linkedin-post, create-plan, draft-email-reply, draft-whatsapp-reply, validate-action)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Multi-Channel Task Detection (Priority: P1) 🎯 MVP

**Goal**: Automatically detect and process tasks from Gmail, WhatsApp, and LinkedIn within 30 seconds

**Independent Test**: Send test messages through Gmail, WhatsApp, and LinkedIn, verify task files created in vault/Inbox/ with proper channel metadata

### Gmail Watcher Implementation

- [ ] T022 [P] [US1] Implement GmailAuth class in src/watchers/auth/gmail_auth.py (OAuth2 flow, token refresh, authentication verification)
- [ ] T023 [P] [US1] Create agent skill classify-email.command.md in .specify/commands/ (email classification logic, priority extraction, metadata parsing)
- [ ] T024 [US1] Implement GmailWatcher class in src/watchers/gmail_watcher.py (inherit from BaseWatcher, implement start/stop/get_new_tasks/mark_processed)
- [ ] T025 [US1] Implement Gmail API integration in GmailWatcher (list messages, get message details, incremental sync with historyId)
- [ ] T026 [US1] Implement email-to-task conversion in GmailWatcher (parse headers, extract body, create task file with gmail channel metadata)
- [ ] T027 [US1] Add Gmail watcher error handling and rate limit management (exponential backoff, retry logic)

### WhatsApp Watcher Implementation

- [ ] T028 [P] [US1] Create agent skill classify-whatsapp.command.md in .specify/commands/ (message classification, task extraction from conversational text)
- [ ] T029 [US1] Implement WhatsAppWatcher class in src/watchers/whatsapp_watcher.py (inherit from BaseWatcher, Playwright integration)
- [ ] T030 [US1] Implement WhatsApp web automation in WhatsAppWatcher (QR code authentication, session persistence, message monitoring)
- [ ] T031 [US1] Implement message detection and extraction in WhatsAppWatcher (DOM observation, sender extraction, message text parsing)
- [ ] T032 [US1] Implement whatsapp-to-task conversion in WhatsAppWatcher (create task file with whatsapp channel metadata)
- [ ] T033 [US1] Add WhatsApp watcher error handling (session expiration, connection loss, automation detection)

### LinkedIn Watcher Implementation

- [ ] T034 [P] [US1] Implement LinkedInAuth class in src/watchers/auth/linkedin_auth.py (OAuth2 flow, token refresh, authentication verification)
- [ ] T035 [P] [US1] Create agent skill classify-linkedin.command.md in .specify/commands/ (content classification, opportunity detection)
- [ ] T036 [US1] Implement LinkedInWatcher class in src/watchers/linkedin_watcher.py (inherit from BaseWatcher, LinkedIn API integration)
- [ ] T037 [US1] Implement LinkedIn API integration in LinkedInWatcher (monitor messages, mentions, posts)
- [ ] T038 [US1] Implement linkedin-to-task conversion in LinkedInWatcher (create task file with linkedin channel metadata)
- [ ] T039 [US1] Add LinkedIn watcher error handling and rate limit management

### Multi-Watcher Orchestration

- [ ] T040 [US1] Update src/orchestrator.py to register and start all watchers concurrently (FileSystem, Gmail, WhatsApp, LinkedIn)
- [ ] T041 [US1] Implement watcher health monitoring in orchestrator (track status, error counts, last check times)
- [ ] T042 [US1] Update vault/Dashboard.md to display multi-channel metrics (tasks per channel, watcher status)
- [ ] T043 [US1] Create vault/Company_Handbook/watcher-config.md with configuration for all watchers (poll intervals, filters, enabled status)

**Checkpoint**: At this point, User Story 1 should be fully functional - all three watchers detect content within 30 seconds and create tasks with proper channel metadata

---

## Phase 4: User Story 2 - Human Approval Workflow (Priority: P2)

**Goal**: Review and approve sensitive actions (emails, posts, messages) before execution with <5 minute review time

**Independent Test**: Trigger action requiring approval, verify it appears in approval queue, test approve/reject/edit workflows

### Approval Queue Implementation

- [ ] T044 [P] [US2] Create agent skill validate-action.command.md in .specify/commands/ (pre-execution validation, risk assessment)
- [ ] T045 [US2] Implement approval request creation in src/approval/queue.py (generate approval_id, write to vault/Needs_Approval/, set 24-hour timeout)
- [ ] T046 [US2] Implement approval status checking in src/approval/queue.py (verify approved, check timeout, validate reviewer)
- [ ] T047 [US2] Implement approval timeout handling in src/approval/queue.py (auto-reject after 24 hours, log decision)

### Approval CLI Implementation

- [ ] T048 [US2] Implement ApprovalCLI class in src/approval/cli.py (command-line interface for approval management)
- [ ] T049 [US2] Implement 'list' command in ApprovalCLI (display all pending approvals with summary)
- [ ] T050 [US2] Implement 'view' command in ApprovalCLI (show detailed approval information: what, why, impact, risk level)
- [ ] T051 [US2] Implement 'approve' command in ApprovalCLI (mark approval as approved, record reviewer and timestamp)
- [ ] T052 [US2] Implement 'reject' command in ApprovalCLI (mark approval as rejected, record reason and reviewer)
- [ ] T053 [US2] Implement 'edit' command in ApprovalCLI (modify action details before approval)
- [ ] T054 [US2] Implement bulk approval support in ApprovalCLI (approve multiple similar actions)

### MCP Server Integration with Approval

- [ ] T055 [US2] Update src/mcp/server.py to check approval before tool execution (verify approval_id, validate status)
- [ ] T056 [US2] Implement approval request creation in MCP server for medium/high risk actions
- [ ] T057 [US2] Add approval metadata logging in src/mcp/server.py (reviewer, timestamp, decision, notes)
- [ ] T058 [US2] Create vault/Logs/mcp-executions-YYYY-MM-DD.md template for audit trail

**Checkpoint**: At this point, User Story 2 should be fully functional - all sensitive actions require approval, CLI interface works, audit trail is complete

---

## Phase 5: User Story 3 - LinkedIn Auto-Posting (Priority: P3)

**Goal**: Automatically generate and post LinkedIn content 2-3 times per week for business development

**Independent Test**: Configure business context, trigger post generation, review draft in approval queue, verify successful posting to LinkedIn

### LinkedIn Post Generation

- [ ] T059 [P] [US3] Create agent skill generate-linkedin-post.command.md in .specify/commands/ (analyze business context, generate engaging content, add hashtags and mentions)
- [ ] T060 [US3] Implement PlanGenerator class in src/planning/plan_generator.py (base class for content generation)
- [ ] T061 [US3] Implement generate_linkedin_post function in src/planning/plan_generator.py (read Company_Handbook, generate post content, format with hashtags)
- [ ] T062 [US3] Create vault/Company_Handbook/business-context.md template (company overview, products, key messages, tone, hashtags)

### LinkedIn MCP Tool Implementation

- [ ] T063 [US3] Implement LinkedInTool class in src/mcp/tools/linkedin_tool.py (create UGC post, get analytics, handle errors)
- [ ] T064 [US3] Register linkedin_tool in src/mcp/server.py (risk_level: medium, requires_approval: true)
- [ ] T065 [US3] Implement LinkedIn post creation in LinkedInTool (format request body, call API, handle response)
- [ ] T066 [US3] Implement LinkedIn analytics retrieval in LinkedInTool (get likes, comments, shares, views)

### LinkedIn Post Storage and Tracking

- [ ] T067 [US3] Implement LinkedInPost entity storage in vault/LinkedIn_Posts/ (create post file with content, metadata, performance metrics)
- [ ] T068 [US3] Implement post history tracking (store post_id, external_id, posted_at, approval_id)
- [ ] T069 [US3] Implement performance metrics update (daily refresh of views, likes, comments, shares)

### LinkedIn Posting Schedule

- [ ] T070 [US3] Create optimal posting schedule configuration (Monday/Wednesday/Friday at 10 AM business hours)
- [ ] T071 [US3] Integrate LinkedIn post generation with scheduler (trigger generate_linkedin_post on schedule)

**Checkpoint**: At this point, User Story 3 should be fully functional - LinkedIn posts generated 2-3 times per week, require approval, post successfully, track performance

---

## Phase 6: User Story 4 - Intelligent Planning (Priority: P4)

**Goal**: Automatically create structured Plan.md files for complex multi-step tasks (>3 steps)

**Independent Test**: Create complex task (>3 steps), verify Plan.md file generated with problem analysis, approach options, execution steps

### Plan.md Generation

- [ ] T072 [P] [US4] Create agent skill create-plan.command.md in .specify/commands/ (analyze task complexity, generate problem analysis, propose approach options, create execution plan)
- [ ] T073 [US4] Implement detect_complex_task function in src/planning/plan_generator.py (identify tasks requiring >3 steps)
- [ ] T074 [US4] Implement generate_plan function in src/planning/plan_generator.py (create Plan.md with problem analysis, approach options, recommended solution, execution steps, success criteria, risk mitigation)
- [ ] T075 [US4] Implement plan file creation in vault/Plans/{task_id}-plan.md (write structured markdown with frontmatter)
- [ ] T076 [US4] Implement plan-to-task linking (store plan_id in task file, reference task_id in plan)

### Plan Revision and Version Control

- [ ] T077 [US4] Implement plan revision support (increment version number, maintain version history)
- [ ] T078 [US4] Implement plan update based on feedback (read existing plan, apply changes, save new version)

### Plan Integration with Task Processing

- [ ] T079 [US4] Update src/task_processor.py to detect complex tasks and trigger plan generation
- [ ] T080 [US4] Update vault/Dashboard.md to display plan generation metrics (plans created, tasks with plans)

**Checkpoint**: At this point, User Story 4 should be fully functional - complex tasks automatically generate Plan.md files with structured thinking

---

## Phase 7: User Story 5 - Scheduled Task Automation (Priority: P5)

**Goal**: Schedule recurring tasks and automated actions so routine work happens automatically

**Independent Test**: Create scheduled task (e.g., daily report), verify it executes at scheduled time, check execution logs

### Scheduler Implementation

- [ ] T081 [US5] Implement Scheduler class in src/scheduling/scheduler.py (APScheduler integration, job store configuration)
- [ ] T082 [US5] Implement CronParser in src/scheduling/cron_parser.py (parse cron syntax, validate expressions, calculate next run time)
- [ ] T083 [US5] Implement schedule creation in Scheduler (add job with cron trigger, store in SQLite job store)
- [ ] T084 [US5] Implement schedule management (list, update, delete, pause, resume schedules)
- [ ] T085 [US5] Implement schedule execution logging (record execution time, result, errors)

### Schedule Storage and Configuration

- [ ] T086 [US5] Create vault/Company_Handbook/schedules.md template (schedule definitions in human-readable format)
- [ ] T087 [US5] Implement schedule persistence (SQLite database for APScheduler, sync with schedules.md)
- [ ] T088 [US5] Implement schedule loading on startup (read schedules.md, register jobs with APScheduler)

### Schedule CLI Commands

- [ ] T089 [US5] Implement schedule CLI commands in src/scheduling/scheduler.py (--list, --create, --update, --delete, --run)
- [ ] T090 [US5] Implement manual schedule execution for testing (--run <schedule_id>)

### Failure Handling and Retry Logic

- [ ] T091 [US5] Implement retry policy in Scheduler (max_retries, retry_delay, exponential_backoff)
- [ ] T092 [US5] Implement failure logging and notification (log to vault/Logs/, track failure count)
- [ ] T093 [US5] Implement schedule auto-disable after max failures (prevent infinite retry loops)

### Scheduler Integration with Orchestrator

- [ ] T094 [US5] Update src/orchestrator.py to start scheduler on system startup
- [ ] T095 [US5] Update .env configuration with scheduler settings (timezone, enable/disable)
- [ ] T096 [US5] Update vault/Dashboard.md to display scheduler metrics (active schedules, next run times, execution history)

**Checkpoint**: At this point, User Story 5 should be fully functional - scheduled tasks execute reliably at specified times with 99%+ success rate

---

## Phase 8: Additional MCP Tools (Supporting Multiple User Stories)

**Purpose**: Implement remaining MCP tools for external actions

### Gmail MCP Tool

- [ ] T097 [P] Create agent skill draft-email-reply.command.md in .specify/commands/ (generate context-aware email responses)
- [ ] T098 [P] Implement GmailTool class in src/mcp/tools/gmail_tool.py (send email, create draft, delete draft)
- [ ] T099 Register gmail_tool in src/mcp/server.py (risk_level: medium, requires_approval: true)
- [ ] T100 Implement email sending in GmailTool (format RFC 822 message, base64 encode, call Gmail API)
- [ ] T101 Implement email draft creation for rollback capability

### WhatsApp MCP Tool

- [ ] T102 [P] Create agent skill draft-whatsapp-reply.command.md in .specify/commands/ (generate WhatsApp message responses)
- [ ] T103 [P] Implement WhatsAppTool class in src/mcp/tools/whatsapp_tool.py (send message via Playwright automation)
- [ ] T104 Register whatsapp_tool in src/mcp/server.py (risk_level: medium, requires_approval: true)
- [ ] T105 Implement message sending in WhatsAppTool (navigate to chat, type message, click send, verify delivery)
- [ ] T106 Implement rate limiting in WhatsAppTool (max 5 messages per minute to avoid spam detection)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Documentation and Configuration

- [ ] T107 [P] Create comprehensive setup guide in specs/002-silver-functional/quickstart.md (already exists, verify completeness)
- [ ] T108 [P] Update README.md with Silver Tier features and setup instructions
- [ ] T109 [P] Create troubleshooting guide for common issues (authentication, session expiration, rate limits)

### Error Handling and Logging

- [ ] T110 [P] Implement comprehensive error logging across all watchers (log to vault/Logs/watcher-errors-YYYY-MM-DD.md)
- [ ] T111 [P] Implement MCP execution logging with privacy considerations (omit sensitive content, log metadata only)
- [ ] T112 Implement watcher health checks and auto-restart on failure

### Security and Privacy

- [ ] T113 [P] Implement token rotation reminders (notify user after 60 days)
- [ ] T114 [P] Implement content sanitization before logging (remove PII from email bodies, messages)
- [ ] T115 Implement secure credential storage verification (ensure tokens not in git or vault)

### Performance Optimization

- [ ] T116 [P] Implement local caching for Gmail messages (reduce API calls, stay under rate limits)
- [ ] T117 [P] Implement connection pooling for API clients (reuse connections, improve performance)
- [ ] T118 Optimize memory usage (ensure <1GB during normal operation)

### Bronze Phase Compatibility Testing

- [ ] T119 Run Bronze phase regression tests (verify FileSystem watcher still works)
- [ ] T120 Verify Dashboard updates correctly with multi-channel metrics
- [ ] T121 Verify all Bronze agent skills still functional

### Final Validation

- [ ] T122 Run end-to-end test for Gmail flow (send test email, verify task creation, verify dashboard update)
- [ ] T123 Run end-to-end test for WhatsApp flow (send test message, verify task creation)
- [ ] T124 Run end-to-end test for LinkedIn flow (trigger LinkedIn watcher, verify task creation)
- [ ] T125 Run end-to-end test for approval workflow (trigger action, approve via CLI, verify execution)
- [ ] T126 Run end-to-end test for LinkedIn posting (generate post, approve, verify posting, check analytics)
- [ ] T127 Run end-to-end test for planning (create complex task, verify Plan.md generation)
- [ ] T128 Run end-to-end test for scheduling (create schedule, verify execution at scheduled time)
- [ ] T129 Verify all success criteria from spec.md (30-second detection, 90% accuracy, 99% reliability, etc.)
- [ ] T130 Run quickstart.md validation (follow setup guide, verify all steps work)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P2): Can start after Foundational - No dependencies on other stories
  - User Story 3 (P3): Depends on User Story 1 (needs LinkedInWatcher) and User Story 2 (needs approval workflow)
  - User Story 4 (P4): Can start after Foundational - No dependencies on other stories
  - User Story 5 (P5): Can start after Foundational - No dependencies on other stories
- **MCP Tools (Phase 8)**: Can start after Foundational, integrates with User Stories 1 and 2
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P3)**: Depends on US1 (LinkedInWatcher) and US2 (approval workflow) - Should start after both complete
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Authentication before watcher implementation
- Agent skills before watcher implementation (classification logic needed)
- Watcher implementation before orchestrator integration
- Core functionality before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup Phase**: T003, T004, T005, T006, T007, T008 can run in parallel
- **Foundational Phase**: T011, T012, T013, T014, T015, T018, T019, T021 can run in parallel
- **User Story 1**: T022, T023 (Gmail) can run parallel with T028 (WhatsApp) and T034, T035 (LinkedIn)
- **User Story 2**: T044, T048 can run in parallel
- **User Story 3**: T059, T063 can run in parallel
- **User Story 4**: T072 can run independently
- **User Story 5**: All tasks sequential (scheduler setup)
- **MCP Tools Phase**: T097, T098 (Gmail) can run parallel with T102, T103 (WhatsApp)
- **Polish Phase**: T107, T108, T109, T110, T111, T113, T114, T116, T117 can run in parallel

---

## Parallel Example: User Story 1 (Multi-Channel Watchers)

```bash
# Launch all authentication modules together:
Task T022: "Implement GmailAuth class in src/watchers/auth/gmail_auth.py"
Task T034: "Implement LinkedInAuth class in src/watchers/auth/linkedin_auth.py"

# Launch all agent skills together:
Task T023: "Create agent skill classify-email.command.md"
Task T028: "Create agent skill classify-whatsapp.command.md"
Task T035: "Create agent skill classify-linkedin.command.md"

# Then implement watchers sequentially (each depends on its auth + agent skill):
Task T024: "Implement GmailWatcher class" (after T022, T023)
Task T029: "Implement WhatsAppWatcher class" (after T028)
Task T036: "Implement LinkedInWatcher class" (after T034, T035)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T009)
2. Complete Phase 2: Foundational (T010-T021) - CRITICAL
3. Complete Phase 3: User Story 1 - Multi-Channel Detection (T022-T043)
4. Complete Phase 4: User Story 2 - Approval Workflow (T044-T058)
5. **STOP and VALIDATE**: Test US1 and US2 independently
6. Deploy/demo if ready (MVP with multi-channel detection + approval)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Multi-channel detection working!)
3. Add User Story 2 → Test independently → Deploy/Demo (Approval workflow working!)
4. Add User Story 3 → Test independently → Deploy/Demo (LinkedIn posting working!)
5. Add User Story 4 → Test independently → Deploy/Demo (Planning capability working!)
6. Add User Story 5 → Test independently → Deploy/Demo (Scheduling working!)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T021)
2. Once Foundational is done:
   - Developer A: User Story 1 (T022-T043) - Multi-Channel Watchers
   - Developer B: User Story 2 (T044-T058) - Approval Workflow
   - Developer C: User Story 4 (T072-T080) - Planning Capability
   - Developer D: User Story 5 (T081-T096) - Scheduling
3. After US1 and US2 complete:
   - Developer A or B: User Story 3 (T059-T071) - LinkedIn Posting (depends on US1 + US2)
4. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 130 tasks

**Tasks per User Story**:
- Setup (Phase 1): 9 tasks
- Foundational (Phase 2): 12 tasks
- User Story 1 (P1): 22 tasks (Multi-Channel Detection)
- User Story 2 (P2): 15 tasks (Approval Workflow)
- User Story 3 (P3): 13 tasks (LinkedIn Auto-Posting)
- User Story 4 (P4): 9 tasks (Intelligent Planning)
- User Story 5 (P5): 16 tasks (Scheduled Automation)
- MCP Tools (Phase 8): 10 tasks
- Polish (Phase 9): 24 tasks

**Parallel Opportunities**: 35 tasks marked [P] can run in parallel within their phase

**Independent Test Criteria**:
- US1: Send test messages through all channels, verify task creation within 30 seconds
- US2: Trigger approval, verify CLI workflow, check audit trail
- US3: Generate LinkedIn post, approve, verify posting and analytics
- US4: Create complex task, verify Plan.md generation with structured content
- US5: Create schedule, verify execution at scheduled time, check logs

**Suggested MVP Scope**: User Stories 1 + 2 (Multi-channel detection + Approval workflow) = 37 implementation tasks after foundational phase

**Format Validation**: ✅ All 130 tasks follow the required checklist format with checkbox, Task ID, [P] marker (where applicable), [Story] label (for user story phases), and file paths

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are NOT included (not requested in specification)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Bronze phase compatibility maintained throughout (regression tests in Phase 9)
- All tasks include specific file paths for immediate execution
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

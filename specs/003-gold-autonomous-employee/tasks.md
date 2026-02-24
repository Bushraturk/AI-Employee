---
description: "Implementation tasks for Gold Tier - Autonomous Employee"
---

# Tasks: Gold Tier - Autonomous Employee

**Input**: Design documents from `/specs/003-gold-autonomous-employee/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: Tests are OPTIONAL and not included (not requested in spec.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US5)
- Include exact file paths in descriptions

## Path Conventions

All paths relative to repository root: `C:\Users\admin\Desktop\b-ai-employee\`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create Gold Tier vault folders: `AI_Employee_Vault/Accounting/transactions/`, `AI_Employee_Vault/Social_Media/posts/`, `AI_Employee_Vault/Audits/weekly/`, `AI_Employee_Vault/Workflows/executions/`, `AI_Employee_Vault/Workflows/plans/`, `AI_Employee_Vault/System/mcp_servers/`, `AI_Employee_Vault/Logs/error_recovery/`, `AI_Employee_Vault/Action_Queue/`, `AI_Employee_Vault/Circuit_State/`
- [x] T002 [P] Update `requirements.txt` with Gold Tier dependencies: odoorpc>=0.10.1, requests>=2.31.0, tweepy>=4.14.0, tenacity>=8.2.0, pybreaker>=1.0.0
- [x] T003 [P] Create MCP server configuration file `config/mcp_servers.yaml` with accounting, social, communications server definitions
- [x] T004 [P] Update scheduling configuration `config/schedules.yaml` with Gold Tier schedules (Odoo sync every 5 min, social metrics every 6 hours, weekly audit Sunday 6 PM, MCP health check every 1 min)
- [x] T005 [P] Create circuit breaker configuration `config/circuit_breakers.yaml` with thresholds for odoo, facebook, instagram, twitter

---

## Phase 2: Foundational Infrastructure (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Multiple MCP Servers (US4 - Infrastructure)

- [x] T006 Create MCPServer entity model in `src/models/mcp_server.py` with attributes: server_id, domain, status, available_tools, rate_limits, last_health_check, error_count, restart_count, process_id, started_at, updated_at
- [x] T007 Create MCPServerOrchestrator class in `src/orchestrator/mcp_server_orchestrator.py` with methods: start_server(), stop_server(), restart_server(), health_check(), route_action()
- [x] T008 Implement process-based server lifecycle management in `src/orchestrator/mcp_server_orchestrator.py` using subprocess module for independent MCP server processes
- [x] T009 Implement action routing logic in `src/orchestrator/mcp_server_orchestrator.py` to route actions to appropriate MCP server based on action type (accounting/social/communications)
- [x] T010 Implement health check system in `src/orchestrator/mcp_server_orchestrator.py` with automatic restart on failure (max 3 restarts per server)
- [x] T011 Create MCP server state persistence in `AI_Employee_Vault/System/mcp_servers/` with Markdown files for each server tracking status, errors, restarts

### Error Recovery System (US6 - Infrastructure)

- [x] T012 Create ErrorRecoveryLog entity model in `src/models/error_recovery_log.py` with attributes: error_id, error_type, service, error_message, retry_count, recovery_strategy, outcome, timestamp, context
- [x] T013 Create ErrorRecoveryService in `src/services/error_recovery.py` with retry logic using tenacity (exponential backoff, max 3 attempts)
- [x] T014 Implement circuit breaker pattern in `src/services/error_recovery.py` using pybreaker for each external service (odoo, facebook, instagram, twitter)
- [x] T015 Create action queue system in `src/services/error_recovery.py` with Markdown-based queue files in `AI_Employee_Vault/Action_Queue/` (odoo_queue.md, facebook_queue.md, twitter_queue.md)
- [x] T016 Implement circuit state persistence in `AI_Employee_Vault/Circuit_State/` with Markdown files tracking circuit breaker states (closed/open/half-open)
- [x] T017 Create error recovery logging in `AI_Employee_Vault/Logs/error_recovery/` with detailed recovery attempt tracking
- [x] T018 Implement graceful degradation logic in `src/services/error_recovery.py` to disable failing integrations after 10 consecutive failures and notify user

### Scheduling Infrastructure

- [x] T019 Update APScheduler configuration in `src/orchestrator/task_processor.py` to use SQLite job store for persistence (`jobs.sqlite`)
- [x] T020 Implement schedule loader in `src/orchestrator/task_processor.py` to read from `config/schedules.yaml` and register Gold Tier jobs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Odoo Accounting Integration (Priority: P1) 🎯 MVP

**Goal**: Bidirectional sync of financial transactions between Odoo Community and vault with conflict detection

**Independent Test**: Set up Odoo locally, create test invoice in Odoo, verify it syncs to vault within 5 minutes. Create expense in vault, verify it syncs to Odoo. Modify same transaction in both systems, verify conflict is flagged.

### Implementation for User Story 1

- [x] T021 [P] [US1] Create OdooTransaction entity model in `src/models/odoo_transaction.py` with attributes: transaction_id, type, amount, currency, date, customer_vendor, category, odoo_id, sync_status, last_synced_at, conflict_flag, conflict_details, created_at, updated_at
- [x] T022 [P] [US1] Create OdooClient wrapper in `src/mcp_servers/accounting_mcp/odoo_client.py` using odoorpc library with connection management, authentication, and error handling
- [x] T023 [US1] Create accounting MCP server in `src/mcp_servers/accounting_mcp/server.py` with JSON-RPC interface and tool registration
- [x] T024 [US1] Implement sync_odoo_transaction tool in `src/mcp_servers/accounting_mcp/server.py` for bidirectional transaction sync with conflict detection
- [x] T025 [US1] Implement create_odoo_invoice tool in `src/mcp_servers/accounting_mcp/server.py` to create invoices in Odoo from vault transactions
- [x] T026 [US1] Implement create_odoo_expense tool in `src/mcp_servers/accounting_mcp/server.py` to record expenses in Odoo from vault transactions
- [x] T027 [US1] Implement create_odoo_customer tool in `src/mcp_servers/accounting_mcp/server.py` to create customers/partners in Odoo
- [x] T028 [US1] Implement Odoo polling service in `src/mcp_servers/accounting_mcp/polling_service.py` to check for changes every 5 minutes using search_read with write_date filter
- [x] T029 [US1] Implement conflict detection logic in `src/mcp_servers/accounting_mcp/conflict_detector.py` comparing write_date (Odoo) vs updated_at (vault) vs last_synced_at
- [x] T030 [US1] Create transaction sync workflow in `src/mcp_servers/accounting_mcp/sync_workflow.py` orchestrating poll → detect changes → sync → handle conflicts
- [x] T031 [US1] Implement category mapping in `src/mcp_servers/accounting_mcp/category_mapper.py` to map vault categories to Odoo account IDs using Company_Handbook rules
- [x] T032 [US1] Add validation logic in `src/mcp_servers/accounting_mcp/validator.py` for transaction data before syncing to Odoo (required fields, valid amounts, proper dates)
- [x] T033 [US1] Integrate accounting MCP server with MCPServerOrchestrator in `src/orchestrator/mcp_server_orchestrator.py` for lifecycle management
- [x] T034 [US1] Add error recovery integration in `src/mcp_servers/accounting_mcp/sync_workflow.py` using ErrorRecoveryService for all Odoo API calls

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Odoo transactions sync bidirectionally with conflict detection.

---

## Phase 4: User Story 2 - Multi-Platform Social Media Management (Priority: P2)

**Goal**: Automated posting to Facebook, Instagram, Twitter with platform-specific optimization and unified metrics dashboard

**Independent Test**: Configure API credentials for all platforms, generate test post, verify it appears in approval queue with platform-specific adaptations, approve post, verify successful publishing to all platforms, wait 24 hours, verify metrics are collected.

### Implementation for User Story 2

- [x] T035 [P] [US2] Create SocialMediaPost entity model in `src/models/social_media_post.py` with attributes: post_id, platforms, content, media_urls, posted_at, performance_metrics, approval_metadata, cross_post_group_id, status, created_at, updated_at
- [x] T036 [P] [US2] Create FacebookGraphAPI client in `src/mcp_servers/social_mcp/facebook_client.py` using requests library with methods: post_to_page(), post_photo(), get_insights(), get_page_info()
- [x] T037 [P] [US2] Create InstagramGraphAPI client in `src/mcp_servers/social_mcp/instagram_client.py` using requests library with two-step publishing: create_media_container(), check_status(), publish_media(), get_insights()
- [x] T038 [P] [US2] Create TwitterAPIClient in `src/mcp_servers/social_mcp/twitter_client.py` using tweepy library with methods: create_tweet(), create_tweet_with_media(), post_thread(), get_metrics(), get_user_info()
- [x] T039 [US2] Create social media MCP server in `src/mcp_servers/social_mcp/server.py` with JSON-RPC interface and tool registration for all platforms
- [x] T040 [US2] Implement post_facebook tool in `src/mcp_servers/social_mcp/server.py` with rate limiting (200 calls/hour) and circuit breaker
- [x] T041 [US2] Implement post_instagram tool in `src/mcp_servers/social_mcp/server.py` with daily limit enforcement (25 posts/day) and two-step publishing flow
- [x] T042 [US2] Implement post_twitter tool in `src/mcp_servers/social_mcp/server.py` with automatic rate limit handling via tweepy (300 tweets/3 hours)
- [x] T043 [US2] Implement content optimizer in `src/mcp_servers/social_mcp/content_optimizer.py` for platform-specific adaptations (character limits, hashtag conventions, media formats)
- [x] T044 [US2] Implement cross-posting coordinator in `src/mcp_servers/social_mcp/cross_post_coordinator.py` to manage simultaneous posting to multiple platforms with cross_post_group_id tracking
- [x] T045 [US2] Implement metrics aggregator in `src/mcp_servers/social_mcp/metrics_aggregator.py` to collect performance data from all platforms (Facebook, Instagram, Twitter, LinkedIn) and update SocialMediaPost entities
- [x] T046 [US2] Create metrics collection scheduler in `src/mcp_servers/social_mcp/metrics_aggregator.py` to update metrics every 6 hours for all published posts
- [x] T047 [US2] Implement rate limiter in `src/mcp_servers/social_mcp/rate_limiter.py` with platform-specific limits (Facebook: 200/hour, Instagram: 25/day, Twitter: 300/3 hours)
- [x] T048 [US2] Integrate social MCP server with MCPServerOrchestrator in `src/orchestrator/mcp_server_orchestrator.py` for lifecycle management
- [x] T049 [US2] Add error recovery integration in `src/mcp_servers/social_mcp/server.py` using ErrorRecoveryService for all social media API calls
- [x] T050 [US2] Extend approval workflow in `src/orchestrator/approval_manager.py` to support multi-platform post review with platform-specific previews

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Posts publish to Facebook, Instagram, Twitter with metrics tracking.

---

## Phase 5: User Story 3 - Weekly Business and Accounting Audit (Priority: P3)

**Goal**: Automated weekly CEO briefing with financial, operational, and social metrics plus trend analysis and recommendations

**Independent Test**: Run system for one week with various activities (transactions, posts, tasks), trigger audit generation (Sunday 6 PM or manual), verify CEO briefing in `Audits/weekly/` includes financial summary, operational metrics, social performance, trends, anomalies, and recommendations.

### Implementation for User Story 3

- [x] T051 [P] [US3] Create AuditReport entity model in `src/models/audit_report.py` with attributes: report_id, week_start_date, week_end_date, financial_summary, operational_metrics, social_metrics, trends, anomalies, recommendations, generated_at
- [x] T052 [US3] Create AuditGeneratorService in `src/services/audit_generator.py` with main generate_weekly_audit() method
- [x] T053 [US3] Implement financial metrics collector in `src/services/audit_generator.py` to aggregate revenue, expenses, profit/loss, cash flow from OdooTransaction entities for the week
- [x] T054 [US3] Implement operational metrics collector in `src/services/audit_generator.py` to aggregate tasks completed, pending, response times, approval rates, system uptime from task files and logs
- [x] T055 [US3] Implement social metrics collector in `src/services/audit_generator.py` to aggregate total posts, reach, engagement, follower growth from SocialMediaPost entities across all platforms
- [x] T056 [US3] Implement trend analyzer in `src/services/audit_generator.py` to compare current week vs previous week for all metrics (revenue, expenses, engagement, etc.) and calculate percent changes
- [x] T057 [US3] Implement anomaly detector in `src/services/audit_generator.py` to identify concerning trends (>30% expense increase, declining engagement, low approval rate) with severity levels (low/medium/high)
- [x] T058 [US3] Implement recommendation engine in `src/services/audit_generator.py` to generate actionable recommendations based on detected trends and anomalies
- [x] T059 [US3] Implement CEO briefing formatter in `src/services/audit_generator.py` to generate Markdown report with executive summary, financial performance, operational metrics, social performance, trends, anomalies, recommendations
- [x] T060 [US3] Create audit report persistence in `AI_Employee_Vault/Audits/weekly/` with Markdown files named by report_id and week dates
- [x] T061 [US3] Register weekly audit job in APScheduler (Sunday 6 PM cron: "0 18 * * 0") in `src/orchestrator/task_processor.py`
- [x] T062 [US3] Implement on-demand audit generation command in `src/cli/gold_tier_cli.py` for manual audit triggers

**Checkpoint**: All user stories 1, 2, and 3 should now be independently functional. Weekly audits generate automatically with comprehensive business intelligence.

---

## Phase 6: User Story 5 - Ralph Wiggum Autonomous Loop (Priority: P5)

**Goal**: Autonomous multi-step workflow execution with automatic error recovery and human escalation when needed

**Independent Test**: Create complex task requiring multiple steps across domains (e.g., "Process invoice for Acme Corp ($1500), sync to Odoo, post announcement on social media"), verify system generates execution plan, executes steps in order, handles errors gracefully, and reports completion.

### Implementation for User Story 5

- [x] T063 [P] [US5] Create WorkflowExecution entity model in `src/models/workflow_execution.py` with attributes: execution_id, task_reference, plan_reference, steps, current_step_index, status, execution_context, started_at, completed_at, lessons_learned, created_at, updated_at
- [x] T064 [US5] Create RalphWiggumOrchestrator in `src/orchestrator/ralph_wiggum.py` with main execute_workflow() method
- [x] T065 [US5] Implement task analyzer in `src/orchestrator/ralph_wiggum.py` to detect complex multi-step tasks requiring autonomous execution (checks for multiple action types, dependencies, cross-domain operations)
- [x] T066 [US5] Implement plan generator in `src/orchestrator/ralph_wiggum.py` to create execution plans with sequential steps, dependencies, success criteria, and rollback procedures (generates Plan.md in `Workflows/plans/`)
- [x] T067 [US5] Implement step executor in `src/orchestrator/ralph_wiggum.py` to execute plan steps automatically in order, waiting for each step to complete before proceeding
- [x] T068 [US5] Implement execution state tracker in `src/orchestrator/ralph_wiggum.py` to track step status (pending/in_progress/completed/failed) and update WorkflowExecution entity
- [x] T069 [US5] Implement execution context manager in `src/orchestrator/ralph_wiggum.py` to maintain data passed between steps (e.g., odoo_id from step 1 available to step 2)
- [x] T070 [US5] Implement automatic error recovery in `src/orchestrator/ralph_wiggum.py` using ErrorRecoveryService for step failures (retry with backoff, alternative approach, graceful degradation)
- [x] T071 [US5] Implement human escalation logic in `src/orchestrator/ralph_wiggum.py` to pause execution, preserve state, request specific guidance, and resume from failure point after receiving input
- [x] T072 [US5] Implement safety boundary enforcement in `src/orchestrator/ralph_wiggum.py` to check each step against risk action policy before execution (CRITICAL: no autonomous execution of high-risk actions without approval per FR-050)
- [x] T073 [US5] Implement process improvement analyzer in `src/orchestrator/ralph_wiggum.py` to identify inefficiencies after workflow completion and suggest improvements (stored in lessons_learned)
- [x] T074 [US5] Create workflow execution persistence in `AI_Employee_Vault/Workflows/executions/` with Markdown files tracking step-by-step progress
- [x] T075 [US5] Integrate Ralph Wiggum loop with task processor in `src/orchestrator/task_processor.py` to automatically invoke for complex tasks
- [x] T076 [US5] Add workflow pause/resume commands in `src/cli/gold_tier_cli.py` for manual intervention

**Checkpoint**: Ralph Wiggum autonomous loop completes multi-step workflows end-to-end with error recovery and safety boundaries.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T077 [P] Update `README.md` with Gold Tier overview, prerequisites, and quickstart reference
- [x] T078 [P] Create MCP server startup script in `src/cli/start_mcp_servers.py` to launch all MCP servers with proper configuration
- [x] T079 [P] Create MCP server status command in `src/cli/gold_tier_cli.py` to display health status of all MCP servers (--mcp-status flag)
- [x] T080 [P] Implement log rotation in `src/services/log_rotator.py` for daily rotation with 30-day retention across all log files
- [x] T081 [P] Create dashboard updater extension in `src/services/dashboard_updater.py` to include Gold Tier metrics (Odoo sync status, social media performance, MCP server health, workflow executions)
- [x] T082 Implement performance monitoring in `src/services/performance_monitor.py` to track memory usage, API call counts, response times, and alert if thresholds exceeded
- [x] T083 Create Gold Tier CLI flag in `src/main.py` (--gold-tier) to start orchestrator with all Gold features enabled
- [x] T084 Validate quickstart.md by following all setup steps and verifying system works end-to-end
- [x] T085 Code cleanup and refactoring across all Gold Tier modules for consistency and maintainability
- [x] T086 Security audit of all credential handling, API calls, and error messages to ensure no secrets are logged or exposed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P5)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1 and US2 data but independently testable
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - Uses all MCP servers but independently testable

### Within Each User Story

- Models before services
- Services before MCP server tools
- MCP server tools before integration with orchestrator
- Core implementation before error recovery integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task T021: "Create OdooTransaction entity model in src/models/odoo_transaction.py"
Task T022: "Create OdooClient wrapper in src/mcp_servers/accounting_mcp/odoo_client.py"

# Then proceed with dependent tasks sequentially:
Task T023: "Create accounting MCP server" (depends on T022)
Task T024: "Implement sync_odoo_transaction tool" (depends on T021, T023)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Odoo Integration)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 5 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Odoo)
   - Developer B: User Story 2 (Social Media)
   - Developer C: User Story 3 (Audits)
3. Stories complete and integrate independently
4. Developer D: User Story 5 (Ralph Wiggum) after others are stable

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are OPTIONAL (not included as they were not requested in spec.md)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US4 and US6 are infrastructure (Phase 2), not feature stories
- Ralph Wiggum loop MUST enforce approval gates for risk actions (FR-050)
- All external API calls must use error recovery with circuit breakers
- All entities stored as Markdown files in vault (constitution compliance)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

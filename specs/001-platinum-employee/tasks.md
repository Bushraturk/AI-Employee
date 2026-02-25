# Tasks: Platinum Tier AI Employee

**Input**: Design documents from `/specs/001-platinum-employee/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the specification, so test tasks are excluded from this implementation plan.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md (cloud_agent/, local_agent/, shared/, mcp_servers/, orchestration/, deployment/, vault/, tests/, config/, docs/)
- [X] T002 [P] Initialize cloud_agent Python project with requirements.txt (watchdog, APScheduler, google-auth, googleapiclient, tenacity, pybreaker, frontmatter, markdown, python-dotenv, GitPython)
- [X] T003 [P] Initialize local_agent Python project with requirements.txt (watchdog, APScheduler, playwright, tenacity, pybreaker, frontmatter, markdown, python-dotenv, GitPython)
- [X] T004 [P] Initialize shared Python package with requirements.txt (frontmatter, markdown, pydantic)
- [X] T005 [P] Initialize email_mcp Node.js project with package.json (googleapis, @modelcontextprotocol/sdk)
- [ ] T006 [P] Initialize social_mcp Node.js project with package.json (axios, @modelcontextprotocol/sdk)
- [ ] T007 [P] Initialize odoo_mcp Python project with requirements.txt (odoorpc, @modelcontextprotocol/sdk)
- [X] T008 Create vault directory structure per contracts/vault-structure.md (Needs_Action/, In_Progress/, Pending_Approval/, Approved/, Rejected/, Done/, Plans/, Logs/, Updates/)
- [X] T009 [P] Create config/.env.example with all required environment variables
- [X] T010 [P] Create config/.gitignore with secret exclusion patterns per research.md
- [X] T011 [P] Create config/pre-commit-config.yaml for secret detection
- [X] T012 [P] Create config/mcp_config.json for MCP server configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Shared Models and Utilities

- [X] T013 [P] Implement ActionFile model in shared/models/action_file.py per contracts/action-file-schema.json
- [X] T014 [P] Implement ApprovalRequest model in shared/models/approval_request.py per contracts/approval-request-schema.json
- [X] T015 [P] Implement AuditLogEntry model in shared/models/audit_log.py per data-model.md
- [X] T016 [P] Implement VaultStructure constants in shared/models/vault_structure.py per contracts/vault-structure.md
- [X] T017 [P] Implement markdown parser utilities in shared/utils/markdown_parser.py (frontmatter parsing, validation)
- [X] T018 [P] Implement safe file operations in shared/utils/file_operations.py (atomic move, claim-by-move)
- [X] T019 [P] Implement structured logging in shared/utils/logging_utils.py (JSON format, audit trail)
- [X] T020 [P] Define shared constants in shared/constants.py (folder names, file patterns, timeouts)

### Base Agent Framework

- [X] T021 Implement BaseAgent abstract class in shared/models/base_agent.py per contracts/agent-api.md (start, stop, process_action_file, claim_task, update_heartbeat, get_capabilities)
- [X] T022 Implement BaseWatcher abstract class in shared/models/base_watcher.py (check, create_action_file, track_processed_ids)
- [X] T023 [P] Implement VaultSync handler in shared/vault_sync.py (Git pull/push, Syncthing status check, sync throttling)
- [X] T024 [P] Implement AgentState model in shared/models/agent_state.py per data-model.md (heartbeat, capabilities, claimed_tasks)

### Orchestration and Process Management

- [ ] T025 Implement Orchestrator in orchestration/orchestrator.py (folder watching, task scheduling, process coordination)
- [ ] T026 Implement Watchdog in orchestration/watchdog.py (health monitoring, process restart, exponential backoff)
- [ ] T027 [P] Create cloud process configuration in orchestration/config/cloud_processes.yaml
- [ ] T028 [P] Create local process configuration in orchestration/config/local_processes.yaml

### Approval Workflow Infrastructure

- [ ] T029 Implement ApprovalHandler base class in shared/approval_handler.py (validate, execute, log, move_to_done)
- [ ] T030 Implement approval file validation in shared/utils/approval_validator.py (schema validation, expiration check)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Autonomous Email Handling While Offline (Priority: P1) 🎯 MVP

**Goal**: Enable 24/7 email monitoring and draft generation even when local machine is offline, with approval workflow for sending

**Independent Test**: Send email to monitored account while local machine is offline, verify draft is created in Pending_Approval, bring local machine online, approve draft, verify email is sent

### Cloud Agent Components for US1

- [X] T031 [P] [US1] Implement GmailWatcher in cloud_agent/src/watchers/gmail_watcher.py (inherit BaseWatcher, Gmail API integration, 2-minute check interval, create action files)
- [X] T032 [P] [US1] Implement EmailDrafter in cloud_agent/src/drafters/email_drafter.py (Claude API integration, context analysis, draft generation, write to Pending_Approval/email/)
- [X] T033 [US1] Implement CloudAgent main orchestrator in cloud_agent/src/agent.py (inherit BaseAgent, start GmailWatcher, process email action files, coordinate drafting)
- [X] T034 [US1] Implement cloud agent configuration in cloud_agent/src/config.py (Gmail credentials, vault path, sync settings, rate limits)

### Local Agent Components for US1

- [X] T035 [P] [US1] Implement EmailExecutor in local_agent/src/executors/email_executor.py (MCP client integration, send email, log action, move to Done)
- [X] T036 [US1] Implement LocalAgent approval handler in local_agent/src/approval_handler.py (monitor Approved/, execute email sends, update Dashboard)
- [X] T037 [US1] Implement LocalAgent main orchestrator in local_agent/src/agent.py (inherit BaseAgent, monitor Approved/, coordinate execution)
- [X] T038 [US1] Implement local agent configuration in local_agent/src/config.py (MCP server endpoints, vault path, sync settings)

### MCP Server for US1

- [X] T039 [P] [US1] Implement Email MCP server in mcp_servers/email_mcp/src/index.js (Gmail API client, send_email tool, list_emails resource)
- [X] T040 [P] [US1] Implement Gmail client in mcp_servers/email_mcp/src/gmail_client.js (authentication, send, list, error handling)
- [X] T041 [US1] Add Email MCP server configuration to config/mcp_config.json

### Dashboard Integration for US1

- [X] T042 [US1] Implement DashboardUpdater in local_agent/src/dashboard_updater.py (merge Updates/, write Dashboard.md, single-writer rule)
- [X] T043 [US1] Implement Dashboard update logic in cloud_agent for email events (write to Updates/ folder)

**Checkpoint**: At this point, User Story 1 should be fully functional - emails detected, drafts created, approvals processed, emails sent

---

## Phase 4: User Story 2 - Social Media Content Scheduling with Approval (Priority: P2)

**Goal**: Enable automated social media post drafting based on business goals with approval workflow for publishing

**Independent Test**: Configure business goals, trigger scheduled post generation, verify draft in Pending_Approval/social, approve draft, verify post is published to platform

### Cloud Agent Components for US2

- [ ] T044 [P] [US2] Implement SocialDrafter in cloud_agent/src/drafters/social_drafter.py (read Business_Goals.md, generate post content, write to Pending_Approval/social/)
- [ ] T045 [US2] Add social post scheduling to cloud_agent/src/agent.py (APScheduler integration, trigger SocialDrafter)
- [ ] T046 [US2] Implement business goals parser in cloud_agent/src/utils/business_goals_parser.py (read Business_Goals.md, extract targets and themes)

### Local Agent Components for US2

- [ ] T047 [P] [US2] Implement SocialExecutor in local_agent/src/executors/social_executor.py (MCP client integration, post to platforms, log action, move to Done)
- [ ] T048 [US2] Add social post execution to local_agent/src/approval_handler.py (handle social_post approval type)

### MCP Server for US2

- [ ] T049 [P] [US2] Implement Social MCP server in mcp_servers/social_mcp/src/index.js (platform routing, post_to_platform tool)
- [ ] T050 [P] [US2] Implement Facebook client in mcp_servers/social_mcp/src/facebook_client.js (Graph API, post, error handling)
- [ ] T051 [P] [US2] Implement Instagram client in mcp_servers/social_mcp/src/instagram_client.js (Graph API, post, error handling)
- [ ] T052 [P] [US2] Implement Twitter client in mcp_servers/social_mcp/src/twitter_client.js (API v2, post, error handling)
- [ ] T053 [P] [US2] Implement LinkedIn client in mcp_servers/social_mcp/src/linkedin_client.js (API, post, error handling)
- [ ] T054 [US2] Add Social MCP server configuration to config/mcp_config.json

### Dashboard Integration for US2

- [ ] T055 [US2] Implement Dashboard update logic in cloud_agent for social events (write to Updates/ folder)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - emails and social posts both functional

---

## Phase 5: User Story 3 - Financial Transaction Monitoring and Invoice Management (Priority: P2)

**Goal**: Enable automated financial transaction monitoring, Odoo entry drafting, and approval workflow for posting to ERP

**Independent Test**: Simulate bank transaction, verify finance watcher detects it, verify draft Odoo entry in Pending_Approval/accounting, approve entry, verify posted to Odoo

### Local Agent Components for US3 (Watcher)

- [ ] T056 [P] [US3] Implement FinanceWatcher in local_agent/src/watchers/finance_watcher.py (inherit BaseWatcher, bank transaction monitoring, 5-minute check interval, create action files)
- [ ] T057 [US3] Add FinanceWatcher to local_agent/src/agent.py (start watcher, coordinate with cloud agent via vault)

### Cloud Agent Components for US3 (Drafter)

- [ ] T058 [P] [US3] Implement AccountingDrafter in cloud_agent/src/drafters/accounting_drafter.py (analyze transactions, match to invoices, draft Odoo entries, write to Pending_Approval/accounting/)
- [ ] T059 [US3] Add accounting entry drafting to cloud_agent/src/agent.py (process accounting action files)

### Local Agent Components for US3 (Executor)

- [ ] T060 [P] [US3] Implement AccountingExecutor in local_agent/src/executors/accounting_executor.py (MCP client integration, post to Odoo, log action, move to Done)
- [ ] T061 [US3] Add accounting entry execution to local_agent/src/approval_handler.py (handle accounting_entry approval type)

### MCP Server for US3

- [ ] T062 [P] [US3] Implement Odoo MCP server in mcp_servers/odoo_mcp/src/server.py per contracts/mcp-odoo-spec.md (odoorpc integration, connection pooling)
- [ ] T063 [P] [US3] Implement Odoo client in mcp_servers/odoo_mcp/src/odoo_client.py (authentication, create_invoice, register_payment, create_expense, get_partner, get_account, validate_entry)
- [ ] T064 [US3] Add Odoo MCP server configuration to config/mcp_config.json

### Odoo Deployment

- [ ] T065 [US3] Create Odoo deployment script in deployment/cloud/scripts/setup_odoo.sh (install Odoo Community Edition v19, configure PostgreSQL, setup HTTPS)
- [ ] T066 [US3] Create Odoo backup script in deployment/cloud/scripts/backup_odoo.sh (pg_dump, compression, retention)
- [ ] T067 [US3] Add Odoo health monitoring to orchestration/watchdog.py

### Dashboard Integration for US3

- [ ] T068 [US3] Implement Dashboard update logic in cloud_agent for accounting events (write to Updates/ folder)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - emails, social posts, and accounting all functional

---

## Phase 6: User Story 4 - WhatsApp Business Communication (Priority: P3)

**Goal**: Enable WhatsApp message monitoring for urgent keywords with approval workflow for sending responses

**Independent Test**: Send WhatsApp message with urgent keyword, verify watcher detects it, verify draft response in Pending_Approval/whatsapp, approve response, verify message sent via WhatsApp Web

### Local Agent Components for US4 (Watcher)

- [ ] T069 [P] [US4] Implement WhatsAppWatcher in local_agent/src/watchers/whatsapp_watcher.py (inherit BaseWatcher, Playwright integration, keyword detection, 30-second check interval, create action files)
- [ ] T070 [US4] Add WhatsAppWatcher to local_agent/src/agent.py (start watcher, session validation)

### Cloud Agent Components for US4 (Drafter)

- [ ] T071 [P] [US4] Implement WhatsApp response drafter in cloud_agent/src/drafters/whatsapp_drafter.py (analyze message context, draft response, write to Pending_Approval/whatsapp/)
- [ ] T072 [US4] Add WhatsApp message drafting to cloud_agent/src/agent.py (process whatsapp action files)

### Local Agent Components for US4 (Executor)

- [ ] T073 [P] [US4] Implement WhatsAppExecutor in local_agent/src/executors/whatsapp_executor.py (Playwright integration, send message, session validation, log action, move to Done)
- [ ] T074 [US4] Add WhatsApp message execution to local_agent/src/approval_handler.py (handle whatsapp_send approval type)

### Dashboard Integration for US4

- [ ] T075 [US4] Implement Dashboard update logic in cloud_agent for WhatsApp events (write to Updates/ folder)

**Checkpoint**: At this point, User Stories 1-4 should all work independently - emails, social posts, accounting, and WhatsApp all functional

---

## Phase 7: User Story 5 - Autonomous Business Audit and Briefing (Priority: P3)

**Goal**: Enable automated weekly business analysis with insights, recommendations, and cost optimization suggestions

**Independent Test**: Trigger scheduled audit, verify it analyzes Business_Goals.md, completed tasks, and transactions, verify comprehensive briefing is generated in vault, verify briefing appears in Dashboard

### Cloud Agent Components for US5

- [ ] T076 [P] [US5] Implement BusinessAuditor in cloud_agent/src/auditors/business_auditor.py (read Business_Goals.md, analyze Logs/, calculate metrics, identify trends)
- [ ] T077 [P] [US5] Implement BriefingGenerator in cloud_agent/src/auditors/briefing_generator.py (generate executive summary, identify bottlenecks, create recommendations, detect cost optimization opportunities)
- [ ] T078 [US5] Add scheduled audit to cloud_agent/src/agent.py (APScheduler weekly trigger, coordinate auditor and generator)
- [ ] T079 [US5] Implement cost optimization detector in cloud_agent/src/auditors/cost_optimizer.py (detect unused subscriptions, identify inefficiencies)

### Dashboard Integration for US5

- [ ] T080 [US5] Implement briefing display in local_agent/src/dashboard_updater.py (show latest briefing summary in Dashboard.md)
- [ ] T081 [US5] Implement Dashboard update logic in cloud_agent for audit events (write briefing to Updates/ folder)

**Checkpoint**: All user stories should now be independently functional - complete Platinum Tier feature set operational

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Error Recovery and Resilience

- [ ] T082 [P] Implement retry logic with exponential backoff in shared/utils/retry_handler.py (tenacity integration, max 3 attempts)
- [ ] T083 [P] Implement circuit breaker pattern in shared/utils/circuit_breaker.py (pybreaker integration, per-service breakers)
- [ ] T084 Add error recovery to all watchers (retry on transient failures, quarantine on permanent failures)
- [ ] T085 Add error recovery to all executors (queue operations when services unavailable)

### Security Hardening

- [ ] T086 [P] Implement secret detection in config/pre-commit-config.yaml (detect-secrets, custom patterns)
- [ ] T087 [P] Implement credential validation in shared/utils/credential_validator.py (check .env completeness, validate formats)
- [ ] T088 Implement rate limiting in local_agent/src/executors/ (10 emails/hour, 3 payments/hour per FR-074)
- [ ] T089 Add audit logging to all executors (timestamp, actor, target, parameters, result per FR-073)

### Development and Testing Modes

- [ ] T089a [P] Implement development mode flag in shared/config.py (prevents real external actions, uses mock services per FR-075)
- [ ] T089b [P] Implement dry-run mode in shared/config.py (logs actions without execution, validates workflows per FR-076)
- [ ] T089c Add development mode checks to all executors (EmailExecutor, SocialExecutor, AccountingExecutor, WhatsAppExecutor)
- [ ] T089d Add dry-run mode logging to all executors (log intended action, skip actual execution)

### Deployment and Operations

- [ ] T090 [P] Create cloud VM provisioning script in deployment/cloud/terraform/main.tf (Oracle Cloud Free Tier, VM configuration)
- [ ] T091 [P] Create cloud agent deployment script in deployment/cloud/scripts/deploy_cloud_agent.sh (install dependencies, configure services, start processes)
- [ ] T092 [P] Create local agent setup script in deployment/local/scripts/setup_local_agent.sh (install dependencies, configure vault sync)
- [ ] T093 [P] Create vault sync configuration script in deployment/local/scripts/configure_vault_sync.sh (Git or Syncthing setup)
- [ ] T094 [P] Create health check endpoint in orchestration/watchdog.py (HTTP endpoint for monitoring)

### Documentation

- [ ] T095 [P] Create architecture documentation in docs/architecture.md (system overview, component diagram, data flow)
- [ ] T096 [P] Create deployment guide in docs/deployment.md (step-by-step cloud and local setup)
- [ ] T097 [P] Create security best practices in docs/security.md (credential management, vault sync security, audit trail)
- [ ] T098 [P] Create troubleshooting guide in docs/troubleshooting.md (common issues, solutions, debugging tips)
- [ ] T099 [P] Update README.md with Platinum Tier overview and quickstart link

### Validation and Testing

- [ ] T100 Run quickstart.md validation (follow all 6 phases, verify end-to-end functionality)
- [ ] T101 Validate all contracts (action-file-schema.json, approval-request-schema.json, agent-api.md, mcp-odoo-spec.md, vault-structure.md)
- [ ] T102 Verify constitution v2.0.0 compliance (all 8 principles, Platinum tier vault structure, justified violations documented)
- [ ] T103 Verify success criteria (SC-001 through SC-015 from spec.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P2 → P3 → P3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 and US2
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Independent of US1, US2, US3
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Reads data from US1-US4 but doesn't block them

### Within Each User Story

- Cloud agent components before local agent execution (drafting before execution)
- MCP servers before executors (executors depend on MCP tools)
- Watchers can run in parallel with drafters
- Dashboard integration after core functionality

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002-T007, T009-T012)
- All Foundational shared models marked [P] can run in parallel (T013-T020)
- All Foundational infrastructure marked [P] can run in parallel (T023-T024, T027-T028)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each user story, tasks marked [P] can run in parallel
- All Polish tasks marked [P] can run in parallel (T082-T083, T086-T087, T090-T094, T095-T099)

---

## Parallel Example: User Story 1

```bash
# Launch cloud agent components for US1 together:
Task T031: "Implement GmailWatcher in cloud_agent/src/watchers/gmail_watcher.py"
Task T032: "Implement EmailDrafter in cloud_agent/src/drafters/email_drafter.py"

# Launch local agent components for US1 together:
Task T035: "Implement EmailExecutor in local_agent/src/executors/email_executor.py"

# Launch MCP server components for US1 together:
Task T039: "Implement Email MCP server in mcp_servers/email_mcp/src/index.js"
Task T040: "Implement Gmail client in mcp_servers/email_mcp/src/gmail_client.js"
```

---

## Parallel Example: User Story 3 MCP Server

```bash
# Launch Odoo MCP server components together:
Task T062: "Implement Odoo MCP server in mcp_servers/odoo_mcp/src/server.py"
Task T063: "Implement Odoo client in mcp_servers/odoo_mcp/src/odoo_client.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T012)
2. Complete Phase 2: Foundational (T013-T030) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T031-T043)
4. **STOP and VALIDATE**: Test User Story 1 independently (email detection → draft → approval → send)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (T001-T030)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!) (T031-T043)
3. Add User Story 2 → Test independently → Deploy/Demo (T044-T055)
4. Add User Story 3 → Test independently → Deploy/Demo (T056-T068)
5. Add User Story 4 → Test independently → Deploy/Demo (T069-T075)
6. Add User Story 5 → Test independently → Deploy/Demo (T076-T081)
7. Add Polish → Final production deployment (T082-T103)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T030)
2. Once Foundational is done:
   - Developer A: User Story 1 (T031-T043)
   - Developer B: User Story 2 (T044-T055)
   - Developer C: User Story 3 (T056-T068)
3. Stories complete and integrate independently
4. Continue with US4, US5, and Polish as capacity allows

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are NOT included as they were not explicitly requested in the specification
- Dual-agent architecture requires careful coordination via vault sync
- Cloud agent can only draft, local agent executes (security boundary)
- All sensitive credentials remain local-only (never synced to vault)
- Approval workflow is mandatory for all sensitive actions (100% compliance)
- Vault sync must exclude secrets (.env, sessions, credentials)
- Odoo deployment requires cloud VM (Oracle Cloud Free Tier recommended)
- WhatsApp integration requires local machine (session cannot be cloud-based)
- Business audit (US5) reads data from other stories but doesn't block them
- Error recovery and circuit breakers are critical for production reliability
- Rate limiting prevents abuse (10 emails/hour, 3 payments/hour)
- Audit logging provides complete traceability for all actions
- Dashboard is single-writer (local agent only) to prevent conflicts
- Claim-by-move rule prevents duplicate work between agents
- Watchdog monitors and restarts failed processes automatically
- Constitution compliance verified with justified Local-First violation
- Success criteria (SC-001 through SC-015) must be validated before production

# Feature Specification: Silver Tier - Functional Assistant

**Feature Branch**: `002-silver-functional`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "Silver Tier: Functional Assistant - All Bronze requirements plus: Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn), Automatically Post on LinkedIn about business to generate sales, Claude reasoning loop that creates Plan.md files, One working MCP server for external action, Human-in-the-loop approval workflow for sensitive actions, Basic scheduling via cron or Task Scheduler, All AI functionality as Agent Skills"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Channel Task Detection (Priority: P1)

As a user, I want the system to automatically detect and process tasks from multiple communication channels (Gmail, WhatsApp, LinkedIn) so that I don't miss important requests regardless of where they come from.

**Why this priority**: This is the foundational capability that extends Bronze phase from single-channel (FileSystem) to multi-channel. Without this, Silver tier cannot function. It provides immediate value by consolidating task detection across all major communication platforms.

**Independent Test**: Can be fully tested by sending test messages through Gmail, WhatsApp, and LinkedIn, then verifying that task files are created in the Inbox folder with proper channel metadata. Delivers value by automatically capturing tasks from all channels without manual intervention.

**Acceptance Scenarios**:

1. **Given** the system is running with all three watchers active, **When** a new email arrives in Gmail with task-related content, **Then** a task file is created in Inbox within 30 seconds with email metadata (sender, subject, thread ID)
2. **Given** the system is monitoring WhatsApp, **When** a message is received requesting a task, **Then** the system extracts task details and creates a task file with WhatsApp metadata (sender, message ID, timestamp)
3. **Given** the LinkedIn watcher is active, **When** a LinkedIn message or mention contains a task request, **Then** a task file is created with LinkedIn metadata (sender profile, post/message link)
4. **Given** tasks are being created from multiple channels simultaneously, **When** processing occurs, **Then** each task maintains its channel-specific metadata and no data loss occurs

---

### User Story 2 - Human Approval Workflow (Priority: P2)

As a user, I want to review and approve sensitive actions (sending emails, posting to LinkedIn, sending WhatsApp messages) before they execute so that I maintain control over external communications and prevent mistakes.

**Why this priority**: Safety and trust are critical for autonomous systems. Without approval workflow, the system could send inappropriate messages or make business-critical errors. This is essential before enabling any external actions.

**Independent Test**: Can be tested by triggering actions that require approval (e.g., draft email reply), verifying they appear in the approval queue, and testing approve/reject/edit workflows. Delivers value by providing safety guardrails for autonomous actions.

**Acceptance Scenarios**:

1. **Given** the system has generated a draft email reply, **When** the action is ready to execute, **Then** it is placed in the Needs_Approval folder and waits for human review
2. **Given** there are pending approvals in the queue, **When** I run the approval CLI command, **Then** I see a list of all pending actions with details (what, why, impact, risk level)
3. **Given** I am reviewing a pending action, **When** I approve it, **Then** the action executes immediately and is logged with approval metadata (reviewer, timestamp, decision)
4. **Given** I am reviewing a pending action, **When** I reject it, **Then** the action is cancelled, logged, and the original task is marked with rejection reason
5. **Given** a pending action has been waiting for 24 hours, **When** the timeout is reached, **Then** the action is automatically rejected and logged

---

### User Story 3 - LinkedIn Auto-Posting for Business Development (Priority: P3)

As a business owner, I want the system to automatically generate and post engaging LinkedIn content about my products/services so that I can maintain consistent social media presence and generate sales leads without manual effort.

**Why this priority**: Automated business development through social media provides direct ROI. This feature generates sales opportunities while requiring minimal user effort. It's lower priority than core task detection and safety features but provides clear business value.

**Independent Test**: Can be tested by configuring business context in Company_Handbook, triggering post generation, reviewing the draft post in approval queue, and verifying successful posting to LinkedIn. Delivers value by automating social media marketing.

**Acceptance Scenarios**:

1. **Given** business context is configured in Company_Handbook, **When** the scheduled posting time arrives, **Then** the system generates a LinkedIn post draft with relevant content, hashtags, and mentions
2. **Given** a LinkedIn post draft has been generated, **When** it enters the approval queue, **Then** I can review the post content, edit if needed, and approve for posting
3. **Given** I have approved a LinkedIn post, **When** the system posts to LinkedIn, **Then** the post appears on my LinkedIn profile and post metadata is stored in the vault
4. **Given** posts have been published, **When** I check post history, **Then** I see performance metrics (views, likes, comments, shares) for each post
5. **Given** the posting schedule is configured for 2-3 times per week, **When** the system runs, **Then** posts are generated and scheduled at optimal times (business hours, weekdays)

---

### User Story 4 - Intelligent Planning with Plan.md Generation (Priority: P4)

As a user, I want the system to automatically create structured Plan.md files for complex multi-step tasks so that I have clear execution roadmaps and can understand the reasoning behind proposed solutions.

**Why this priority**: Planning capability adds intelligence and transparency to task execution. While valuable, it's not essential for basic functionality. Users can still process tasks without automated planning, making this an enhancement rather than core feature.

**Independent Test**: Can be tested by creating a complex task (>3 steps), verifying that a Plan.md file is generated with problem analysis, approach options, and execution steps. Delivers value by providing structured thinking for complex problems.

**Acceptance Scenarios**:

1. **Given** a task requires multiple steps to complete, **When** the system analyzes the task, **Then** it generates a Plan.md file with problem analysis, approach options with tradeoffs, and recommended solution
2. **Given** a Plan.md file has been created, **When** I review it, **Then** I see a step-by-step execution plan with success criteria and risk mitigation strategies
3. **Given** a plan is being executed, **When** steps are completed, **Then** the plan is updated with progress and outcomes
4. **Given** a plan needs revision based on feedback, **When** I provide input, **Then** the system updates the plan and maintains version history

---

### User Story 5 - Scheduled Task Automation (Priority: P5)

As a user, I want to schedule recurring tasks and automated actions so that routine work happens automatically without manual triggering.

**Why this priority**: Scheduling adds convenience and automation but is not essential for core functionality. Users can manually trigger tasks as needed. This is a quality-of-life enhancement that becomes more valuable as the system matures.

**Independent Test**: Can be tested by creating a scheduled task (e.g., daily report generation), verifying it executes at the scheduled time, and checking execution logs. Delivers value by automating routine work.

**Acceptance Scenarios**:

1. **Given** I want to automate a recurring task, **When** I create a schedule using cron syntax, **Then** the task executes automatically at the specified times
2. **Given** a scheduled task is configured, **When** the execution time arrives, **Then** the task runs and results are logged with execution timestamp
3. **Given** a scheduled task fails, **When** the failure is detected, **Then** the system retries according to retry policy and logs the failure
4. **Given** I want to manage schedules, **When** I use the schedule CLI commands, **Then** I can list, create, update, and delete schedules

---

### Edge Cases

- What happens when multiple channels receive the same task request (duplicate detection)?
- How does the system handle rate limits from Gmail, WhatsApp, or LinkedIn APIs?
- What happens when a watcher loses authentication (OAuth token expires)?
- How does the system handle conflicting approvals (multiple reviewers)?
- What happens when LinkedIn posting fails after approval?
- How does the system handle WhatsApp group messages vs direct messages?
- What happens when a scheduled task conflicts with a manual task?
- How does the system handle Plan.md generation for tasks that don't need planning?
- What happens when the approval queue grows too large (>100 pending items)?
- How does the system handle voice notes in WhatsApp (transcription)?

## Requirements *(mandatory)*

### Functional Requirements

**Multi-Channel Watchers**:
- **FR-001**: System MUST implement Gmail watcher that monitors inbox for new emails and classifies them as tasks or non-tasks
- **FR-002**: System MUST implement WhatsApp watcher that monitors messages and extracts task requests from conversational text
- **FR-003**: System MUST implement LinkedIn watcher that monitors messages, mentions, and relevant posts for task-related content
- **FR-004**: All watchers MUST run concurrently and independently without blocking each other
- **FR-005**: Each watcher MUST detect new content within 30 seconds of arrival
- **FR-006**: System MUST preserve channel-specific metadata (sender, message ID, thread ID, timestamp) in task files
- **FR-007**: System MUST handle authentication for each channel
- **FR-008**: System MUST handle rate limits gracefully for each platform with exponential backoff

**Content Classification**:
- **FR-009**: System MUST classify incoming content as: task, question, notification, spam, or other
- **FR-010**: System MUST extract priority level (P1/P2/P3) from content based on urgency indicators
- **FR-011**: System MUST extract task metadata (title, description, due date, category) from unstructured content
- **FR-012**: System MUST provide confidence scoring (0-100%) for classifications
- **FR-013**: System MUST support multi-language content (English, Urdu)

**LinkedIn Auto-Posting**:
- **FR-014**: System MUST generate LinkedIn post content based on business context from Company_Handbook
- **FR-015**: System MUST include relevant hashtags and mentions in generated posts
- **FR-016**: System MUST schedule posts at optimal times (business hours, weekdays)
- **FR-017**: System MUST maintain posting frequency of 2-3 times per week
- **FR-018**: System MUST track post performance metrics (views, likes, comments, shares)
- **FR-019**: System MUST store post history in vault with timestamps and performance data

**Plan.md Generation**:
- **FR-020**: System MUST detect complex tasks requiring multi-step execution (>3 steps)
- **FR-021**: System MUST generate Plan.md files with problem analysis, approach options, and recommended solution
- **FR-022**: System MUST include step-by-step execution plan with success criteria
- **FR-023**: System MUST include risk mitigation strategies in plans
- **FR-024**: System MUST support plan revisions based on feedback
- **FR-025**: System MUST link plans to original tasks

**MCP Server Integration**:
- **FR-026**: System MUST implement MCP (Model Context Protocol) server for external actions
- **FR-027**: MCP server MUST support email sending
- **FR-028**: MCP server MUST support LinkedIn posting
- **FR-029**: MCP server MUST support WhatsApp messaging
- **FR-030**: System MUST maintain tool registry with whitelisted actions
- **FR-031**: System MUST validate actions before execution
- **FR-032**: System MUST provide rollback capability for failed actions
- **FR-033**: System MUST log all MCP calls comprehensively
- **FR-034**: System MUST implement rate limiting per tool

**Human Approval Workflow**:
- **FR-035**: System MUST create approval queue for sensitive actions (email sends, LinkedIn posts, WhatsApp messages)
- **FR-036**: System MUST store pending actions in Needs_Approval folder with action details
- **FR-037**: System MUST provide CLI interface for listing pending approvals
- **FR-038**: System MUST allow users to view action details (what, why, impact, risk level)
- **FR-039**: System MUST support approve, reject, and edit operations for pending actions
- **FR-040**: System MUST support bulk approval for similar actions
- **FR-041**: System MUST store approval metadata (reviewer, timestamp, decision, notes)
- **FR-042**: System MUST auto-reject actions after 24-hour timeout
- **FR-043**: System MUST classify actions by risk level (low/medium/high)
- **FR-044**: System MUST log all approval decisions to audit trail

**Scheduling**:
- **FR-045**: System MUST support cron-like syntax for schedule definitions
- **FR-046**: System MUST integrate with Windows Task Scheduler (Windows) or cron (Linux/Mac)
- **FR-047**: System MUST support one-time, recurring (daily/weekly/monthly), and event-triggered schedules
- **FR-048**: System MUST provide CLI commands for schedule management (list, create, update, delete)
- **FR-049**: System MUST store schedules persistently in vault
- **FR-050**: System MUST log execution history for scheduled tasks
- **FR-051**: System MUST implement failure handling and retry logic for scheduled tasks

**Agent Skills Architecture**:
- **FR-052**: All AI functionality MUST be implemented as agent skills (command files)
- **FR-053**: System MUST implement /classify-email agent skill
- **FR-054**: System MUST implement /classify-whatsapp agent skill
- **FR-055**: System MUST implement /classify-linkedin agent skill
- **FR-056**: System MUST implement /generate-linkedin-post agent skill
- **FR-057**: System MUST implement /create-plan agent skill
- **FR-058**: System MUST implement /draft-email-reply agent skill
- **FR-059**: System MUST implement /draft-whatsapp-reply agent skill
- **FR-060**: System MUST implement /validate-action agent skill

**Bronze Phase Compatibility**:
- **FR-061**: All Bronze phase features MUST continue working (FileSystem watcher, Dashboard, Logs, Company_Handbook)
- **FR-062**: System MUST maintain local-first architecture with all state in Markdown files
- **FR-063**: System MUST follow constitution principles
- **FR-064**: System MUST maintain vault structure (Inbox, Needs_Action, Done, Logs, Company_Handbook, Needs_Approval)

### Key Entities

- **Task**: Work item from any channel. Attributes: task_id, title, description, priority, status, channel (filesystem/gmail/whatsapp/linkedin), channel_metadata (sender, message_id, thread_id), created_at, processed_at
- **Watcher**: Input channel monitor. Attributes: watcher_type (filesystem/gmail/whatsapp/linkedin), status (running/stopped/error), last_check_at, authentication_status
- **Approval**: Pending action requiring human review. Attributes: approval_id, action_type (send_email/post_linkedin/send_whatsapp), action_details, risk_level (low/medium/high), created_at, timeout_at, status (pending/approved/rejected/expired)
- **Schedule**: Recurring task definition. Attributes: schedule_id, cron_expression, task_template, enabled, last_run_at, next_run_at, execution_history
- **Plan**: Multi-step execution plan. Attributes: plan_id, task_reference, problem_analysis, approach_options, recommended_solution, execution_steps, success_criteria, risk_mitigation, version
- **LinkedInPost**: Published social media content. Attributes: post_id, content, hashtags, posted_at, performance_metrics (views, likes, comments, shares), approval_metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Multi-Channel Detection**:
- **SC-001**: System detects new content from Gmail, WhatsApp, and LinkedIn within 30 seconds of arrival
- **SC-002**: Content classification achieves 90%+ accuracy across all channels
- **SC-003**: System processes 100+ tasks per day across all channels without performance degradation
- **SC-004**: Zero data loss occurs during multi-channel processing

**Approval Workflow**:
- **SC-005**: Users can review and approve/reject actions in under 5 minutes
- **SC-006**: 100% of sensitive actions (email sends, LinkedIn posts, WhatsApp messages) require approval before execution
- **SC-007**: Approval decisions are logged with complete audit trail (who, when, what, why)
- **SC-008**: System handles approval queue of 50+ pending items without performance issues

**LinkedIn Auto-Posting**:
- **SC-009**: System generates and posts 2-3 LinkedIn posts per week automatically
- **SC-010**: Generated posts achieve 80%+ approval rate from human reviewers
- **SC-011**: Posts are published at optimal times (business hours, weekdays)
- **SC-012**: Post performance metrics are tracked and stored for all published content

**Planning Capability**:
- **SC-013**: System generates Plan.md files for 100% of complex tasks (>3 steps)
- **SC-014**: Generated plans include problem analysis, approach options, and execution steps
- **SC-015**: Plans are linked to original tasks and accessible for review

**Scheduling**:
- **SC-016**: Scheduled tasks execute with 99%+ reliability at specified times
- **SC-017**: Failed scheduled tasks are retried according to retry policy
- **SC-018**: Users can create, update, and delete schedules via CLI commands

**System Reliability**:
- **SC-019**: All Bronze phase features continue working without regression
- **SC-020**: System runs continuously for 7 days without crashes or manual intervention
- **SC-021**: System memory usage stays under 1GB during normal operation
- **SC-022**: Complete audit trail exists for all actions across all channels

### Assumptions

- Users have Gmail, WhatsApp, and LinkedIn accounts configured
- Users have necessary API credentials (Gmail API, LinkedIn API, WhatsApp Business API)
- OAuth2 tokens can be stored securely outside the vault
- Users will review approval queue at least once per day
- Business context in Company_Handbook is sufficient for LinkedIn post generation
- Users have permissions to post on LinkedIn on behalf of their business
- Cron or Task Scheduler is available on the host system
- Users understand cron syntax for schedule definitions
- WhatsApp Business API is accessible or web automation is permitted
- Network connectivity is reliable for API calls
- Users have Bronze phase already working and tested
- System has sufficient permissions to access email, WhatsApp, and LinkedIn
- Users want automated LinkedIn posting for business development
- Complex tasks requiring planning are identifiable (>3 steps)
- Users are comfortable with CLI interface for approvals

### Out of Scope

- Multi-user support (single user only)
- Web UI for approval workflow (CLI only)
- Advanced analytics and reporting dashboards
- Integration with CRM systems (Salesforce, HubSpot, etc.)
- Payment processing or e-commerce features
- Video content generation for LinkedIn
- Instagram, Twitter, Facebook, or TikTok integration
- Email template management UI
- Advanced AI training or fine-tuning
- Mobile app for approvals
- Real-time collaboration features
- Custom workflow builders
- Integration with project management tools (Jira, Asana)
- Voice call handling or transcription
- Calendar integration
- Document generation or editing
- Advanced security features (2FA, encryption at rest)

### Dependencies

- All Bronze phase dependencies (Python 3.9+, watchdog, python-frontmatter, markdown, python-dotenv, pytest)
- Gmail API access and OAuth2 credentials
- LinkedIn API access and OAuth2 credentials  
- WhatsApp Business API access or web automation capability (Selenium/Playwright)
- MCP protocol implementation library
- Scheduling system (cron on Linux/Mac, Task Scheduler on Windows)
- Secure token storage mechanism (OS keyring or encrypted file)
- Network connectivity for API calls
- Bronze phase fully implemented and working
- Existing vault structure (Inbox, Needs_Action, Done, Logs, Company_Handbook)
- Existing BaseWatcher interface from Bronze phase
- Existing agent skills infrastructure from Bronze phase
- Claude Code CLI for agent skill execution

### Constraints

- Must maintain local-first architecture (emails/messages cached locally as Markdown)
- Must follow constitution principles (human-in-the-loop for risk actions, Markdown as state, no hidden state)
- Must be compatible with existing Bronze phase code without breaking changes
- Must use agent skills for all AI functionality (no direct AI calls in Python code)
- Must inherit from BaseWatcher interface for all watchers
- OAuth2 tokens must be stored securely (not in vault, not in git)
- Rate limits must be respected for all external APIs (Gmail, LinkedIn, WhatsApp)
- Approval workflow must not be bypassable (no backdoor for sensitive actions)
- All external actions must go through MCP server (no direct API calls from orchestrator)
- System must work offline for local tasks (Bronze phase functionality must remain available)
- Must support Windows, macOS, and Linux
- Must run on single machine (no distributed architecture)
- Memory usage must stay under 1GB during normal operation
- Must handle 100+ tasks per day across all channels
- Approval queue must support at least 50 pending items
- Must maintain backward compatibility with Bronze phase task files

# Feature Specification: Platinum Tier AI Employee

**Feature Branch**: `001-platinum-employee`
**Created**: 2026-02-25
**Status**: Draft
**Input**: User description: "Platinum Tier: Always-On Cloud + Local Executive (Production-ish AI Employee) - A comprehensive AI employee system with cloud-based 24/7 watchers, local executive for approvals, synced vault architecture, Odoo integration, and human-in-the-loop safety mechanisms."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Autonomous Email Handling While Offline (Priority: P1)

As a business owner, I need my AI employee to monitor and draft responses to important emails even when my local machine is offline, so that I can maintain timely communication with clients without being constantly available.

**Why this priority**: This is the core value proposition of the Platinum tier - always-on availability that extends beyond local machine uptime. It directly addresses the pain point of missed opportunities due to delayed responses.

**Independent Test**: Can be fully tested by sending an email to the monitored account while the local machine is powered off, verifying that a draft response is created in the approval queue, and confirming that the user can approve and send it when they return online. Delivers immediate value by ensuring no email goes unnoticed.

**Acceptance Scenarios**:

1. **Given** local machine is offline and cloud agent is running, **When** an important email arrives in Gmail, **Then** cloud agent detects the email within 2 minutes and creates an action file in the synced vault
2. **Given** cloud agent has detected an email, **When** it analyzes the content and context, **Then** it drafts an appropriate reply and writes it to the Pending_Approval folder with all necessary metadata
3. **Given** a draft reply is in Pending_Approval, **When** local machine comes online and syncs the vault, **Then** user sees the pending approval notification with email context and draft response
4. **Given** user reviews the draft, **When** they move the approval file to the Approved folder, **Then** local agent sends the email via the email service and logs the action
5. **Given** the email is sent, **When** the action completes, **Then** all related files move to Done folder and Dashboard is updated with the activity

---

### User Story 2 - Social Media Content Scheduling with Approval (Priority: P2)

As a business owner, I need my AI employee to draft and schedule social media posts based on my business goals and calendar, but require my approval before anything is published, so that I maintain brand control while reducing content creation workload.

**Why this priority**: Social media presence is important for business growth but time-consuming. This provides significant time savings while maintaining quality control through the approval workflow.

**Independent Test**: Can be tested by configuring business goals and content calendar, verifying that cloud agent generates post drafts at scheduled times, and confirming that posts only publish after local approval. Delivers value by automating content creation while preserving brand safety.

**Acceptance Scenarios**:

1. **Given** business goals and content calendar are configured, **When** a scheduled post time arrives, **Then** cloud agent generates a draft post based on recent business activities and goals
2. **Given** a draft post is created, **When** cloud agent writes it to Pending_Approval/social, **Then** the draft includes post content, target platform, suggested timing, and relevant context
3. **Given** user reviews the draft post, **When** they approve it by moving to Approved folder, **Then** local agent publishes the post to the specified platform and logs the action
4. **Given** user rejects a draft, **When** they move it to Rejected folder with feedback, **Then** cloud agent learns from the feedback for future drafts
5. **Given** multiple posts are pending, **When** user is offline for extended period, **Then** cloud agent continues drafting but never publishes without approval

---

### User Story 3 - Financial Transaction Monitoring and Invoice Management (Priority: P2)

As a business owner, I need my AI employee to monitor bank transactions, detect invoice-related activities, and draft accounting entries in my ERP system, so that my financial records stay current without manual data entry.

**Why this priority**: Financial accuracy is critical for business operations. Automating transaction monitoring and draft entries saves significant time while the approval workflow ensures accuracy before posting to official records.

**Independent Test**: Can be tested by simulating a bank transaction, verifying that the finance watcher detects it, cloud agent drafts an Odoo accounting entry, and confirming that the entry only posts after local approval. Delivers value by maintaining real-time financial visibility.

**Acceptance Scenarios**:

1. **Given** finance watcher is monitoring bank account, **When** a new transaction appears, **Then** watcher creates an action file with transaction details within 5 minutes
2. **Given** transaction is detected, **When** cloud agent analyzes it against business context, **Then** it drafts an appropriate Odoo accounting entry (invoice, payment, expense)
3. **Given** draft accounting entry is created, **When** cloud agent writes it to Pending_Approval/accounting, **Then** the draft includes transaction details, suggested account codes, and supporting documentation
4. **Given** user reviews the draft entry, **When** they approve it, **Then** local agent posts the entry to Odoo via the accounting integration and updates financial dashboard
5. **Given** a payment over the approval threshold is detected, **When** cloud agent processes it, **Then** it always requires approval regardless of confidence level

---

### User Story 4 - WhatsApp Business Communication (Priority: P3)

As a business owner, I need my AI employee to monitor WhatsApp messages for urgent keywords and draft responses, but keep the WhatsApp session and sending capability on my local machine for security, so that I can respond quickly to clients while maintaining message security.

**Why this priority**: WhatsApp is increasingly used for business communication. This provides quick response capability while respecting the security constraints of WhatsApp Web sessions.

**Independent Test**: Can be tested by sending a WhatsApp message with an urgent keyword, verifying that the watcher detects it, cloud agent drafts a response, and confirming that the message only sends from the local machine after approval. Delivers value by ensuring urgent messages get timely attention.

**Acceptance Scenarios**:

1. **Given** WhatsApp watcher is running on local machine, **When** a message arrives with urgent keywords (invoice, payment, urgent, asap, help), **Then** watcher creates an action file within 30 seconds
2. **Given** urgent message is detected, **When** cloud agent analyzes the message context, **Then** it drafts an appropriate response based on business rules and conversation history
3. **Given** draft response is created, **When** cloud agent writes it to Pending_Approval/whatsapp, **Then** the draft includes original message, sender context, and suggested reply
4. **Given** user approves the response, **When** local agent processes the approval, **Then** it sends the message via WhatsApp Web session and logs the interaction
5. **Given** WhatsApp session expires, **When** local agent attempts to send, **Then** it notifies user to re-authenticate and queues the message for retry

---

### User Story 5 - Autonomous Business Audit and Briefing (Priority: P3)

As a business owner, I need my AI employee to analyze my weekly business activities, financial transactions, and task completion, then generate a comprehensive briefing with insights and recommendations, so that I can make informed decisions without manual data analysis.

**Why this priority**: Strategic insights are valuable but time-consuming to generate. This provides proactive business intelligence that helps identify opportunities and issues early.

**Independent Test**: Can be tested by running the scheduled audit process, verifying that it analyzes data from multiple sources (tasks, transactions, goals), and confirming that it generates a comprehensive briefing with actionable recommendations. Delivers value by providing business intelligence without manual effort.

**Acceptance Scenarios**:

1. **Given** scheduled audit time arrives (e.g., Sunday night), **When** cloud agent triggers the audit process, **Then** it reads Business_Goals, completed tasks, and financial transactions for the period
2. **Given** data is collected, **When** cloud agent analyzes it, **Then** it identifies revenue trends, bottlenecks, cost optimization opportunities, and upcoming deadlines
3. **Given** analysis is complete, **When** cloud agent generates the briefing, **Then** it creates a structured report with executive summary, metrics, bottlenecks, and proactive suggestions
4. **Given** briefing is generated, **When** local machine syncs, **Then** user sees the briefing in their dashboard on Monday morning
5. **Given** briefing includes cost optimization suggestions, **When** cloud agent identifies unused subscriptions, **Then** it creates approval requests for cancellation with supporting data

---

### Edge Cases

- **What happens when vault sync fails?** Cloud agent continues operating and queues updates locally; local agent operates on last known state; system alerts user to sync failure and provides manual sync instructions
- **What happens when both agents try to claim the same task?** Claim-by-move rule ensures first agent to move file from Needs_Action to In_Progress owns it; second agent sees file is gone and skips it
- **What happens when cloud agent is down?** Local agent continues operating independently; watchers on local machine continue collecting data; cloud-specific features (24/7 monitoring) are unavailable until cloud agent restarts
- **What happens when local agent is offline for extended period?** Cloud agent continues drafting and queuing approvals; no sensitive actions (payments, final sends) occur; user sees backlog of pending approvals when they return online
- **What happens when Odoo server is unreachable?** Cloud agent queues draft accounting entries locally; system retries with exponential backoff; user is notified of integration failure; manual posting option is available
- **What happens when approval expires?** System moves expired approval to a separate folder; user is notified of expiration; cloud agent may regenerate draft with updated context if still relevant
- **What happens when user rejects multiple drafts of the same type?** Cloud agent learns from rejection patterns; adjusts drafting strategy; may request explicit guidance for that category
- **What happens when secrets accidentally get committed to vault?** Pre-commit hooks prevent secret files from being added; .gitignore blocks common secret patterns; system alerts user if secret-like content is detected
- **What happens when WhatsApp Web session is active on multiple devices?** System detects session conflict; pauses WhatsApp operations; alerts user to resolve device conflict
- **What happens during vault merge conflicts?** System prioritizes local agent writes for Dashboard; uses last-write-wins for other files; alerts user to manual resolution if critical files conflict

## Requirements *(mandatory)*

### Functional Requirements

#### Core Architecture

- **FR-001**: System MUST operate with two independent agents: cloud agent (always-on) and local agent (user machine)
- **FR-002**: System MUST synchronize state between agents using a shared vault containing only markdown files and state data
- **FR-003**: System MUST never synchronize secrets, credentials, tokens, or session data to the shared vault
- **FR-004**: System MUST implement claim-by-move rule where first agent to move a file from Needs_Action to In_Progress owns that task
- **FR-005**: System MUST enforce single-writer rule for Dashboard.md (local agent only) with cloud agent writing to Updates folder for local merge

#### Cloud Agent Capabilities

- **FR-006**: Cloud agent MUST run continuously (24/7) on a cloud virtual machine
- **FR-007**: Cloud agent MUST monitor Gmail for new messages and create action files within 2 minutes of receipt
- **FR-008**: Cloud agent MUST draft email replies based on message content, sender context, and business rules
- **FR-009**: Cloud agent MUST draft social media posts based on business goals and content calendar
- **FR-010**: Cloud agent MUST schedule social media posts but never publish without local approval
- **FR-011**: Cloud agent MUST draft accounting entries for Odoo based on detected financial transactions
- **FR-012**: Cloud agent MUST never post financial entries to Odoo without local approval
- **FR-013**: Cloud agent MUST write all draft actions to Pending_Approval folder with complete context and metadata
- **FR-014**: Cloud agent MUST perform scheduled business audits and generate briefings
- **FR-015**: Cloud agent MUST operate independently when local agent is offline

#### Local Agent Capabilities

- **FR-016**: Local agent MUST handle all approval workflows for sensitive actions
- **FR-017**: Local agent MUST maintain exclusive access to WhatsApp Web sessions
- **FR-018**: Local agent MUST maintain exclusive access to payment and banking credentials
- **FR-019**: Local agent MUST execute all final "send" and "post" actions after approval
- **FR-020**: Local agent MUST be the only writer to Dashboard.md
- **FR-021**: Local agent MUST merge updates from cloud agent's Updates folder into Dashboard
- **FR-022**: Local agent MUST log all executed actions with timestamp, actor, target, and result
- **FR-023**: Local agent MUST send emails via configured email service after approval
- **FR-024**: Local agent MUST post to social media platforms after approval
- **FR-025**: Local agent MUST post accounting entries to Odoo after approval

#### Watcher System

- **FR-026**: System MUST implement Gmail watcher that monitors for unread important messages
- **FR-027**: System MUST implement WhatsApp watcher that monitors for messages with urgent keywords
- **FR-028**: System MUST implement finance watcher that monitors bank transactions
- **FR-029**: Gmail watcher MUST run on cloud agent for 24/7 monitoring
- **FR-030**: WhatsApp watcher MUST run on local agent due to session requirements
- **FR-031**: Finance watcher MUST run on local agent due to credential requirements
- **FR-032**: Each watcher MUST create action files in Needs_Action folder with standardized metadata
- **FR-033**: Watchers MUST track processed items to avoid duplicate action files
- **FR-034**: Watchers MUST implement configurable check intervals (default: 30-120 seconds)

#### Vault Structure and Synchronization

- **FR-035**: System MUST organize vault with folders: Needs_Action, In_Progress, Pending_Approval, Approved, Rejected, Done, Plans, Logs, Updates
- **FR-036**: System MUST support domain-specific subfolders (email, social, accounting, whatsapp) under main folders
- **FR-037**: System MUST support agent-specific subfolders under In_Progress (cloud, local)
- **FR-038**: System MUST synchronize vault using Git or Syncthing
- **FR-039**: System MUST implement .gitignore rules to prevent secret synchronization
- **FR-040**: System MUST handle vault sync failures gracefully with local queuing and user notification

#### Approval Workflow

- **FR-041**: System MUST create approval request files with action type, target, parameters, reason, created timestamp, and expiration
- **FR-042**: System MUST support approval by moving file from Pending_Approval to Approved folder
- **FR-043**: System MUST support rejection by moving file from Pending_Approval to Rejected folder
- **FR-044**: System MUST execute approved actions within 1 minute of approval
- **FR-045**: System MUST move expired approvals to separate folder and notify user
- **FR-046**: System MUST require approval for all new email recipients
- **FR-047**: System MUST require approval for all payments regardless of amount
- **FR-048**: System MUST require approval for all social media posts
- **FR-049**: System MUST require approval for all accounting entries

#### Odoo Integration

- **FR-051**: System MUST deploy Odoo Community Edition on cloud virtual machine
- **FR-052**: System MUST configure Odoo with HTTPS access
- **FR-053**: System MUST implement automated backups of Odoo database
- **FR-054**: System MUST implement health monitoring for Odoo service
- **FR-055**: System MUST integrate with Odoo via JSON-RPC API
- **FR-056**: Cloud agent MUST draft accounting entries (invoices, payments, expenses) in Odoo
- **FR-057**: Local agent MUST post approved accounting entries to Odoo
- **FR-058**: System MUST validate accounting entries before posting
- **FR-059**: System MUST log all Odoo operations with transaction details

#### Orchestration and Process Management

- **FR-060**: System MUST implement orchestrator process for scheduling and folder watching
- **FR-061**: System MUST implement watchdog process for health monitoring and restart
- **FR-062**: Orchestrator MUST monitor Needs_Action folder and trigger agent processing
- **FR-063**: Orchestrator MUST monitor Approved folder and trigger action execution
- **FR-064**: Orchestrator MUST implement scheduled tasks (daily briefings, weekly audits)
- **FR-065**: Watchdog MUST monitor critical processes (orchestrator, watchers, agents)
- **FR-066**: Watchdog MUST restart failed processes automatically
- **FR-067**: Watchdog MUST log process failures and restarts
- **FR-068**: Watchdog MUST notify user of repeated failures (3+ restarts within 1 hour)

#### Security and Audit

- **FR-069**: System MUST store all credentials in environment variables or secure credential managers
- **FR-070**: System MUST never commit credentials to version control
- **FR-071**: System MUST implement audit logging for all actions with JSON format
- **FR-072**: System MUST retain audit logs for minimum 90 days
- **FR-073**: System MUST log: timestamp, action_type, actor, target, parameters, approval_status, approved_by, result
- **FR-074**: System MUST implement rate limiting (max 10 emails/hour, max 3 payments/hour)
- **FR-075**: System MUST support development mode that prevents real external actions
- **FR-076**: System MUST support dry-run mode for testing without execution

#### Error Handling and Recovery

- **FR-077**: System MUST implement retry logic with exponential backoff for transient errors
- **FR-078**: System MUST implement maximum retry attempts (default: 3)
- **FR-079**: System MUST quarantine corrupted files and alert user
- **FR-080**: System MUST queue operations when external services are unavailable
- **FR-081**: System MUST alert user when authentication tokens expire
- **FR-082**: System MUST pause operations when critical errors occur
- **FR-083**: System MUST provide manual recovery options for failed operations

#### Dashboard and Reporting

- **FR-084**: System MUST maintain Dashboard.md with real-time activity summary
- **FR-085**: Dashboard MUST show recent activities with timestamps
- **FR-086**: Dashboard MUST show pending approvals count by category
- **FR-087**: Dashboard MUST show system health status (agents, watchers, integrations)
- **FR-088**: System MUST generate weekly business briefings with revenue, bottlenecks, and recommendations
- **FR-089**: System MUST identify cost optimization opportunities (unused subscriptions)
- **FR-090**: System MUST track upcoming deadlines from business goals

### Key Entities

- **Action File**: Represents a detected event requiring processing; contains type (email, whatsapp, transaction, file_drop), source metadata, priority, status, and suggested actions
- **Approval Request**: Represents a draft action requiring human approval; contains action type, target, parameters, reason, created timestamp, expiration, and approval status
- **Agent**: Represents a processing entity (cloud or local); has capabilities, running status, last heartbeat, and claimed tasks
- **Watcher**: Represents a monitoring process; has source (gmail, whatsapp, bank), check interval, last check timestamp, and processed item IDs
- **Business Goal**: Represents strategic objectives; contains revenue targets, key metrics, active projects, and alert thresholds
- **Audit Log Entry**: Represents a completed action; contains timestamp, action type, actor, target, parameters, approval status, approver, and result
- **Dashboard State**: Represents current system status; contains recent activities, pending approvals, system health, and key metrics
- **Odoo Entry**: Represents a financial transaction; contains entry type (invoice, payment, expense), amount, account codes, and supporting documentation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cloud agent detects and drafts responses to important emails within 5 minutes of receipt, even when local machine is offline
- **SC-002**: User can review and approve pending actions within 30 seconds of opening the dashboard
- **SC-003**: System successfully handles 100+ emails per day with 95% draft quality (requiring minimal edits)
- **SC-004**: System maintains 99.9% uptime for cloud agent monitoring (less than 9 hours downtime per year)
- **SC-005**: Vault synchronization completes within 10 seconds for typical updates (under 100 files)
- **SC-006**: Zero unauthorized actions occur (100% compliance with approval workflow)
- **SC-007**: System reduces email response time by 80% compared to manual handling
- **SC-008**: System reduces social media content creation time by 70%
- **SC-009**: System reduces financial data entry time by 90%
- **SC-010**: User spends less than 30 minutes per day on approval workflows
- **SC-011**: System generates weekly business briefings with 90% accuracy in identifying bottlenecks and opportunities
- **SC-012**: System successfully recovers from transient failures (network, API) without user intervention in 95% of cases
- **SC-013**: Watchdog successfully restarts failed processes within 60 seconds of detection
- **SC-014**: System maintains complete audit trail with zero gaps in logging
- **SC-015**: User can demonstrate complete end-to-end flow (email arrival → draft → approval → send) in under 5 minutes

## Assumptions

- User has access to a cloud virtual machine (Oracle Cloud Free Tier or equivalent) for deploying cloud agent and Odoo
- User has Gmail account with API access enabled
- User has WhatsApp Web access on local machine
- User has bank account with transaction export capability (CSV or API)
- User has basic understanding of Git for vault synchronization
- User's business operates primarily in English language
- User has Obsidian or compatible markdown editor for viewing vault
- User's local machine runs Windows, macOS, or Linux
- User has Node.js and Python installed for running MCP servers and watchers
- User has stable internet connection on both cloud and local machines
- User's email volume is under 500 messages per day
- User's social media posting frequency is under 10 posts per day
- User's financial transactions are under 100 per day
- User is willing to review and approve actions daily (not suitable for extended absences without approval)
- User has legal right to automate communications on behalf of their business

## Dependencies

- **External Services**: Gmail API, WhatsApp Web, Banking API/CSV export, Social media platform APIs (Facebook, Instagram, Twitter, LinkedIn)
- **Infrastructure**: Cloud VM provider (Oracle Cloud, AWS, Azure, GCP), Git hosting (GitHub, GitLab) or Syncthing
- **Software**: Odoo Community Edition v19+, Python 3.9+, Node.js 18+, Git, Playwright
- **MCP Servers**: Email MCP, Browser MCP, Accounting MCP (custom for Odoo), Social Media MCP
- **Libraries**: watchdog (Python), APScheduler (Python), odoorpc (Python), google-auth (Python), playwright (Python), tenacity (Python), pybreaker (Python)
- **Local Tools**: Obsidian (recommended) or any markdown editor, Claude Code CLI
- **Existing Features**: Gold Tier features (local watchers, orchestrator, MCP integration, Ralph Wiggum loop)

## Out of Scope

- Multi-user support (single business owner only)
- Mobile app interface (vault access via file sync only)
- Voice/audio message handling (text-based only)
- Video content creation or editing
- Real-time chat/messaging (asynchronous only)
- Automated contract signing or legal document generation
- Medical or health-related decision making
- Automated hiring or HR decisions
- Automated financial trading or investment decisions
- Multi-language support beyond English (Phase 1)
- Agent-to-Agent direct messaging (Phase 1 - file-based only, A2A is Phase 2)
- Custom AI model training or fine-tuning
- Integration with ERP systems other than Odoo
- Blockchain or cryptocurrency operations
- Automated tax filing or regulatory compliance
- Customer support ticket system integration (Phase 1)
- CRM system integration beyond basic contact management (Phase 1)
- Automated legal advice or compliance checking
- Automated medical diagnosis or health recommendations

## Notes

This specification represents the Platinum Tier of the AI Employee system, building upon Bronze (local foundation), Silver (scheduled operations), and Gold (autonomous operations with error recovery) tiers. The key differentiator is the always-on cloud agent that provides 24/7 monitoring and drafting capabilities while maintaining strict security boundaries through the approval workflow and local-only sensitive operations.

The architecture prioritizes safety through multiple layers:
1. Cloud agent can only draft, never execute sensitive actions
2. All sensitive credentials and sessions remain local-only
3. Approval workflow prevents unauthorized actions
4. Audit logging provides complete traceability
5. Claim-by-move rule prevents duplicate work
6. Vault sync excludes all secrets

The system is designed for gradual rollout:
- Phase 1: File-based communication via synced vault
- Phase 2: Optional Agent-to-Agent direct messaging while maintaining vault as audit record

Success depends on user discipline in daily approval reviews and proper security configuration (secrets management, .gitignore rules, credential rotation).

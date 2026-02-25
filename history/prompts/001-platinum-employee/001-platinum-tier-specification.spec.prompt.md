---
id: 001
title: Platinum Tier AI Employee Specification
stage: spec
date: 2026-02-25
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-platinum-employee
branch: 001-platinum-employee
user: admin
command: /sp.specify
labels: ["platinum-tier", "cloud-agent", "local-agent", "vault-sync", "odoo-integration", "approval-workflow", "always-on"]
links:
  spec: specs/001-platinum-employee/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-platinum-employee/spec.md
  - specs/001-platinum-employee/checklists/requirements.md
tests:
  - Specification validation checklist (all items passed)
---

## Prompt

/sp.specify Platinum Tier: Always-On Cloud + Local Executive (Production-ish AI Employee)
Estimated time: 60+ hours
All Gold requirements plus:
Run the AI Employee on Cloud 24/7 (always-on watchers + orchestrator + health monitoring). You can deploy a Cloud VM (Oracle/AWS/etc.) - Oracle Cloud Free VMs can be used for this (subject to limits/availability).
Work-Zone Specialization (domain ownership):
Cloud owns: Email triage + draft replies + social post drafts/scheduling (draft-only; requires Local approval before send/post)
Local owns: approvals, WhatsApp session, payments/banking, and final "send/post" actions
Delegation via Synced Vault (Phase 1)
Agents communicate by writing files into:
/Needs_Action/<domain>/, /Plans/<domain>/, /Pending_Approval/<domain>/
Prevent double-work using:
/In_Progress/<agent>/ claim-by-move rule
single-writer rule for Dashboard.md (Local)
Cloud writes updates to /Updates/ (or /Signals/), and Local merges them into Dashboard.md.
For Vault sync (Phase 1) use Git (recommended) or Syncthing.
Claim-by-move rule: first agent to move an item from /Needs_Action to /In_Progress/<agent>/ owns it; other agents must ignore it.
Security rule: Vault sync includes only markdown/state. Secrets never sync (.env, tokens, WhatsApp sessions, banking creds). So Cloud never stores or uses WhatsApp sessions, banking credentials, or payment tokens.
Deploy Odoo Community on a Cloud VM (24/7) with HTTPS, backups, and health monitoring; integrate Cloud Agent with Odoo via MCP for draft-only accounting actions and Local approval for posting invoices/payments.
Optional A2A Upgrade (Phase 2): Replace some file handoffs with direct A2A messages later, while keeping the vault as the audit record
Platinum demo (minimum passing gate): Email arrives while Local is offline → Cloud drafts reply + writes approval file → when Local returns, user approves → Local executes send via MCP → logs → moves task to /Done.

## Response snapshot

Created comprehensive specification for Platinum Tier AI Employee system with:

**Architecture**: Dual-agent system (cloud always-on + local executive) with synced vault for state management and strict security boundaries.

**5 Prioritized User Stories**:
- P1: Autonomous Email Handling While Offline (core value proposition)
- P2: Social Media Content Scheduling with Approval
- P2: Financial Transaction Monitoring and Invoice Management
- P3: WhatsApp Business Communication
- P3: Autonomous Business Audit and Briefing

**90 Functional Requirements** organized across 10 architectural domains:
- Core Architecture (FR-001 to FR-005): Dual agents, vault sync, security boundaries
- Cloud Agent Capabilities (FR-006 to FR-015): 24/7 monitoring, drafting, scheduling
- Local Agent Capabilities (FR-016 to FR-025): Approvals, sensitive operations, final actions
- Watcher System (FR-026 to FR-034): Gmail, WhatsApp, finance monitoring
- Vault Structure (FR-035 to FR-040): Folder organization, sync, security
- Approval Workflow (FR-041 to FR-050): HITL safety mechanisms
- Odoo Integration (FR-051 to FR-059): ERP deployment and accounting
- Orchestration (FR-060 to FR-068): Process management and health monitoring
- Security and Audit (FR-069 to FR-076): Credentials, logging, rate limiting
- Error Handling (FR-077 to FR-083): Retry logic, recovery, queuing
- Dashboard and Reporting (FR-084 to FR-090): Activity tracking, briefings

**15 Measurable Success Criteria**: All technology-agnostic, covering performance (5-minute email detection, 10-second vault sync), compliance (zero unauthorized actions), efficiency gains (80% email response time reduction, 70% social media time reduction, 90% financial data entry reduction), reliability (99.9% uptime, 95% automatic recovery), and user experience (30-second approval review, under 30 minutes daily approval time).

**Security Architecture**: Multi-layered safety with cloud draft-only operations, local-only sensitive credentials, approval workflow for all actions, complete audit logging, claim-by-move rule for task ownership, and vault sync exclusion of all secrets.

**Validation**: Created requirements checklist with all items passing. Specification is ready for planning phase with no clarifications needed.

## Outcome

- ✅ Impact: Complete specification for Platinum Tier AI Employee with comprehensive requirements, user stories, success criteria, and security architecture. Ready for planning phase.
- 🧪 Tests: Specification validation checklist created and passed (14/14 items). All requirements testable and unambiguous.
- 📁 Files: Created spec.md (338 lines, 90 requirements) and requirements.md checklist (144 lines). Committed to branch 001-platinum-employee.
- 🔁 Next prompts: Run /sp.plan to generate implementation plan, or /sp.clarify to explore alternative approaches (optional)
- 🧠 Reflection: Successfully created a production-ready specification that balances ambitious functionality (24/7 cloud monitoring, multi-domain automation) with strict security boundaries (local-only secrets, approval workflows, audit logging). The dual-agent architecture with synced vault provides clear separation of concerns while maintaining operational flexibility.

## Evaluation notes (flywheel)

- Failure modes observed: None. Specification creation completed successfully without clarifications needed.
- Graders run and results (PASS/FAIL): Specification validation checklist - PASS (14/14 items). Content quality: PASS. Requirement completeness: PASS. Feature readiness: PASS.
- Prompt variant (if applicable): Standard /sp.specify workflow with comprehensive hackathon documentation input
- Next experiment (smallest change to try): Consider adding explicit performance benchmarks for vault sync under high load (100+ files, 1000+ files) to validate 10-second success criterion

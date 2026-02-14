---
id: 001
title: Initial AI Employee System Constitution
stage: constitution
date: 2026-02-14
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: master
user: admin
command: /sp.constitution
labels: ["constitution", "hackathon", "ai-employee", "local-first", "phased-development"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution document)
---

## Prompt

Personal AI Employee Hackathon 2026 – Autonomous FTE System
 # Personal AI Employee Hackathon 2026
## Building Autonomous Full-Time Equivalent (FTE) Systems

---

# 1. Vision

Create a Local-First Autonomous AI Employee capable of:

- Perceiving inputs from multiple channels
- Reasoning over structured company knowledge
- Acting safely through defined tools
- Maintaining audit logs
- Escalating to humans when needed

The system must evolve in phases:
Bronze → Silver → Gold → Platinum

Each phase must be independently functional.

---

# 2. Core Philosophy

1. Local-First by default
2. Human-in-the-Loop for risk actions
3. Markdown as system memory
4. Modular watchers
5. Clear perception → reasoning → action loop
6. No hidden state

---

# 3. System Architecture

Perception Layer:
- FileSystem Watcher
- Gmail Watcher (future)
- WhatsApp Watcher (future)

Reasoning Layer:
- Claude Code task processor
- Structured task parsing
- Priority classification

Action Layer:
- File operations
- Draft generation
- Structured outputs
- External integrations (later phases)

Memory Layer:
- Obsidian Vault
- Dashboard
- Logs
- Company Handbook

Security Layer:
- Credential isolation
- No plaintext secrets
- Action logging

---

# 4. Phase Breakdown

========================
BRONZE – Local Foundation
========================

Scope:
- Local Obsidian vault
- Inbox → Needs_Action → Done workflow
- FileSystem watcher
- Claude processes Markdown tasks
- Dashboard auto-updates

Deliverables:
- Folder structure
- base_watcher.py
- filesystem_watcher.py
- orchestrator.py
- README
- Logging system

Success Criteria:
File dropped in Inbox triggers full processing loop.

No external APIs allowed.

---

========================
SILVER – Multi-Channel Perception
========================

Add:
- Gmail integration
- Email classification
- Automatic draft replies
- Task prioritization
- Structured tagging

Must maintain:
- Bronze stability
- Human approval before sending emails

---

========================
GOLD – Tool Execution Layer
========================

Add:
- MCP server integration
- Structured tool registry
- Safe tool calling
- Action validation
- Role-based permission model

AI can:
- Trigger workflows
- Generate documents
- Execute pre-approved actions

Must include:
- Audit logs
- Rollback capability

---

========================
PLATINUM – Autonomous Business Agent
========================

Add:
- Ralph Wiggum loop (self-correction cycle)
- Performance metrics
- Self-improvement logs
- Multi-agent coordination
- Deployment configuration

System should:
- Identify inefficiencies
- Suggest process improvements
- Maintain operational memory

---

# 5. Safety Constraints

- No destructive file operations outside vault
- All actions logged
- Email sending requires approval
- External tool calls must be whitelisted
- Secrets must use environment variables

---

# 6. Definition of Hackathon Completion

Hackathon is complete when:

1. Bronze fully stable
2. Silver multi-channel works with HITL
3. Gold tool execution works safely
4. Platinum demonstrates self-improvement loop
5. End-to-end demo possible in under 5 minutes

---

# 7. Required Outputs From SpecKit

SpecKit must generate:

- Phased technical specs
- Folder structures per phase
- Implementation tasks
- Risk analysis
- Testing strategy
- Demo script
- Final presentation outline

---

This system must be modular, extensible, and production-minded.

## Response snapshot

Created Personal AI Employee System Constitution v1.0.0 with 8 core principles:

1. Local-First Architecture - System operates locally by default, no external API dependencies for core functionality
2. Human-in-the-Loop for Risk Actions - Explicit approval required for emails, external tools, destructive operations
3. Markdown as System Memory - All state stored as human-readable Markdown in Obsidian vault
4. Modular Watcher Architecture - Independent, pluggable perception modules (FileSystem, Gmail, WhatsApp)
5. Clear Perception → Reasoning → Action Loop - Explicit three-stage pipeline, no bypassing
6. No Hidden State - All behavior deterministic and traceable through Markdown files
7. Phased Development with Independent Functionality - Bronze → Silver → Gold → Platinum, each phase standalone
8. Safety-First Constraints - Strict boundaries on file operations, logging, approvals, whitelisting

Additional sections defined:
- Vault Structure Requirements (Inbox/Needs_Action/Done workflow)
- Watcher Interface Contract (start/stop/get_new_tasks/mark_processed)
- Claude Code Integration (task parsing, classification, action planning)
- Action Execution Policy (Safe/Approval Required/Forbidden categories)
- Logging and Audit Requirements (ISO timestamps, append-only logs)
- Phase Completion Criteria (specific deliverables for each phase)
- Testing Requirements (unit/integration/e2e/regression per phase)
- Security Requirements (env vars, no plaintext secrets, path validation)
- Performance Standards (2s file detection, 30s task processing, 500MB memory)
- Governance (amendment process, compliance verification, semantic versioning)

Constitution written to `.specify/memory/constitution.md` with Sync Impact Report prepended.

## Outcome

- ✅ Impact: Project constitution established, defines all architectural principles and constraints for hackathon development
- 🧪 Tests: N/A (constitution is governance document, not code)
- 📁 Files: Created .specify/memory/constitution.md (v1.0.0)
- 🔁 Next prompts: /sp.specify to create Bronze phase feature spec, /sp.plan for Bronze architecture
- 🧠 Reflection: Constitution successfully captures local-first, safety-first, phased development philosophy. All 8 principles are testable and enforceable. Phase completion criteria provide clear hackathon milestones.

## Evaluation notes (flywheel)

- Failure modes observed: None - constitution creation successful
- Graders run and results (PASS/FAIL): Manual review - PASS (all placeholders filled, principles clear and testable)
- Prompt variant (if applicable): N/A (initial constitution)
- Next experiment (smallest change to try): Validate constitution principles during Bronze phase spec creation to ensure alignment

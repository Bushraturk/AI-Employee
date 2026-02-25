# ADR-001: Dual-Agent Architecture with Cloud Drafting and Local Execution

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Accepted
- **Date:** 2026-02-25
- **Feature:** platinum-employee
- **Context:** The Platinum Tier AI Employee requires 24/7 monitoring and response capabilities even when the user's local machine is offline. This creates a fundamental architectural challenge: how to provide always-on availability while maintaining security boundaries and keeping sensitive credentials local-only. The system must handle email monitoring, social media posting, financial transactions, and WhatsApp messaging - all requiring different security postures.

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? YES - Defines entire system architecture
     2) Alternatives: Multiple viable options considered with tradeoffs? YES - Single cloud, single local, direct messaging
     3) Scope: Cross-cutting concern (not an isolated detail)? YES - Affects all components, deployment, security
     If any are false, prefer capturing as a PHR note instead of an ADR. -->

## Decision

Implement a dual-agent distributed system with the following architecture:

- **Cloud Agent**: Runs 24/7 on cloud VM (Oracle Cloud Free Tier), monitors Gmail, drafts responses/posts/entries, writes to vault Pending_Approval folder. Read-only access to external services, write-only to vault drafts. No sensitive credentials.

- **Local Agent**: Runs on user's local machine, monitors WhatsApp and bank transactions, handles approval workflow, executes all final actions (sends, posts, payments). Exclusive access to sensitive credentials and sessions.

- **Vault Synchronization**: Agents communicate asynchronously via synced vault (Git or Syncthing). File-based coordination using claim-by-move rule and single-writer pattern for Dashboard.md.

- **Security Boundary**: Cloud agent can only draft (never execute), local agent owns all secrets and final actions. Approval workflow enforced via file movement (Pending_Approval → Approved → execution).

- **Coordination Protocol**: Claim-by-move rule prevents duplicate work (first agent to move file from Needs_Action to In_Progress owns task). Single-writer rule for Dashboard (local agent only, cloud writes to Updates folder).

## Consequences

### Positive

- **24/7 Availability**: Cloud agent provides always-on monitoring even when local machine is offline, meeting core Platinum tier value proposition
- **Security Isolation**: Sensitive credentials (WhatsApp session, banking, payment) never leave local machine or sync to vault
- **Graceful Degradation**: System continues operating if either agent fails - cloud agent queues drafts, local agent operates independently
- **Audit Trail**: File-based communication provides natural audit trail via Git history
- **Debuggability**: All agent coordination visible as files in vault, easy to inspect and debug
- **Offline Operation**: Local agent can operate independently when cloud agent is unavailable
- **Human-in-the-Loop**: Approval workflow prevents unauthorized actions (100% compliance requirement)
- **Platform Independence**: Cloud agent (Linux VM) and local agent (Windows/macOS/Linux) can run on different platforms

### Negative

- **Coordination Complexity**: File-based coordination requires careful implementation of claim-by-move and single-writer rules to prevent conflicts
- **Sync Latency**: Vault synchronization introduces latency (10 seconds target) between agent actions
- **Deployment Overhead**: Requires provisioning and maintaining cloud VM in addition to local setup
- **Split Responsibility**: Debugging issues requires checking both agents and vault sync status
- **Network Dependency**: Vault sync requires network connectivity (though agents can queue operations offline)
- **Constitution Violation**: Violates Local-First Architecture principle (justified by explicit requirement for 24/7 monitoring)
- **Operational Complexity**: Two agents to monitor, restart, and maintain instead of one

## Alternatives Considered

### Alternative 1: Single Cloud Agent with All Credentials

**Architecture**: Run entire system on cloud VM with all credentials stored in cloud environment.

**Why Rejected**:
- **Security Risk**: WhatsApp session, banking credentials, and payment credentials on cloud VM creates single point of compromise
- **WhatsApp Limitation**: WhatsApp Web session cannot reliably run on cloud VM (requires active browser session, subject to detection)
- **Constitution Violation**: Violates Safety-First Constraints principle (secrets must be local-only)
- **User Trust**: Users unlikely to trust cloud VM with banking and payment credentials

### Alternative 2: Single Local Agent Only

**Architecture**: Run entire system on user's local machine with scheduled wake-up for monitoring.

**Why Rejected**:
- **Availability Gap**: Cannot monitor emails when local machine is offline, defeating primary Platinum tier value proposition
- **Specification Violation**: Fails to meet FR-006, FR-007, FR-015 (24/7 monitoring requirement)
- **User Experience**: Misses time-sensitive emails during offline periods (nights, travel, power outages)
- **Competitive Disadvantage**: No differentiation from Gold tier (local-only operation)

### Alternative 3: Direct Agent-to-Agent Messaging (A2A)

**Architecture**: Agents communicate via direct network messages (WebSocket, gRPC, message queue) instead of file-based vault sync.

**Why Rejected for Phase 1** (considered for Phase 2):
- **Complexity**: Requires implementing message protocol, connection management, retry logic, authentication
- **Debugging**: Network messages are ephemeral, harder to debug than file-based audit trail
- **Offline Operation**: Requires message queuing when agents are offline, adding complexity
- **Audit Trail**: Requires separate audit logging system instead of natural Git history
- **Scope Creep**: Adds significant complexity to MVP without clear benefit over file-based approach
- **Phase 2 Option**: Can be added later while maintaining vault as audit record

### Alternative 4: Hybrid with Optional Cloud Execution

**Architecture**: Allow cloud agent to execute low-risk actions (e.g., email replies to known contacts) without approval.

**Why Rejected**:
- **Specification Violation**: Fails FR-046 (all new recipients require approval), FR-048 (all social posts require approval)
- **Security Risk**: Blurs security boundary between drafting and execution
- **Complexity**: Requires risk classification system and auto-approval thresholds
- **User Trust**: Users may not trust automated execution without approval, even for "low-risk" actions
- **Scope Creep**: Adds complexity without clear user demand

## References

- Feature Spec: [specs/001-platinum-employee/spec.md](../../specs/001-platinum-employee/spec.md)
- Implementation Plan: [specs/001-platinum-employee/plan.md](../../specs/001-platinum-employee/plan.md)
- Research: [specs/001-platinum-employee/research.md](../../specs/001-platinum-employee/research.md)
- Agent API Contract: [specs/001-platinum-employee/contracts/agent-api.md](../../specs/001-platinum-employee/contracts/agent-api.md)
- Vault Structure Contract: [specs/001-platinum-employee/contracts/vault-structure.md](../../specs/001-platinum-employee/contracts/vault-structure.md)
- Related ADRs: None (first ADR for this feature)
- Evaluator Evidence: [history/prompts/platinum-employee/001-planning-phase-complete.plan.prompt.md](../../history/prompts/platinum-employee/001-planning-phase-complete.plan.prompt.md)

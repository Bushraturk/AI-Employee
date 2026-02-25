# Research: Platinum Tier AI Employee

**Date**: 2026-02-25
**Feature**: 001-platinum-employee
**Purpose**: Document technical decisions, alternatives considered, and rationale for implementation approach

## Overview

This research document captures the technical decisions made during the planning phase for the Platinum Tier AI Employee. While the specification is comprehensive, several architectural and technology choices required evaluation of alternatives and best practices.

## Key Technical Decisions

### 1. Vault Synchronization: Git vs Syncthing

**Decision**: Support both Git and Syncthing, with Git as the recommended default

**Rationale**:
- **Git advantages**: Built-in version control, conflict resolution, audit trail, familiar to developers, works with existing GitHub/GitLab infrastructure
- **Syncthing advantages**: Real-time sync (no manual push/pull), simpler for non-technical users, works without internet (local network), no merge conflicts (last-write-wins)
- **Hybrid approach**: Git for users comfortable with version control, Syncthing for users wanting automatic sync

**Alternatives considered**:
- **Dropbox/Google Drive**: Rejected due to lack of atomic operations, poor handling of concurrent writes, and potential for file corruption
- **rsync**: Rejected due to lack of conflict resolution and no built-in change detection
- **Custom sync protocol**: Rejected due to development complexity and maintenance burden

**Implementation notes**:
- Git sync: Use GitPython library for programmatic git operations (pull before read, commit+push after write)
- Syncthing sync: Use Syncthing REST API for monitoring sync status
- Both agents must implement same sync interface for consistency
- Sync failures must be detected and queued for retry

**Best practices**:
- Git: Use separate branch per agent to avoid conflicts, merge to main periodically
- Syncthing: Configure ignore patterns for .git directory if using Git for version control
- Both: Implement file locking mechanism (claim-by-move rule) to prevent concurrent edits

### 2. Cloud VM Provider: Oracle Cloud Free Tier

**Decision**: Recommend Oracle Cloud Free Tier as primary option, with AWS/Azure/GCP as alternatives

**Rationale**:
- **Oracle Cloud Free Tier**: Always-free tier includes 2 AMD-based VMs (1/8 OCPU, 1GB RAM each) or 4 Arm-based VMs (1 OCPU, 6GB RAM each), sufficient for cloud agent + Odoo
- **Cost**: Free tier is genuinely free (no credit card expiration), suitable for hackathon and personal use
- **Limitations**: Subject to availability, may require waiting for capacity, limited to specific regions

**Alternatives considered**:
- **AWS Free Tier**: 12 months free, then paid. t2.micro (1 vCPU, 1GB RAM) sufficient for cloud agent but tight for Odoo
- **Azure Free Tier**: 12 months free, then paid. B1s (1 vCPU, 1GB RAM) similar to AWS
- **GCP Free Tier**: Always-free e2-micro (0.25 vCPU, 1GB RAM) too small for Odoo, would need paid tier
- **DigitalOcean**: No free tier, $6/month minimum
- **Linode**: No free tier, $5/month minimum

**Implementation notes**:
- Provide Terraform configurations for all major providers
- Document resource requirements: Cloud agent (512MB RAM, 1 vCPU), Odoo (2GB RAM, 2 vCPU recommended)
- Include cost estimates for paid tiers if free tier unavailable

**Best practices**:
- Use infrastructure-as-code (Terraform) for reproducible deployments
- Implement health monitoring and auto-restart for services
- Configure automated backups for Odoo database
- Use HTTPS with Let's Encrypt for Odoo access

### 3. Odoo Integration: JSON-RPC vs XML-RPC

**Decision**: Use JSON-RPC API (odoorpc library) for Odoo integration

**Rationale**:
- **JSON-RPC**: Modern, better performance, native JSON support, easier debugging
- **XML-RPC**: Legacy API, still supported but verbose
- **odoorpc library**: Provides high-level Python interface, handles authentication, supports both protocols

**Alternatives considered**:
- **Direct XML-RPC**: Rejected due to verbosity and manual session management
- **Odoo REST API**: Not available in Community Edition (Enterprise only)
- **Direct PostgreSQL access**: Rejected due to bypassing Odoo business logic and breaking data integrity

**Implementation notes**:
- Use odoorpc v0.10.1+ for Odoo 19 compatibility
- Implement connection pooling for performance
- Cache Odoo metadata (models, fields) to reduce API calls
- Implement retry logic with exponential backoff for transient failures

**Best practices**:
- Always use Odoo API methods, never direct database access
- Validate data before posting to Odoo
- Use Odoo's built-in access control (don't bypass security)
- Log all Odoo operations for audit trail

### 4. Email Drafting: Claude API vs Local LLM

**Decision**: Use Claude API (via Claude Code MCP integration) for email drafting

**Rationale**:
- **Claude API**: High-quality drafts, context understanding, no local GPU required, consistent with existing Claude Code usage
- **Cost**: Pay-per-use, but reasonable for typical email volumes (500 emails/day = ~$5-10/month)
- **Latency**: Acceptable for draft generation (2-5 seconds), not user-facing

**Alternatives considered**:
- **Local LLM (Llama, Mistral)**: Rejected due to GPU requirements, slower inference, lower quality drafts
- **GPT-4 API**: Similar quality to Claude, but higher cost and less integration with existing Claude Code setup
- **Template-based**: Rejected due to lack of context understanding and poor quality

**Implementation notes**:
- Use Claude Code's existing MCP integration for consistency
- Implement prompt templates for different email types (reply, follow-up, inquiry)
- Include sender context, conversation history, and business rules in prompts
- Cache common responses to reduce API calls

**Best practices**:
- Include clear instructions in prompts (tone, length, key points)
- Provide examples of good responses in prompts
- Implement quality checks (length, tone, completeness)
- Allow user feedback to improve future drafts

### 5. WhatsApp Integration: Playwright vs WhatsApp Business API

**Decision**: Use Playwright for WhatsApp Web automation (local agent only)

**Rationale**:
- **Playwright**: Works with personal WhatsApp accounts, no API approval required, free
- **Limitations**: Requires active WhatsApp Web session, local machine only, subject to WhatsApp ToS
- **Security**: Session stays local, no credentials sent to cloud

**Alternatives considered**:
- **WhatsApp Business API**: Rejected due to business account requirement, approval process, and cost ($0.005-0.09 per message)
- **WhatsApp Cloud API**: Similar limitations to Business API
- **Unofficial libraries (yowsup, whatsapp-web.js)**: Rejected due to ToS violations and ban risk

**Implementation notes**:
- Use Playwright's persistent context to maintain session
- Implement session validation before sending messages
- Detect session expiration and prompt user to re-authenticate
- Monitor for WhatsApp Web updates that might break automation

**Best practices**:
- Clearly document WhatsApp ToS risks
- Implement rate limiting to avoid detection
- Use headless mode for efficiency
- Provide fallback to manual sending if automation fails

### 6. Process Management: PM2 vs Systemd vs Custom Watchdog

**Decision**: Implement custom Python watchdog with optional PM2/systemd integration

**Rationale**:
- **Custom watchdog**: Provides fine-grained control, cross-platform (Windows/macOS/Linux), integrated with system
- **PM2**: Good for Node.js, works with Python, but adds dependency
- **Systemd**: Linux-only, requires root access, complex configuration

**Alternatives considered**:
- **PM2 only**: Rejected due to platform limitations (Windows support is experimental)
- **Systemd only**: Rejected due to platform limitations (Linux only)
- **Supervisor**: Rejected due to Python 2 legacy and limited Windows support

**Implementation notes**:
- Custom watchdog monitors process PIDs and restarts on failure
- Watchdog logs all restarts and failures
- Watchdog implements exponential backoff for repeated failures
- Watchdog notifies user after 3+ restarts within 1 hour
- Optional PM2/systemd integration for production deployments

**Best practices**:
- Store PIDs in /tmp or platform-specific temp directory
- Implement graceful shutdown (SIGTERM before SIGKILL)
- Log stdout/stderr to files for debugging
- Implement health checks (not just process existence)

### 7. Approval Workflow: File-based vs Database vs API

**Decision**: File-based approval workflow using vault folders

**Rationale**:
- **File-based**: Simple, auditable, works offline, no database required, consistent with markdown-as-memory principle
- **Approval by file movement**: Intuitive (drag-and-drop in file manager), atomic operation, no API needed
- **Audit trail**: Git history provides complete approval history

**Alternatives considered**:
- **SQLite database**: Rejected due to sync complexity and hidden state
- **REST API**: Rejected due to requiring always-on server and network dependency
- **Web UI**: Rejected due to development complexity and scope creep

**Implementation notes**:
- Use watchdog library to monitor folder changes
- Implement file locking to prevent race conditions
- Validate approval file format before execution
- Move files atomically (rename, not copy+delete)

**Best practices**:
- Use frontmatter for structured metadata
- Include expiration timestamp in approval files
- Implement approval timeout (move to expired folder)
- Log all approval decisions (approved, rejected, expired)

### 8. Error Recovery: Retry Logic with Circuit Breaker

**Decision**: Implement retry logic with exponential backoff and circuit breaker pattern

**Rationale**:
- **Retry logic**: Handles transient failures (network timeouts, API rate limits)
- **Exponential backoff**: Prevents overwhelming failing services
- **Circuit breaker**: Prevents cascading failures and allows services to recover

**Alternatives considered**:
- **Simple retry**: Rejected due to potential for overwhelming failing services
- **No retry**: Rejected due to poor user experience for transient failures
- **Manual retry**: Rejected due to requiring user intervention for common failures

**Implementation notes**:
- Use tenacity library for retry logic (max 3 attempts, exponential backoff)
- Use pybreaker library for circuit breaker (open after 5 failures, half-open after 60 seconds)
- Implement separate circuit breakers for each external service (Gmail, Odoo, social media)
- Queue operations when circuit breaker is open

**Best practices**:
- Log all retry attempts and circuit breaker state changes
- Notify user when circuit breaker opens (service unavailable)
- Implement manual circuit breaker reset option
- Monitor circuit breaker metrics for service health

## Technology Stack Summary

### Cloud Agent
- **Language**: Python 3.9+
- **Key Libraries**: watchdog, APScheduler, google-auth, googleapiclient, tenacity, pybreaker, frontmatter, markdown, python-dotenv
- **Deployment**: Cloud VM (Oracle Cloud Free Tier recommended)
- **Process Management**: Custom watchdog + optional PM2/systemd

### Local Agent
- **Language**: Python 3.9+
- **Key Libraries**: watchdog, APScheduler, playwright, tenacity, pybreaker, frontmatter, markdown, python-dotenv
- **Deployment**: User's local machine (Windows/macOS/Linux)
- **Process Management**: Custom watchdog + optional PM2/systemd

### MCP Servers
- **Email MCP**: Node.js 18+, Gmail API client
- **Social MCP**: Node.js 18+, platform-specific API clients (Facebook, Instagram, Twitter, LinkedIn)
- **Odoo MCP**: Python 3.9+, odoorpc library

### Infrastructure
- **Vault Sync**: Git (GitPython) or Syncthing (REST API)
- **Cloud VM**: Oracle Cloud Free Tier (2 AMD VMs or 4 Arm VMs)
- **Odoo**: Community Edition v19+, PostgreSQL database
- **Deployment**: Terraform (infrastructure), Ansible (configuration)

### Testing
- **Framework**: pytest
- **Coverage**: unit tests, integration tests, contract tests, end-to-end tests
- **CI/CD**: GitHub Actions (recommended)

## Security Considerations

### Credential Management
- All credentials stored in environment variables (.env file)
- .env file never committed to version control
- Cloud agent has read-only Gmail credentials only
- Local agent has all sensitive credentials (WhatsApp session, banking, payment)
- Odoo credentials stored on cloud VM only (not synced to vault)

### Vault Sync Security
- .gitignore configured to exclude .env, sessions, credentials
- Pre-commit hooks detect and block secret patterns
- Vault contains only markdown files and state data
- No binary files or executables in vault

### Network Security
- Odoo accessed via HTTPS only (Let's Encrypt)
- MCP servers use local sockets or authenticated connections
- No direct agent-to-agent network communication (file-based only)

### Audit and Compliance
- All actions logged with timestamp, actor, target, result
- Logs retained for minimum 90 days
- Approval workflow provides complete audit trail
- Git history provides version control for all state changes

## Performance Optimization

### Vault Sync
- Sync only changed files (not entire vault)
- Use .gitignore to exclude large files
- Implement sync throttling (max 1 sync per 10 seconds)
- Cache vault state to reduce file system reads

### Email Processing
- Batch process multiple emails in single Claude API call
- Cache sender context to reduce lookups
- Implement email deduplication (processed IDs set)
- Use Gmail API filters to reduce irrelevant emails

### Odoo Integration
- Connection pooling for Odoo API
- Cache Odoo metadata (models, fields, account codes)
- Batch create/update operations when possible
- Implement read-through cache for frequently accessed data

### Process Management
- Use multiprocessing for parallel watcher execution
- Implement graceful shutdown to avoid data loss
- Monitor memory usage and restart if exceeds threshold
- Use asyncio for I/O-bound operations

## Deployment Strategy

### Phase 1: Local Development
1. Set up local vault with Git
2. Configure local agent with test credentials
3. Implement and test watchers locally
4. Verify approval workflow with manual file movement

### Phase 2: Cloud Agent Deployment
1. Provision cloud VM (Oracle Cloud Free Tier)
2. Deploy cloud agent with Gmail credentials
3. Configure vault sync (Git or Syncthing)
4. Test cloud agent independently

### Phase 3: Odoo Deployment
1. Deploy Odoo on cloud VM
2. Configure HTTPS with Let's Encrypt
3. Set up automated backups
4. Implement health monitoring

### Phase 4: Integration Testing
1. Test vault sync between agents
2. Verify claim-by-move rule
3. Test approval workflow end-to-end
4. Validate error recovery and retry logic

### Phase 5: Production Rollout
1. Configure production credentials
2. Enable all watchers
3. Monitor system health for 24 hours
4. Gradually increase automation (start with draft-only)

## Risk Mitigation

### Risk: Vault sync conflicts
- **Mitigation**: Claim-by-move rule, single-writer rule for Dashboard, conflict detection and alerting

### Risk: Cloud agent compromise
- **Mitigation**: Cloud agent has no sensitive credentials, can only draft (not execute), audit logging

### Risk: WhatsApp session expiration
- **Mitigation**: Session validation before sending, user notification, message queuing for retry

### Risk: Odoo downtime
- **Mitigation**: Circuit breaker, operation queuing, manual posting option, automated backups

### Risk: Email API rate limits
- **Mitigation**: Rate limiting (10 emails/hour), exponential backoff, operation queuing

### Risk: Approval workflow bypass
- **Mitigation**: File validation, approval file format checks, audit logging, no direct execution path

## Open Questions

None. All technical decisions have been made based on specification requirements and best practices.

## References

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Odoo 19 JSON-RPC API](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [Playwright Python Documentation](https://playwright.dev/python/docs/intro)
- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [GitPython Documentation](https://gitpython.readthedocs.io/)
- [Syncthing REST API](https://docs.syncthing.net/dev/rest.html)
- [Tenacity Retry Library](https://tenacity.readthedocs.io/)
- [PyBreaker Circuit Breaker](https://pybreaker.readthedocs.io/)

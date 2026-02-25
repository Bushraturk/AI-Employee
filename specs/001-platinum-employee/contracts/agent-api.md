# Agent API Contract

**Version**: 1.0.0
**Date**: 2026-02-25
**Purpose**: Define the interface contract between cloud and local agents

## Overview

The Platinum Tier AI Employee uses a dual-agent architecture where agents communicate asynchronously via the synced vault. This document defines the API contract that both agents must implement for coordination and interoperability.

## Agent Interface

### Base Agent Contract

All agents (cloud and local) MUST implement the following interface:

```python
class BaseAgent(ABC):
    """Abstract base class for all agents"""

    @abstractmethod
    def start(self) -> None:
        """Start the agent and all its watchers"""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Gracefully stop the agent and all its watchers"""
        pass

    @abstractmethod
    def process_action_file(self, action_file_path: str) -> None:
        """Process an action file from Needs_Action folder"""
        pass

    @abstractmethod
    def claim_task(self, action_file_path: str) -> bool:
        """Claim a task by moving it to In_Progress/{agent}/"""
        pass

    @abstractmethod
    def update_heartbeat(self) -> None:
        """Update agent heartbeat in agent_state.md"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
```

## Cloud Agent Contract

### Capabilities
- `gmail_monitoring`: Monitor Gmail for new messages
- `email_drafting`: Draft email responses
- `social_drafting`: Draft social media posts
- `accounting_drafting`: Draft Odoo accounting entries
- `business_auditing`: Generate business briefings

### Responsibilities
1. **Monitor Gmail**: Check for new important emails every 2 minutes
2. **Draft Responses**: Generate draft email replies based on context
3. **Draft Social Posts**: Generate social media posts based on business goals
4. **Draft Accounting Entries**: Generate Odoo entries based on transactions
5. **Generate Briefings**: Create weekly business audit reports
6. **Update Vault**: Write drafts to Pending_Approval/ and updates to Updates/

### Restrictions
- MUST NOT access Approved/ folder
- MUST NOT write to Dashboard.md directly
- MUST NOT execute any final actions (sends, posts, payments)
- MUST NOT access sensitive credentials (WhatsApp session, banking, payment)

### API Methods

```python
class CloudAgent(BaseAgent):
    def monitor_gmail(self) -> List[ActionFile]:
        """Monitor Gmail and create action files for new messages"""
        pass

    def draft_email_reply(self, action_file: ActionFile) -> ApprovalRequest:
        """Draft email reply based on action file"""
        pass

    def draft_social_post(self, business_goals: BusinessGoals) -> ApprovalRequest:
        """Draft social media post based on business goals"""
        pass

    def draft_accounting_entry(self, transaction: Transaction) -> ApprovalRequest:
        """Draft Odoo accounting entry based on transaction"""
        pass

    def generate_business_briefing(self) -> Briefing:
        """Generate weekly business audit and briefing"""
        pass

    def write_update(self, update_content: str) -> None:
        """Write update to Updates/ folder for Dashboard merge"""
        pass
```

## Local Agent Contract

### Capabilities
- `whatsapp_monitoring`: Monitor WhatsApp for urgent messages
- `finance_monitoring`: Monitor bank transactions
- `approval_handling`: Process approval workflow
- `email_execution`: Send emails via MCP
- `social_execution`: Post to social media via MCP
- `accounting_execution`: Post to Odoo via MCP
- `dashboard_management`: Update Dashboard.md

### Responsibilities
1. **Monitor WhatsApp**: Check for urgent keyword messages every 30 seconds
2. **Monitor Transactions**: Check for new bank transactions every 5 minutes
3. **Handle Approvals**: Monitor Approved/ folder and execute actions
4. **Execute Actions**: Send emails, post to social media, post to Odoo
5. **Update Dashboard**: Merge Updates/ into Dashboard.md
6. **Maintain Audit Log**: Log all executed actions

### Exclusive Access
- WhatsApp Web session (local only)
- Banking credentials (local only)
- Payment credentials (local only)
- Dashboard.md write access (local only)
- Approved/ folder execution (local only)

### API Methods

```python
class LocalAgent(BaseAgent):
    def monitor_whatsapp(self) -> List[ActionFile]:
        """Monitor WhatsApp and create action files for urgent messages"""
        pass

    def monitor_transactions(self) -> List[ActionFile]:
        """Monitor bank transactions and create action files"""
        pass

    def process_approval(self, approval_request: ApprovalRequest) -> None:
        """Process approved action and execute via MCP"""
        pass

    def send_email(self, approval_request: ApprovalRequest) -> None:
        """Send email via Email MCP"""
        pass

    def post_social(self, approval_request: ApprovalRequest) -> None:
        """Post to social media via Social MCP"""
        pass

    def post_accounting(self, approval_request: ApprovalRequest) -> None:
        """Post accounting entry to Odoo via Odoo MCP"""
        pass

    def update_dashboard(self) -> None:
        """Merge Updates/ into Dashboard.md"""
        pass

    def log_action(self, action: Action) -> None:
        """Log action to audit log"""
        pass
```

## Coordination Protocol

### Claim-by-Move Rule

**Purpose**: Prevent duplicate work when both agents are online

**Protocol**:
1. Agent scans Needs_Action/ folder for new action files
2. Agent attempts to move file to In_Progress/{agent}/
3. If move succeeds, agent owns the task
4. If move fails (file already moved), agent skips the task
5. Agent processes the task and moves to Pending_Approval/ or Done/

**Implementation**:
```python
def claim_task(self, action_file_path: str) -> bool:
    """Claim task using atomic file move"""
    source = Path(action_file_path)
    destination = Path(f"vault/In_Progress/{self.agent_id}/{source.name}")

    try:
        source.rename(destination)  # Atomic operation
        return True
    except FileNotFoundError:
        # File already moved by other agent
        return False
```

### Single-Writer Rule for Dashboard

**Purpose**: Prevent merge conflicts in Dashboard.md

**Protocol**:
1. Local agent is the ONLY writer to Dashboard.md
2. Cloud agent writes updates to Updates/ folder
3. Local agent periodically merges Updates/ into Dashboard.md
4. Local agent deletes merged update files

**Implementation**:
```python
# Cloud agent
def write_update(self, update_content: str) -> None:
    """Write update to Updates/ folder"""
    update_file = Path(f"vault/Updates/update_{timestamp()}.md")
    update_file.write_text(update_content)

# Local agent
def update_dashboard(self) -> None:
    """Merge Updates/ into Dashboard.md"""
    updates = list(Path("vault/Updates").glob("*.md"))
    for update_file in updates:
        content = update_file.read_text()
        self.merge_into_dashboard(content)
        update_file.unlink()  # Delete after merge
```

## Heartbeat Protocol

**Purpose**: Monitor agent health and detect failures

**Protocol**:
1. Each agent updates agent_state.md every 60 seconds
2. Heartbeat includes timestamp, status, and claimed tasks
3. Agent is considered dead if heartbeat is older than 5 minutes
4. Watchdog process monitors heartbeats and restarts dead agents

**Implementation**:
```python
def update_heartbeat(self) -> None:
    """Update agent heartbeat"""
    state_file = Path(f"vault/In_Progress/{self.agent_id}/agent_state.md")
    state = {
        "agent_id": self.agent_id,
        "status": self.status,
        "last_heartbeat": datetime.now().isoformat(),
        "capabilities": self.get_capabilities(),
        "claimed_tasks": self.claimed_tasks,
        "version": self.version
    }
    write_frontmatter_file(state_file, state, self.get_status_body())
```

## Error Handling Protocol

### Transient Errors

**Examples**: Network timeout, API rate limit, temporary service unavailable

**Protocol**:
1. Implement retry logic with exponential backoff (max 3 attempts)
2. Log retry attempts
3. If all retries fail, move to error handling

**Implementation**:
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=60))
def call_external_service(self, request):
    """Call external service with retry logic"""
    return service.call(request)
```

### Permanent Errors

**Examples**: Invalid credentials, missing file, corrupted data

**Protocol**:
1. Log error with full context
2. Move action file to quarantine folder
3. Alert user for manual intervention
4. Do not retry

**Implementation**:
```python
def handle_permanent_error(self, action_file: Path, error: Exception) -> None:
    """Handle permanent error"""
    quarantine = Path("vault/Quarantine")
    quarantine.mkdir(exist_ok=True)

    # Move to quarantine
    action_file.rename(quarantine / action_file.name)

    # Log error
    self.log_error(action_file, error)

    # Alert user
    self.alert_user(f"Action file quarantined: {action_file.name}")
```

### Circuit Breaker Protocol

**Purpose**: Prevent cascading failures when external service is down

**Protocol**:
1. Implement circuit breaker for each external service
2. Open circuit after 5 consecutive failures
3. Half-open circuit after 60 seconds
4. Close circuit after successful call
5. Queue operations when circuit is open

**Implementation**:
```python
gmail_breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@gmail_breaker
def call_gmail_api(self, request):
    """Call Gmail API with circuit breaker"""
    return gmail_service.call(request)
```

## Synchronization Protocol

### Vault Sync Timing

**Git Sync**:
- Pull before reading action files
- Commit and push after writing files
- Max 1 sync per 10 seconds (throttling)

**Syncthing Sync**:
- Continuous real-time sync
- No manual sync required
- Monitor sync status via REST API

### Conflict Resolution

**Dashboard.md**: Manual resolution required (single-writer rule prevents most conflicts)

**Other files**: Last-write-wins (acceptable for action files and logs)

**Action files**: Claim-by-move rule prevents conflicts

## Testing Contract

### Unit Tests
- Test claim_task with concurrent access
- Test heartbeat update
- Test error handling (transient and permanent)
- Test circuit breaker behavior

### Integration Tests
- Test agent coordination (claim-by-move)
- Test dashboard merge (single-writer)
- Test vault sync (Git and Syncthing)
- Test approval workflow end-to-end

### Contract Tests
- Verify agent implements all required methods
- Verify agent respects access restrictions
- Verify agent follows coordination protocols
- Verify agent handles errors correctly

## Performance Requirements

### Response Times
- Heartbeat update: < 100ms
- Claim task: < 500ms
- Process action file: < 30 seconds
- Execute approved action: < 60 seconds

### Throughput
- Handle 100 action files per day
- Process 10 approvals per hour
- Update dashboard every 60 seconds
- Sync vault every 10 seconds (Git) or real-time (Syncthing)

### Resource Limits
- Memory: < 500MB per agent
- CPU: < 10% average utilization
- Disk: < 1GB vault size
- Network: < 10MB/hour (excluding Odoo)

## Security Requirements

### Credential Management
- Cloud agent: Gmail credentials only (read-only)
- Local agent: All credentials (WhatsApp, banking, payment, Odoo)
- Credentials stored in environment variables (.env file)
- Never commit credentials to vault

### Access Control
- Cloud agent: Read Needs_Action/, Write Pending_Approval/ and Updates/
- Local agent: Read all, Write all, Execute Approved/
- User: Move files between Pending_Approval/, Approved/, Rejected/

### Audit Trail
- Log all agent actions with timestamp, actor, target, result
- Log all file operations (create, move, delete)
- Log all approval decisions (approved, rejected, expired)
- Retain logs for minimum 90 days

## Versioning

### Agent Version Format
- Semantic versioning: MAJOR.MINOR.PATCH
- Example: 1.0.0

### Compatibility
- Agents with same MAJOR version are compatible
- Agents with different MAJOR versions may not be compatible
- Version checked during startup and logged

### Upgrade Protocol
1. Stop old agent
2. Deploy new agent
3. Run migration scripts if needed
4. Start new agent
5. Verify compatibility with other agent

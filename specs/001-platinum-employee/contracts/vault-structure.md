# Vault Structure Contract

**Version**: 1.0.0
**Date**: 2026-02-25
**Purpose**: Define the canonical vault folder structure and file organization

## Folder Structure

```
vault/
├── Needs_Action/           # REQUIRED: New events detected by watchers
│   ├── email/              # REQUIRED: Email events
│   ├── social/             # OPTIONAL: Social media events
│   ├── accounting/         # REQUIRED: Financial transaction events
│   └── whatsapp/           # REQUIRED: WhatsApp message events
├── In_Progress/            # REQUIRED: Tasks currently being processed
│   ├── cloud/              # REQUIRED: Cloud agent claimed tasks
│   │   ├── agent_state.md  # REQUIRED: Cloud agent state
│   │   └── watcher_gmail.md # REQUIRED: Gmail watcher state
│   └── local/              # REQUIRED: Local agent claimed tasks
│       ├── agent_state.md  # REQUIRED: Local agent state
│       ├── watcher_whatsapp.md # REQUIRED: WhatsApp watcher state
│       └── watcher_finance.md  # REQUIRED: Finance watcher state
├── Pending_Approval/       # REQUIRED: Draft actions requiring approval
│   ├── email/              # REQUIRED: Email send approvals
│   ├── social/             # OPTIONAL: Social post approvals
│   ├── accounting/         # REQUIRED: Accounting entry approvals
│   └── whatsapp/           # REQUIRED: WhatsApp send approvals
├── Approved/               # REQUIRED: Approved actions ready for execution
├── Rejected/               # REQUIRED: Rejected actions (for learning)
├── Done/                   # REQUIRED: Completed actions (archived)
├── Plans/                  # OPTIONAL: Generated plans and strategies
├── Logs/                   # REQUIRED: Audit logs (one file per day)
├── Updates/                # REQUIRED: Cloud agent updates (for Dashboard merge)
├── Dashboard.md            # REQUIRED: System status (local agent only)
├── Company_Handbook.md     # OPTIONAL: Business rules and context
└── Business_Goals.md       # OPTIONAL: Strategic objectives and metrics
```

## Folder Contracts

### Needs_Action/
- **Purpose**: Entry point for all detected events
- **Writers**: Watchers only
- **Readers**: Agents (cloud and local)
- **File Format**: Action files with frontmatter
- **Retention**: Files moved to In_Progress/ when claimed
- **Subdirectories**: Domain-specific (email, social, accounting, whatsapp)

### In_Progress/
- **Purpose**: Track tasks currently being processed by agents
- **Writers**: Agents (cloud and local)
- **Readers**: Agents (for coordination)
- **File Format**: Action files moved from Needs_Action/
- **Retention**: Files moved to Pending_Approval/ or Done/ when complete
- **Subdirectories**: Agent-specific (cloud, local)
- **Claim Rule**: First agent to move file owns the task

### Pending_Approval/
- **Purpose**: Store draft actions requiring human approval
- **Writers**: Agents (cloud and local)
- **Readers**: User (for approval), Agents (for execution)
- **File Format**: Approval request files with frontmatter
- **Retention**: Files moved to Approved/, Rejected/, or Expired/ based on user action
- **Subdirectories**: Domain-specific (email, social, accounting, whatsapp)

### Approved/
- **Purpose**: Queue approved actions for execution
- **Writers**: User (via file move)
- **Readers**: Local agent only
- **File Format**: Approval request files
- **Retention**: Files moved to Done/ after execution
- **Subdirectories**: None (flat structure)

### Rejected/
- **Purpose**: Store rejected actions for learning
- **Writers**: User (via file move)
- **Readers**: Agents (for learning)
- **File Format**: Approval request files with rejection reason
- **Retention**: Retained for 90 days, then archived
- **Subdirectories**: None (flat structure)

### Done/
- **Purpose**: Archive completed actions
- **Writers**: Agents (cloud and local)
- **Readers**: Agents (for reporting), User (for review)
- **File Format**: Action files and approval request files
- **Retention**: Retained for 90 days, then compressed
- **Subdirectories**: None (flat structure)

### Logs/
- **Purpose**: Store audit logs
- **Writers**: Agents (cloud and local)
- **Readers**: User (for audit), Agents (for reporting)
- **File Format**: Daily log files (YYYY-MM-DD.md) with JSON entries
- **Retention**: Retained for minimum 90 days
- **Subdirectories**: None (flat structure)

### Updates/
- **Purpose**: Cloud agent writes dashboard updates
- **Writers**: Cloud agent only
- **Readers**: Local agent only
- **File Format**: Markdown files with update content
- **Retention**: Files deleted after merge into Dashboard.md
- **Subdirectories**: None (flat structure)

## File Naming Conventions

### Action Files
- **Format**: `{type}_{source_id}_{timestamp}.md`
- **Example**: `email_msg123_20260225T103000Z.md`
- **Validation**: Must match regex `^(email|whatsapp|transaction|file_drop)_[a-zA-Z0-9]+_\d{8}T\d{6}Z\.md$`

### Approval Request Files
- **Format**: `{action_type}_{target_id}_{timestamp}.md`
- **Example**: `email_send_client@example.com_20260225T103000Z.md`
- **Validation**: Must match regex `^(email_send|social_post|accounting_entry|whatsapp_send|payment)_[a-zA-Z0-9@._-]+_\d{8}T\d{6}Z\.md$`

### Audit Log Files
- **Format**: `{YYYY-MM-DD}.md`
- **Example**: `2026-02-25.md`
- **Validation**: Must match regex `^\d{4}-\d{2}-\d{2}\.md$`

### Agent State Files
- **Format**: `agent_state.md`
- **Location**: `In_Progress/{agent}/agent_state.md`
- **Validation**: Must exist in agent-specific directory

### Watcher State Files
- **Format**: `watcher_{source}.md`
- **Example**: `watcher_gmail.md`
- **Location**: `In_Progress/{agent}/watcher_{source}.md`
- **Validation**: Must match regex `^watcher_(gmail|whatsapp|bank)\.md$`

## Synchronization Rules

### Git Sync
- **Included**: All markdown files, all folders
- **Excluded**: .env, *.session, *.credentials, .git/
- **Conflict Resolution**: Last-write-wins for most files, manual resolution for Dashboard.md
- **Sync Frequency**: On-demand (after write operations)

### Syncthing Sync
- **Included**: All markdown files, all folders
- **Excluded**: .env, *.session, *.credentials
- **Conflict Resolution**: Last-write-wins (automatic)
- **Sync Frequency**: Real-time (continuous)

## Access Control

### Cloud Agent
- **Read**: Needs_Action/, In_Progress/, Company_Handbook.md, Business_Goals.md
- **Write**: In_Progress/cloud/, Pending_Approval/, Updates/
- **Forbidden**: Approved/, Dashboard.md (direct write), Logs/ (except own actions)

### Local Agent
- **Read**: All folders
- **Write**: All folders
- **Exclusive Write**: Dashboard.md, Approved/ (execution)

### User
- **Read**: All folders
- **Write**: Pending_Approval/ → Approved/Rejected/ (via file move)
- **Forbidden**: Direct writes to In_Progress/, Logs/

## Validation Rules

### Folder Existence
- All REQUIRED folders must exist
- Agents must create missing folders on startup
- Missing folders logged as warnings

### File Format
- All files must have .md extension
- All files must have valid frontmatter (YAML between --- markers)
- All files must have body content (after frontmatter)

### Referential Integrity
- action_file_id references must point to existing files
- approval_request_id references must point to existing files
- Dangling references logged as warnings

### Concurrency
- Atomic file operations (rename, not copy+delete)
- Check file existence before claiming
- Retry on race conditions (max 3 attempts)

## Error Handling

### Missing Folders
- **Action**: Create folder automatically
- **Log**: Warning with folder path
- **Recovery**: Continue operation

### Invalid Files
- **Action**: Move to quarantine folder
- **Log**: Error with validation details
- **Recovery**: Alert user for manual review

### Sync Failures
- **Action**: Queue operations locally
- **Log**: Error with sync details
- **Recovery**: Retry with exponential backoff

## Performance Considerations

### File System Watching
- Use watchdog library for efficient monitoring
- Watch only active folders (Needs_Action/, Approved/)
- Debounce rapid changes (100ms delay)

### Caching
- Cache folder listings (invalidate on change)
- Cache file metadata (size, mtime)
- Cache parsed frontmatter (invalidate on change)

### Batch Operations
- Batch file moves when possible
- Batch log writes (flush every 10 entries or 1 second)
- Batch sync operations (max 1 sync per 10 seconds)

## Migration Path

### From Gold Tier
1. Create new folders: Updates/, Pending_Approval/{domain}/
2. Add agent_state.md files
3. Add watcher state files
4. No changes to existing files required

### Version Upgrades
1. Check vault version in .vault_version file
2. Run migration scripts if needed
3. Update .vault_version file
4. Log migration completion

## Testing Contract

### Unit Tests
- Validate folder structure creation
- Validate file naming conventions
- Validate frontmatter parsing
- Validate referential integrity

### Integration Tests
- Test claim-by-move rule
- Test single-writer rule for Dashboard
- Test approval workflow (Pending → Approved → Done)
- Test sync operations (Git and Syncthing)

### Contract Tests
- Verify all REQUIRED folders exist
- Verify file format compliance
- Verify access control enforcement
- Verify concurrency control

# MCP (Model Context Protocol) Server Contract

**Version**: 1.0 | **Date**: 2026-02-14 | **Feature**: 002-silver-functional

## Overview

This contract defines the internal MCP server interface for executing external actions with validation, approval, and audit logging.

## Architecture

```
┌─────────────────────────────────────────┐
│         Python Orchestrator             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│          MCP Server                     │
│  - Tool Registry                        │
│  - Validation Layer                     │
│  - Approval Check                       │
│  - Execution Engine                     │
│  - Audit Logger                         │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐ ┌─────────────┐
│ Gmail Tool  │ │LinkedIn Tool│
└─────────────┘ └─────────────┘
       ▼               ▼
┌─────────────┐ ┌─────────────┐
│ Gmail API   │ │LinkedIn API │
└─────────────┘ └─────────────┘
```

---

## Tool Registry

**Purpose**: Maintain whitelist of available tools with metadata

**Tool Registration**:
```python
class MCPServer:
    def register_tool(
        self,
        name: str,
        handler: callable,
        risk_level: str,
        requires_approval: bool,
        description: str,
        parameters_schema: dict
    ):
        """Register a tool in the registry"""
        self.tools[name] = {
            'handler': handler,
            'risk_level': risk_level,  # low, medium, high
            'requires_approval': requires_approval,
            'description': description,
            'parameters_schema': parameters_schema,
            'enabled': True,
            'rate_limit': None  # Optional rate limit config
        }
```

**Tool Metadata**:
```python
TOOL_REGISTRY = {
    "send_email": {
        "handler": gmail_tool.send_email,
        "risk_level": "medium",
        "requires_approval": True,
        "description": "Send email via Gmail API",
        "parameters_schema": {
            "to": {"type": "array", "items": {"type": "string"}},
            "subject": {"type": "string"},
            "body": {"type": "string"}
        }
    },
    "post_linkedin": {
        "handler": linkedin_tool.create_post,
        "risk_level": "medium",
        "requires_approval": True,
        "description": "Create LinkedIn post",
        "parameters_schema": {
            "content": {"type": "string", "maxLength": 3000},
            "hashtags": {"type": "array", "maxItems": 10}
        }
    },
    "send_whatsapp": {
        "handler": whatsapp_tool.send_message,
        "risk_level": "medium",
        "requires_approval": True,
        "description": "Send WhatsApp message",
        "parameters_schema": {
            "to": {"type": "string"},
            "message": {"type": "string"}
        }
    }
}
```

---

## Tool Execution Flow

**Request Format**:
```python
{
    "tool_name": "send_email",
    "parameters": {
        "to": ["recipient@example.com"],
        "subject": "Email subject",
        "body": "Email body content"
    },
    "task_reference": "550e8400-e29b-41d4-a716-446655440000",
    "approval_id": "660e8400-e29b-41d4-a716-446655440001"  # If approved
}
```

**Execution Steps**:
1. **Validate Tool Exists**: Check tool is registered and enabled
2. **Validate Parameters**: Check against parameters_schema
3. **Check Risk Level**: Determine if approval required
4. **Check Approval**: If required, verify approval_id exists and is approved
5. **Execute Tool**: Call handler with parameters
6. **Log Result**: Write to audit trail
7. **Return Response**: Success or error

**Response Format** (Success):
```python
{
    "success": True,
    "tool_name": "send_email",
    "execution_id": "exec-123",
    "result": {
        "message_id": "sent-email-id-123",
        "status": "sent"
    },
    "executed_at": "2026-02-14T11:00:00Z"
}
```

**Response Format** (Error):
```python
{
    "success": False,
    "tool_name": "send_email",
    "execution_id": "exec-124",
    "error": {
        "code": "APPROVAL_REQUIRED",
        "message": "This action requires human approval",
        "approval_id": "660e8400-e29b-41d4-a716-446655440001"
    },
    "executed_at": "2026-02-14T11:00:00Z"
}
```

---

## Validation Layer

**Parameter Validation**:
```python
def validate_parameters(tool_name: str, parameters: dict) -> tuple[bool, str]:
    """Validate parameters against schema"""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return False, f"Tool '{tool_name}' not found"

    schema = tool['parameters_schema']

    # Validate using jsonschema or custom validation
    try:
        validate(instance=parameters, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e)
```

**Risk Classification**:
```python
def classify_risk(tool_name: str, parameters: dict) -> str:
    """Determine risk level for tool execution"""
    base_risk = TOOL_REGISTRY[tool_name]['risk_level']

    # Escalate risk for bulk operations
    if tool_name == "send_email":
        if len(parameters.get('to', [])) > 5:
            return "high"  # Bulk email

    if tool_name == "post_linkedin":
        # Check for sensitive content
        if contains_sensitive_keywords(parameters['content']):
            return "high"

    return base_risk
```

---

## Approval Integration

**Approval Check**:
```python
async def check_approval(approval_id: str) -> tuple[bool, str]:
    """Verify approval exists and is approved"""
    approval_file = f"vault/Needs_Approval/{approval_id}.md"

    if not os.path.exists(approval_file):
        return False, "Approval not found"

    approval = parse_markdown_file(approval_file)

    if approval['status'] != 'approved':
        return False, f"Approval status is '{approval['status']}'"

    if approval['timeout_at'] < datetime.now():
        return False, "Approval expired"

    return True, ""
```

**Create Approval Request**:
```python
async def create_approval_request(
    tool_name: str,
    parameters: dict,
    task_reference: str = None
) -> str:
    """Create approval request and return approval_id"""
    approval_id = str(uuid.uuid4())

    approval_data = {
        'approval_id': approval_id,
        'action_type': tool_name,
        'action_details': parameters,
        'risk_level': classify_risk(tool_name, parameters),
        'task_reference': task_reference,
        'created_at': datetime.now().isoformat(),
        'timeout_at': (datetime.now() + timedelta(hours=24)).isoformat(),
        'status': 'pending'
    }

    # Write to Needs_Approval folder
    write_approval_file(approval_id, approval_data)

    return approval_id
```

---

## Audit Logging

**Log Entry Format**:
```python
{
    "execution_id": "exec-123",
    "timestamp": "2026-02-14T11:00:00Z",
    "tool_name": "send_email",
    "parameters": {
        "to": ["recipient@example.com"],
        "subject": "Email subject"
        # Body omitted for privacy
    },
    "approval_id": "660e8400-e29b-41d4-a716-446655440001",
    "reviewer": "user@example.com",
    "result": {
        "success": True,
        "message_id": "sent-email-id-123"
    },
    "execution_time_ms": 1250
}
```

**Log Storage**: `vault/Logs/mcp-executions-YYYY-MM-DD.md`

**Privacy Considerations**:
- Omit email body content (log subject only)
- Omit WhatsApp message content
- Omit LinkedIn post content (log post_id only)
- Log only metadata for audit trail

---

## Rate Limiting

**Per-Tool Rate Limits**:
```python
RATE_LIMITS = {
    "send_email": {
        "max_per_minute": 5,
        "max_per_hour": 50,
        "max_per_day": 200
    },
    "post_linkedin": {
        "max_per_hour": 3,
        "max_per_day": 5
    },
    "send_whatsapp": {
        "max_per_minute": 5,
        "max_per_hour": 50
    }
}
```

**Rate Limit Check**:
```python
def check_rate_limit(tool_name: str) -> tuple[bool, str]:
    """Check if tool execution is within rate limits"""
    limits = RATE_LIMITS.get(tool_name)
    if not limits:
        return True, ""

    recent_executions = get_recent_executions(tool_name)

    # Check per-minute limit
    last_minute = [e for e in recent_executions
                   if e['timestamp'] > datetime.now() - timedelta(minutes=1)]
    if len(last_minute) >= limits['max_per_minute']:
        return False, "Rate limit exceeded (per minute)"

    # Check per-hour limit
    last_hour = [e for e in recent_executions
                 if e['timestamp'] > datetime.now() - timedelta(hours=1)]
    if len(last_hour) >= limits['max_per_hour']:
        return False, "Rate limit exceeded (per hour)"

    return True, ""
```

---

## Error Handling

**Error Categories**:
```python
class MCPError(Exception):
    """Base MCP error"""
    pass

class ToolNotFoundError(MCPError):
    """Tool not registered"""
    pass

class ValidationError(MCPError):
    """Parameter validation failed"""
    pass

class ApprovalRequiredError(MCPError):
    """Action requires approval"""
    pass

class ApprovalDeniedError(MCPError):
    """Approval was rejected or expired"""
    pass

class RateLimitError(MCPError):
    """Rate limit exceeded"""
    pass

class ExecutionError(MCPError):
    """Tool execution failed"""
    pass
```

**Error Response**:
```python
{
    "success": False,
    "error": {
        "type": "ApprovalRequiredError",
        "code": "APPROVAL_REQUIRED",
        "message": "This action requires human approval",
        "details": {
            "approval_id": "660e8400-e29b-41d4-a716-446655440001",
            "approval_url": "vault/Needs_Approval/660e8400-e29b-41d4-a716-446655440001.md"
        }
    }
}
```

---

## Rollback Capability

**Rollback Support** (where possible):
```python
ROLLBACK_HANDLERS = {
    "send_email": gmail_tool.delete_draft,  # If draft created
    "post_linkedin": linkedin_tool.delete_post,  # Within 24 hours
    "send_whatsapp": None  # Cannot rollback sent messages
}

async def rollback_execution(execution_id: str) -> bool:
    """Attempt to rollback a tool execution"""
    execution = get_execution_log(execution_id)

    rollback_handler = ROLLBACK_HANDLERS.get(execution['tool_name'])
    if not rollback_handler:
        return False  # Rollback not supported

    try:
        await rollback_handler(execution['result'])
        log_rollback(execution_id, success=True)
        return True
    except Exception as e:
        log_rollback(execution_id, success=False, error=str(e))
        return False
```

---

## Testing Strategy

**Unit Tests**:
- Test tool registration
- Test parameter validation
- Test approval checking
- Test rate limiting
- Test error handling

**Integration Tests**:
- Test end-to-end tool execution
- Test approval workflow
- Test audit logging
- Test rollback capability

**Mock Tools**:
```python
# tests/fixtures/mock_tools.py
async def mock_send_email(to, subject, body):
    """Mock email sending for tests"""
    return {"message_id": "test-123", "status": "sent"}

async def mock_post_linkedin(content, hashtags):
    """Mock LinkedIn posting for tests"""
    return {"post_id": "urn:li:share:test-456"}
```

---

## Implementation Checklist

- [ ] MCPServer class implementation
- [ ] Tool registry with metadata
- [ ] Parameter validation
- [ ] Risk classification
- [ ] Approval integration
- [ ] Audit logging
- [ ] Rate limiting
- [ ] Error handling
- [ ] Rollback capability
- [ ] Unit tests
- [ ] Integration tests
- [ ] Documentation

---

## Security Considerations

- Validate all tool parameters (prevent injection)
- Require approval for medium/high risk actions
- Log all executions (audit trail)
- Implement rate limiting (prevent abuse)
- Sanitize logged data (privacy)
- Use HTTPS for external API calls
- Handle secrets securely (never log)
- Implement timeout for long-running tools

---

## Performance Considerations

- Async execution for non-blocking operations
- Connection pooling for API clients
- Caching for frequently accessed data
- Batch operations where possible
- Timeout handling (max 60 seconds per tool)
- Memory-efficient logging (rotate logs daily)

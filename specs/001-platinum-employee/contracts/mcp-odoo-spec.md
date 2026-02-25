# MCP Odoo Server Specification

**Version**: 1.0.0
**Date**: 2026-02-25
**Purpose**: Define the MCP server interface for Odoo Community Edition integration

## Overview

The Odoo MCP server provides a Model Context Protocol interface for interacting with Odoo Community Edition v19+. This server enables the local agent to post approved accounting entries to Odoo while maintaining proper authentication, validation, and error handling.

## Server Configuration

### Connection Parameters

```json
{
  "name": "odoo",
  "command": "python",
  "args": ["-m", "mcp_servers.odoo_mcp.src.server"],
  "env": {
    "ODOO_URL": "https://odoo.example.com",
    "ODOO_DATABASE": "production",
    "ODOO_USERNAME": "admin@example.com",
    "ODOO_PASSWORD": "${ODOO_PASSWORD}",
    "ODOO_API_KEY": "${ODOO_API_KEY}"
  }
}
```

### Environment Variables

- `ODOO_URL`: Odoo server URL (HTTPS required)
- `ODOO_DATABASE`: Odoo database name
- `ODOO_USERNAME`: Odoo user email
- `ODOO_PASSWORD`: Odoo user password (stored in .env)
- `ODOO_API_KEY`: Odoo API key (alternative to password)

## MCP Tools

### 1. create_invoice

**Purpose**: Create a customer invoice in Odoo

**Parameters**:
```json
{
  "partner_id": "integer (required) - Odoo partner ID",
  "invoice_date": "string (required) - Invoice date (YYYY-MM-DD)",
  "invoice_lines": [
    {
      "product_id": "integer (required) - Product ID",
      "quantity": "number (required) - Quantity",
      "price_unit": "number (required) - Unit price",
      "account_id": "integer (optional) - Account ID",
      "name": "string (optional) - Description"
    }
  ],
  "payment_term_id": "integer (optional) - Payment term ID",
  "currency_id": "integer (optional) - Currency ID (default: company currency)"
}
```

**Returns**:
```json
{
  "invoice_id": "integer - Created invoice ID",
  "invoice_number": "string - Invoice number",
  "amount_total": "number - Total amount",
  "state": "string - Invoice state (draft, posted)"
}
```

**Errors**:
- `InvalidPartnerError`: Partner ID does not exist
- `InvalidProductError`: Product ID does not exist
- `ValidationError`: Invoice data validation failed
- `OdooAPIError`: Odoo API call failed

### 2. register_payment

**Purpose**: Register a payment for an invoice

**Parameters**:
```json
{
  "invoice_id": "integer (required) - Invoice ID",
  "amount": "number (required) - Payment amount",
  "payment_date": "string (required) - Payment date (YYYY-MM-DD)",
  "journal_id": "integer (required) - Payment journal ID",
  "payment_method_id": "integer (required) - Payment method ID",
  "communication": "string (optional) - Payment reference"
}
```

**Returns**:
```json
{
  "payment_id": "integer - Created payment ID",
  "payment_reference": "string - Payment reference",
  "amount": "number - Payment amount",
  "state": "string - Payment state (draft, posted)"
}
```

**Errors**:
- `InvalidInvoiceError`: Invoice ID does not exist
- `InvalidAmountError`: Payment amount exceeds invoice amount
- `ValidationError`: Payment data validation failed
- `OdooAPIError`: Odoo API call failed

### 3. create_expense

**Purpose**: Create an expense entry in Odoo

**Parameters**:
```json
{
  "product_id": "integer (required) - Expense product ID",
  "quantity": "number (required) - Quantity",
  "unit_amount": "number (required) - Unit amount",
  "date": "string (required) - Expense date (YYYY-MM-DD)",
  "employee_id": "integer (required) - Employee ID",
  "description": "string (optional) - Expense description",
  "analytic_account_id": "integer (optional) - Analytic account ID"
}
```

**Returns**:
```json
{
  "expense_id": "integer - Created expense ID",
  "expense_reference": "string - Expense reference",
  "total_amount": "number - Total amount",
  "state": "string - Expense state (draft, submitted, approved)"
}
```

**Errors**:
- `InvalidProductError`: Product ID does not exist
- `InvalidEmployeeError`: Employee ID does not exist
- `ValidationError`: Expense data validation failed
- `OdooAPIError`: Odoo API call failed

### 4. get_partner

**Purpose**: Search for a partner by name or email

**Parameters**:
```json
{
  "name": "string (optional) - Partner name",
  "email": "string (optional) - Partner email",
  "limit": "integer (optional) - Max results (default: 10)"
}
```

**Returns**:
```json
{
  "partners": [
    {
      "id": "integer - Partner ID",
      "name": "string - Partner name",
      "email": "string - Partner email",
      "phone": "string - Partner phone",
      "is_company": "boolean - Is company flag"
    }
  ]
}
```

**Errors**:
- `NoResultsError`: No partners found matching criteria
- `OdooAPIError`: Odoo API call failed

### 5. get_account

**Purpose**: Get account by code or name

**Parameters**:
```json
{
  "code": "string (optional) - Account code",
  "name": "string (optional) - Account name",
  "account_type": "string (optional) - Account type filter"
}
```

**Returns**:
```json
{
  "accounts": [
    {
      "id": "integer - Account ID",
      "code": "string - Account code",
      "name": "string - Account name",
      "account_type": "string - Account type",
      "currency_id": "integer - Currency ID"
    }
  ]
}
```

**Errors**:
- `NoResultsError`: No accounts found matching criteria
- `OdooAPIError`: Odoo API call failed

### 6. validate_entry

**Purpose**: Validate accounting entry before posting (dry-run)

**Parameters**:
```json
{
  "entry_type": "string (required) - invoice | payment | expense",
  "entry_data": "object (required) - Entry data matching create_* parameters"
}
```

**Returns**:
```json
{
  "valid": "boolean - Validation result",
  "errors": ["array of validation error messages"],
  "warnings": ["array of validation warning messages"]
}
```

**Errors**:
- `ValidationError`: Entry data validation failed
- `OdooAPIError`: Odoo API call failed

## MCP Resources

### 1. odoo://partners

**Purpose**: List all partners

**Returns**: JSON array of partner objects

### 2. odoo://accounts

**Purpose**: List all accounts

**Returns**: JSON array of account objects

### 3. odoo://journals

**Purpose**: List all journals

**Returns**: JSON array of journal objects

### 4. odoo://products

**Purpose**: List all products

**Returns**: JSON array of product objects

## Authentication

### API Key Authentication (Recommended)

```python
import odoorpc

odoo = odoorpc.ODOO(url, protocol='jsonrpc+ssl', port=443)
odoo.login(database, username, api_key)
```

### Password Authentication (Fallback)

```python
import odoorpc

odoo = odoorpc.ODOO(url, protocol='jsonrpc+ssl', port=443)
odoo.login(database, username, password)
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "string - Error code",
    "message": "string - Human-readable error message",
    "details": "object - Additional error details"
  }
}
```

### Error Codes

- `AUTHENTICATION_FAILED`: Invalid credentials
- `CONNECTION_ERROR`: Cannot connect to Odoo server
- `INVALID_PARAMETER`: Invalid parameter value
- `VALIDATION_ERROR`: Data validation failed
- `NOT_FOUND`: Resource not found
- `PERMISSION_DENIED`: Insufficient permissions
- `ODOO_API_ERROR`: Odoo API returned error
- `TIMEOUT`: Request timeout

### Retry Logic

- Transient errors (connection, timeout): Retry with exponential backoff (max 3 attempts)
- Permanent errors (authentication, validation): Do not retry, return error immediately
- Circuit breaker: Open after 5 consecutive failures, half-open after 60 seconds

## Validation Rules

### Invoice Validation

- Partner ID must exist in Odoo
- Invoice date must not be in the future
- Invoice lines must have valid product IDs
- Invoice lines must have positive quantities and prices
- Total amount must be positive

### Payment Validation

- Invoice ID must exist and be in posted state
- Payment amount must not exceed invoice residual amount
- Payment date must not be before invoice date
- Journal ID must exist and be of type 'bank' or 'cash'
- Payment method ID must exist

### Expense Validation

- Product ID must exist and be of type 'expense'
- Employee ID must exist
- Expense date must not be in the future
- Unit amount must be positive
- Quantity must be positive

## Performance Considerations

### Connection Pooling

- Maintain connection pool (max 5 connections)
- Reuse connections for multiple requests
- Close idle connections after 5 minutes

### Caching

- Cache partner lookups (TTL: 1 hour)
- Cache account lookups (TTL: 1 hour)
- Cache product lookups (TTL: 1 hour)
- Invalidate cache on create/update operations

### Batch Operations

- Support batch invoice creation (max 10 invoices per batch)
- Support batch payment registration (max 10 payments per batch)
- Use Odoo's batch API when available

## Security Considerations

### Credential Storage

- Store credentials in environment variables (.env file)
- Never log credentials
- Use API key authentication when possible (more secure than password)

### HTTPS Requirement

- Always use HTTPS for Odoo connections
- Verify SSL certificates
- Reject self-signed certificates in production

### Access Control

- Use dedicated Odoo user for MCP server (not admin)
- Grant minimum required permissions (accounting only)
- Audit all MCP operations in Odoo logs

### Data Sanitization

- Sanitize all input parameters
- Validate data types and ranges
- Escape special characters in strings
- Prevent SQL injection (use ORM only)

## Testing

### Unit Tests

- Test each MCP tool with valid parameters
- Test error handling for invalid parameters
- Test authentication (success and failure)
- Test connection pooling and caching

### Integration Tests

- Test against real Odoo instance (test database)
- Test invoice creation and payment registration flow
- Test expense creation flow
- Test partner and account lookups

### Contract Tests

- Verify MCP tool signatures match specification
- Verify error response format
- Verify authentication methods
- Verify resource endpoints

## Deployment

### Cloud VM Deployment

1. Install Python 3.9+ and pip
2. Install odoorpc library: `pip install odoorpc`
3. Configure environment variables in .env file
4. Start MCP server: `python -m mcp_servers.odoo_mcp.src.server`
5. Verify connection to Odoo: `curl http://localhost:8080/health`

### Health Check

```bash
curl http://localhost:8080/health
```

**Response**:
```json
{
  "status": "healthy",
  "odoo_connection": "connected",
  "odoo_version": "19.0",
  "database": "production"
}
```

## Monitoring

### Metrics

- Request count (by tool)
- Request latency (p50, p95, p99)
- Error rate (by error code)
- Connection pool utilization
- Cache hit rate

### Logging

- Log all MCP tool calls with parameters (sanitized)
- Log all Odoo API calls with response times
- Log all errors with stack traces
- Log authentication attempts (success and failure)

### Alerts

- Alert on authentication failures (> 3 in 5 minutes)
- Alert on high error rate (> 10% in 5 minutes)
- Alert on connection failures (> 5 in 5 minutes)
- Alert on slow requests (> 5 seconds)

## Example Usage

### Create Invoice

```python
# Local agent calls MCP tool
result = mcp_client.call_tool("create_invoice", {
    "partner_id": 123,
    "invoice_date": "2026-02-25",
    "invoice_lines": [
        {
            "product_id": 456,
            "quantity": 1,
            "price_unit": 1500.00,
            "name": "Consulting Services - January 2026"
        }
    ]
})

# Result
{
    "invoice_id": 789,
    "invoice_number": "INV/2026/0001",
    "amount_total": 1500.00,
    "state": "draft"
}
```

### Register Payment

```python
# Local agent calls MCP tool
result = mcp_client.call_tool("register_payment", {
    "invoice_id": 789,
    "amount": 1500.00,
    "payment_date": "2026-02-25",
    "journal_id": 1,
    "payment_method_id": 1,
    "communication": "Payment for INV/2026/0001"
})

# Result
{
    "payment_id": 101,
    "payment_reference": "PAY/2026/0001",
    "amount": 1500.00,
    "state": "posted"
}
```

### Validate Entry (Dry-Run)

```python
# Local agent validates before posting
result = mcp_client.call_tool("validate_entry", {
    "entry_type": "invoice",
    "entry_data": {
        "partner_id": 123,
        "invoice_date": "2026-02-25",
        "invoice_lines": [...]
    }
})

# Result
{
    "valid": true,
    "errors": [],
    "warnings": ["Invoice date is in the past"]
}
```

## Version Compatibility

### Odoo Versions

- Odoo Community Edition v19+ (required)
- Odoo Community Edition v18 (supported with limitations)
- Odoo Enterprise Edition (not tested, may work)

### odoorpc Library

- odoorpc v0.10.1+ (required for Odoo 19)
- odoorpc v0.9.0+ (supported for Odoo 18)

### Python Versions

- Python 3.9+ (required)
- Python 3.8 (supported with limitations)

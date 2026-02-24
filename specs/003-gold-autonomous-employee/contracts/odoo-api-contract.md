# Odoo JSON-RPC API Contract

**Service**: Odoo Community Edition v19+
**Protocol**: JSON-RPC over HTTP/HTTPS
**Library**: odoorpc v0.10.1+
**Authentication**: Database credentials (username/password)

## Connection

### Endpoint
```
http://localhost:8069/jsonrpc
```

### Authentication
```python
import odoorpc

odoo = odoorpc.ODOO('localhost', port=8069)
odoo.login('database_name', 'username', 'password')
```

### Configuration (Environment Variables)
```bash
ODOO_HOST=localhost
ODOO_PORT=8069
ODOO_DB=business_db
ODOO_USER=admin
ODOO_PASSWORD=secure_password
```

---

## Operations

### 1. Sync Invoice (Read)

**Purpose**: Retrieve invoices created/modified since last sync

**Method**: `search_read`

**Request**:
```python
Invoice = odoo.env['account.move']
domain = [
    ('move_type', '=', 'out_invoice'),
    ('create_date', '>', last_sync_timestamp)
]
fields = ['name', 'partner_id', 'amount_total', 'currency_id', 'invoice_date', 'state']
invoices = Invoice.search_read(domain, fields)
```

**Response**:
```python
[
    {
        'id': 12345,
        'name': 'INV/2026/0001',
        'partner_id': [42, 'Acme Corp'],
        'amount_total': 1500.00,
        'currency_id': [1, 'USD'],
        'invoice_date': '2026-02-20',
        'state': 'posted'
    }
]
```

**Error Handling**:
- `odoorpc.error.RPCError`: Odoo server error (retry with backoff)
- `ConnectionError`: Network issue (retry with backoff)
- `TimeoutError`: Request timeout (retry with backoff)

**Rate Limit**: 60 calls/minute (configurable in MCP server)

---

### 2. Create Invoice (Write)

**Purpose**: Create new invoice in Odoo from vault transaction

**Method**: `create`

**Request**:
```python
Invoice = odoo.env['account.move']
invoice_data = {
    'move_type': 'out_invoice',
    'partner_id': customer_id,
    'invoice_date': '2026-02-20',
    'invoice_line_ids': [
        (0, 0, {
            'name': 'Consulting Services',
            'quantity': 1,
            'price_unit': 1500.00,
            'account_id': revenue_account_id
        })
    ]
}
invoice_id = Invoice.create(invoice_data)
```

**Response**:
```python
12345  # New invoice ID
```

**Validation**:
- `partner_id` must exist in Odoo
- `invoice_date` cannot be in future
- `invoice_line_ids` must have at least one line
- `account_id` must be valid revenue account

**Error Handling**:
- `odoorpc.error.RPCError` with "ValidationError": Invalid data (escalate to human)
- `odoorpc.error.RPCError` with "AccessError": Permission denied (escalate to human)
- Network errors: Retry with backoff

**Rate Limit**: 60 calls/minute

---

### 3. Create Expense (Write)

**Purpose**: Record expense in Odoo from vault transaction

**Method**: `create`

**Request**:
```python
Expense = odoo.env['hr.expense']
expense_data = {
    'name': 'Software Subscription',
    'product_id': product_id,
    'unit_amount': 99.00,
    'date': '2026-02-20',
    'employee_id': employee_id
}
expense_id = Expense.create(expense_data)
```

**Response**:
```python
67890  # New expense ID
```

**Validation**:
- `product_id` must exist
- `employee_id` must exist
- `unit_amount` must be positive
- `date` cannot be in future

**Error Handling**:
- Same as Create Invoice

**Rate Limit**: 60 calls/minute

---

### 4. Create Customer (Write)

**Purpose**: Create new customer/partner in Odoo

**Method**: `create`

**Request**:
```python
Partner = odoo.env['res.partner']
partner_data = {
    'name': 'New Customer Inc',
    'email': 'contact@newcustomer.com',
    'phone': '+1-555-0123',
    'is_company': True,
    'customer_rank': 1
}
partner_id = Partner.create(partner_data)
```

**Response**:
```python
42  # New partner ID
```

**Validation**:
- `name` is required
- `email` must be valid format (if provided)
- `phone` must be valid format (if provided)

**Error Handling**:
- Duplicate email: Return existing partner ID instead of error
- Network errors: Retry with backoff

**Rate Limit**: 60 calls/minute

---

### 5. Search Transactions (Read)

**Purpose**: Poll for changes every 5 minutes

**Method**: `search_read`

**Request**:
```python
# Get all transactions modified since last poll
domain = [
    '|', '|',
    ('move_type', '=', 'out_invoice'),
    ('move_type', '=', 'in_invoice'),
    ('move_type', '=', 'entry'),
    ('write_date', '>', last_poll_timestamp)
]
fields = ['name', 'move_type', 'partner_id', 'amount_total', 'date', 'state']
transactions = odoo.env['account.move'].search_read(domain, fields, limit=100)
```

**Response**:
```python
[
    {
        'id': 12345,
        'name': 'INV/2026/0001',
        'move_type': 'out_invoice',
        'partner_id': [42, 'Acme Corp'],
        'amount_total': 1500.00,
        'date': '2026-02-20',
        'state': 'posted'
    }
]
```

**Polling Strategy**:
- Interval: Every 5 minutes (300 seconds)
- Limit: 100 records per poll
- Timestamp tracking: Store `write_date` of last processed record

**Error Handling**:
- Network errors: Skip this poll cycle, retry next cycle
- No results: Normal, continue polling

**Rate Limit**: 12 calls/hour (every 5 minutes)

---

## Error Codes

| Error Type | Odoo Error | Recovery Strategy |
|------------|------------|-------------------|
| Network timeout | `ConnectionError` | Retry with exponential backoff (3 attempts) |
| Authentication failed | `RPCError: Access Denied` | Escalate to human (check credentials) |
| Validation error | `RPCError: ValidationError` | Escalate to human (fix data) |
| Record not found | `RPCError: MissingError` | Escalate to human (check references) |
| Rate limit exceeded | `RPCError: Too Many Requests` | Wait and retry (exponential backoff) |
| Server error | `RPCError: Internal Server Error` | Retry with backoff, escalate if persists |

---

## Rate Limiting

**Configuration**:
```yaml
rate_limits:
  calls_per_minute: 60
  calls_per_hour: 1000
  concurrent_requests: 5
```

**Implementation**:
- Use tenacity for retry logic
- Use pybreaker for circuit breaker (10 consecutive failures)
- Queue actions when circuit is open

---

## Data Mapping

### Odoo → Vault (OdooTransaction)

| Odoo Field | Vault Field | Transformation |
|------------|-------------|----------------|
| `id` | `odoo_id` | Direct mapping |
| `name` | Transaction title | Direct mapping |
| `move_type` | `type` | Map: out_invoice→invoice, in_invoice→expense, entry→journal_entry |
| `amount_total` | `amount` | Direct mapping |
| `currency_id[1]` | `currency` | Extract currency code |
| `date` or `invoice_date` | `date` | Direct mapping |
| `partner_id[1]` | `customer_vendor` | Extract partner name |
| `state` | Determines `sync_status` | posted→synced, draft→pending |

### Vault → Odoo (Create Operations)

| Vault Field | Odoo Field | Transformation |
|-------------|------------|----------------|
| `amount` | `amount_total` | Direct mapping |
| `currency` | `currency_id` | Lookup currency ID by code |
| `date` | `invoice_date` or `date` | Direct mapping |
| `customer_vendor` | `partner_id` | Lookup partner ID by name |
| `category` | `account_id` | Map category to account via Company_Handbook |

---

## Conflict Detection

**Scenario**: Same transaction modified in both Odoo and vault

**Detection**:
1. Compare `write_date` in Odoo with `updated_at` in vault
2. If both > `last_synced_at`, conflict exists

**Resolution**:
1. Set `conflict_flag: true` in vault transaction
2. Set `conflict_details` with both versions
3. Escalate to human for resolution
4. Do NOT overwrite either version automatically

---

## Testing

**Contract Tests** (tests/contract/test_odoo_contracts.py):
- Test connection and authentication
- Test each operation (create invoice, expense, customer)
- Test search and polling
- Test error handling for each error type
- Test rate limiting behavior
- Test conflict detection

**Mock Odoo Server**:
- Use `responses` library to mock HTTP responses
- Simulate success, errors, timeouts
- Verify request format and parameters

---

## Security

- Credentials stored in `.env` file (never in code or vault)
- Use HTTPS in production (HTTP acceptable for localhost)
- Validate all input data before sending to Odoo
- Sanitize error messages before logging (remove credentials)
- Use read-only user for polling operations (if possible)

---

## Performance

**Optimization**:
- Batch operations when possible (create multiple invoices in one call)
- Use `search_read` instead of separate `search` + `read`
- Limit fields in queries to only what's needed
- Cache partner/product lookups to reduce API calls

**Monitoring**:
- Track API call count per minute/hour
- Monitor response times (alert if >2 seconds)
- Log all errors for analysis
- Track sync lag (time between Odoo change and vault sync)

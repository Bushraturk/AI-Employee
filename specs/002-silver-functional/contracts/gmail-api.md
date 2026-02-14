# Gmail API Contract

**Version**: 1.0 | **Date**: 2026-02-14 | **Feature**: 002-silver-functional

## Overview

This contract defines the interface between the GmailWatcher and the Gmail API for email monitoring and sending.

## Authentication

**Method**: OAuth2 with refresh tokens

**Scopes Required**:
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails

**Token Storage**: OS keyring or encrypted file (outside vault)

**Token Refresh**: Automatic before expiration

---

## Endpoint: List Messages

**Purpose**: Retrieve new emails from inbox

**API Call**:
```python
GET https://www.googleapis.com/gmail/v1/users/me/messages
```

**Request Parameters**:
```python
{
    "q": "in:inbox is:unread",  # Query filter
    "maxResults": 10,             # Limit results
    "labelIds": ["INBOX"]         # Filter by labels
}
```

**Response**:
```json
{
    "messages": [
        {
            "id": "18d1e2f3a4b5c6d7",
            "threadId": "18d1e2f3a4b5c6d7"
        }
    ],
    "nextPageToken": "token123",
    "resultSizeEstimate": 42
}
```

**Rate Limits**: 250 quota units per user per second

**Error Handling**:
- 401 Unauthorized → Refresh token and retry
- 403 Forbidden → Check scopes, re-authenticate
- 429 Too Many Requests → Exponential backoff
- 500 Server Error → Retry with backoff

---

## Endpoint: Get Message

**Purpose**: Retrieve full email content and metadata

**API Call**:
```python
GET https://www.googleapis.com/gmail/v1/users/me/messages/{id}
```

**Request Parameters**:
```python
{
    "format": "full",  # full, metadata, minimal, raw
    "metadataHeaders": ["From", "To", "Subject", "Date"]
}
```

**Response**:
```json
{
    "id": "18d1e2f3a4b5c6d7",
    "threadId": "18d1e2f3a4b5c6d7",
    "labelIds": ["INBOX", "UNREAD"],
    "snippet": "Email preview text...",
    "payload": {
        "headers": [
            {"name": "From", "value": "sender@example.com"},
            {"name": "Subject", "value": "Email subject"},
            {"name": "Date", "value": "Thu, 14 Feb 2026 10:30:00 +0000"}
        ],
        "body": {
            "data": "base64_encoded_content"
        }
    },
    "internalDate": "1708771800000"
}
```

**Data Extraction**:
- Decode base64 body content
- Parse headers for sender, subject, date
- Extract thread_id for reply threading
- Store message_id for reference

---

## Endpoint: Send Message

**Purpose**: Send email (reply or new)

**API Call**:
```python
POST https://www.googleapis.com/gmail/v1/users/me/messages/send
```

**Request Body**:
```json
{
    "raw": "base64_encoded_rfc822_message"
}
```

**RFC 822 Message Format**:
```
From: me@example.com
To: recipient@example.com
Subject: Re: Original subject
In-Reply-To: <original-message-id>
References: <original-message-id>

Email body content here.
```

**Response**:
```json
{
    "id": "18d1e2f3a4b5c6d8",
    "threadId": "18d1e2f3a4b5c6d7",
    "labelIds": ["SENT"]
}
```

**Rate Limits**: 100 quota units per user per second (sending)

**Error Handling**:
- 400 Bad Request → Validate message format
- 401 Unauthorized → Refresh token
- 403 Forbidden → Check send scope
- 429 Too Many Requests → Queue and retry

---

## Endpoint: Modify Message

**Purpose**: Mark email as read, add/remove labels

**API Call**:
```python
POST https://www.googleapis.com/gmail/v1/users/me/messages/{id}/modify
```

**Request Body**:
```json
{
    "addLabelIds": ["Label_123"],
    "removeLabelIds": ["UNREAD"]
}
```

**Response**:
```json
{
    "id": "18d1e2f3a4b5c6d7",
    "threadId": "18d1e2f3a4b5c6d7",
    "labelIds": ["INBOX", "Label_123"]
}
```

---

## Incremental Sync Pattern

**Purpose**: Avoid re-processing emails using historyId

**Initial Sync**:
1. Get current historyId: `GET /users/me/profile`
2. Store historyId in watcher state
3. Process all unread messages

**Subsequent Syncs**:
1. Get history since last historyId: `GET /users/me/history?startHistoryId={id}`
2. Process only new/modified messages
3. Update stored historyId

**History Response**:
```json
{
    "history": [
        {
            "id": "12345",
            "messages": [{"id": "msg1"}],
            "messagesAdded": [{"message": {...}}]
        }
    ],
    "historyId": "12346"
}
```

---

## Local Caching Strategy

**Cache Structure**:
```
vault/.cache/gmail/
├── messages/
│   └── {message_id}.json  # Full message metadata
└── state.json             # historyId, last_sync_at
```

**Cache Benefits**:
- Reduce API calls (stay under rate limits)
- Enable offline task viewing
- Faster classification (no API wait)

**Cache Invalidation**:
- Refresh every 24 hours
- Clear on authentication change
- Manual clear via CLI command

---

## Error Codes Reference

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Validate request format |
| 401 | Unauthorized | Refresh OAuth2 token |
| 403 | Forbidden | Check scopes, re-authenticate |
| 404 | Not Found | Message deleted, skip |
| 429 | Rate Limit | Exponential backoff (start 1s, max 60s) |
| 500 | Server Error | Retry with backoff |
| 503 | Service Unavailable | Retry with backoff |

---

## Rate Limit Management

**Quota Units**:
- List messages: 5 units
- Get message: 5 units
- Send message: 100 units
- Modify message: 5 units

**Daily Quota**: 1 billion units per day (effectively unlimited for single user)

**Per-Second Quota**: 250 units per user per second

**Strategy**:
- Track quota usage in-memory
- Implement token bucket algorithm
- Queue requests when approaching limit
- Use batch requests where possible

---

## Testing Strategy

**Unit Tests**:
- Mock Gmail API responses
- Test OAuth2 flow
- Test error handling
- Test rate limit backoff

**Integration Tests**:
- Use Gmail API test account
- Send/receive test emails
- Verify incremental sync
- Test token refresh

**Fixtures**:
```python
# tests/fixtures/mock_gmail_api.py
MOCK_MESSAGE_RESPONSE = {
    "id": "test123",
    "threadId": "thread123",
    "payload": {...}
}
```

---

## Security Considerations

- Never log email content (PII)
- Store tokens securely (OS keyring)
- Validate sender addresses (prevent spoofing)
- Sanitize email content before processing
- Use HTTPS only (enforced by API)
- Rotate tokens periodically (90 days)

---

## Implementation Checklist

- [ ] OAuth2 authentication flow
- [ ] Token storage and refresh
- [ ] List messages endpoint
- [ ] Get message endpoint
- [ ] Send message endpoint
- [ ] Incremental sync with historyId
- [ ] Rate limit handling
- [ ] Error handling and retries
- [ ] Local caching
- [ ] Unit tests with mocks
- [ ] Integration tests with test account

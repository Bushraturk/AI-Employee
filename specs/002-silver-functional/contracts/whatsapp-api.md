# WhatsApp Integration Contract

**Version**: 1.0 | **Date**: 2026-02-14 | **Feature**: 002-silver-functional

## Overview

This contract defines two integration approaches for WhatsApp: web automation (MVP) and Business API (production scale).

## Approach 1: Web Automation (MVP)

**Technology**: Playwright for web.whatsapp.com automation

**Rationale**: Faster setup, no business verification required, suitable for MVP

**Limitations**:
- Requires QR code scan
- Session may expire
- Risk of automation detection
- Not suitable for high volume

---

### Authentication (Web Automation)

**Method**: QR code scan with session persistence

**Setup Flow**:
1. Launch browser with persistent context
2. Navigate to web.whatsapp.com
3. Display QR code for user to scan
4. Wait for successful authentication
5. Save session data for future use

**Session Storage**: `./whatsapp_session/` (outside vault, not in git)

**Session Expiration**: Variable (days to weeks), requires re-scan

---

### Operation: Monitor Messages

**Purpose**: Detect new incoming messages

**Implementation**:
```python
from playwright.async_api import async_playwright

async def monitor_messages():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Required for QR scan
            user_data_dir='./whatsapp_session'
        )
        page = await browser.new_page()
        await page.goto('https://web.whatsapp.com')

        # Wait for chat list to load
        await page.wait_for_selector('[data-testid="chat-list"]')

        # Monitor for new messages
        await page.on('response', handle_new_message)
```

**Message Detection**:
- Monitor DOM for new message elements
- Watch for unread message indicators
- Listen to WebSocket events (if accessible)

**Message Extraction**:
```python
message_data = {
    "sender": "+1234567890",
    "sender_name": "John Doe",
    "message_text": "Can you help with...",
    "timestamp": "2026-02-14T10:30:00Z",
    "chat_type": "direct",  # or "group"
    "group_name": "Team Chat",  # if group
    "message_id": "unique_msg_id"
}
```

**Selectors** (may change):
```python
SELECTORS = {
    "chat_list": '[data-testid="chat-list"]',
    "message_text": '[data-testid="msg-text"]',
    "sender_name": '[data-testid="sender-name"]',
    "unread_indicator": '[data-testid="unread-count"]'
}
```

---

### Operation: Send Message

**Purpose**: Send text message to contact or group

**Implementation**:
```python
async def send_message(phone_number: str, message: str):
    # Navigate to chat
    await page.goto(f'https://web.whatsapp.com/send?phone={phone_number}')

    # Wait for input box
    input_box = await page.wait_for_selector('[data-testid="conversation-compose-box-input"]')

    # Type message
    await input_box.type(message)

    # Click send button
    send_button = await page.wait_for_selector('[data-testid="send"]')
    await send_button.click()

    # Wait for message to be sent (checkmark)
    await page.wait_for_selector('[data-testid="msg-check"]')
```

**Rate Limiting**:
- Max 5 messages per minute (avoid spam detection)
- Add random delays (1-3 seconds) between messages
- Monitor for warning messages

---

### Error Handling (Web Automation)

| Error | Detection | Action |
|-------|-----------|--------|
| Session Expired | Login screen appears | Notify user, require QR scan |
| Connection Lost | Network error | Reconnect, resume monitoring |
| Automation Detected | Verification prompt | Pause, notify user, manual verification |
| Rate Limited | Warning message | Pause sending, wait 1 hour |
| Element Not Found | Selector timeout | Update selectors, retry |

---

### Limitations & Risks

**Limitations**:
- Requires browser window (headless may be detected)
- Session expires unpredictably
- Selectors may change (WhatsApp updates)
- No official API support
- Limited to single device

**Risks**:
- Account ban if detected as bot
- Terms of Service violation
- Unreliable for production use
- Maintenance burden (selector updates)

**Mitigation**:
- Conservative message frequency
- Human-like delays
- Monitor for warnings
- Document migration path to Business API
- Provide manual fallback

---

## Approach 2: WhatsApp Business API (Production)

**Technology**: WhatsApp Cloud API (Meta)

**Rationale**: Official, reliable, scalable, suitable for production

**Requirements**:
- Meta Business Account
- Business verification (weeks)
- Phone number registration
- Webhook endpoint (for receiving messages)

---

### Authentication (Business API)

**Method**: Access token from Meta Business Manager

**Setup**:
1. Create Meta Business Account
2. Register phone number
3. Complete business verification
4. Generate access token
5. Configure webhook for incoming messages

**Token Storage**: OS keyring or encrypted file

**Token Type**: Long-lived access token (60 days)

---

### Endpoint: Send Message

**Purpose**: Send text message to WhatsApp user

**API Call**:
```python
POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
```

**Headers**:
```python
{
    "Authorization": "Bearer {access_token}",
    "Content-Type": "application/json"
}
```

**Request Body** (Text Message):
```json
{
    "messaging_product": "whatsapp",
    "to": "1234567890",
    "type": "text",
    "text": {
        "body": "Message content here"
    }
}
```

**Response**:
```json
{
    "messaging_product": "whatsapp",
    "contacts": [
        {
            "input": "1234567890",
            "wa_id": "1234567890"
        }
    ],
    "messages": [
        {
            "id": "wamid.HBgLMTIzNDU2Nzg5MAA="
        }
    ]
}
```

---

### Endpoint: Receive Messages (Webhook)

**Purpose**: Receive incoming messages via webhook

**Webhook URL**: `https://your-domain.com/webhook/whatsapp`

**Verification Request** (GET):
```python
GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token={token}&hub.challenge={challenge}
```

**Verification Response**:
```python
return hub.challenge  # Echo back the challenge
```

**Message Notification** (POST):
```json
{
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "business_account_id",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "1234567890",
                            "phone_number_id": "phone_id"
                        },
                        "contacts": [
                            {
                                "profile": {"name": "John Doe"},
                                "wa_id": "1234567890"
                            }
                        ],
                        "messages": [
                            {
                                "from": "1234567890",
                                "id": "wamid.ABC123",
                                "timestamp": "1708771800",
                                "text": {"body": "Message content"},
                                "type": "text"
                            }
                        ]
                    },
                    "field": "messages"
                }
            ]
        }
    ]
}
```

---

### Rate Limits (Business API)

**Messaging Limits** (tiered):
- Tier 1: 1,000 conversations per 24 hours
- Tier 2: 10,000 conversations per 24 hours
- Tier 3: 100,000 conversations per 24 hours
- Tier 4: Unlimited

**Tier Progression**: Automatic based on quality rating

**Quality Rating**: Based on user blocks, reports, and engagement

---

### Error Codes (Business API)

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Validate message format |
| 401 | Unauthorized | Refresh access token |
| 403 | Forbidden | Check permissions |
| 429 | Rate Limit | Queue message, retry later |
| 470 | Message Failed | User blocked or invalid number |
| 500 | Server Error | Retry with backoff |

---

## Implementation Strategy

**Phase 1 (MVP)**: Web Automation
- Faster setup (no business verification)
- Suitable for testing and low volume
- Document limitations clearly

**Phase 2 (Production)**: Business API
- Apply for business verification early
- Migrate when volume increases
- Maintain backward compatibility

**Migration Path**:
1. Implement web automation first
2. Apply for Business API access in parallel
3. Build Business API integration
4. Test both approaches
5. Switch to Business API when approved
6. Deprecate web automation

---

## Data Model

**WhatsApp Message Entity**:
```yaml
message_id: "wamid.ABC123"
sender: "+1234567890"
sender_name: "John Doe"
message_text: "Can you help with..."
timestamp: "2026-02-14T10:30:00Z"
chat_type: "direct"  # or "group"
group_name: "Team Chat"  # if group
status: "received|sent|delivered|read|failed"
```

**Storage**: Convert to Task entity in vault/Inbox/

---

## Testing Strategy

**Web Automation Tests**:
- Mock Playwright browser
- Test message detection
- Test message sending
- Test session persistence
- Test error handling

**Business API Tests**:
- Mock WhatsApp API responses
- Test webhook verification
- Test message sending
- Test webhook message parsing
- Test rate limit handling

**Integration Tests**:
- Use test WhatsApp account
- Send/receive test messages
- Verify task creation
- Test end-to-end flow

---

## Security Considerations

- Never log message content (PII)
- Store session data securely (outside vault)
- Validate webhook signatures (Business API)
- Sanitize message content before processing
- Use HTTPS for webhooks
- Rotate access tokens periodically
- Monitor for suspicious activity

---

## Implementation Checklist

**Web Automation (MVP)**:
- [ ] Playwright setup
- [ ] QR code authentication
- [ ] Session persistence
- [ ] Message monitoring
- [ ] Message sending
- [ ] Error handling
- [ ] Rate limit protection
- [ ] Unit tests with mocks

**Business API (Production)**:
- [ ] Meta Business Account setup
- [ ] Business verification
- [ ] Phone number registration
- [ ] Webhook endpoint
- [ ] Webhook verification
- [ ] Send message endpoint
- [ ] Receive message webhook
- [ ] Rate limit handling
- [ ] Error handling
- [ ] Unit tests with mocks
- [ ] Integration tests

---

## Recommendation

**Start with**: Web Automation (Playwright) for MVP
**Migrate to**: Business API when:
- Volume exceeds 50 messages/day
- Automation detection occurs
- Business verification completes
- Production reliability required

**Timeline**:
- Week 1-2: Implement web automation
- Week 1 (parallel): Apply for Business API
- Week 3-4: Implement Business API
- Week 5: Migration and testing

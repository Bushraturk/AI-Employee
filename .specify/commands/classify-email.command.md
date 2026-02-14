"""
Agent Skill: Classify Email

Classifies incoming emails as task, question, notification, spam, or other.
Extracts priority, category, and metadata.
"""

# Purpose
Classify incoming email and extract task metadata

# Input Format
- Email subject
- Email body
- Sender information
- Timestamp

# Output Format (JSON)
```json
{
  "classification": "task|question|notification|spam|other",
  "confidence": 0.95,
  "priority": "P1|P2|P3",
  "category": "support|sales|internal|technical|administrative",
  "extracted_metadata": {
    "due_date": "2026-02-20",
    "action_required": "Reply with pricing information",
    "urgency_indicators": ["urgent", "asap"],
    "key_entities": ["customer name", "product name"]
  }
}
```

# Classification Rules

## Task Classification
Email is a TASK if it contains:
- Action verbs: "please", "can you", "need", "request", "send", "provide", "review", "approve"
- Questions requiring action
- Requests for information or deliverables
- Follow-up items from meetings

## Question Classification
Email is a QUESTION if it:
- Asks for information without requiring action
- Seeks clarification
- Is informational inquiry

## Notification Classification
Email is a NOTIFICATION if it:
- Is automated (from noreply@, no-reply@)
- Contains status updates
- Is a receipt or confirmation
- Is a newsletter or announcement

## Spam Classification
Email is SPAM if it:
- Contains excessive promotional language
- Has suspicious links
- Is from unknown sender with generic content
- Contains typical spam indicators

## Priority Extraction

**P1 (High Priority)** - Urgent, requires immediate attention:
- Keywords: "urgent", "asap", "critical", "emergency", "immediate"
- Deadline within 24 hours
- From VIP contacts (CEO, key customers)
- Contains "urgent" in subject line

**P2 (Medium Priority)** - Important, requires timely response:
- Keywords: "important", "soon", "deadline"
- Deadline within 1 week
- From regular business contacts
- Standard business requests

**P3 (Low Priority)** - Can be handled later:
- No urgency indicators
- No specific deadline
- Informational or routine
- Can wait for batch processing

## Category Extraction

- **support**: Customer support requests, bug reports, help requests
- **sales**: Sales inquiries, pricing questions, demos, proposals
- **internal**: Internal team communication, updates, coordination
- **technical**: Technical questions, API issues, integration problems
- **administrative**: HR, finance, operations, scheduling

# Examples

## Example 1: Task Email
**Input:**
```
Subject: Urgent: Need pricing for enterprise plan
From: customer@company.com
Body: Hi, we need pricing information for 100+ users on the enterprise plan. Can you send this by end of day? Thanks!
```

**Output:**
```json
{
  "classification": "task",
  "confidence": 0.95,
  "priority": "P1",
  "category": "sales",
  "extracted_metadata": {
    "due_date": "2026-02-14T23:59:59Z",
    "action_required": "Provide enterprise pricing for 100+ users",
    "urgency_indicators": ["urgent", "end of day"],
    "key_entities": ["enterprise plan", "100+ users"]
  }
}
```

## Example 2: Notification Email
**Input:**
```
Subject: Your order has shipped
From: noreply@store.com
Body: Your order #12345 has been shipped and will arrive in 3-5 business days.
```

**Output:**
```json
{
  "classification": "notification",
  "confidence": 0.98,
  "priority": "P3",
  "category": "administrative",
  "extracted_metadata": {
    "due_date": null,
    "action_required": null,
    "urgency_indicators": [],
    "key_entities": ["order #12345"]
  }
}
```

# Edge Cases

- **Ambiguous emails**: Default to "question" with lower confidence
- **Multiple requests**: Extract primary action, note secondary actions in metadata
- **No clear priority**: Default to P2 (medium)
- **Unknown category**: Default to "internal"
- **Multi-language**: Detect language, translate key phrases for classification

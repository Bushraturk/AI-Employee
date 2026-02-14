"""
Agent Skill: Classify WhatsApp Message

Classifies WhatsApp messages and extracts task information from conversational text.
"""

# Purpose
Classify WhatsApp messages and extract task metadata from conversational context

# Input Format
- Message text
- Sender name
- Sender phone number
- Chat type (direct/group)
- Group name (if applicable)
- Timestamp

# Output Format (JSON)
```json
{
  "classification": "task|question|casual|notification|spam",
  "confidence": 0.90,
  "priority": "P1|P2|P3",
  "category": "support|sales|internal|personal",
  "extracted_metadata": {
    "action_required": "Schedule meeting for next week",
    "urgency_indicators": ["asap", "urgent"],
    "context": "Follow-up from previous conversation",
    "key_entities": ["meeting", "next week"]
  }
}
```

# Classification Rules

## Task Classification
Message is a TASK if it contains:
- Direct requests: "can you", "please", "need you to"
- Action items: "schedule", "send", "prepare", "review"
- Questions requiring action
- Follow-up requests

## Question Classification
Message is a QUESTION if it:
- Asks for information
- Seeks clarification
- Is informational inquiry without action

## Casual Classification
Message is CASUAL if it:
- Is greeting or small talk
- Is social conversation
- Contains emojis without business context
- Is personal chat

## Notification Classification
Message is NOTIFICATION if it:
- Is automated message
- Is status update
- Is broadcast message
- Is group announcement

## Priority Extraction

**P1 (High Priority)**:
- Keywords: "urgent", "asap", "now", "immediately", "emergency"
- Time-sensitive requests
- From key contacts

**P2 (Medium Priority)**:
- Keywords: "soon", "today", "this week"
- Standard business requests
- Regular follow-ups

**P3 (Low Priority)**:
- No urgency indicators
- Casual inquiries
- Can wait for response

## Category Extraction

- **support**: Help requests, issues, problems
- **sales**: Business inquiries, opportunities
- **internal**: Team coordination, updates
- **personal**: Personal matters, social

# Examples

## Example 1: Task Message
**Input:**
```
Sender: John Doe (+1234567890)
Chat: Direct
Message: "Hey, can you send me the report we discussed? Need it by tomorrow morning. Thanks!"
```

**Output:**
```json
{
  "classification": "task",
  "confidence": 0.92,
  "priority": "P1",
  "category": "internal",
  "extracted_metadata": {
    "action_required": "Send report discussed previously",
    "urgency_indicators": ["by tomorrow morning"],
    "context": "Follow-up from previous discussion",
    "key_entities": ["report", "tomorrow morning"]
  }
}
```

## Example 2: Casual Message
**Input:**
```
Sender: Jane Smith (+9876543210)
Chat: Direct
Message: "Hey! How are you? 😊"
```

**Output:**
```json
{
  "classification": "casual",
  "confidence": 0.95,
  "priority": "P3",
  "category": "personal",
  "extracted_metadata": {
    "action_required": null,
    "urgency_indicators": [],
    "context": "Social greeting",
    "key_entities": []
  }
}
```

# Edge Cases

- **Voice notes**: Indicate transcription needed
- **Media messages**: Extract caption text for classification
- **Group messages**: Consider group context and @mentions
- **Multi-language**: Support English and Urdu
- **Emojis**: Interpret emoji context (🔥 = urgent, ✅ = completed)

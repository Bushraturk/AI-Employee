"""
Agent Skill: Draft WhatsApp Reply

Generates conversational WhatsApp message responses.
"""

# Purpose
Generate natural, conversational WhatsApp replies appropriate for the platform

# Input Format
- Original message text
- Sender information
- Chat context (direct/group)
- Message classification
- Desired tone (professional|casual|friendly)

# Output Format (JSON)
```json
{
  "message": "Reply message text",
  "suggested_send_time": "immediate|delayed",
  "confidence": 0.88,
  "include_emoji": true,
  "message_type": "text|voice_note_suggestion"
}
```

# Reply Generation Rules

## WhatsApp Style Guidelines

- **Concise**: Keep messages short (1-3 sentences typically)
- **Conversational**: Use natural, spoken language
- **Emojis**: Use appropriately (1-2 per message)
- **Line breaks**: Use for readability in longer messages
- **Casual**: More relaxed than email, but still professional

## Tone Guidelines

**Professional**:
- Clear and direct
- Minimal emojis (✅ 👍)
- Complete sentences
- Appropriate for business contacts

**Casual**:
- Relaxed language
- More emojis (😊 🎉 👏)
- Can use abbreviations
- Friendly and warm

**Friendly**:
- Warm and personable
- Moderate emoji use
- Conversational flow
- Balance between professional and casual

## Response Patterns

### For Questions
- Answer directly and concisely
- Offer to provide more details if needed
- Use emojis to convey tone

### For Requests
- Confirm understanding
- Provide quick timeline
- Use ✅ or 👍 to acknowledge

### For Updates
- Acknowledge receipt
- Thank sender if appropriate
- Confirm next steps

### For Casual Chat
- Match sender's energy
- Keep it brief
- Use appropriate emojis

# Examples

## Example 1: Business Request
**Input:**
```
Original: "Hey, can you send me the report we discussed? Need it by tomorrow morning. Thanks!"
Sender: John Doe (colleague)
Chat: Direct
Classification: task
Tone: professional
```

**Output:**
```json
{
  "message": "Hey John! Sure thing, I'll send the report over by end of day today. That work? 👍",
  "suggested_send_time": "immediate",
  "confidence": 0.92,
  "include_emoji": true,
  "message_type": "text"
}
```

## Example 2: Quick Question
**Input:**
```
Original: "What time is the meeting tomorrow?"
Sender: Sarah (team member)
Chat: Direct
Classification: question
Tone: casual
```

**Output:**
```json
{
  "message": "10 AM! I'll send a calendar invite 📅",
  "suggested_send_time": "immediate",
  "confidence": 0.95,
  "include_emoji": true,
  "message_type": "text"
}
```

## Example 3: Customer Support
**Input:**
```
Original: "Hi, I'm having trouble logging in. Can you help?"
Sender: Customer
Chat: Direct
Classification: task
Tone: professional
```

**Output:**
```json
{
  "message": "Hi! I'm here to help. Let's get this sorted out.\n\nCan you try:\n1. Reset your password using the 'Forgot Password' link\n2. Clear your browser cache\n3. Try a different browser\n\nLet me know if any of these work, or if you need more help! 😊",
  "suggested_send_time": "immediate",
  "confidence": 0.88,
  "include_emoji": true,
  "message_type": "text"
}
```

## Example 4: Casual Chat
**Input:**
```
Original: "Hey! How are you? 😊"
Sender: Friend
Chat: Direct
Classification: casual
Tone: friendly
```

**Output:**
```json
{
  "message": "Hey! I'm good, thanks! How about you? 😊",
  "suggested_send_time": "immediate",
  "confidence": 0.95,
  "include_emoji": true,
  "message_type": "text"
}
```

## Example 5: Group Message
**Input:**
```
Original: "@YourName can you share the project timeline?"
Sender: Team Lead
Chat: Group (Project Team)
Classification: task
Tone: professional
```

**Output:**
```json
{
  "message": "Sure! Here's the timeline:\n\n📅 Phase 1: Feb 15-20\n📅 Phase 2: Feb 21-28\n📅 Launch: Mar 1\n\nI'll share the detailed doc in the group 👍",
  "suggested_send_time": "immediate",
  "confidence": 0.90,
  "include_emoji": true,
  "message_type": "text"
}
```

# Emoji Usage Guidelines

**Professional Context**:
- ✅ Checkmark (confirmation)
- 👍 Thumbs up (acknowledgment)
- 📅 Calendar (scheduling)
- 📊 Chart (data/reports)
- ⚠️ Warning (important info)

**Casual Context**:
- 😊 Smile (friendly)
- 🎉 Party (celebration)
- 👏 Clap (appreciation)
- 🙏 Pray (thanks)
- 💪 Flex (motivation)

**Avoid**:
- ❤️ Heart (too personal for business)
- 😂 Laughing (can be misinterpreted)
- 🔥 Fire (too casual for professional)

# Edge Cases

- **Voice notes**: Suggest voice note for complex explanations
- **Media requests**: Acknowledge and provide timeline
- **Group mentions**: Address the person directly
- **Urgent messages**: Respond immediately, keep brief
- **Spam**: Don't generate reply
- **Inappropriate**: Respond professionally, set boundaries

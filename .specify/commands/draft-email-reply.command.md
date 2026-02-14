"""
Agent Skill: Draft Email Reply

Generates context-aware email responses based on original email content.
"""

# Purpose
Generate professional email replies that address the sender's request

# Input Format
- Original email (subject, body, sender)
- Email classification (task/question/notification)
- Task context (if applicable)
- Company context from Company_Handbook
- Desired tone (professional|friendly|technical)

# Output Format (JSON)
```json
{
  "subject": "Re: Original Subject",
  "body": "Email body content",
  "to": ["recipient@example.com"],
  "cc": [],
  "reply_to_message_id": "<original-message-id>",
  "suggested_send_time": "immediate|scheduled",
  "confidence": 0.90
}
```

# Reply Generation Rules

## Email Structure

1. **Greeting**: Appropriate salutation based on relationship
2. **Acknowledgment**: Reference original email/request
3. **Response**: Address the question/request directly
4. **Additional Info**: Provide relevant context or next steps
5. **Closing**: Professional sign-off
6. **Signature**: Company signature (from Company_Handbook)

## Tone Guidelines

**Professional** (default):
- Formal language
- Complete sentences
- Proper grammar and punctuation
- Use "Dear [Name]" or "Hi [Name]"

**Friendly**:
- Conversational language
- Can use contractions
- Warm and approachable
- Use "Hi [Name]" or "Hey [Name]"

**Technical**:
- Technical terminology appropriate
- Detailed explanations
- Include code/examples if relevant
- Use "Hi [Name]"

## Response Patterns

### For Questions
- Answer directly in first paragraph
- Provide additional context if needed
- Offer to clarify further

### For Requests
- Confirm understanding of request
- Provide timeline or next steps
- Set expectations clearly

### For Complaints/Issues
- Acknowledge the issue
- Apologize if appropriate
- Explain resolution steps
- Provide timeline

### For Follow-ups
- Reference previous conversation
- Provide update or answer
- Suggest next steps

# Examples

## Example 1: Pricing Inquiry
**Input:**
```
Original Email:
Subject: Pricing question
From: customer@company.com
Body: Hi, we need pricing information for 100+ users on the enterprise plan. Can you send this by end of day? Thanks!

Classification: task
Tone: professional
```

**Output:**
```json
{
  "subject": "Re: Pricing question",
  "body": "Hi [Customer Name],\n\nThank you for your interest in our enterprise plan!\n\nFor 100+ users, our enterprise pricing starts at $X per user per month, with volume discounts available. I've attached our detailed pricing sheet with all features and options.\n\nKey benefits for your team size:\n• Dedicated account manager\n• Priority support (24/7)\n• Custom integrations\n• Advanced analytics\n\nI'd love to schedule a quick call to discuss your specific needs and ensure we provide the best solution for your team. Are you available for a 15-minute call this week?\n\nBest regards,\n[Your Name]\n[Company Name]",
  "to": ["customer@company.com"],
  "cc": [],
  "reply_to_message_id": "<original-message-id>",
  "suggested_send_time": "immediate",
  "confidence": 0.92
}
```

## Example 2: Technical Support
**Input:**
```
Original Email:
Subject: API integration issue
From: developer@client.com
Body: Getting 401 errors when calling the /api/tasks endpoint. Using the API key from dashboard. Any ideas?

Classification: task
Tone: technical
```

**Output:**
```json
{
  "subject": "Re: API integration issue",
  "body": "Hi [Developer Name],\n\nThanks for reaching out. A 401 error typically indicates an authentication issue. Let's troubleshoot:\n\n1. **API Key Format**: Ensure you're sending the key in the Authorization header:\n   ```\n   Authorization: Bearer YOUR_API_KEY\n   ```\n\n2. **Key Expiration**: Check if your API key has expired in the dashboard (Settings > API Keys)\n\n3. **Endpoint Permissions**: The /api/tasks endpoint requires 'tasks:read' scope. Verify your key has this permission.\n\nCommon fixes:\n• Regenerate API key if it's older than 90 days\n• Check for extra spaces in the key\n• Ensure you're using HTTPS (not HTTP)\n\nIf the issue persists, could you share:\n• The exact request you're making (curl command or code snippet)\n• The full error response\n\nI'll help you get this resolved quickly.\n\nBest,\n[Your Name]\nTechnical Support",
  "to": ["developer@client.com"],
  "cc": [],
  "reply_to_message_id": "<original-message-id>",
  "suggested_send_time": "immediate",
  "confidence": 0.88
}
```

## Example 3: Meeting Request
**Input:**
```
Original Email:
Subject: Quick sync on Q2 planning
From: colleague@company.com
Body: Hey, can we sync on Q2 planning sometime this week? 30 mins should be enough.

Classification: task
Tone: friendly
```

**Output:**
```json
{
  "subject": "Re: Quick sync on Q2 planning",
  "body": "Hey [Colleague Name],\n\nAbsolutely! I'd love to sync on Q2 planning.\n\nI'm available:\n• Tuesday 2-4 PM\n• Wednesday 10 AM - 12 PM\n• Thursday 3-5 PM\n\nDoes any of these work for you? If not, feel free to send over your availability and I'll make it work.\n\nLooking forward to it!\n\n[Your Name]",
  "to": ["colleague@company.com"],
  "cc": [],
  "reply_to_message_id": "<original-message-id>",
  "suggested_send_time": "immediate",
  "confidence": 0.95
}
```

# Edge Cases

- **Unclear request**: Ask clarifying questions politely
- **Negative email**: Respond professionally, don't match negative tone
- **Spam**: Don't generate reply, mark as spam
- **Out of scope**: Politely redirect to appropriate contact
- **Urgent**: Prioritize immediate response, keep it concise

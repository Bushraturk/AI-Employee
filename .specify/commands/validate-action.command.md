"""
Agent Skill: Validate Action

Pre-execution validation for actions to ensure safety and correctness.
"""

# Purpose
Validate actions before execution to prevent errors and ensure safety

# Input Format
- Action type (send_email|post_linkedin|send_whatsapp)
- Action parameters
- Risk level
- Task context

# Output Format (JSON)
```json
{
  "valid": true,
  "risk_level": "medium",
  "validation_errors": [],
  "warnings": [],
  "recommendations": [],
  "requires_approval": true,
  "estimated_impact": "Sends email to 1 recipient"
}
```

# Validation Rules

## Email Validation
- **To addresses**: Valid email format, not empty
- **Subject**: Present, not empty, reasonable length (<200 chars)
- **Body**: Present, not empty, reasonable length (<10000 chars)
- **Attachments**: Valid file paths if present
- **Reply-to**: Valid message ID if replying

## LinkedIn Post Validation
- **Content**: Present, not empty, within 3000 character limit
- **Hashtags**: Max 10, valid format (#word)
- **Mentions**: Valid LinkedIn profile format
- **Media**: Valid URL if present

## WhatsApp Message Validation
- **To**: Valid phone number format
- **Message**: Present, not empty, reasonable length
- **Reply-to**: Valid message ID if replying

## Safety Checks

### Content Safety
- No PII exposure (credit cards, SSNs, passwords)
- No offensive language
- No spam indicators
- No malicious links

### Operational Safety
- Not exceeding rate limits
- Valid authentication
- Proper permissions
- No duplicate sends (within 5 minutes)

### Business Safety
- Appropriate tone for recipient
- Correct recipient (not accidental)
- Reasonable timing (business hours)

# Examples

## Example 1: Valid Email
**Input:**
```json
{
  "action_type": "send_email",
  "parameters": {
    "to": ["customer@company.com"],
    "subject": "Re: Pricing inquiry",
    "body": "Thank you for your interest..."
  }
}
```

**Output:**
```json
{
  "valid": true,
  "risk_level": "medium",
  "validation_errors": [],
  "warnings": [],
  "recommendations": ["Consider adding a call-to-action"],
  "requires_approval": true,
  "estimated_impact": "Sends email to 1 recipient (customer@company.com)"
}
```

## Example 2: Invalid Email (Missing Subject)
**Input:**
```json
{
  "action_type": "send_email",
  "parameters": {
    "to": ["customer@company.com"],
    "subject": "",
    "body": "Thank you for your interest..."
  }
}
```

**Output:**
```json
{
  "valid": false,
  "risk_level": "medium",
  "validation_errors": ["Subject is required and cannot be empty"],
  "warnings": [],
  "recommendations": ["Add a descriptive subject line"],
  "requires_approval": true,
  "estimated_impact": "Cannot send - validation failed"
}
```

## Example 3: High Risk (Bulk Email)
**Input:**
```json
{
  "action_type": "send_email",
  "parameters": {
    "to": ["user1@example.com", "user2@example.com", "user3@example.com", "user4@example.com", "user5@example.com", "user6@example.com"],
    "subject": "Important update",
    "body": "..."
  }
}
```

**Output:**
```json
{
  "valid": true,
  "risk_level": "high",
  "validation_errors": [],
  "warnings": ["Bulk email detected (6 recipients)", "Consider using BCC for privacy"],
  "recommendations": ["Review recipient list carefully", "Consider sending in batches"],
  "requires_approval": true,
  "estimated_impact": "Sends email to 6 recipients (bulk operation)"
}
```

## Example 4: Sensitive Content Detected
**Input:**
```json
{
  "action_type": "send_email",
  "parameters": {
    "to": ["customer@company.com"],
    "subject": "Payment details",
    "body": "Your credit card 4532-1234-5678-9010 has been charged..."
  }
}
```

**Output:**
```json
{
  "valid": false,
  "risk_level": "high",
  "validation_errors": ["Potential credit card number detected in body"],
  "warnings": ["Sensitive financial information should not be sent via email"],
  "recommendations": ["Remove credit card number", "Use secure payment link instead"],
  "requires_approval": true,
  "estimated_impact": "Cannot send - contains sensitive data"
}
```

# Validation Checklist

## Format Validation
- [ ] All required fields present
- [ ] Field types correct
- [ ] Field lengths within limits
- [ ] Valid email/phone/URL formats

## Content Validation
- [ ] No PII exposure
- [ ] No offensive language
- [ ] No spam indicators
- [ ] No malicious links
- [ ] Appropriate tone

## Safety Validation
- [ ] Within rate limits
- [ ] Valid authentication
- [ ] Proper permissions
- [ ] No recent duplicates
- [ ] Appropriate timing

## Business Validation
- [ ] Correct recipient
- [ ] Appropriate content
- [ ] Reasonable timing
- [ ] Follows company policies

# Edge Cases

- **Empty content**: Reject with clear error
- **Very long content**: Warn about truncation
- **Special characters**: Validate encoding
- **Multiple recipients**: Check for bulk operation
- **Urgent timing**: Validate business hours
- **Reply threading**: Verify original message exists

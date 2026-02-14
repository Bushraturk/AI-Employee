"""
Agent Skill: Classify LinkedIn Content

Classifies LinkedIn messages, mentions, and posts for business opportunities.
"""

# Purpose
Classify LinkedIn content and identify business opportunities, leads, and engagement

# Input Format
- Content type (message/mention/comment/post)
- Content text
- Sender profile (name, title, company)
- Timestamp
- Post URL (if applicable)

# Output Format (JSON)
```json
{
  "classification": "opportunity|engagement|notification|spam",
  "confidence": 0.88,
  "priority": "P1|P2|P3",
  "category": "lead|partnership|recruitment|networking|content",
  "extracted_metadata": {
    "opportunity_type": "sales_lead|partnership|job_offer|collaboration",
    "action_required": "Follow up with connection request",
    "business_value": "high|medium|low",
    "key_entities": ["company name", "product interest"]
  }
}
```

# Classification Rules

## Opportunity Classification
Content is an OPPORTUNITY if it:
- Expresses interest in products/services
- Asks about pricing or demos
- Mentions potential partnership
- Indicates hiring interest
- Shows business development potential

## Engagement Classification
Content is ENGAGEMENT if it:
- Comments on your posts
- Likes or shares content
- Mentions you in discussions
- Responds to your content
- Professional networking

## Notification Classification
Content is NOTIFICATION if it:
- Is automated LinkedIn notification
- Is connection request
- Is endorsement or recommendation
- Is group invitation
- Is event invitation

## Priority Extraction

**P1 (High Priority)** - Hot leads, urgent opportunities:
- Direct sales inquiries
- Partnership proposals
- Job offers from target companies
- High-value connections
- Time-sensitive opportunities

**P2 (Medium Priority)** - Warm leads, standard engagement:
- General inquiries
- Networking requests
- Content engagement
- Regular business development

**P3 (Low Priority)** - Cold leads, passive engagement:
- Profile views
- Generic connection requests
- Automated notifications
- Low-value interactions

## Category Extraction

- **lead**: Sales opportunities, product inquiries
- **partnership**: Collaboration proposals, joint ventures
- **recruitment**: Job offers, hiring inquiries
- **networking**: Professional connections, introductions
- **content**: Engagement with your posts, thought leadership

# Examples

## Example 1: Sales Lead
**Input:**
```
Type: Message
From: Sarah Johnson, VP of Operations @ TechCorp
Message: "Hi! I saw your post about AI automation. We're looking for a solution for our team of 50+. Would love to discuss pricing and implementation. Are you available for a call this week?"
```

**Output:**
```json
{
  "classification": "opportunity",
  "confidence": 0.95,
  "priority": "P1",
  "category": "lead",
  "extracted_metadata": {
    "opportunity_type": "sales_lead",
    "action_required": "Schedule call to discuss pricing and implementation",
    "business_value": "high",
    "key_entities": ["TechCorp", "50+ team", "AI automation", "this week"]
  }
}
```

## Example 2: Content Engagement
**Input:**
```
Type: Comment
From: Mike Chen, Software Engineer @ StartupXYZ
Post: Your post about "Building AI Agents"
Comment: "Great insights! We're implementing something similar at our company. Would love to connect and share experiences."
```

**Output:**
```json
{
  "classification": "engagement",
  "confidence": 0.90,
  "priority": "P2",
  "category": "networking",
  "extracted_metadata": {
    "opportunity_type": "collaboration",
    "action_required": "Accept connection request and follow up",
    "business_value": "medium",
    "key_entities": ["StartupXYZ", "AI Agents", "similar implementation"]
  }
}
```

## Example 3: Spam/Low Value
**Input:**
```
Type: Message
From: Generic Recruiter, Recruiter @ RecruitingAgency
Message: "Hi! I have an exciting opportunity that matches your profile. Are you open to new opportunities?"
```

**Output:**
```json
{
  "classification": "spam",
  "confidence": 0.85,
  "priority": "P3",
  "category": "recruitment",
  "extracted_metadata": {
    "opportunity_type": null,
    "action_required": null,
    "business_value": "low",
    "key_entities": ["generic recruiter message"]
  }
}
```

# Edge Cases

- **Connection requests**: Evaluate profile quality and relevance
- **Group posts**: Consider group context and relevance
- **Sponsored content**: Filter out ads and promotions
- **Multiple mentions**: Prioritize by sender authority and context
- **Language**: Support professional English content

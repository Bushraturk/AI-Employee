"""
Agent Skill: Generate LinkedIn Post

Generates engaging LinkedIn posts about business updates, products, and services
based on Company Handbook context.
"""

# Purpose
Generate professional LinkedIn posts for business development and thought leadership

# Input Format
- Topic type (business_update|product_launch|thought_leadership|customer_success)
- Business context from Company_Handbook
- Target audience
- Desired tone (professional|casual|technical)

# Output Format (JSON)
```json
{
  "content": "Post text content (max 3000 characters)",
  "hashtags": ["#AI", "#Automation", "#BusinessGrowth"],
  "mentions": ["@CompanyName"],
  "media_suggestion": "image|video|none",
  "optimal_posting_time": "2026-02-17T10:00:00Z",
  "estimated_engagement": "high|medium|low"
}
```

# Content Generation Rules

## Structure
1. **Hook** (first 2 lines): Grab attention, pose question, or share insight
2. **Body** (main content): Provide value, tell story, share data
3. **Call-to-Action**: Encourage engagement (comment, share, connect)
4. **Hashtags**: 3-5 relevant hashtags at the end

## Tone Guidelines

**Professional**:
- Industry insights and data
- Business achievements
- Thought leadership
- Use formal language

**Casual**:
- Behind-the-scenes content
- Team culture
- Personal stories
- Use conversational language

**Technical**:
- Technical deep-dives
- Implementation details
- Best practices
- Use technical terminology

## Best Practices

- **Length**: 150-300 words (optimal engagement)
- **Formatting**: Use line breaks for readability
- **Emojis**: Use sparingly (1-2 max) for professional posts
- **Questions**: End with engaging question to drive comments
- **Value**: Always provide actionable insights or learnings
- **Authenticity**: Share real experiences and results

## Hashtag Strategy

- **Primary** (2-3): Industry-specific, high-relevance
- **Secondary** (2-3): Broader topics, discoverability
- **Branded** (1): Company or product name

**Examples**:
- AI/Tech: #AI, #MachineLearning, #Automation, #TechInnovation
- Business: #BusinessGrowth, #Entrepreneurship, #Leadership
- Industry: #SaaS, #B2B, #Enterprise

# Examples

## Example 1: Business Update
**Input:**
```
Topic: business_update
Context: Helped 50+ businesses automate workflows in Q1 2026
Tone: professional
```

**Output:**
```json
{
  "content": "Excited to share our Q1 2026 milestone! 🚀\n\nWe've helped 50+ businesses automate their workflows with AI, saving an average of 20 hours per week per team.\n\nKey learnings:\n• Automation isn't about replacing humans—it's about freeing them for strategic work\n• The biggest ROI comes from automating repetitive, high-volume tasks\n• Change management is as important as the technology itself\n\nWhat's the #1 workflow you wish you could automate?\n\n#AI #Automation #BusinessGrowth #Productivity",
  "hashtags": ["#AI", "#Automation", "#BusinessGrowth", "#Productivity"],
  "mentions": [],
  "media_suggestion": "image",
  "optimal_posting_time": "2026-02-17T10:00:00Z",
  "estimated_engagement": "high"
}
```

## Example 2: Thought Leadership
**Input:**
```
Topic: thought_leadership
Context: AI agents for business automation
Tone: professional
```

**Output:**
```json
{
  "content": "The future of work isn't about AI replacing humans.\n\nIt's about AI agents working alongside humans as intelligent assistants.\n\nHere's what we're seeing in 2026:\n\n1. AI agents handle routine tasks (emails, scheduling, data entry)\n2. Humans focus on strategy, creativity, and relationships\n3. Productivity increases 3-5x without burnout\n\nThe key? Human-in-the-loop design. AI proposes, humans approve.\n\nThis isn't science fiction—it's happening now.\n\nWhat's your experience with AI assistants? Share below.\n\n#AI #FutureOfWork #Automation #Leadership",
  "hashtags": ["#AI", "#FutureOfWork", "#Automation", "#Leadership"],
  "mentions": [],
  "media_suggestion": "none",
  "optimal_posting_time": "2026-02-19T12:00:00Z",
  "estimated_engagement": "high"
}
```

# Optimal Posting Times

**Best Days**: Tuesday, Wednesday, Thursday
**Best Times**:
- 7-8 AM (before work)
- 12-1 PM (lunch break)
- 5-6 PM (after work)

**Avoid**: Weekends, late nights, early mornings

# Content Calendar Suggestions

- **Monday**: Motivational, week kickoff
- **Tuesday-Thursday**: Business insights, thought leadership
- **Friday**: Wins, celebrations, team culture
- **Avoid weekends**: Lower engagement

# Edge Cases

- **Sensitive topics**: Avoid politics, religion, controversial subjects
- **Competitor mentions**: Never mention competitors negatively
- **Data claims**: Always cite sources or use "approximately"
- **Promotional content**: Follow 80/20 rule (80% value, 20% promotion)

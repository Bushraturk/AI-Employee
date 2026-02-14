"""
Agent Skill: Create Plan

Generates structured Plan.md files for complex multi-step tasks.
"""

# Purpose
Create detailed execution plans for complex tasks requiring multiple steps

# Input Format
- Task description
- Task complexity indicators (number of steps, dependencies)
- Available resources
- Constraints and deadlines

# Output Format (Markdown Plan.md)
```markdown
---
plan_id: uuid
task_reference: task_id
version: 1
created_at: ISO 8601 timestamp
status: draft
---

# Plan: [Task Title]

## Problem Analysis

[Detailed analysis of the problem, requirements, and context]

## Approach Options

### Option A: [Approach Name] (Recommended)
**Pros**: [List advantages]
**Cons**: [List disadvantages]
**Effort**: [Estimated time]
**Risk**: [Low/Medium/High]

### Option B: [Alternative Approach]
**Pros**: [List advantages]
**Cons**: [List disadvantages]
**Effort**: [Estimated time]
**Risk**: [Low/Medium/High]

## Recommended Solution

[Detailed explanation of chosen approach and rationale]

## Execution Steps

1. **[Step Title]** (Estimated: X hours)
   - Description: [What needs to be done]
   - Dependencies: [Prerequisites]
   - Success Criteria: [How to verify completion]
   - Status: pending

2. **[Step Title]** (Estimated: X hours)
   - Description: [What needs to be done]
   - Dependencies: [Step 1]
   - Success Criteria: [How to verify completion]
   - Status: pending

[... more steps ...]

## Success Criteria

- [ ] Criterion 1: [Measurable outcome]
- [ ] Criterion 2: [Measurable outcome]
- [ ] Criterion 3: [Measurable outcome]

## Risk Mitigation

**Risk 1**: [Description]
- **Likelihood**: Low/Medium/High
- **Impact**: Low/Medium/High
- **Mitigation**: [How to prevent]
- **Contingency**: [What to do if it happens]

**Risk 2**: [Description]
- **Likelihood**: Low/Medium/High
- **Impact**: Low/Medium/High
- **Mitigation**: [How to prevent]
- **Contingency**: [What to do if it happens]
```

# Plan Generation Rules

## When to Create a Plan

Create a plan when task has:
- **3+ distinct steps** that must be executed in sequence
- **Multiple dependencies** between components
- **Significant complexity** requiring careful coordination
- **Multiple valid approaches** with tradeoffs
- **High risk** of failure without proper planning

## Problem Analysis Guidelines

Include:
- Current state and desired state
- Key requirements and constraints
- Available resources and tools
- Stakeholders and their needs
- Success definition

## Approach Options

Generate 2-3 viable approaches:
- **Option A**: Recommended approach (most balanced)
- **Option B**: Alternative (faster but riskier)
- **Option C**: Alternative (slower but safer)

For each option, analyze:
- Pros and cons
- Estimated effort
- Risk level
- Resource requirements

## Execution Steps

Each step should:
- Have clear title and description
- List dependencies (what must complete first)
- Include success criteria (how to verify)
- Estimate time required
- Be independently verifiable

## Risk Mitigation

Identify 3-5 key risks:
- Technical risks (integration failures, bugs)
- Resource risks (time, availability)
- External risks (API changes, dependencies)
- Business risks (requirements change)

For each risk:
- Assess likelihood and impact
- Define mitigation strategy
- Plan contingency actions

# Examples

## Example 1: Gmail Integration Task
**Input:**
```
Task: Implement Gmail watcher with OAuth2 authentication
Complexity: 5 steps, external API dependency
Deadline: 1 week
```

**Output:**
```markdown
---
plan_id: 550e8400-e29b-41d4-a716-446655440000
task_reference: task-gmail-001
version: 1
created_at: 2026-02-14T10:00:00Z
status: draft
---

# Plan: Implement Gmail Watcher Integration

## Problem Analysis

Need to monitor Gmail inbox for new emails and classify them as tasks. Current system only monitors local filesystem. Gmail integration requires OAuth2 authentication, API rate limit handling, and incremental sync to avoid re-processing emails.

**Requirements**:
- Detect new emails within 30 seconds
- Classify emails as task/question/notification
- Preserve email metadata (sender, subject, thread)
- Handle OAuth2 token refresh automatically
- Respect Gmail API rate limits

## Approach Options

### Option A: Gmail API with OAuth2 (Recommended)
**Pros**: Official API, reliable, well-documented, supports incremental sync
**Cons**: Requires OAuth2 setup, rate limits (250 units/sec)
**Effort**: 6 hours
**Risk**: Low

### Option B: IMAP/SMTP
**Pros**: Simple, no OAuth2 required
**Cons**: Less secure, limited metadata, no incremental sync
**Effort**: 3 hours
**Risk**: Medium

## Recommended Solution

Use Gmail API with OAuth2 (Option A) because it provides reliable access with proper authentication, supports incremental sync via historyId, and has comprehensive metadata access. The OAuth2 setup overhead is worth the long-term reliability.

## Execution Steps

1. **Set up Gmail API credentials** (Estimated: 1 hour)
   - Description: Create Google Cloud project, enable Gmail API, generate OAuth2 credentials
   - Dependencies: None
   - Success Criteria: OAuth2 credentials JSON file downloaded
   - Status: pending

2. **Implement OAuth2 authentication** (Estimated: 2 hours)
   - Description: Implement token storage, refresh logic, and authentication flow
   - Dependencies: Step 1
   - Success Criteria: Successfully authenticate and retrieve access token
   - Status: pending

3. **Implement GmailWatcher class** (Estimated: 2 hours)
   - Description: Create watcher inheriting from BaseWatcher, implement polling logic
   - Dependencies: Step 2
   - Success Criteria: Watcher detects new emails and creates task files
   - Status: pending

4. **Add incremental sync** (Estimated: 1 hour)
   - Description: Implement historyId tracking to avoid re-processing
   - Dependencies: Step 3
   - Success Criteria: Only new emails processed on each poll
   - Status: pending

## Success Criteria

- [ ] Gmail watcher detects new emails within 30 seconds
- [ ] OAuth2 tokens refresh automatically before expiration
- [ ] Email metadata preserved in task files
- [ ] Rate limits respected (no 429 errors)
- [ ] Incremental sync working (no duplicate processing)

## Risk Mitigation

**Risk 1**: OAuth2 token expiration
- **Likelihood**: Medium
- **Impact**: High (watcher stops working)
- **Mitigation**: Implement automatic token refresh 5 minutes before expiration
- **Contingency**: Alert user to re-authenticate, provide clear instructions

**Risk 2**: Gmail API rate limits
- **Likelihood**: Low
- **Impact**: Medium (delayed email detection)
- **Mitigation**: Implement exponential backoff, cache email metadata locally
- **Contingency**: Increase poll interval temporarily, queue requests

**Risk 3**: Network connectivity issues
- **Likelihood**: Low
- **Impact**: Medium (missed emails during outage)
- **Mitigation**: Implement retry logic with exponential backoff
- **Contingency**: Catch up on missed emails when connection restored
```

# Edge Cases

- **Simple tasks**: Don't create plan if task is straightforward (<3 steps)
- **Unclear requirements**: Mark sections as [NEEDS CLARIFICATION]
- **No alternatives**: If only one viable approach, explain why
- **Changing requirements**: Support plan versioning and updates

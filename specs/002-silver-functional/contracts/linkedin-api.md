# LinkedIn API Contract

**Version**: 1.0 | **Date**: 2026-02-14 | **Feature**: 002-silver-functional

## Overview

This contract defines the interface between the LinkedInWatcher and LinkedIn API v2 for content monitoring and posting.

## Authentication

**Method**: OAuth2 with 3-legged authorization

**Scopes Required**:
- `r_liteprofile` - Read basic profile info
- `r_emailaddress` - Read email address
- `w_member_social` - Create posts on behalf of user

**Token Storage**: OS keyring or encrypted file (outside vault)

**Token Expiration**: 60 days (refresh required)

**Authorization URL**: `https://www.linkedin.com/oauth/v2/authorization`

**Token URL**: `https://www.linkedin.com/oauth/v2/accessToken`

---

## Endpoint: Get Profile

**Purpose**: Retrieve authenticated user's profile information

**API Call**:
```python
GET https://api.linkedin.com/v2/me
```

**Headers**:
```python
{
    "Authorization": "Bearer {access_token}",
    "X-Restli-Protocol-Version": "2.0.0"
}
```

**Response**:
```json
{
    "id": "abc123XYZ",
    "firstName": {
        "localized": {"en_US": "John"},
        "preferredLocale": {"country": "US", "language": "en"}
    },
    "lastName": {
        "localized": {"en_US": "Doe"},
        "preferredLocale": {"country": "US", "language": "en"}
    }
}
```

**Usage**: Store user ID for post creation

---

## Endpoint: Create UGC Post

**Purpose**: Create a new post on user's LinkedIn profile

**API Call**:
```python
POST https://api.linkedin.com/v2/ugcPosts
```

**Headers**:
```python
{
    "Authorization": "Bearer {access_token}",
    "Content-Type": "application/json",
    "X-Restli-Protocol-Version": "2.0.0"
}
```

**Request Body** (Text Post):
```json
{
    "author": "urn:li:person:{user_id}",
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": "Post content here with #hashtags and @mentions"
            },
            "shareMediaCategory": "NONE"
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
}
```

**Request Body** (Post with Link):
```json
{
    "author": "urn:li:person:{user_id}",
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": "Check out this article!"
            },
            "shareMediaCategory": "ARTICLE",
            "media": [
                {
                    "status": "READY",
                    "originalUrl": "https://example.com/article"
                }
            ]
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
}
```

**Response**:
```json
{
    "id": "urn:li:share:7034567890"
}
```

**Rate Limits**: Not publicly documented (monitor 429 responses)

**Error Handling**:
- 400 Bad Request → Validate post format
- 401 Unauthorized → Refresh token
- 403 Forbidden → Check scopes or content policy violation
- 429 Too Many Requests → Exponential backoff
- 500 Server Error → Retry with backoff

---

## Endpoint: Get Post Analytics

**Purpose**: Retrieve engagement metrics for published posts

**API Call**:
```python
GET https://api.linkedin.com/v2/socialActions/{share_urn}
```

**Headers**:
```python
{
    "Authorization": "Bearer {access_token}",
    "X-Restli-Protocol-Version": "2.0.0"
}
```

**Response**:
```json
{
    "likesSummary": {
        "totalLikes": 45
    },
    "commentsSummary": {
        "totalComments": 8
    }
}
```

**Note**: Full analytics (views, impressions) require additional API access

---

## Endpoint: Get Share Statistics

**Purpose**: Retrieve detailed post statistics

**API Call**:
```python
GET https://api.linkedin.com/v2/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity={urn}
```

**Response**:
```json
{
    "elements": [
        {
            "totalShareStatistics": {
                "shareCount": 12,
                "likeCount": 45,
                "commentCount": 8,
                "impressionCount": 1250,
                "clickCount": 43
            }
        }
    ]
}
```

**Limitations**:
- Analytics may have 24-48 hour delay
- Requires organization admin access for full metrics
- Personal profiles have limited analytics

---

## Content Guidelines

**Text Limits**:
- Post text: 3,000 characters maximum
- Hashtags: 10 maximum recommended
- Mentions: 10 maximum recommended

**Hashtag Format**:
- Must start with #
- No spaces (use camelCase: #BusinessGrowth)
- Alphanumeric only

**Mention Format**:
- Use @mention in text
- LinkedIn auto-converts to profile links

**Best Practices**:
- Post during business hours (9 AM - 5 PM local time)
- Optimal frequency: 2-3 posts per week
- Include visual content when possible
- Use 3-5 relevant hashtags
- Engage with comments within 24 hours

---

## Rate Limit Management

**Strategy**:
- Monitor 429 responses (rate limit not publicly documented)
- Implement exponential backoff (start 5s, max 300s)
- Queue posts when rate limited
- Track daily post count (recommend max 5 per day)

**Backoff Algorithm**:
```python
def calculate_backoff(attempt: int) -> int:
    """Exponential backoff with jitter"""
    base_delay = 5  # seconds
    max_delay = 300  # 5 minutes
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter
```

---

## Optimal Posting Times

**Research-Based Schedule**:
- **Best Days**: Tuesday, Wednesday, Thursday
- **Best Times**:
  - 7-8 AM (before work)
  - 12-1 PM (lunch break)
  - 5-6 PM (after work)
- **Avoid**: Weekends, late nights, early mornings

**Implementation**:
```python
OPTIMAL_POSTING_SCHEDULE = {
    "monday": ["10:00"],
    "wednesday": ["12:00"],
    "friday": ["10:00"]
}
```

---

## Error Codes Reference

| Code | Meaning | Action |
|------|---------|--------|
| 400 | Bad Request | Validate post format, check character limits |
| 401 | Unauthorized | Refresh OAuth2 token |
| 403 | Forbidden | Check scopes or content policy violation |
| 404 | Not Found | Post deleted or invalid URN |
| 422 | Unprocessable Entity | Content violates LinkedIn policies |
| 429 | Rate Limit | Exponential backoff, queue post |
| 500 | Server Error | Retry with backoff |
| 503 | Service Unavailable | Retry with backoff |

---

## Content Policy Compliance

**Prohibited Content**:
- Spam or misleading information
- Hate speech or harassment
- Adult content
- Illegal activities
- Excessive self-promotion

**Validation Before Posting**:
- Check for prohibited keywords
- Validate URLs (no malicious links)
- Ensure professional tone
- Verify hashtag relevance

**Risk Classification**:
- All LinkedIn posts: **Medium Risk** (requires approval)
- Bulk posts (>3 per day): **High Risk** (requires approval + confirmation)

---

## Local Caching Strategy

**Cache Structure**:
```
vault/LinkedIn_Posts/
├── {post_id}.md           # Post content and metadata
└── analytics/
    └── {post_id}.json     # Performance metrics
```

**Cache Updates**:
- Post content: Immediate after creation
- Analytics: Daily refresh (24-hour delay)
- Manual refresh via CLI command

---

## Testing Strategy

**Unit Tests**:
- Mock LinkedIn API responses
- Test OAuth2 flow
- Test post creation
- Test error handling

**Integration Tests**:
- Use LinkedIn test account
- Create test posts (mark as test in content)
- Verify post appears on profile
- Test analytics retrieval

**Fixtures**:
```python
# tests/fixtures/mock_linkedin_api.py
MOCK_POST_RESPONSE = {
    "id": "urn:li:share:7034567890"
}

MOCK_ANALYTICS_RESPONSE = {
    "likesSummary": {"totalLikes": 45},
    "commentsSummary": {"totalComments": 8}
}
```

---

## Security Considerations

- Never log access tokens
- Store tokens securely (OS keyring)
- Validate post content (prevent injection)
- Sanitize user input
- Use HTTPS only (enforced by API)
- Rotate tokens every 60 days
- Monitor for suspicious activity

---

## Implementation Checklist

- [ ] OAuth2 authorization flow
- [ ] Token storage and refresh
- [ ] Get profile endpoint
- [ ] Create UGC post endpoint
- [ ] Get post analytics endpoint
- [ ] Content validation
- [ ] Rate limit handling
- [ ] Error handling and retries
- [ ] Optimal posting time scheduler
- [ ] Local post storage
- [ ] Unit tests with mocks
- [ ] Integration tests with test account
- [ ] Content policy compliance checks

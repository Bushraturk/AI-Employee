# Facebook Graph API Contract

**Service**: Facebook Graph API v18.0+
**Protocol**: REST over HTTPS
**Library**: requests
**Authentication**: OAuth 2.0 Access Token

## Connection

### Endpoint
```
https://graph.facebook.com/v18.0
```

### Authentication
```python
import requests

headers = {
    'Authorization': f'Bearer {access_token}'
}
# Or pass as query parameter
params = {
    'access_token': access_token
}
```

### Configuration (Environment Variables)
```bash
FACEBOOK_ACCESS_TOKEN=your_long_lived_access_token
FACEBOOK_PAGE_ID=your_page_id
```

---

## Operations

### 1. Post to Page (Text Only)

**Purpose**: Publish text post to Facebook page

**Method**: POST

**Endpoint**: `/v18.0/{page-id}/feed`

**Request**:
```python
url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
data = {
    'message': 'Your post content here',
    'access_token': access_token
}
response = requests.post(url, data=data)
```

**Response** (Success):
```json
{
    "id": "123456789_987654321"
}
```

**Response** (Error):
```json
{
    "error": {
        "message": "Error message",
        "type": "OAuthException",
        "code": 190,
        "fbtrace_id": "ABC123"
    }
}
```

**Validation**:
- `message` is required
- `message` max length: 63,206 characters
- Access token must have `pages_manage_posts` permission

**Error Handling**:
- 190 (OAuthException): Token expired (escalate to human)
- 200 (Permissions error): Missing permission (escalate to human)
- 368 (Temporarily blocked): Rate limit (queue and retry later)
- Network errors: Retry with backoff

**Rate Limit**: 200 calls per user per hour

---

### 2. Post to Page (With Photo)

**Purpose**: Publish photo post to Facebook page

**Method**: POST

**Endpoint**: `/v18.0/{page-id}/photos`

**Request**:
```python
url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
data = {
    'url': 'https://example.com/image.jpg',  # Or upload file
    'caption': 'Your photo caption',
    'access_token': access_token
}
response = requests.post(url, data=data)
```

**Alternative (File Upload)**:
```python
files = {
    'source': open('image.jpg', 'rb')
}
data = {
    'caption': 'Your photo caption',
    'access_token': access_token
}
response = requests.post(url, data=data, files=files)
```

**Response** (Success):
```json
{
    "id": "123456789",
    "post_id": "123456789_987654321"
}
```

**Validation**:
- Image URL must be publicly accessible or file must be valid
- Supported formats: JPG, PNG, GIF, BMP
- Max file size: 4MB
- Caption max length: 2,200 characters

**Error Handling**:
- Same as text post
- 324 (Missing or invalid image): Escalate to human

**Rate Limit**: 200 calls per user per hour

---

### 3. Get Post Insights (Metrics)

**Purpose**: Retrieve performance metrics for published post

**Method**: GET

**Endpoint**: `/v18.0/{post-id}/insights`

**Request**:
```python
url = f"https://graph.facebook.com/v18.0/{post_id}/insights"
params = {
    'metric': 'post_impressions,post_engaged_users,post_clicks',
    'access_token': access_token
}
response = requests.get(url, params=params)
```

**Response**:
```json
{
    "data": [
        {
            "name": "post_impressions",
            "period": "lifetime",
            "values": [{"value": 1800}],
            "title": "Lifetime Post Total Impressions",
            "description": "Lifetime: The number of times your Page's post entered a person's screen.",
            "id": "123456789_987654321/insights/post_impressions/lifetime"
        },
        {
            "name": "post_engaged_users",
            "period": "lifetime",
            "values": [{"value": 95}],
            "title": "Lifetime Engaged Users",
            "description": "Lifetime: The number of people who clicked anywhere in your post.",
            "id": "123456789_987654321/insights/post_engaged_users/lifetime"
        },
        {
            "name": "post_clicks",
            "period": "lifetime",
            "values": [{"value": 42}],
            "title": "Lifetime Post Clicks",
            "description": "Lifetime: The number of times people clicked on anywhere in your post.",
            "id": "123456789_987654321/insights/post_clicks/lifetime"
        }
    ]
}
```

**Available Metrics**:
- `post_impressions`: Total impressions
- `post_impressions_unique`: Unique reach
- `post_engaged_users`: Total engagement
- `post_clicks`: Total clicks
- `post_reactions_by_type_total`: Reactions breakdown

**Mapping to SocialMediaPost**:
```python
performance_metrics = {
    'facebook': {
        'reach': data['post_impressions_unique'],
        'impressions': data['post_impressions'],
        'engagement': data['post_engaged_users'],
        'clicks': data['post_clicks'],
        'last_updated': datetime.now().isoformat()
    }
}
```

**Error Handling**:
- 100 (Invalid parameter): Metric not available yet (retry later)
- Network errors: Retry with backoff

**Rate Limit**: 200 calls per user per hour

---

### 4. Get Page Info

**Purpose**: Retrieve page details and follower count

**Method**: GET

**Endpoint**: `/v18.0/{page-id}`

**Request**:
```python
url = f"https://graph.facebook.com/v18.0/{page_id}"
params = {
    'fields': 'name,fan_count,followers_count',
    'access_token': access_token
}
response = requests.get(url, params=params)
```

**Response**:
```json
{
    "name": "Your Business Page",
    "fan_count": 1250,
    "followers_count": 1280,
    "id": "123456789"
}
```

**Use Case**: Track follower growth for weekly audit

**Rate Limit**: 200 calls per user per hour

---

## Error Codes

| Code | Type | Description | Recovery Strategy |
|------|------|-------------|-------------------|
| 190 | OAuthException | Access token expired | Escalate to human (refresh token) |
| 200 | PermissionsError | Missing permission | Escalate to human (grant permission) |
| 368 | TemporarilyBlocked | Rate limit exceeded | Queue action, retry after cooldown |
| 100 | InvalidParameter | Invalid request parameter | Escalate to human (fix request) |
| 324 | MissingOrInvalidImage | Image error | Escalate to human (check image) |
| 1 | UnknownError | Generic API error | Retry with backoff, escalate if persists |
| 2 | ServiceError | Facebook service down | Queue action, retry later |

---

## Rate Limiting

**Limits**:
- 200 calls per user per hour
- 4800 calls per app per hour (if multiple users)

**Implementation**:
```python
from functools import wraps
import time

class FacebookRateLimiter:
    def __init__(self, calls=200, period=3600):
        self.calls = calls
        self.period = period
        self.timestamps = []

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            self.timestamps = [ts for ts in self.timestamps if now - ts < self.period]

            if len(self.timestamps) >= self.calls:
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.timestamps = []

            self.timestamps.append(time.time())
            return func(*args, **kwargs)
        return wrapper

@FacebookRateLimiter(calls=200, period=3600)
def post_to_facebook(message):
    # API call here
    pass
```

**Circuit Breaker**:
- Open circuit after 10 consecutive failures
- Half-open after 5 minutes
- Close circuit after 1 successful call

---

## Authentication

### Access Token Types

1. **User Access Token**: Short-lived (1-2 hours)
2. **Page Access Token**: Can be long-lived (60 days)
3. **Long-Lived User Token**: 60 days

**Recommended**: Use long-lived page access token

### Token Generation

1. Get short-lived user token via OAuth flow
2. Exchange for long-lived user token:
```python
url = "https://graph.facebook.com/v18.0/oauth/access_token"
params = {
    'grant_type': 'fb_exchange_token',
    'client_id': app_id,
    'client_secret': app_secret,
    'fb_exchange_token': short_lived_token
}
response = requests.get(url, params=params)
```

3. Get page access token:
```python
url = f"https://graph.facebook.com/v18.0/{user_id}/accounts"
params = {'access_token': long_lived_user_token}
response = requests.get(url, params=params)
# Extract page access token from response
```

**Security**:
- Store tokens in `.env` file
- Never commit tokens to git
- Rotate tokens every 60 days
- Use HTTPS for all requests

---

## Content Policies

**Prohibited Content**:
- Spam or misleading content
- Hate speech or violence
- Adult content
- Copyright violations

**Best Practices**:
- Avoid excessive hashtags (max 2-3)
- Include engaging visuals when possible
- Post during peak engagement times
- Respond to comments promptly

**Handling Policy Violations**:
- Facebook may reject posts that violate policies
- Error code 368 (temporarily blocked) indicates policy issue
- Escalate to human for review

---

## Testing

**Contract Tests** (tests/contract/test_facebook_contracts.py):
- Test text post creation
- Test photo post creation
- Test metrics retrieval
- Test error handling for each error code
- Test rate limiting behavior
- Mock Facebook API responses

**Mock Responses**:
```python
import responses

@responses.activate
def test_post_to_facebook():
    responses.add(
        responses.POST,
        'https://graph.facebook.com/v18.0/123456789/feed',
        json={'id': '123456789_987654321'},
        status=200
    )

    result = post_to_facebook('Test message')
    assert result['id'] == '123456789_987654321'
```

---

## Performance

**Optimization**:
- Batch metrics requests (multiple posts in one call)
- Cache page info (fan count doesn't change frequently)
- Use webhooks for real-time updates (if available)
- Compress images before upload

**Monitoring**:
- Track API call count per hour
- Monitor response times (alert if >3 seconds)
- Log all errors for analysis
- Track post success rate (target: 95%+)

---

## Data Mapping

### Vault → Facebook

| Vault Field | Facebook Parameter | Transformation |
|-------------|-------------------|----------------|
| `content` | `message` or `caption` | Direct mapping |
| `media_urls[0]` | `url` or `source` | Use first media URL |
| `platforms` | Determines if post is sent | Check if 'facebook' in list |

### Facebook → Vault

| Facebook Field | Vault Field | Transformation |
|----------------|-------------|----------------|
| `id` | `post_id` (Facebook-specific) | Store in platform-specific metadata |
| `post_impressions` | `performance_metrics.facebook.impressions` | Direct mapping |
| `post_impressions_unique` | `performance_metrics.facebook.reach` | Direct mapping |
| `post_engaged_users` | `performance_metrics.facebook.engagement` | Direct mapping |
| `post_clicks` | `performance_metrics.facebook.clicks` | Direct mapping |

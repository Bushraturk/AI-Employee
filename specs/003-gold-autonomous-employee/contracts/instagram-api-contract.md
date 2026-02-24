# Instagram Graph API Contract

**Service**: Instagram Graph API (via Facebook Graph API)
**Protocol**: REST over HTTPS
**Library**: requests
**Authentication**: OAuth 2.0 Access Token (Facebook-based)

## Prerequisites

**CRITICAL**: Instagram Graph API requires:
1. Facebook Business Manager account
2. Instagram Business or Creator account (NOT personal account)
3. Instagram account connected to Facebook Page
4. Facebook app with Instagram permissions

**Personal accounts cannot use this API**. Attempting to use instagram-private-api violates Instagram ToS and risks account ban.

## Connection

### Endpoint
```
https://graph.facebook.com/v18.0
```

### Authentication
```python
import requests

# Same access token as Facebook (page access token)
headers = {
    'Authorization': f'Bearer {access_token}'
}
```

### Configuration (Environment Variables)
```bash
FACEBOOK_ACCESS_TOKEN=your_long_lived_page_access_token
INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id
```

### Get Instagram Account ID
```python
url = f"https://graph.facebook.com/v18.0/{page_id}"
params = {
    'fields': 'instagram_business_account',
    'access_token': access_token
}
response = requests.get(url, params=params)
instagram_account_id = response.json()['instagram_business_account']['id']
```

---

## Operations

### 1. Create Media Container (Step 1 of 2)

**Purpose**: Prepare media for publishing (required before posting)

**Method**: POST

**Endpoint**: `/v18.0/{ig-account-id}/media`

**Request (Image)**:
```python
url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
data = {
    'image_url': 'https://example.com/image.jpg',
    'caption': 'Your caption here #hashtag',
    'access_token': access_token
}
response = requests.post(url, data=data)
```

**Request (Video)**:
```python
data = {
    'video_url': 'https://example.com/video.mp4',
    'caption': 'Your caption here #hashtag',
    'media_type': 'VIDEO',
    'access_token': access_token
}
```

**Response** (Success):
```json
{
    "id": "17895695668004550"
}
```

**Response** (Error):
```json
{
    "error": {
        "message": "Invalid image URL",
        "type": "OAuthException",
        "code": 100,
        "fbtrace_id": "ABC123"
    }
}
```

**Validation**:
- Image URL must be publicly accessible (HTTPS)
- Supported formats: JPG, PNG
- Max file size: 8MB (images), 100MB (videos)
- Caption max length: 2,200 characters
- Max 30 hashtags per caption
- Video duration: 3-60 seconds (feed), up to 15 minutes (IGTV)

**Error Handling**:
- 100 (Invalid parameter): Image URL not accessible (escalate to human)
- 190 (OAuthException): Token expired (escalate to human)
- Network errors: Retry with backoff

**Rate Limit**: 25 media container creations per 24 hours per user

---

### 2. Publish Media Container (Step 2 of 2)

**Purpose**: Publish prepared media to Instagram feed

**Method**: POST

**Endpoint**: `/v18.0/{ig-account-id}/media_publish`

**Request**:
```python
url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media_publish"
data = {
    'creation_id': container_id,  # From step 1
    'access_token': access_token
}
response = requests.post(url, data=data)
```

**Response** (Success):
```json
{
    "id": "17895695668004551"
}
```

**Important**: Wait for container to be ready before publishing. Check status:
```python
url = f"https://graph.facebook.com/v18.0/{container_id}"
params = {
    'fields': 'status_code',
    'access_token': access_token
}
response = requests.get(url, params=params)
# status_code: FINISHED (ready), IN_PROGRESS (wait), ERROR (failed)
```

**Error Handling**:
- 100 (Invalid parameter): Container not ready (wait and retry)
- 9007 (Media already published): Duplicate publish attempt (ignore)
- Network errors: Retry with backoff

**Rate Limit**: 25 posts per 24 hours per user

---

### 3. Get Media Insights (Metrics)

**Purpose**: Retrieve performance metrics for published post

**Method**: GET

**Endpoint**: `/v18.0/{ig-media-id}/insights`

**Request**:
```python
url = f"https://graph.facebook.com/v18.0/{media_id}/insights"
params = {
    'metric': 'impressions,reach,engagement,saved',
    'access_token': access_token
}
response = requests.get(url, params=params)
```

**Response**:
```json
{
    "data": [
        {
            "name": "impressions",
            "period": "lifetime",
            "values": [{"value": 1200}],
            "title": "Impressions",
            "description": "Total number of times the media object has been seen",
            "id": "17895695668004551/insights/impressions/lifetime"
        },
        {
            "name": "reach",
            "period": "lifetime",
            "values": [{"value": 890}],
            "title": "Reach",
            "description": "Total number of unique accounts that have seen the media object",
            "id": "17895695668004551/insights/reach/lifetime"
        },
        {
            "name": "engagement",
            "period": "lifetime",
            "values": [{"value": 67}],
            "title": "Engagement",
            "description": "Total number of likes and comments on the media object",
            "id": "17895695668004551/insights/engagement/lifetime"
        },
        {
            "name": "saved",
            "period": "lifetime",
            "values": [{"value": 12}],
            "title": "Saved",
            "description": "Total number of unique accounts that have saved the media object",
            "id": "17895695668004551/insights/saved/lifetime"
        }
    ]
}
```

**Available Metrics**:
- `impressions`: Total impressions
- `reach`: Unique reach
- `engagement`: Likes + comments
- `saved`: Saves count
- `video_views`: Video views (video posts only)

**Mapping to SocialMediaPost**:
```python
performance_metrics = {
    'instagram': {
        'reach': data['reach'],
        'impressions': data['impressions'],
        'engagement': data['engagement'],
        'clicks': data.get('saved', 0),  # Use saved as proxy for clicks
        'last_updated': datetime.now().isoformat()
    }
}
```

**Important**: Insights available 24 hours after publishing

**Error Handling**:
- 10 (Insights not available): Post too recent (retry after 24 hours)
- Network errors: Retry with backoff

**Rate Limit**: 200 calls per hour per user

---

### 4. Get Account Info

**Purpose**: Retrieve account details and follower count

**Method**: GET

**Endpoint**: `/v18.0/{ig-account-id}`

**Request**:
```python
url = f"https://graph.facebook.com/v18.0/{instagram_account_id}"
params = {
    'fields': 'username,followers_count,follows_count,media_count',
    'access_token': access_token
}
response = requests.get(url, params=params)
```

**Response**:
```json
{
    "username": "yourbusiness",
    "followers_count": 1280,
    "follows_count": 450,
    "media_count": 156,
    "id": "17841405309211844"
}
```

**Use Case**: Track follower growth for weekly audit

**Rate Limit**: 200 calls per hour per user

---

## Error Codes

| Code | Type | Description | Recovery Strategy |
|------|------|-------------|-------------------|
| 190 | OAuthException | Access token expired | Escalate to human (refresh token) |
| 100 | InvalidParameter | Invalid request parameter | Escalate to human (fix request) |
| 10 | PermissionsError | Missing permission | Escalate to human (grant permission) |
| 9007 | DuplicatePost | Media already published | Ignore (already succeeded) |
| 368 | TemporarilyBlocked | Rate limit exceeded | Queue action, retry after 24 hours |
| 2207051 | MediaUploadError | Media processing failed | Escalate to human (check media) |

---

## Rate Limiting

**Limits**:
- 25 media container creations per 24 hours per user
- 25 posts per 24 hours per user
- 200 API calls per hour per user

**Critical**: Instagram has strict daily posting limits. Exceeding 25 posts/day can result in temporary blocks.

**Implementation**:
```python
from functools import wraps
import time
from datetime import datetime, timedelta

class InstagramRateLimiter:
    def __init__(self):
        self.daily_posts = []
        self.hourly_calls = []

    def check_daily_limit(self):
        now = datetime.now()
        cutoff = now - timedelta(days=1)
        self.daily_posts = [ts for ts in self.daily_posts if ts > cutoff]
        return len(self.daily_posts) < 25

    def check_hourly_limit(self):
        now = time.time()
        cutoff = now - 3600
        self.hourly_calls = [ts for ts in self.hourly_calls if ts > cutoff]
        return len(self.hourly_calls) < 200

    def record_post(self):
        self.daily_posts.append(datetime.now())

    def record_call(self):
        self.hourly_calls.append(time.time())
```

**Circuit Breaker**:
- Open circuit after 10 consecutive failures
- Half-open after 24 hours (due to daily rate limits)
- Close circuit after 1 successful call

---

## Content Guidelines

**Best Practices**:
- Use high-quality images (min 1080x1080 pixels)
- Square format (1:1) or portrait (4:5) recommended
- Include 5-10 relevant hashtags
- Post during peak engagement times (varies by audience)
- Use first line of caption for hook (only first 125 chars visible)

**Prohibited Content**:
- Spam or misleading content
- Hate speech or violence
- Adult content
- Copyright violations
- Excessive promotional content

**Handling Policy Violations**:
- Instagram may reject posts that violate policies
- Error code 368 (temporarily blocked) indicates policy issue
- Repeated violations can result in account restrictions
- Escalate to human for review

---

## Two-Step Publishing Flow

**Complete Implementation**:
```python
import requests
import time

def post_to_instagram(image_url, caption, access_token, instagram_account_id):
    # Step 1: Create media container
    url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
    data = {
        'image_url': image_url,
        'caption': caption,
        'access_token': access_token
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    container_id = response.json()['id']

    # Step 2: Wait for container to be ready
    max_attempts = 10
    for attempt in range(max_attempts):
        url = f"https://graph.facebook.com/v18.0/{container_id}"
        params = {
            'fields': 'status_code',
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        status = response.json().get('status_code')

        if status == 'FINISHED':
            break
        elif status == 'ERROR':
            raise Exception("Media container processing failed")

        time.sleep(2)  # Wait 2 seconds before checking again

    # Step 3: Publish media
    url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media_publish"
    data = {
        'creation_id': container_id,
        'access_token': access_token
    }
    response = requests.post(url, data=data)
    response.raise_for_status()

    return response.json()['id']
```

---

## Testing

**Contract Tests** (tests/contract/test_instagram_contracts.py):
- Test media container creation
- Test container status checking
- Test media publishing
- Test metrics retrieval
- Test error handling for each error code
- Test rate limiting behavior
- Mock Instagram API responses

**Mock Responses**:
```python
import responses

@responses.activate
def test_post_to_instagram():
    # Mock container creation
    responses.add(
        responses.POST,
        'https://graph.facebook.com/v18.0/123456789/media',
        json={'id': '17895695668004550'},
        status=200
    )

    # Mock container status
    responses.add(
        responses.GET,
        'https://graph.facebook.com/v18.0/17895695668004550',
        json={'status_code': 'FINISHED'},
        status=200
    )

    # Mock publish
    responses.add(
        responses.POST,
        'https://graph.facebook.com/v18.0/123456789/media_publish',
        json={'id': '17895695668004551'},
        status=200
    )

    result = post_to_instagram('https://example.com/image.jpg', 'Test caption')
    assert result == '17895695668004551'
```

---

## Data Mapping

### Vault → Instagram

| Vault Field | Instagram Parameter | Transformation |
|-------------|---------------------|----------------|
| `content` | `caption` | Direct mapping |
| `media_urls[0]` | `image_url` or `video_url` | Use first media URL |
| `platforms` | Determines if post is sent | Check if 'instagram' in list |

### Instagram → Vault

| Instagram Field | Vault Field | Transformation |
|-----------------|-------------|----------------|
| `id` | `post_id` (Instagram-specific) | Store in platform-specific metadata |
| `impressions` | `performance_metrics.instagram.impressions` | Direct mapping |
| `reach` | `performance_metrics.instagram.reach` | Direct mapping |
| `engagement` | `performance_metrics.instagram.engagement` | Direct mapping |
| `saved` | `performance_metrics.instagram.clicks` | Use saved as proxy |

---

## Limitations

**API Restrictions**:
- Cannot post Stories via API (manual only)
- Cannot post Reels via API (manual only)
- Cannot schedule posts (must publish immediately)
- Cannot edit published posts
- Cannot delete posts via API
- Insights available 24 hours after publishing

**Account Requirements**:
- Must be Business or Creator account
- Must be connected to Facebook Page
- Personal accounts not supported

**Workarounds**:
- For Stories: Escalate to human for manual posting
- For Reels: Escalate to human for manual posting
- For scheduling: Use approval workflow, publish when approved

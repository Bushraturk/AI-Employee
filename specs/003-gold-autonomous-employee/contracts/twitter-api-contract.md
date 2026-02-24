# Twitter (X) API v2 Contract

**Service**: Twitter API v2
**Protocol**: REST over HTTPS
**Library**: tweepy v4.14+
**Authentication**: OAuth 1.0a (for posting) + OAuth 2.0 Bearer Token (for reading)

## Connection

### Endpoint
```
https://api.twitter.com/2
```

### Authentication
```python
import tweepy

# OAuth 1.0a for posting (requires all 4 credentials)
client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret,
    wait_on_rate_limit=True  # Auto-handle rate limits
)

# API v1.1 for media upload (tweepy handles this internally)
auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
api = tweepy.API(auth)
```

### Configuration (Environment Variables)
```bash
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
```

---

## Operations

### 1. Post Tweet (Text Only)

**Purpose**: Publish text tweet

**Method**: `create_tweet`

**Request**:
```python
response = client.create_tweet(text="Your tweet content here")
```

**Response**:
```python
Response(
    data={'id': '1234567890123456789', 'text': 'Your tweet content here'},
    includes={},
    errors=[],
    meta={}
)
```

**Validation**:
- Text max length: 280 characters
- Text is required
- URLs count as 23 characters (t.co shortening)
- Media counts toward character limit

**Error Handling**:
- `tweepy.TweepyException`: Generic error (check error message)
- `tweepy.Forbidden`: Authentication issue (escalate to human)
- `tweepy.TooManyRequests`: Rate limit (wait_on_rate_limit handles this)
- `tweepy.BadRequest`: Invalid parameters (escalate to human)

**Rate Limit**: 300 tweets per 3 hours (100/hour average)

---

### 2. Post Tweet with Media

**Purpose**: Publish tweet with image/video

**Method**: `create_tweet` + `media_upload`

**Request**:
```python
# Step 1: Upload media (uses API v1.1)
media = api.media_upload(filename='image.jpg')

# Step 2: Create tweet with media
response = client.create_tweet(
    text="Your tweet content here",
    media_ids=[media.media_id]
)
```

**Multiple Images**:
```python
media_ids = []
for image_path in ['image1.jpg', 'image2.jpg', 'image3.jpg']:
    media = api.media_upload(filename=image_path)
    media_ids.append(media.media_id)

response = client.create_tweet(
    text="Your tweet content here",
    media_ids=media_ids
)
```

**Validation**:
- Max 4 images per tweet
- Max 1 video per tweet (cannot mix video and images)
- Image formats: JPG, PNG, GIF, WEBP
- Max image size: 5MB
- Video formats: MP4, MOV
- Max video size: 512MB
- Max video duration: 2 minutes 20 seconds

**Error Handling**:
- `tweepy.BadRequest` with "media_ids": Invalid media (escalate to human)
- Media upload errors: Retry with backoff

**Rate Limit**: 300 tweets per 3 hours (includes media tweets)

---

### 3. Post Thread

**Purpose**: Publish series of connected tweets

**Method**: `create_tweet` with `in_reply_to_tweet_id`

**Request**:
```python
tweets = [
    "First tweet in thread (1/3)",
    "Second tweet in thread (2/3)",
    "Third tweet in thread (3/3)"
]

previous_id = None
tweet_ids = []

for tweet_text in tweets:
    response = client.create_tweet(
        text=tweet_text,
        in_reply_to_tweet_id=previous_id
    )
    tweet_id = response.data['id']
    tweet_ids.append(tweet_id)
    previous_id = tweet_id
```

**Validation**:
- Each tweet in thread must be ≤280 characters
- Thread can be any length (no limit)
- First tweet has no `in_reply_to_tweet_id`
- Subsequent tweets reply to previous tweet

**Error Handling**:
- If one tweet fails, stop thread and escalate to human
- Do not continue thread with broken chain

**Rate Limit**: Counts toward 300 tweets per 3 hours limit

---

### 4. Get Tweet Metrics

**Purpose**: Retrieve performance metrics for published tweet

**Method**: `get_tweet`

**Request**:
```python
response = client.get_tweet(
    id=tweet_id,
    tweet_fields=['public_metrics', 'non_public_metrics', 'organic_metrics'],
    user_auth=True  # Required for non-public metrics
)
```

**Response**:
```python
Response(
    data=Tweet(
        id='1234567890123456789',
        text='Your tweet content',
        public_metrics={
            'retweet_count': 12,
            'reply_count': 8,
            'like_count': 34,
            'quote_count': 2,
            'bookmark_count': 5,
            'impression_count': 450
        },
        non_public_metrics={
            'impression_count': 450,
            'url_link_clicks': 15,
            'user_profile_clicks': 8
        },
        organic_metrics={
            'impression_count': 420,
            'like_count': 32,
            'reply_count': 7,
            'retweet_count': 11
        }
    )
)
```

**Available Metrics**:
- `public_metrics`: Publicly visible counts
  - `retweet_count`: Retweets
  - `reply_count`: Replies
  - `like_count`: Likes
  - `quote_count`: Quote tweets
  - `bookmark_count`: Bookmarks
  - `impression_count`: Impressions
- `non_public_metrics`: Owner-only metrics
  - `impression_count`: Total impressions
  - `url_link_clicks`: Link clicks
  - `user_profile_clicks`: Profile clicks
- `organic_metrics`: Non-promoted metrics

**Mapping to SocialMediaPost**:
```python
metrics = tweet.public_metrics
performance_metrics = {
    'twitter': {
        'reach': metrics['impression_count'],  # Use impressions as reach
        'impressions': metrics['impression_count'],
        'engagement': metrics['like_count'] + metrics['retweet_count'] + metrics['reply_count'],
        'clicks': tweet.non_public_metrics.get('url_link_clicks', 0),
        'last_updated': datetime.now().isoformat()
    }
}
```

**Error Handling**:
- `tweepy.Forbidden`: No access to tweet (deleted or private)
- `tweepy.NotFound`: Tweet doesn't exist
- Network errors: Retry with backoff

**Rate Limit**: 900 requests per 15 minutes (60/minute)

---

### 5. Get User Info

**Purpose**: Retrieve account details and follower count

**Method**: `get_user`

**Request**:
```python
response = client.get_user(
    username='yourusername',
    user_fields=['public_metrics']
)
```

**Response**:
```python
Response(
    data=User(
        id='1234567890',
        name='Your Name',
        username='yourusername',
        public_metrics={
            'followers_count': 1280,
            'following_count': 450,
            'tweet_count': 3456,
            'listed_count': 12
        }
    )
)
```

**Use Case**: Track follower growth for weekly audit

**Rate Limit**: 900 requests per 15 minutes

---

## Error Codes

| Exception | HTTP Code | Description | Recovery Strategy |
|-----------|-----------|-------------|-------------------|
| `tweepy.Unauthorized` | 401 | Authentication failed | Escalate to human (check credentials) |
| `tweepy.Forbidden` | 403 | Permission denied | Escalate to human (check permissions) |
| `tweepy.NotFound` | 404 | Resource not found | Escalate to human (check ID) |
| `tweepy.TooManyRequests` | 429 | Rate limit exceeded | Wait (tweepy handles automatically) |
| `tweepy.BadRequest` | 400 | Invalid parameters | Escalate to human (fix request) |
| `tweepy.TwitterServerError` | 500-599 | Twitter server error | Retry with backoff |

---

## Rate Limiting

**Posting Limits**:
- 300 tweets per 3 hours (100/hour average)
- 2,400 tweets per day
- Includes original tweets, retweets, and quote tweets

**Reading Limits**:
- 900 requests per 15 minutes (60/minute) for most endpoints
- Varies by endpoint (check Twitter API docs)

**Implementation**:
tweepy handles rate limiting automatically with `wait_on_rate_limit=True`:
```python
client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret,
    wait_on_rate_limit=True  # Automatically waits when rate limited
)
```

**Circuit Breaker**:
- Open circuit after 10 consecutive failures
- Half-open after 15 minutes (rate limit window)
- Close circuit after 1 successful call

---

## Content Guidelines

**Best Practices**:
- Keep tweets concise and engaging
- Use 1-2 relevant hashtags (max 2 for best engagement)
- Include media when possible (tweets with images get 150% more retweets)
- Tag relevant accounts with @mentions
- Post during peak engagement times (varies by audience)
- Use threads for longer content

**Character Counting**:
- URLs: 23 characters (t.co shortening)
- Images: 24 characters
- Videos: 24 characters
- @mentions: Full length
- Hashtags: Full length

**Prohibited Content**:
- Spam or misleading content
- Hate speech or violence
- Adult content
- Copyright violations
- Impersonation

**Handling Policy Violations**:
- Twitter may reject tweets that violate policies
- Error code 403 (Forbidden) may indicate policy issue
- Repeated violations can result in account suspension
- Escalate to human for review

---

## Authentication

### OAuth 1.0a (Required for Posting)

**Credentials Needed**:
1. API Key (Consumer Key)
2. API Secret (Consumer Secret)
3. Access Token
4. Access Token Secret

**Setup**:
1. Create Twitter Developer account
2. Create app in Developer Portal
3. Generate API keys and tokens
4. Store in `.env` file

### OAuth 2.0 Bearer Token (Read-Only)

**Use Case**: Reading public data (metrics, user info)

**Setup**:
1. Generate bearer token in Developer Portal
2. Store in `.env` file

**Note**: tweepy Client accepts both for maximum flexibility

---

## Testing

**Contract Tests** (tests/contract/test_twitter_contracts.py):
- Test text tweet creation
- Test tweet with media
- Test thread creation
- Test metrics retrieval
- Test error handling for each error type
- Test rate limiting behavior (with mocks)
- Mock Twitter API responses

**Mock Responses**:
```python
from unittest.mock import Mock, patch

def test_post_tweet():
    with patch('tweepy.Client') as mock_client:
        mock_response = Mock()
        mock_response.data = {'id': '1234567890123456789', 'text': 'Test tweet'}
        mock_client.return_value.create_tweet.return_value = mock_response

        result = post_to_twitter('Test tweet')
        assert result['id'] == '1234567890123456789'
```

---

## Performance

**Optimization**:
- Use `wait_on_rate_limit=True` to avoid manual rate limit handling
- Batch metric requests when possible
- Cache user info (follower count doesn't change frequently)
- Compress images before upload to reduce upload time

**Monitoring**:
- Track API call count per 15-minute window
- Monitor response times (alert if >2 seconds)
- Log all errors for analysis
- Track tweet success rate (target: 95%+)

---

## Data Mapping

### Vault → Twitter

| Vault Field | Twitter Parameter | Transformation |
|-------------|-------------------|----------------|
| `content` | `text` | Truncate to 280 chars if needed |
| `media_urls[0-3]` | `media_ids` | Upload media, use IDs |
| `platforms` | Determines if tweet is sent | Check if 'twitter' in list |

### Twitter → Vault

| Twitter Field | Vault Field | Transformation |
|---------------|-------------|----------------|
| `id` | `post_id` (Twitter-specific) | Store in platform-specific metadata |
| `public_metrics.impression_count` | `performance_metrics.twitter.impressions` | Direct mapping |
| `public_metrics.impression_count` | `performance_metrics.twitter.reach` | Use impressions as reach |
| `like_count + retweet_count + reply_count` | `performance_metrics.twitter.engagement` | Sum of interactions |
| `non_public_metrics.url_link_clicks` | `performance_metrics.twitter.clicks` | Direct mapping |

---

## Special Features

### Automatic Rate Limit Handling

tweepy's `wait_on_rate_limit=True` automatically:
- Detects rate limit errors (429)
- Calculates wait time from response headers
- Sleeps until rate limit resets
- Retries request automatically

**No manual rate limit handling needed!**

### Error Recovery

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(tweepy.TwitterServerError)
)
def post_to_twitter(text, media_ids=None):
    return client.create_tweet(text=text, media_ids=media_ids)
```

### Thread Helper

```python
def post_thread(tweets: list[str]) -> list[str]:
    """Post a thread of tweets, returns list of tweet IDs"""
    tweet_ids = []
    previous_id = None

    for i, tweet_text in enumerate(tweets):
        try:
            response = client.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=previous_id
            )
            tweet_id = response.data['id']
            tweet_ids.append(tweet_id)
            previous_id = tweet_id
        except Exception as e:
            # If thread breaks, log error and stop
            logger.error(f"Thread failed at tweet {i+1}/{len(tweets)}: {e}")
            break

    return tweet_ids
```

---

## Limitations

**API Restrictions**:
- Cannot schedule tweets (must post immediately)
- Cannot edit published tweets
- Cannot delete tweets via API v2 (use v1.1)
- Metrics may have delay (up to 15 minutes)
- Cannot post polls via API

**Account Requirements**:
- Must have Twitter Developer account
- Must have app approved (Elevated access for full features)
- Free tier has lower rate limits

**Workarounds**:
- For scheduling: Use approval workflow, post when approved
- For editing: Delete and repost (loses engagement)
- For polls: Escalate to human for manual posting

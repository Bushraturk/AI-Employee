# Research: Gold Tier - Autonomous Employee

**Feature**: 003-gold-autonomous-employee
**Date**: 2026-02-23
**Phase**: Phase 0 - Research and Technology Selection

## Overview

This document consolidates research findings for technology choices required by Gold Tier implementation. All decisions prioritize local-first architecture, constitution compliance, and production reliability.

---

## 1. Odoo JSON-RPC Integration

### Decision: odoorpc library

### Rationale
- **Development Velocity**: High-level API mirrors server-side Odoo patterns, reduces implementation time by 60-70%
- **Error Handling**: Built-in retry logic, connection management, and dedicated error module
- **API Ergonomics**: Clean patterns for required operations (sync transactions, create entities, polling)
- **Maintenance**: Maintained by OCA (Odoo Community Association), version 0.10.1 (August 2023)
- **Constitution Compliance**: Aligns with "smallest viable change" principle, reduces custom code

### Alternatives Considered
- **requests (direct JSON-RPC)**: Maximum control but requires 200+ lines of boilerplate for authentication, session management, error handling. Rejected due to development time cost and increased complexity.
- **Hybrid approach**: Use odoorpc for standard operations, requests for edge cases. Rejected due to maintaining two parallel implementations.

### Implementation Notes
```python
# Add to requirements.txt
odoorpc>=0.10.1

# Configuration pattern (FR-002 - secure credentials)
import odoorpc
import os
from dotenv import load_dotenv

load_dotenv()

class OdooClient:
    def __init__(self):
        self.odoo = odoorpc.ODOO(
            os.getenv('ODOO_HOST'),
            port=int(os.getenv('ODOO_PORT'))
        )
        self.odoo.login(
            os.getenv('ODOO_DB'),
            os.getenv('ODOO_USER'),
            os.getenv('ODOO_PASSWORD')
        )
```

---

## 2. Social Media API Integration

### 2.1 Facebook API

#### Decision: requests + Direct Graph API calls

#### Rationale
- **Full Control**: Complete control over API calls, error handling, rate limiting
- **No Abstraction Overhead**: Graph API is well-documented and RESTful
- **Maintenance Independence**: Not dependent on third-party library updates
- **Production-Grade**: Most enterprise applications use direct API calls

#### Alternatives Considered
- **facebook-sdk**: Sporadic updates, lags behind Graph API changes, limited documentation. Rejected for production use.

### 2.2 Instagram API

#### Decision: Instagram Graph API via requests (Business/Creator accounts only)

#### Rationale
- **Official API**: Only legitimate way to post programmatically
- **Business Requirement**: Requires Facebook Business account and Instagram Business/Creator account
- **Compliance**: Follows Instagram ToS
- **Metrics Access**: Full access to insights and engagement data

#### Alternatives Considered
- **instagram-private-api (instagrapi)**: Violates Instagram ToS, account ban risk, no metrics access, unreliable. Rejected for production.

#### Important Limitations
- Requires Facebook Business Manager setup
- Only works with Business/Creator accounts (not personal)
- Cannot post Stories via API
- Requires app review for some permissions

### 2.3 Twitter (X) API

#### Decision: tweepy v4.14+

#### Rationale
- **Most Mature**: 10+ years of development, large community
- **Full API v2 Support**: Complete coverage of Twitter API v2 endpoints
- **Active Maintenance**: Regular updates through 2024-2025
- **Rate Limit Handling**: Built-in rate limit detection and waiting
- **OAuth 2.0 Support**: Modern authentication flow

#### Alternatives Considered
- **twitter-api-v2**: Focused on API v2, smaller community. Rejected in favor of tweepy's larger ecosystem.
- **requests (direct API calls)**: Must implement OAuth manually, no rate limit handling. Rejected due to boilerplate overhead.

### Implementation Notes
```python
# Add to requirements.txt
requests>=2.31.0
tweepy>=4.14.0

# Facebook/Instagram
class FacebookGraphAPI:
    BASE_URL = "https://graph.facebook.com/v18.0"

    def post_to_page(self, page_id: str, message: str, image_url: str = None):
        endpoint = f"{self.BASE_URL}/{page_id}/photos" if image_url else f"{self.BASE_URL}/{page_id}/feed"
        data = {"access_token": self.access_token, "message": message}
        if image_url:
            data["url"] = image_url
        response = self.session.post(endpoint, data=data)
        response.raise_for_status()
        return response.json()

# Twitter
import tweepy

class TwitterAPIClient:
    def __init__(self, bearer_token, api_key, api_secret, access_token, access_secret):
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
            wait_on_rate_limit=True
        )
```

---

## 3. Scheduling

### Decision: APScheduler (Continue Current Choice) with SQLite Job Store

### Rationale
- **Already Integrated**: APScheduler is already in use, no new learning curve
- **Persistence Support**: SQLite job store persists scheduled jobs across restarts
- **Multiple Trigger Types**: Supports cron (weekly audits), interval (5-minute polling), one-time triggers
- **Timezone Handling**: Built-in timezone support via pytz
- **Background Execution**: BackgroundScheduler runs in separate thread
- **Python 3.9+ Compatible**: Actively maintained

### Alternatives Considered
- **schedule library**: No persistence, no timezone support, no cron syntax. Rejected as too basic.
- **System cron**: Platform-specific, no programmatic control, violates local-first principle. Rejected.
- **Celery Beat**: Requires message broker, massive overkill. Rejected as over-engineered.

### Implementation Gap
Current implementation lacks persistence. Jobs are loaded from Markdown files on startup but APScheduler's in-memory job store doesn't survive crashes.

### Implementation Notes
```python
# Add to requirements.txt
APScheduler>=3.10.0  # Already present

# Add SQLite job store for persistence
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = BackgroundScheduler(jobstores=jobstores, timezone=timezone)
```

---

## 4. Error Recovery

### 4.1 Retry Logic

#### Decision: tenacity

#### Rationale
- **Declarative Syntax**: Clean decorator-based API
- **Comprehensive Strategies**: Exponential backoff, jitter, max attempts, time limits
- **Exception Filtering**: Distinguish transient vs permanent errors (FR-052)
- **Callbacks**: Before/after/retry callbacks for logging (FR-059, FR-064)
- **Actively Maintained**: 6K+ GitHub stars, Python 3.9+ compatible

#### Alternatives Considered
- **backoff library**: Less flexible exception handling, smaller community. Rejected in favor of tenacity's features.
- **Custom retry logic**: Error-prone, maintenance burden. Rejected as reinventing the wheel.
- **requests built-in retry**: Only works with requests, not applicable to Odoo or other integrations. Rejected as too narrow.

### 4.2 Circuit Breaker

#### Decision: pybreaker

#### Rationale
- **Simple API**: Easy to integrate with existing code
- **State Management**: Tracks closed/open/half-open states automatically
- **Callbacks**: Listeners for state changes, enables FR-056 (notify users)
- **Thread-Safe**: Safe for concurrent use with multiple MCP servers
- **Persistent State**: Can be extended to persist circuit state to Markdown files
- **Python 3.9+ Compatible**: Actively maintained

#### Alternatives Considered
- **Custom circuit breaker**: Complex state management, threading issues. Rejected as too complex to implement correctly.
- **pycircuitbreaker**: Less maintained (last update 2019). Rejected in favor of pybreaker.
- **No circuit breaker (retry only)**: Doesn't meet FR-055 requirement. Rejected as insufficient.

### 4.3 Action Queuing

#### Decision: Custom Queue with Markdown Persistence

#### Rationale
- **Constitution Compliance**: Must store queue state as Markdown files (Principle III)
- **Simple Requirements**: FIFO queue with persistence, no complex message broker features needed
- **Integration**: Tight integration with vault structure and MCP server routing

#### Alternatives Considered
- **Redis/RabbitMQ**: Violates local-first architecture, external dependency. Rejected.
- **Python queue.Queue**: In-memory only, no persistence, violates "no hidden state". Rejected.
- **SQLite queue**: Not Markdown, violates constitution. Rejected.

### Implementation Notes
```python
# Add to requirements.txt
tenacity>=8.2.0
pybreaker>=1.0.0

# Integration pattern
from tenacity import retry, stop_after_attempt, wait_exponential
from pybreaker import CircuitBreaker

odoo_breaker = CircuitBreaker(fail_max=10, timeout_duration=300)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(TransientError)
)
@odoo_breaker
def sync_odoo_transaction(transaction):
    # If circuit is open, raises CircuitBreakerError
    # If transient error, retries with backoff
    # If permanent error, raises immediately
    pass

# Queue structure in vault
AI_Employee_Vault/
├── Action_Queue/
│   ├── odoo_queue.md
│   ├── facebook_queue.md
│   └── twitter_queue.md
```

---

## 5. MCP Server Orchestration

### Decision: Process-Based Approach (subprocess module)

### Rationale
- **Fault Isolation**: Each MCP server runs in separate memory space, critical for FR-037
- **Independent Lifecycle**: Each server can be started/stopped/restarted independently
- **Resource Management**: Clear resource boundaries, easier monitoring
- **Proven Pattern**: Orchestrator already uses subprocess for Claude Code CLI
- **Cross-Platform**: subprocess works on Windows, macOS, Linux

### Alternatives Considered
- **Thread-Based (threading)**: Python GIL limits parallelism, shared memory means one crash can corrupt others, no fault isolation. Rejected.
- **Async-Based (asyncio)**: Single process means no fault isolation, one exception crashes all servers. Rejected.
- **Hybrid (multiprocessing)**: More complex than subprocess, adds IPC overhead we don't need. Rejected as over-engineered.

### Implementation Pattern
```python
# Architecture
┌─────────────────────────────────────────────────┐
│         Orchestrator (Main Process)             │
│  - Routes actions to appropriate MCP server     │
│  - Monitors server health                       │
│  - Handles server lifecycle                     │
└────┬────────────┬────────────┬─────────────────┘
     │            │            │
     ▼            ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Accounting  │ │   Social    │ │    Comms    │
│ MCP Server  │ │ MCP Server  │ │ MCP Server  │
│ (Process 1) │ │ (Process 2) │ │ (Process 3) │
└─────────────┘ └─────────────┘ └─────────────┘

# Key components
class MCPServerOrchestrator:
    def start_server(self, server_id: str) -> bool:
        process = subprocess.Popen(
            ['python', script_path, '--vault', str(self.vault_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1
        )

    def health_check(self, server_id: str) -> bool:
        # Check if process is alive
        # Send ping command
        # Attempt restart if configured

    def route_action(self, action_type: str) -> Optional[str]:
        # Route to accounting/social/communications based on action type
```

---

## Summary of Dependencies

Add to `requirements.txt`:
```
# Gold Tier - Odoo Integration
odoorpc>=0.10.1

# Gold Tier - Social Media
requests>=2.31.0
tweepy>=4.14.0

# Gold Tier - Error Recovery
tenacity>=8.2.0
pybreaker>=1.0.0

# Already present (verify versions)
APScheduler>=3.10.0
python-dotenv>=1.0.0
```

---

## Persistence Strategy

For reliable operation across restarts:

1. **APScheduler**: Use SQLite job store for job persistence
2. **Circuit Breakers**: Persist state to Markdown files in `Circuit_State/` folder
3. **Action Queues**: Store as Markdown files in `Action_Queue/` folder
4. **On Startup**: Load circuit states, restore queues, verify APScheduler jobs match Markdown schedules

This maintains constitution compliance (Markdown as source of truth) while providing production reliability.

---

## Next Steps

Phase 1 will use these research findings to:
1. Design data models for new entities (OdooTransaction, SocialMediaPost, etc.)
2. Generate API contracts for Odoo, Facebook, Instagram, Twitter integrations
3. Create quickstart guide for Gold Tier setup
4. Update agent context with new technologies

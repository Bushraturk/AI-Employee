---
id: 003
title: LinkedIn Token Storage .env Fallback Implementation
stage: green
date: 2026-02-21
surface: agent
model: claude-sonnet-4-5
feature: 002-silver-functional
branch: 002-silver-functional
user: admin
command: implement
labels: ["linkedin", "oauth2", "token-storage", "windows-keyring", "env-fallback"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - linkedin_authenticate.py
  - linkedin_publish.py
  - .env
tests:
  - Manual test: python linkedin_authenticate.py (successful token save to .env)
  - Manual test: python linkedin_publish.py (successful token load and LinkedIn post)
---

## Prompt

Implement the following plan:

# Plan: Fix LinkedIn Token Storage & Enable Posting

## Problem Summary

LinkedIn OAuth2 authentication succeeded but token storage failed with Windows keyring error:
```
[ERROR] (1783, 'CredWrite', 'The stub received bad data')
```

User needs:
1. Save LinkedIn tokens to .env file as fallback
2. Learn how to post to LinkedIn using the saved tokens

[Full plan details provided in previous context]

## Response snapshot

Implemented .env fallback for LinkedIn token storage:

**linkedin_authenticate.py changes:**
- Added `from dotenv import set_key` import
- Created `_save_tokens_to_env()` function to write tokens to .env
- Modified token storage (line 150-162) to try keyring first, then fallback to .env on error
- Tokens saved as: LINKEDIN_ACCESS_TOKEN, LINKEDIN_TOKEN_TYPE, LINKEDIN_EXPIRES_IN, LINKEDIN_OBTAINED_AT, LINKEDIN_EXPIRES_AT, LINKEDIN_REFRESH_TOKEN

**linkedin_publish.py changes:**
- Added `import os` and `from dotenv import load_dotenv`
- Created `_load_tokens_from_env()` function to read tokens from .env
- Modified `get_linkedin_tokens()` to try keyring first, then fallback to .env
- Returns token dictionary compatible with existing code

**.env changes:**
- Added LinkedIn OAuth2 token placeholders (auto-populated by authentication script)

**Testing:**
- Ran `python linkedin_authenticate.py` - tokens saved to .env successfully
- Ran `python linkedin_publish.py` - loaded tokens from .env and posted to LinkedIn
- Post ID: urn:li:share:7430992934721753088
- Approval file updated to 'completed' status

## Outcome

- ✅ Impact: LinkedIn authentication now works on Windows despite keyring limitations. Tokens stored securely in .env (already in .gitignore). LinkedIn posting fully functional.
- 🧪 Tests: Manual authentication test passed, manual publishing test passed, post successfully published to LinkedIn
- 📁 Files: Modified 3 files (linkedin_authenticate.py, linkedin_publish.py, .env)
- 🔁 Next prompts: Consider migrating to TokenStorage class for encrypted file storage as long-term solution
- 🧠 Reflection: Simple .env fallback solved immediate problem. Windows Credential Manager has data format restrictions that cause keyring failures with JSON tokens.

## Evaluation notes (flywheel)

- Failure modes observed: Windows keyring error 1783 when storing JSON token data
- Graders run and results (PASS/FAIL): PASS - Authentication successful, tokens saved, posting successful
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Monitor token expiration (60 days) and implement refresh flow if needed

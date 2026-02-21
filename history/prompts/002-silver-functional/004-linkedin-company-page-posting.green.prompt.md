---
id: 004
title: LinkedIn Company Page Posting Setup
stage: green
date: 2026-02-21
surface: agent
model: claude-sonnet-4-5
feature: 002-silver-functional
branch: 002-silver-functional
user: admin
command: implement
labels: ["linkedin", "company-page", "api-limitation", "semi-automated", "workaround"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - linkedin_company_helper.py
  - linkedin_quick_post.py
  - get_linkedin_organizations.py
  - linkedin_authenticate.py
  - LINKEDIN_COMPANY_PAGE_SETUP.md
  - COMPANY_PAGE_GUIDE_URDU.md
  - LINKEDIN_ORG_POSTING_ISSUE.md
  - setup_company_page.bat
tests:
  - Manual test: linkedin_quick_post.py (successful clipboard copy and browser open)
  - Manual test: User successfully posted to Smart AI System company page
---

## Prompt

User reported that LinkedIn post went to personal profile instead of "Smart AI System" company page. User wanted to post to company page, not personal profile.

User confirmed:
- They are admin of "Smart AI System" LinkedIn page
- They want all future posts to go to company page

## Response snapshot

**Investigation:**
- Checked LinkedIn app permissions in developer portal
- Found only `w_member_social` scope (personal posting)
- Missing `w_organization_social` scope (company page posting)
- LinkedIn restricts organization posting to verified apps/partners

**LinkedIn API Limitation Discovered:**
```
Current scopes: openid, profile, email, w_member_social
Required scope: w_organization_social (NOT AVAILABLE)
API Response: 403 Forbidden - "Not enough permissions"
```

**Why Automatic Posting Failed:**
1. LinkedIn "Share on LinkedIn" product has Default Tier
2. Default Tier only allows personal profile posting
3. Organization posting requires:
   - Marketing Developer Platform access
   - App verification
   - Partner program approval
4. Individual developers rarely get this access

**Solution Implemented - Semi-Automated Helper:**

Created `linkedin_quick_post.py` that:
1. Reads approved post from approval file
2. Copies content to clipboard (using pyperclip)
3. Opens LinkedIn company page admin in browser
4. User pastes (Ctrl+V) and clicks "Post"

**Files Created:**
- `linkedin_company_helper.py` - Full interactive version
- `linkedin_quick_post.py` - Simple non-interactive version
- `get_linkedin_organizations.py` - Find organization ID (for future if API access granted)
- `LINKEDIN_COMPANY_PAGE_SETUP.md` - English setup guide
- `COMPANY_PAGE_GUIDE_URDU.md` - Urdu setup guide
- `LINKEDIN_ORG_POSTING_ISSUE.md` - Technical explanation of API limitation
- `setup_company_page.bat` - Automated setup script (for if API access granted)

**Updated Files:**
- `linkedin_authenticate.py` - Added `w_organization_social` to scope (ready if permission granted)

**Testing:**
- Installed pyperclip package
- Ran linkedin_quick_post.py
- Content copied to clipboard successfully
- Browser opened to company page admin
- User manually pasted and posted successfully
- Post now live on "Smart AI System" company page

**User Education:**
Explained why automatic posting wasn't possible:
- Not a code limitation
- LinkedIn API policy restriction
- Only verified partners get organization posting access
- Semi-automated approach is best available solution

## Outcome

- ✅ Impact: User can now post to company page using semi-automated helper. Content preparation is automatic, only final click is manual. Much faster than writing posts from scratch.
- 🧪 Tests: Manual posting test passed, post successfully published to Smart AI System company page
- 📁 Files: Created 8 new files (helper scripts, documentation, guides)
- 🔁 Next prompts: If LinkedIn grants organization API access in future, can switch to fully automatic posting using get_linkedin_organizations.py
- 🧠 Reflection: LinkedIn heavily restricts company page posting APIs. Semi-automated approach is pragmatic solution. User understood the limitation and successfully used the workaround.

## Evaluation notes (flywheel)

- Failure modes observed: LinkedIn API 403 Forbidden for organization posting, w_organization_social scope not available in app
- Graders run and results (PASS/FAIL): PASS - User successfully posted to company page using helper script
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Monitor if LinkedIn grants organization API access, or explore LinkedIn Partner Program application

# LinkedIn Company Page Posting Setup Guide

## Current Status
- ✅ Personal profile posting works
- ❌ Company page posting needs `w_organization_social` permission

## Step-by-Step Instructions

### Step 1: Add Organization Permission to LinkedIn App

1. **Open LinkedIn Developers Portal:**
   - Go to: https://www.linkedin.com/developers/apps
   - Login if needed

2. **Select Your App:**
   - Find and click on app: `777wvydg3gcbhy`
   - Or search for your app name

3. **Add "Share on LinkedIn" Product:**
   - Click on "Products" tab
   - Look for "Share on LinkedIn" product
   - If not added, click "Request access" or "Add product"
   - Wait for approval (usually instant for some apps)

4. **Add Organization Scope:**
   - Click on "Auth" tab
   - Scroll to "OAuth 2.0 scopes"
   - Find and enable: `w_organization_social`
   - Current scopes: `openid`, `profile`, `email`, `w_member_social`
   - Add: `w_organization_social`
   - Click "Update" or "Save"

5. **Verify Redirect URI:**
   - Still in "Auth" tab
   - Check "Redirect URLs" section
   - Ensure this is listed: `http://localhost:8001/callback`
   - If not, add it and save

### Step 2: Re-authenticate with New Permissions

After adding the permission in LinkedIn Developer Portal:

```powershell
# Run authentication again to get new token with organization access
python linkedin_authenticate.py
```

**What will happen:**
- Browser will open
- You'll see new permission request: "Post on behalf of organizations"
- Approve it
- New token will be saved to .env

### Step 3: Find Your Company Page

```powershell
# This will find "Smart AI System" page and save its ID
python get_linkedin_organizations.py
```

**Expected output:**
- List of organizations you manage
- "Smart AI System" page ID saved to .env

### Step 4: Post to Company Page

```powershell
# Modified script will post to company page instead of personal profile
python linkedin_publish_company.py
```

---

## Troubleshooting

### If "Share on LinkedIn" product is not available:
- Your app might need verification
- Contact LinkedIn support
- Or create a new app with proper settings

### If you don't see w_organization_social scope:
- Make sure "Share on LinkedIn" product is added first
- Refresh the page
- Check if your app has the right permissions

### If organization not found after re-auth:
- Verify you're admin of "Smart AI System" page
- Check page is published and active
- Try logging out and back into LinkedIn

---

## Next Steps

1. ✅ Add `w_organization_social` permission in LinkedIn Developer Portal
2. ⏳ Re-run: `python linkedin_authenticate.py`
3. ⏳ Run: `python get_linkedin_organizations.py`
4. ⏳ I'll create the company page posting script

---

**Current App Details:**
- Client ID: 777wvydg3gcbhy
- Redirect URI: http://localhost:8001/callback
- Current Scopes: openid, profile, email, w_member_social
- Needed Scope: w_organization_social

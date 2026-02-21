# LinkedIn Company Page Posting - Quick Guide (Urdu)

## Kya Ready Hai?

✅ `linkedin_authenticate.py` - Organization permission ke saath updated
✅ `linkedin_publish_company.py` - Company page par post karne ke liye
✅ `get_linkedin_organizations.py` - Aapka company page dhoondhne ke liye
✅ `setup_company_page.bat` - Automatic setup script

---

## Ab Kya Karna Hai? (Step by Step)

### Step 1: LinkedIn Developer Portal mein Permission Add Karein

**Manual Steps (Browser mein):**

1. **Developer Portal kholein:**
   ```
   https://www.linkedin.com/developers/apps
   ```

2. **Apni app select karein:**
   - App ID: `777wvydg3gcbhy` dhoondhein
   - Click karein

3. **"Products" tab mein jaayein:**
   - "Share on LinkedIn" product check karein
   - Agar nahi hai to "Request access" click karein
   - Wait karein approval ke liye (usually instant)

4. **"Auth" tab mein jaayein:**
   - "OAuth 2.0 scopes" section dhoondhein
   - Ye scopes hone chahiye:
     - ✅ openid
     - ✅ profile
     - ✅ email
     - ✅ w_member_social
     - ❌ w_organization_social (YE ADD KARNA HAI!)
   - `w_organization_social` checkbox check karein
   - "Update" ya "Save" button click karein

5. **Confirm karein:**
   - Page refresh karein
   - Check karein ke `w_organization_social` ab list mein hai

---

### Step 2: Naye Permission ke Saath Re-authenticate Karein

**PowerShell mein run karein:**

```powershell
python linkedin_authenticate.py
```

**Kya hoga:**
- Browser khulega
- LinkedIn login page aayega
- **IMPORTANT:** Naya permission dikhega: "Post on behalf of organizations"
- "Allow" ya "Authorize" click karein
- Success message aayega
- Token .env file mein save hoga

---

### Step 3: "Smart AI System" Page Dhoondhein

**PowerShell mein run karein:**

```powershell
python get_linkedin_organizations.py
```

**Expected Output:**
```
[SUCCESS] Found 1 organization(s)

1. Smart AI System
   Organization ID: 12345678
   Organization URN: urn:li:organization:12345678
   >>> THIS IS YOUR 'Smart AI System' PAGE! <<<

[SUCCESS] Saved organization ID to .env file!
```

---

### Step 4: Company Page Par Post Karein

**Pehle approval file ko reset karein (kyunki already completed hai):**

```powershell
# Open file in notepad
notepad AI_Employee_Vault\Needs_Approval\07723a50-6f86-40d0-a4d1-e5fc3c8eb54a.md

# Change this line:
status: completed
# To:
status: approved
```

**Phir post karein:**

```powershell
python linkedin_publish_company.py
```

**Expected Output:**
```
[SUCCESS] Post published to LinkedIn Company Page!
Post ID: urn:li:share:...
Company Page: Smart AI System
```

---

## Automatic Setup (Optional)

Agar aap automatic setup chahte hain:

```powershell
.\setup_company_page.bat
```

Ye script automatically sab steps guide karega.

---

## Troubleshooting

### Agar "w_organization_social" scope nahi mil raha:
- "Share on LinkedIn" product pehle add karein
- Page refresh karein
- LinkedIn support se contact karein

### Agar organization nahi mila:
- Verify karein ke aap "Smart AI System" page ke admin hain
- LinkedIn par jaake check karein: https://www.linkedin.com/company/smart-ai-system/admin/
- Page published aur active hona chahiye

### Agar permission error aaye:
- Step 1 aur 2 dobara karein
- Ensure karein ke authentication mein "Post on behalf of organizations" permission approve kiya

---

## Summary

**Current Status:**
- ✅ Personal profile posting works
- ⏳ Company page posting setup in progress

**What You Need to Do:**
1. Add `w_organization_social` permission in LinkedIn Developer Portal
2. Run: `python linkedin_authenticate.py`
3. Run: `python get_linkedin_organizations.py`
4. Reset approval file status to "approved"
5. Run: `python linkedin_publish_company.py`

**Result:**
- Post will appear on "Smart AI System" LinkedIn company page
- Not on your personal profile

---

## Need Help?

Agar koi step samajh nahi aaya ya error aaya, mujhe batayein!

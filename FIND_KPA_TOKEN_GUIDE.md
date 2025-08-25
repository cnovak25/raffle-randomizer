# Finding Your KPA API Token - Step by Step Guide

## What You're Looking For

You need to find **API requests to KPA**, not JavaScript files. The files you showed are all frontend code.

## Steps to Find the Real KPA API Calls:

### 1. Filter the Network Tab
In Chrome DevTools Network tab:
- Click the **"XHR"** button to show only API calls
- Or click **"Fetch/XHR"** to filter out JavaScript files
- This will hide all the `.js` files you're seeing

### 2. Look for KPA Domain Requests
Look for requests going to domains like:
- `api.kpa.io`
- `mvncorp.kpaehs.com` 
- `kpa.com`
- Any domain with "kpa" in the name

### 3. Trigger a KPA Action
To generate API calls:
- Navigate to a different page in KPA
- Search for employees
- Access the Great Save Raffle form
- Refresh the KPA page

### 4. Find the Authorization Header
Click on a KPA API request and look in the **Request Headers** section for:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Alternative: Check KPA Directly

If you can't find API calls, try:

1. **Go directly to KPA API documentation** in your browser
2. **Open KPA admin/settings** where API tokens might be shown
3. **Check if KPA has an "API Keys" or "Tokens" section**

## Manual Token Entry

If you find a token, you can enter it directly by editing the `.env` file:

```bash
# Edit this file directly:
/workspaces/raffle-randomizer/secrets/.env

# Change this line:
KPA_API_TOKEN=your_actual_token_here
```

The token should be a long string (100+ characters) that starts with something like:
- `eyJ0eXAiOiJKV1QiLCJ...` (JWT token)
- Or another long alphanumeric string

Let me know what you find when you filter to XHR/API requests!

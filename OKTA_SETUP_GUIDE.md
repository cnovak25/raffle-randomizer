# OKTA SSO Setup for KPA API Integration

## Overview

Since your organization uses OKTA SSO, the KPA API likely requires OKTA authentication instead of simple Bearer tokens. This document explains two ways to configure OKTA authentication for the raffle system.

## Option 1: Use Your Personal OKTA Credentials (Recommended for Testing)

This is the simplest approach - use your own OKTA username and password to authenticate with the KPA API.

### Quick Setup

1. **Run the setup script**:
   ```bash
   cd /workspaces/raffle-randomizer
   python3 setup_okta_credentials.py
   ```

2. **Or manually update** `/workspaces/raffle-randomizer/secrets/.env`:
   ```bash
   # Your personal OKTA credentials
   OKTA_DOMAIN=your-company.okta.com
   OKTA_USERNAME=your.email@company.com
   OKTA_PASSWORD=your_okta_password
   ```

3. **Restart the server** and test:
   ```bash
   curl http://127.0.0.1:5000/api/v1/health
   ```

### Expected Result
```json
{
  "services": {
    "okta_sso": {
      "status": "connected_user_credentials",
      "method": "user: your.email@company.com"
    },
    "kpa_api": "connected"
  }
}
```

## Option 2: Service-to-Service Authentication (For Production)

Your OKTA administrator needs to:

1. **Create a new OKTA application** for the raffle system
   - Application type: "Service App" or "API Service"
   - Grant type: "Client Credentials" (for service-to-service auth)

2. **Configure API scopes** for KPA access
   - Scope name: `kpa_api_access` (or whatever KPA requires)
   - Description: "Access to KPA API for raffle system"

3. **Provide credentials** to the raffle team:
   - OKTA Domain (e.g., `your-company.okta.com`)
   - Client ID
   - Client Secret
   - Required scopes

### 2. Environment Configuration

Update `/workspaces/raffle-randomizer/secrets/.env`:

```bash
# OKTA SSO Configuration for KPA API Authentication
OKTA_DOMAIN=your-company.okta.com
OKTA_CLIENT_ID=your_actual_client_id_here
OKTA_CLIENT_SECRET=your_actual_client_secret_here
OKTA_SCOPE=kpa_api_access

# Keep the direct token as fallback
KPA_API_TOKEN=pTfES8COPXiB3fCCE0udSxg1g2vslyB2q
```

## How OKTA Authentication Works

### 1. Token Exchange Flow

```
Raffle API Server → OKTA Token Endpoint → Get Access Token → Use Token for KPA API
```

### 2. Code Implementation

The system now supports both authentication methods:

- **Primary**: OKTA SSO (preferred)
- **Fallback**: Direct API token (if OKTA not configured)

### 3. Token Management

- Tokens are obtained on-demand for each KPA API request
- Failed authentication triggers automatic retry
- Health endpoint shows OKTA connection status

## Testing Authentication

### 1. Health Check with OKTA Status

```bash
curl http://127.0.0.1:5000/api/v1/health
```

Response shows:
```json
{
  "services": {
    "okta_sso": "connected|not_configured|authentication_failed",
    "kpa_api": "connected|okta_authentication_failed|error"
  }
}
```

### 2. Authentication Priority

1. **OKTA configured** → Use OKTA tokens
2. **OKTA not configured** → Fall back to direct API token  
3. **Neither working** → Return authentication error

## Common Issues & Solutions

### ❌ "OKTA authentication failed"
- **Cause**: Wrong OKTA credentials or configuration
- **Solution**: Verify OKTA_DOMAIN, CLIENT_ID, CLIENT_SECRET in `.env`

### ❌ "KPA API authentication failed" 
- **Cause**: OKTA token doesn't have proper scopes for KPA
- **Solution**: Ask OKTA admin to add KPA API scopes

### ❌ "Token expired or invalid"
- **Cause**: OKTA token expired
- **Solution**: System automatically gets new token on next request

### ❌ "Scope insufficient"
- **Cause**: OKTA app doesn't have required KPA scopes
- **Solution**: OKTA admin needs to grant `kpa_api_access` scope

## Next Steps

1. **Get OKTA credentials** from your OKTA administrator
2. **Update `.env` file** with real OKTA values
3. **Test authentication** using health endpoint
4. **Verify KPA API access** with actual employee data

Once OKTA is properly configured, all authentication errors should resolve and the system will be able to access KPA's "Great Save Raffle" form data.

## Questions for OKTA Admin

1. What is our organization's OKTA domain?
2. Can you create a service application for the raffle system?
3. What scopes are required to access the KPA API?
4. Is there a specific OKTA group or policy for KPA API access?
5. Should we use client credentials flow or a different grant type?

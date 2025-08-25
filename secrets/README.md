# Secrets folder - DO NOT COMMIT TO VERSION CONTROL

This folder contains sensitive configuration files including:
- API tokens
- Database credentials  
- Secret keys

Files in this folder should never be committed to git.

## Setup Instructions:

1. Copy `.env.example` to `.env`
2. Fill in your actual KPA API token and other credentials
3. Ensure this folder is in your `.gitignore`

## Security Notes:

- API tokens should be treated as passwords
- Rotate tokens regularly
- Use environment-specific tokens (dev/staging/prod)
- Monitor API usage and rate limits

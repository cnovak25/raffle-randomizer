#!/usr/bin/env python3
"""
Manual OKTA Token Setup
Since automated OKTA authentication can be complex, this script helps you
manually extract and use an OKTA token from your browser session.
"""

def setup_manual_token():
    """Help user set up manual OKTA token"""
    print("🔧 Manual OKTA Token Setup for KPA API")
    print("=" * 50)
    print()
    print("Since OKTA automation can be complex, let's use a manual token approach:")
    print()
    print("📋 Steps to get your OKTA token:")
    print("1. Open your browser and log into OKTA/KPA")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Network tab")
    print("4. Make a request to KPA (refresh the page)")
    print("5. Look for a request to KPA API")
    print("6. In the request headers, find 'Authorization: Bearer <token>'")
    print("7. Copy the token (the part after 'Bearer ')")
    print()
    
    token = input("🔑 pTfES8COPXiB3fCCE0udSxg1g2vslyB2q: ").strip()
    
    if not token:
        print("❌ No token provided")
        return
    
    print(f"📝 Token length: {len(token)} characters")
    print(f"📝 Token preview: {token[:20]}...")
    
    confirm = input("\n✅ Save this token? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Setup cancelled")
        return
    
    # Update .env file
    env_path = "secrets/.env"
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    updated_lines = []
    found_kpa_token = False
    
    for line in lines:
        if line.startswith('KPA_API_TOKEN='):
            updated_lines.append(f'KPA_API_TOKEN={token}\n')
            found_kpa_token = True
        else:
            updated_lines.append(line)
    
    if not found_kpa_token:
        updated_lines.append(f'KPA_API_TOKEN={token}\n')
    
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ Token saved to secrets/.env")
    print("\n🚀 Next steps:")
    print("1. Restart the KPA API server")
    print("2. Test: curl http://127.0.0.1:5000/api/v1/health")
    print("3. The token should work until your OKTA session expires")
    print()
    print("⚠️  Note: You'll need to repeat this process when the token expires")

if __name__ == '__main__':
    setup_manual_token()

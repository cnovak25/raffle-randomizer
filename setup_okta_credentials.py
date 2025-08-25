#!/usr/bin/env python3
"""
Quick setup script for OKTA user credentials
"""
import os
from getpass import getpass

def setup_user_credentials():
    """Interactive setup for OKTA user credentials"""
    print("🔧 OKTA User Credentials Setup for KPA API")
    print("=" * 50)
    
    # Read current .env file
    env_path = "secrets/.env"
    if not os.path.exists(env_path):
        print("❌ secrets/.env file not found!")
        return
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    print("\n📝 Please provide your OKTA credentials:")
    
    # Get user input
    okta_domain = input("https://mvncorp.okta.com/oauth2/v1/authorize?client_id=okta.2b1959c8-bcc0-56eb-a589-cfcfb7422f26&code_challenge=tt8bTuSj8UZ6PE37Tm1QUD9D_E0yTRT-j10gHfYzQ5Q&code_challenge_method=S256&nonce=oI6yiIYsWqViMpsGuHHn6yiZWPQQLtyzFhCQOZquORX0k1udsXFFF8yfy2vOKYjM&redirect_uri=https%3A%2F%2Fmvncorp.okta.com%2Fenduser%2Fcallback&response_type=code&state=wggzYynQzACH4etlynhTsQ1jtvoppbAssOG0eKugiFG7DczZDc0JOQ7iXrCOwYqU&scope=openid%20profile%20email%20okta.users.read.self%20okta.users.manage.self%20okta.internal.enduser.read%20okta.internal.enduser.manage%20okta.enduser.dashboard.read%20okta.enduser.dashboard.manage%20okta.myAccount.sessions.manage): ").strip()
    okta_username = input("cnovak@mvncorp.com: ").strip()
    okta_password = getpass("Connor500$: ").strip()
    
    print(f"\n🔍 Using OKTA Domain: {okta_domain}")
    print(f"🔍 Using Username: {okta_username}")
    print("🔍 Password: [HIDDEN]")
    
    confirm = input("\n✅ Save these credentials to secrets/.env? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Setup cancelled")
        return
    
    # Update .env file
    updated_lines = []
    for line in lines:
        if line.startswith('OKTA_DOMAIN='):
            updated_lines.append(f'OKTA_DOMAIN={okta_domain}\n')
        elif line.startswith('OKTA_USERNAME='):
            updated_lines.append(f'OKTA_USERNAME={okta_username}\n')
        elif line.startswith('OKTA_PASSWORD='):
            updated_lines.append(f'OKTA_PASSWORD={okta_password}\n')
        else:
            updated_lines.append(line)
    
    # Write updated .env file
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ OKTA credentials saved to secrets/.env")
    print("\n🚀 Next steps:")
    print("1. Restart the KPA API server")
    print("2. Check health endpoint: curl http://127.0.0.1:5000/api/v1/health")
    print("3. Look for 'okta_sso': 'connected_user_credentials'")
    
    print("\n⚠️  Security Note:")
    print("- Your password is stored in plain text in .env file")
    print("- Make sure secrets/.env is in .gitignore")
    print("- Consider using app-specific passwords if available")

if __name__ == '__main__':
    setup_user_credentials()

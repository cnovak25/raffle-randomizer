#!/usr/bin/env python3
"""
Test KPA photo authentication directly
"""
import os
import requests

# Use the session cookie from browser tools
session_cookie = 's%3Am3njt8thebwkb0kk0jnc6wj.460QPgA3FJzSxchjUanrUPbrMuthy6pX4vrz1DZuGQQ'

# Test photo ID
photo_id = '60e0a0b6-b0f6-4374-b9d8-1e7a98773451'

# KPA photo URL
photo_url = f"https://mvncorp.kpaehs.com/get-upload?key={photo_id}"

# Headers with session authentication
headers = {
    'Cookie': f'6Pphk3dbK4Y-mvncorp={session_cookie}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"🔍 Testing KPA photo authentication...")
print(f"URL: {photo_url}")
print(f"Cookie: 6Pphk3dbK4Y-mvncorp={session_cookie[:20]}...")

try:
    response = requests.get(photo_url, headers=headers, timeout=10, allow_redirects=True)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
    print(f"Content-Length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Photo authentication working!")
        if response.content.startswith(b'\xff\xd8\xff'):
            print("✅ Valid JPEG image received")
        else:
            print("⚠️  Response is not a JPEG image")
    else:
        print(f"❌ Failed with status {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Error: {e}")

#!/usr/bin/env python3
"""
Ultra-simple KPA photo proxy for Railway
"""
import os
from flask import Flask, Response, request
import requests

app = Flask(__name__)

# Get session cookie from environment (with fallback)
SESSION_COOKIE = os.environ.get('KPA_SESSION_COOKIE', '6Pphk3dbK4Y-mvncorp')
print(f"Using KPA session cookie: {SESSION_COOKIE[:10]}...")  # Only show first 10 chars for security

@app.route('/')
def home():
    return {"message": "KPA Photo Proxy", "status": "running"}

@app.route('/health')
def health():
    return {"status": "healthy"}

@app.route('/test')
def test_endpoint():
    """Test endpoint to verify proxy is working"""
    test_key = request.args.get('key', 'test-key-123')
    return {
        "message": "Test endpoint working",
        "test_key": test_key,
        "session_cookie": f"{SESSION_COOKIE[:10]}...",
        "test_url": f"https://mvncorp.kpaehs.com/get-upload?key={test_key}"
    }

@app.route('/kpa-photo')
def get_photo():
    key = request.args.get('key')
    if not key:
        return {"error": "Missing key parameter"}, 400
    
    try:
        # Construct KPA URL - using the correct domain and path
        kpa_url = f"https://mvncorp.kpaehs.com/get-upload?key={key}"
        print(f"Fetching photo from: {kpa_url}")
        
        # Headers with session - using correct session cookie name
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': f'ASP.NET_SessionId={SESSION_COOKIE}',
            'Referer': 'https://mvncorp.kpaehs.com/',
            'Accept': 'image/*'
        }
        print(f"Using headers: {headers}")
        
        # Fetch photo
        response = requests.get(kpa_url, headers=headers, timeout=10, allow_redirects=True)
        print(f"KPA response status: {response.status_code}")
        print(f"Final URL after redirects: {response.url}")
        print(f"KPA response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"Photo size: {len(response.content)} bytes")
            print(f"Content type: {response.headers.get('content-type', 'unknown')}")
            return Response(
                response.content,
                mimetype=response.headers.get('content-type', 'image/jpeg'),
                headers={'Cache-Control': 'public, max-age=3600'}
            )
        else:
            print(f"KPA error response: {response.text[:200]}...")
            return {"error": f"KPA returned {response.status_code}", "details": response.text[:200]}, response.status_code
            
    except Exception as e:
        print(f"Exception in get_photo: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "type": type(e).__name__}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

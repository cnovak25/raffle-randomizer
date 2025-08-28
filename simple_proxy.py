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

@app.route('/kpa-photo')
def get_photo():
    key = request.args.get('key')
    if not key:
        return {"error": "Missing key parameter"}, 400
    
    try:
        # Construct KPA URL
        kpa_url = f"https://mvncorp.kpadata.com/kpa/get-upload?key={key}"
        
        # Headers with session
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': f'KPASESSIONID={SESSION_COOKIE}',
            'Referer': 'https://mvncorp.kpadata.com/',
            'Accept': 'image/*'
        }
        
        # Fetch photo
        response = requests.get(kpa_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return Response(
                response.content,
                mimetype='image/jpeg',
                headers={'Cache-Control': 'public, max-age=3600'}
            )
        else:
            return {"error": f"KPA returned {response.status_code}"}, response.status_code
            
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

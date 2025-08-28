#!/usr/bin/env python3
"""
Unified Railway app - combines FastAPI proxy with Streamlit startup
"""
import os
import subprocess
import time
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import requests
import uvicorn

# Create FastAPI app for the proxy
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable for session cookie
KPA_SESSION_COOKIE = os.environ.get('KPA_SESSION_COOKIE', 's%3Am3njt8thebwkb0kk0jnc6wj.460QPgA3FJzSxchjUanrUPbrMuthy6pX4vrz1DZuGQQ')
KPA_SUBDOMAIN_COOKIE = os.environ.get('KPA_SUBDOMAIN_COOKIE', 's%3Amvncorp.zRRHS9UAtvE%2BnpuY6dV%2BGi2N3E0F3StPtWmcfIjtNkM')

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/kpa-photo")
async def get_kpa_photo(key: str):
    """Proxy endpoint to fetch KPA employee photos with authentication"""
    try:
        # KPA photo URL - using the correct get-upload endpoint (not thumbnail)
        photo_url = f"https://mvncorp.kpaehs.com/get-upload?key={key}"
        
        # Headers with session authentication
        headers = {
            'Cookie': f'6Pphk3dbK4Y-mvncorp={KPA_SESSION_COOKIE}; last-subdomain={KPA_SUBDOMAIN_COOKIE}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"🔍 Fetching photo: {photo_url}")
        print(f"🍪 Using session cookie: 6Pphk3dbK4Y-mvncorp={KPA_SESSION_COOKIE[:20]}...")
        print(f"🍪 Using subdomain cookie: last-subdomain={KPA_SUBDOMAIN_COOKIE[:20]}...")
        
        # Fetch the photo with redirect following
        response = requests.get(photo_url, headers=headers, timeout=15, allow_redirects=True)
        
        print(f"📊 Status: {response.status_code}")
        print(f"🔗 Final URL: {response.url}")
        print(f"📋 Content-Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"📏 Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '').lower()
            if 'image' in content_type or response.content.startswith(b'\xff\xd8\xff'):
                return Response(
                    content=response.content,
                    media_type="image/jpeg",
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "Access-Control-Allow-Origin": "*"
                    }
                )
            else:
                print(f"⚠️  Not an image - Content-Type: {content_type}")
                print(f"🔍 First 200 chars: {response.text[:200]}")
                raise HTTPException(status_code=500, detail="Response is not an image")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            raise HTTPException(status_code=404, detail="Photo not found")
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching photo: {str(e)}")

def start_streamlit():
    """Start Streamlit in a separate thread"""
    port = int(os.environ.get('PORT', 8080))  # Railway typically uses 8080
    streamlit_port = port + 1  # Use next port for Streamlit
    
    print(f"🎯 Starting Streamlit on port {streamlit_port}...")
    
    try:
        subprocess.run([
            "python", "-m", "streamlit", "run", "app.py",
            "--server.port", str(streamlit_port),
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--server.enableCORS", "false"
        ])
    except Exception as e:
        print(f"❌ Streamlit failed: {e}")

@app.get("/")
async def root():
    """Redirect to Streamlit app"""
    port = int(os.environ.get('PORT', 8080))  # Railway typically uses 8080
    streamlit_port = port + 1
    return {
        "message": "MVN Raffle System", 
        "streamlit_url": f"http://localhost:{streamlit_port}",
        "proxy_health": "/health",
        "photo_endpoint": "/kpa-photo?key=YOUR_PHOTO_KEY"
    }

if __name__ == "__main__":
    print("🎊 Starting unified Railway app...")
    
    # Start Streamlit in background thread
    streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Give Streamlit time to start
    time.sleep(3)
    
    # Start FastAPI on main port
    port = int(os.environ.get('PORT', 8080))  # Railway typically uses 8080
    print(f"🚀 Starting FastAPI on port {port}...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

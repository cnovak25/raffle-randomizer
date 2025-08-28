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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/kpa-photo")
async def get_kpa_photo(photo_id: str):
    """Proxy endpoint to fetch KPA employee photos with authentication"""
    try:
        # KPA photo URL - updated to correct domain and path
        photo_url = f"https://mvncorp.kpaehs.com/get-upload?key={photo_id}"
        
        # Headers with session authentication
        headers = {
            'Cookie': f'6Pphk3dbK4Y-mvncorp={KPA_SESSION_COOKIE}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Fetch the photo with redirect following
        response = requests.get(photo_url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            return Response(
                content=response.content,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        else:
            raise HTTPException(status_code=404, detail="Photo not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching photo: {str(e)}")

def start_streamlit():
    """Start Streamlit in a separate thread"""
    port = int(os.environ.get('PORT', 8501))
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
    port = int(os.environ.get('PORT', 8501))
    streamlit_port = port + 1
    return {
        "message": "MVN Raffle System", 
        "streamlit_url": f"http://localhost:{streamlit_port}",
        "proxy_health": "/health",
        "photo_endpoint": "/kpa-photo?photo_id=YOUR_PHOTO_ID"
    }

if __name__ == "__main__":
    print("🎊 Starting unified Railway app...")
    
    # Start Streamlit in background thread
    streamlit_thread = threading.Thread(target=start_streamlit, daemon=True)
    streamlit_thread.start()
    
    # Give Streamlit time to start
    time.sleep(3)
    
    # Start FastAPI on main port
    port = int(os.environ.get('PORT', 8501))
    print(f"🚀 Starting FastAPI on port {port}...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

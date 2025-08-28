import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
from typing import Optional
import time

app = FastAPI(title="KPA Photo Proxy", description="Proxy server for authenticated KPA photo access")

# Enable CORS for all origins (Railway will handle domain routing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get KPA session cookies from environment variables
KPA_SESSION_COOKIE = os.environ.get('KPA_SESSION_COOKIE', 's%3Am3njt8thebwkb0kk0jnc6wj.460QPgA3FJzSxchjUanrUPbrMuthy6pX4vrz1DZuGQQ')
KPA_SUBDOMAIN_COOKIE = os.environ.get('KPA_SUBDOMAIN_COOKIE', 's%3Amvncorp.zRRHS9UAtvE%2BnpuY6dV%2BGi2N3E0F3StPtWmcfIjtNkM')

# Simple in-memory cache
cache = {}
CACHE_TTL = 3600  # 1 hour

@app.get("/")
async def root():
    return {"message": "KPA Photo Proxy Server - UPDATED", "status": "running", "version": "2.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/debug")
async def debug_info():
    return {
        "session_cookie": KPA_SESSION_COOKIE[:20] + "..." if KPA_SESSION_COOKIE else "Not set",
        "subdomain_cookie": KPA_SUBDOMAIN_COOKIE[:20] + "..." if KPA_SUBDOMAIN_COOKIE else "Not set",
        "cookie_format": "6Pphk3dbK4Y-mvncorp + last-subdomain"
    }

@app.get("/kpa-photo")
async def get_kpa_photo(key: str = Query(..., description="KPA photo key")):
    """Fetch photo from KPA using authenticated session"""
    
    # Check cache first
    if key in cache:
        cached_data, cached_time = cache[key]
        if time.time() - cached_time < CACHE_TTL:
            return Response(content=cached_data, media_type="image/jpeg")
        else:
            del cache[key]
    
    try:
        # Construct KPA URL with correct domain and path
        kpa_url = f"https://mvncorp.kpaehs.com/get-upload?key={key}"
        print(f"Fetching photo from: {kpa_url}")
        
        # Set up headers with session cookies (updated format)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': f'6Pphk3dbK4Y-mvncorp={KPA_SESSION_COOKIE}; last-subdomain={KPA_SUBDOMAIN_COOKIE}',
            'Referer': 'https://mvncorp.kpaehs.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
        }
        print(f"Using headers: {headers}")
        
        # Fetch photo from KPA with redirect handling
        response = requests.get(kpa_url, headers=headers, timeout=30, allow_redirects=True)
        print(f"KPA response status: {response.status_code}")
        print(f"Final URL after redirects: {response.url}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"Photo size: {len(response.content)} bytes")
            print(f"Content type: {response.headers.get('content-type', 'unknown')}")
            
            # Cache the result
            cache[key] = (response.content, time.time())
            
            # Return the image with proper content type
            content_type = response.headers.get('content-type', 'image/jpeg')
            return Response(
                content=response.content, 
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        else:
            print(f"KPA error response: {response.text[:200]}...")
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Failed to fetch photo from KPA: {response.status_code}"
            )
            
    except Exception as e:
        print(f"Exception in get_kpa_photo: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching photo: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

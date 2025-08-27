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

# Get KPA session cookie from environment variable
KPA_SESSION_COOKIE = os.environ.get('KPA_SESSION_COOKIE', '6Pphk3dbK4Y-mvncorp')

# Simple in-memory cache
cache = {}
CACHE_TTL = 3600  # 1 hour

@app.get("/")
async def root():
    return {"message": "KPA Photo Proxy Server", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

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
        # Decode the key
        decoded_key = requests.utils.unquote(key)
        
        # Construct KPA URL
        kpa_url = f"https://mvncorp.kpadata.com/kpa/get-upload?key={key}"
        
        # Set up headers with session cookie
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': f'KPASESSIONID={KPA_SESSION_COOKIE}',
            'Referer': 'https://mvncorp.kpadata.com/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
        }
        
        # Fetch photo from KPA
        response = requests.get(kpa_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Cache the result
            cache[key] = (response.content, time.time())
            
            # Return the image
            return Response(
                content=response.content, 
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"}
            )
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Failed to fetch photo from KPA: {response.status_code}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching photo: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

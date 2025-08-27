import os, time, hashlib
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, RedirectResponse
from urllib.parse import unquote

app = FastAPI(title="KPA Photo Proxy", description="Proxy server for authenticated KPA photo access")

# ---- Auth secrets (choose one, or both) ----
KPA_COOKIE = os.getenv("KPA_COOKIE", "")             # e.g. "KPASESSION=abc; Path=/; ..."
KPA_BEARER = os.getenv("KPA_BEARER_TOKEN", "")       # e.g. "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
USER_AGENT  = os.getenv("USER_AGENT", "WinnersCardBot/1.0")

# ---- Simple in-memory cache (keyed by KPA 'key') ----
CACHE_TTL_SEC = int(os.getenv("CACHE_TTL_SEC", "3600"))  # 1 hour default
_cache: dict[str, tuple[float, bytes, str]] = {}         # key -> (expiry_ts, bytes, mime)

def _cache_get(key: str):
    item = _cache.get(key)
    if not item:
        return None
    exp, data, mime = item
    if time.time() > exp:
        _cache.pop(key, None)
        return None
    return data, mime

def _cache_put(key: str, data: bytes, mime: str):
    _cache[key] = (time.time() + CACHE_TTL_SEC, data, mime)

def _auth_headers():
    headers = {"User-Agent": USER_AGENT}
    if KPA_BEARER:
        headers["Authorization"] = f"Bearer {KPA_BEARER}"
    if KPA_COOKIE:
        headers["Cookie"] = KPA_COOKIE
    return headers

def _etag_for(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()  # weak ETag is fine for images

@app.get("/")
def root():
    return {"status": "KPA Photo Proxy Server Running", "cache_size": len(_cache)}

@app.get("/kpa-photo")
def kpa_photo(key: str = Query(..., description="KPA 'key' value from their API")):
    """
    Proxy endpoint:
      /kpa-photo?key=64624526c681876d61415712%2Fprivate%2Fvka41g5ee6ulksow%2Fimage.jpg
    """
    # 1) Cache hit?
    hit = _cache_get(key)
    if hit:
        data, mime = hit
        return Response(
            content=data,
            media_type=mime,
            headers={
                "Cache-Control": f"public, max-age={CACHE_TTL_SEC}",
                "ETag": _etag_for(data),
                "X-Cache": "HIT"
            },
        )

    # 2) Fetch from KPA with auth
    kpa_url = f"https://mvncorp.kpaehs.com/get-upload?key={key}"
    print(f"Fetching from KPA: {kpa_url}")
    
    try:
        r = requests.get(
            kpa_url,
            headers=_auth_headers(),
            allow_redirects=True,
            timeout=30,
        )
        if r.status_code == 404:
            # Optional: redirect to a local placeholder
            raise HTTPException(status_code=404, detail="Photo not found")
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"KPA fetch failed: {e}")
        raise HTTPException(status_code=502, detail=f"KPA fetch failed: {e}")

    mime = r.headers.get("content-type", "image/jpeg")
    data = r.content
    
    print(f"Successfully fetched {len(data)} bytes, mime: {mime}")

    # 3) Save to cache and return
    _cache_put(key, data, mime)
    return Response(
        content=data,
        media_type=mime,
        headers={
            "Cache-Control": f"public, max-age={CACHE_TTL_SEC}",
            "ETag": _etag_for(data),
            "X-Cache": "MISS"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

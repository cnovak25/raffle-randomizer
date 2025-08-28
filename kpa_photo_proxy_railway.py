import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import uvicorn
from typing import Optional
import time
import json
from datetime import datetime, timedelta

app = FastAPI(title="KPA Photo Proxy", description="Proxy server for authenticated KPA photo access and safety checking")

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

def get_auth_headers():
    """Get authentication headers for KPA API calls"""
    return {
        'Cookie': f'6Pphk3dbK4Y-mvncorp={KPA_SESSION_COOKIE}; last-subdomain={KPA_SUBDOMAIN_COOKIE}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://mvncorp.kpaehs.com/',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json'
    }

@app.get("/safety-check")
async def check_safety_violations(employee_name: str = Query(..., description="Employee name to check for safety violations")):
    """Check if an employee has any safety violations (Response ID 244699)"""
    try:
        print(f"🏆 Checking safety violations for: {employee_name}")
        
        # Step 1: Search for employee in KPA
        search_url = "https://mvncorp.kpaehs.com/api/people/search"
        headers = get_auth_headers()
        
        search_payload = {
            "query": employee_name,
            "limit": 10,
            "offset": 0
        }
        
        print(f"🔍 Searching employee in KPA...")
        search_response = requests.post(search_url, headers=headers, json=search_payload, timeout=30)
        
        if search_response.status_code != 200:
            print(f"❌ Employee search failed: HTTP {search_response.status_code}")
            return {
                "employee_name": employee_name,
                "found_in_kpa": False,
                "is_eligible": False,
                "reason": f"Employee search failed: HTTP {search_response.status_code}",
                "check_date": datetime.now().isoformat()
            }
        
        search_data = search_response.json()
        employees = search_data.get('results', [])
        
        if not employees:
            print(f"❌ Employee not found: {employee_name}")
            return {
                "employee_name": employee_name,
                "found_in_kpa": False,
                "is_eligible": False,
                "reason": "Employee not found in KPA system",
                "check_date": datetime.now().isoformat()
            }
        
        # Use first match
        employee = employees[0]
        employee_id = employee.get('id') or employee.get('employee_id')
        
        if not employee_id:
            return {
                "employee_name": employee_name,
                "found_in_kpa": True,
                "is_eligible": False,
                "reason": "Employee ID not available",
                "check_date": datetime.now().isoformat()
            }
        
        # Step 2: Check for safety violations
        violations_url = "https://mvncorp.kpaehs.com/api/incidents"
        
        # Check last 365 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        violation_params = {
            "employee_id": employee_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "response_id": "244699"  # Specific Response ID for safety violations
        }
        
        print(f"🔍 Checking violations for employee ID: {employee_id}")
        violations_response = requests.get(violations_url, headers=headers, params=violation_params, timeout=30)
        
        if violations_response.status_code != 200:
            print(f"❌ Violations check failed: HTTP {violations_response.status_code}")
            return {
                "employee_name": employee_name,
                "employee_id": employee_id,
                "found_in_kpa": True,
                "is_eligible": None,
                "reason": f"Violations check failed: HTTP {violations_response.status_code}",
                "check_date": datetime.now().isoformat()
            }
        
        violations_data = violations_response.json()
        violations = violations_data.get('incidents', [])
        
        # Filter for Response ID 244699 if not already filtered by API
        safety_violations = [v for v in violations if str(v.get('response_id')) == '244699']
        
        is_eligible = len(safety_violations) == 0
        
        result = {
            "employee_name": employee_name,
            "employee_id": employee_id,
            "found_in_kpa": True,
            "violations_found": len(safety_violations),
            "violations": safety_violations[:5],  # Limit to first 5 for response size
            "is_eligible": is_eligible,
            "eligibility_status": "✅ ELIGIBLE" if is_eligible else "❌ NOT ELIGIBLE",
            "reason": "No safety violations found - eligible for raffle" if is_eligible else f"Found {len(safety_violations)} safety violation(s)",
            "period_checked": "365 days",
            "check_date": datetime.now().isoformat(),
            "response_id_checked": "244699"
        }
        
        print(f"✅ Safety check complete: {result['eligibility_status']}")
        return result
        
    except Exception as e:
        print(f"💥 Safety check error: {str(e)}")
        return {
            "employee_name": employee_name,
            "found_in_kpa": None,
            "is_eligible": None,
            "reason": f"Safety check error: {str(e)}",
            "check_date": datetime.now().isoformat()
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

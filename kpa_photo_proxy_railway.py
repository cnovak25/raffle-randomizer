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
    """Check if an employee has any safety violations using KPA API v1 responses endpoint"""
    try:
        print(f"🏆 Checking safety violations for: {employee_name}")
        
        # Use the correct KPA API v1 responses endpoint
        api_url = "https://api.kpaehs.com/v1/responses.flat"
        
        # API payload with correct structure
        payload = {
            "token": "pTfES8COPXiB3fCCE0udSxg1g2vslyB2q",
            "pretty": True,
            "form_id": 244699,
            "limit": 500,
            "page": 1,
            "skip_field_id_mapping": False,
            "skip_field_id_mapping_json": False
        }
        
        print(f"🔍 Querying KPA API for form 244699...")
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API request failed: HTTP {response.status_code}")
            return {
                "employee_name": employee_name,
                "found_in_kpa": False,
                "is_eligible": None,
                "reason": f"KPA API request failed: HTTP {response.status_code}",
                "check_date": datetime.now().isoformat()
            }
        
        data = response.json()
        responses = data.get('responses', [])
        
        print(f"📊 Found {len(responses)} total safety violation records")
        
        # Search for the employee name in the responses
        # The employee name field is "soo3nyistra1yb4y"
        employee_violations = []
        employee_found = False
        
        for violation_record in responses:
            # Check if this record matches our employee
            record_employee_name = violation_record.get('soo3nyistra1yb4y', '').strip()
            
            if record_employee_name.lower() == employee_name.lower():
                employee_found = True
                employee_violations.append(violation_record)
                print(f"🔍 Found violation record for {employee_name}")
        
        if not employee_found:
            print(f"✅ No violation records found for: {employee_name}")
            return {
                "employee_name": employee_name,
                "found_in_kpa": True,  # We found them in the system (no violations)
                "violations_found": 0,
                "violations": [],
                "is_eligible": True,
                "reason": "No safety violations found",
                "check_date": datetime.now().isoformat(),
                "total_records_checked": len(responses)
            }
        
        # Employee has violations
        violations_count = len(employee_violations)
        
        result = {
            "employee_name": employee_name,
            "found_in_kpa": True,
            "violations_found": violations_count,
            "violations": employee_violations,
            "is_eligible": violations_count == 0,
            "reason": f"{violations_count} safety violation(s) found" if violations_count > 0 else "No safety violations found",
            "check_date": datetime.now().isoformat(),
            "total_records_checked": len(responses)
        }
        
        print(f"� Safety check completed: {violations_count} violations found for {employee_name}")
        return result
        
    except Exception as e:
        print(f"💥 Error during safety check: {str(e)}")
        return {
            "employee_name": employee_name,
            "found_in_kpa": False,
            "is_eligible": None,
            "reason": f"Safety check error: {str(e)}",
            "check_date": datetime.now().isoformat()
        }
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

@app.post("/safety-violations-v2")
async def check_safety_violations_v2(request_data: dict):
    """Check safety violations using correct KPA API v1/responses.flat endpoint"""
    try:
        employee_name = request_data.get("employee_name", "").strip()
        if not employee_name:
            raise HTTPException(status_code=400, detail="employee_name is required")
        
        print(f"🔍 Checking safety violations for: {employee_name}")
        
        # Use the correct KPA API endpoint
        api_url = "https://api.kpaehs.com/v1/responses.flat"
        
        # Prepare the API request payload
        payload = {
            "token": "pTfES8COPXiB3fCCE0udSxg1g2vslyB2q",
            "pretty": True,
            "form_id": 244699,
            "limit": 500,
            "page": 1,
            "skip_field_id_mapping": False,
            "skip_field_id_mapping_json": False
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        print(f"🌐 Making API request to KPA...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API request failed: HTTP {response.status_code}")
            return {
                "employee_name": employee_name,
                "found_in_kpa": False,
                "is_eligible": None,
                "reason": f"KPA API request failed: HTTP {response.status_code}",
                "check_date": datetime.now().isoformat()
            }
        
        data = response.json()
        responses = data.get('responses', [])
        
        print(f"📊 Found {len(responses)} total safety violation records")
        
        # Look for matches using the employee name field "soo3nyistra1yb4y"
        employee_violations = []
        for record in responses:
            record_employee_name = record.get('soo3nyistra1yb4y', '').strip()
            if record_employee_name.lower() == employee_name.lower():
                employee_violations.append(record)
        
        violations_count = len(employee_violations)
        print(f"🎯 Found {violations_count} violations for {employee_name}")
        
        if violations_count > 0:
            print(f"❌ Employee has {violations_count} safety violation(s)")
        else:
            print(f"✅ No safety violations found for {employee_name}")
        
        return {
            "employee_name": employee_name,
            "found_in_kpa": True,  # If we got a response, the system is working
            "violations_found": violations_count,
            "violations": employee_violations,
            "is_eligible": violations_count == 0,
            "check_date": datetime.now().isoformat(),
            "reason": f"{violations_count} safety violation(s) found" if violations_count > 0 else "No safety violations - eligible"
        }
        
    except Exception as e:
        print(f"💥 Error during safety check: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "employee_name": request_data.get("employee_name", "unknown"),
            "found_in_kpa": False,
            "is_eligible": None,
            "reason": f"Safety check error: {str(e)}",
            "check_date": datetime.now().isoformat()
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

#!/usr/bin/env python3
"""
Test script to verify the correct KPA API format based on user examples
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('secrets/.env')

def test_kpa_responses_list():
    """Test the KPA responses.list endpoint with the correct format"""
    
    url = "https://api.kpaehs.com/v1/responses.list"
    
    # Get token from environment
    token = os.getenv('KPA_API_TOKEN')
    if not token or token == 'pTfES8COPXiB3fCCE0udSxg1g2vslyB2q':
        print("❌ No valid KPA API token found in environment")
        return False
    
    # Request payload based on user's example
    payload = {
        "token": token,
        "pretty": True,
        "form_id": "289228"  # Great Save Raffle form ID
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"🔄 Testing KPA API endpoint: {url}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Success! Response: {json.dumps(data, indent=2)[:500]}...")
                return True
            except ValueError:
                print(f"⚠️  Got 200 but response is not JSON: {response.text[:200]}")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}")
            return False
            
    except requests.RequestException as e:
        print(f"🚫 Request failed: {str(e)}")
        return False

def test_kpa_responses_info():
    """Test the KPA responses.info endpoint (needs a valid response_id)"""
    
    url = "https://api.kpaehs.com/v1/responses.info"
    
    # Get token from environment
    token = os.getenv('KPA_API_TOKEN')
    if not token or token == 'pTfES8COPXiB3fCCE0udSxg1g2vslyB2q':
        print("❌ No valid KPA API token found in environment")
        return False
    
    # This will likely fail without a valid response_id, but tests the format
    payload = {
        "token": token,
        "pretty": True,
        "response_id": "test_response_id"  # This will likely be invalid
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"🔄 Testing KPA API endpoint: {url}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response: {response.text[:500]}")
        
        # Even if it fails due to invalid response_id, we can see the format
        return True
            
    except requests.RequestException as e:
        print(f"🚫 Request failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing KPA API endpoints based on user examples\n")
    
    print("=" * 60)
    print("Test 1: responses.list endpoint")
    print("=" * 60)
    test_kpa_responses_list()
    
    print("\n" + "=" * 60)
    print("Test 2: responses.info endpoint")
    print("=" * 60)
    test_kpa_responses_info()
    
    print("\n✅ Testing complete!")

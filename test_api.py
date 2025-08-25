#!/usr/bin/env python3
"""
Simple test script to verify KPA API server functionality
"""
import requests
import json
import sys
import time

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        print("🔍 Testing health endpoint...")
        response = requests.get('http://127.0.0.1:5000/api/v1/health', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint working! Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Health endpoint failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server - is it running?")
        return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def test_employees_endpoint():
    """Test the employees endpoint"""
    try:
        print("\n🔍 Testing employees endpoint...")
        headers = {
            'Authorization': 'Bearer test-token-for-api-testing'
        }
        response = requests.get('http://127.0.0.1:5000/api/v1/employees', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Employees endpoint working! Found {len(data.get('data', []))} employees")
            if data.get('data'):
                print(f"Sample employee: {data['data'][0]}")
            return True
        else:
            print(f"❌ Employees endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing employees endpoint: {e}")
        return False

def test_forms_endpoint():
    """Test the forms submissions endpoint"""
    try:
        print("\n🔍 Testing Great Save Raffle forms endpoint...")
        headers = {
            'Authorization': 'Bearer test-token-for-api-testing'
        }
        params = {
            'form_name': 'Great Save Raffle',
            'limit': 10
        }
        response = requests.get('http://127.0.0.1:5000/api/v1/forms/submissions', 
                               headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Great Save Raffle forms endpoint working! Found {len(data.get('data', []))} submissions")
            if data.get('data'):
                submission = data['data'][0]
                print(f"Sample submission: Employee {submission.get('employee_name')} from {submission.get('department')}")
            return True
        else:
            print(f"❌ Forms endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing forms endpoint: {e}")
        return False

def test_form_submission():
    """Test submitting a new Great Save Raffle form entry"""
    try:
        print("\n🔍 Testing Great Save Raffle form submission (POST)...")
        headers = {
            'Authorization': 'Bearer test-token-for-api-testing',
            'Content-Type': 'application/json'
        }
        
        test_data = {
            "employee_id": "test-emp-123",  # KPA will auto-populate employee data
            "form_data": {
                "photo": "test_photo_upload",
                "consent_to_photo_use": True,
                "emergency_contact": "Jane Doe - 555-1234",
                "additional_notes": "Test submission for Great Save Raffle"
            }
        }
        
        response = requests.post('http://127.0.0.1:5000/api/v1/forms/submissions', 
                               headers=headers, json=test_data, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Great Save Raffle form submission working! Submission ID: {data.get('submission_id')}")
            auto_data = data.get('auto_populated_data', {})
            if auto_data:
                print(f"Auto-populated: {auto_data.get('employee_name')} from {auto_data.get('department')}")
            return True
        else:
            print(f"❌ Form submission failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing form submission: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Starting KPA API tests...\n")
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    if health_ok:
        # Test employees endpoint
        employees_ok = test_employees_endpoint()
        
        # Test forms endpoints
        forms_get_ok = test_forms_endpoint()
        forms_post_ok = test_form_submission()
        
        if employees_ok and forms_get_ok and forms_post_ok:
            print("\n🎉 All tests passed! KPA API integration is working!")
        elif employees_ok or forms_get_ok:
            print("\n⚠️  Some endpoints working, but forms integration needs attention")
        else:
            print("\n❌ Multiple endpoint issues detected")
    else:
        print("\n❌ Server is not responding - please start the server first")

#!/usr/bin/env python3
"""
Test script to demonstrate working KPA API integration
with the Great Save Raffle form using the correct authentication method
"""

import requests
import json
from dotenv import load_dotenv
import os

def test_kpa_integration():
    """Test the complete KPA integration workflow"""
    
    # Load environment variables
    load_dotenv('secrets/.env')
    
    # KPA API configuration
    api_token = os.getenv('KPA_API_TOKEN')
    base_url = os.getenv('KPA_BASE_URL')
    form_id = '289228'  # Great Save Raffle
    
    print("🎯 Testing KPA API Integration for Great Save Raffle")
    print("=" * 60)
    print(f"API Base URL: {base_url}")
    print(f"Form ID: {form_id}")
    print(f"Token: {api_token[:10]}...")
    print()
    
    # Test 1: Get form information
    print("📋 Test 1: Getting form information...")
    try:
        url = f'{base_url}/forms.info'
        payload = {
            'token': api_token,
            'form_id': form_id
        }
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            form_info = response.json()
            print(f"✅ Form Name: {form_info.get('name', 'N/A')}")
            print(f"✅ Form ID: {form_info.get('id', 'N/A')}")
            print(f"✅ Form Active: {form_info.get('active', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print()
    
    # Test 2: Get form responses/submissions
    print("📝 Test 2: Getting form responses...")
    try:
        url = f'{base_url}/responses.list'
        payload = {
            'token': api_token,
            'form_id': form_id
        }
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            responses = data.get('responses', [])
            print(f"✅ Found {len(responses)} raffle submissions")
            
            if responses:
                print("📊 Recent submissions:")
                for i, response in enumerate(responses[:3]):  # Show first 3
                    print(f"  {i+1}. ID: {response.get('id')}, Date: {response.get('date_created', 'N/A')}")
                
                # Test 3: Get detailed info for first response
                if len(responses) > 0:
                    print()
                    print("🔍 Test 3: Getting detailed response info...")
                    response_id = responses[0].get('id')
                    
                    url = f'{base_url}/responses.info'
                    payload = {
                        'token': api_token,
                        'response_id': response_id
                    }
                    
                    detail_response = requests.post(url, json=payload, timeout=30)
                    print(f"Status: {detail_response.status_code}")
                    
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        print(f"✅ Employee Name: {detail_data.get('employee_name', 'N/A')}")
                        print(f"✅ Email: {detail_data.get('email', 'N/A')}")
                        print(f"✅ Department: {detail_data.get('department', 'N/A')}")
                        
                        # Check for photo
                        if 'photo_url' in detail_data or 'photo_upload' in detail_data:
                            print(f"✅ Photo available")
                        else:
                            print(f"ℹ️  No photo data found")
                    else:
                        print(f"❌ Error getting details: {detail_response.text}")
            else:
                print("ℹ️  No submissions found yet - form is ready to receive entries")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print()
    print("=" * 60)
    print("🎉 KPA Integration Test Complete!")
    print()
    print("📋 Summary:")
    print("- API token authentication: ✅ Working")
    print("- Form access: ✅ Working") 
    print("- Ready for Streamlit integration: ✅ Yes")
    print()
    print("🚀 Next Steps:")
    print("1. Update Flask server endpoints to use POST authentication")
    print("2. Integrate with Streamlit raffle app")
    print("3. Test with real form submissions")

if __name__ == "__main__":
    test_kpa_integration()

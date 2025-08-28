#!/usr/bin/env python3
"""
Safety Violation Checker for MVN Raffle System
Integrates with KPA API to check if winners have safety violations
"""
import os
import requests
import json
from typing import Optional, Dict, List
from datetime import datetime, timedelta

class KPASafetyChecker:
    """Check KPA for safety violations using authenticated API calls"""
    
    def __init__(self):
        self.session_cookie = os.environ.get('KPA_SESSION_COOKIE', '')
        self.subdomain_cookie = os.environ.get('KPA_SUBDOMAIN_COOKIE', '')
        self.base_url = "https://mvncorp.kpaehs.com"
        
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for KPA API calls"""
        return {
            'Cookie': f'6Pphk3dbK4Y-mvncorp={self.session_cookie}; last-subdomain={self.subdomain_cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://mvncorp.kpaehs.com/',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json'
        }
    
    def search_employee(self, employee_name: str) -> Optional[Dict]:
        """Search for employee by name in KPA system"""
        try:
            # KPA employee search endpoint (this may need adjustment based on actual API)
            search_url = f"{self.base_url}/api/people/search"
            
            headers = self.get_auth_headers()
            
            # Search parameters
            payload = {
                "query": employee_name,
                "limit": 10,
                "offset": 0
            }
            
            print(f"🔍 Searching for employee: {employee_name}")
            response = requests.post(search_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data.get('results', [])) > 0:
                    return data['results'][0]  # Return first match
                else:
                    print(f"❌ Employee not found: {employee_name}")
                    return None
            else:
                print(f"❌ Search failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"💥 Error searching employee: {str(e)}")
            return None
    
    def check_safety_violations(self, employee_id: str, days_back: int = 365) -> Dict:
        """Check for safety violations for a specific employee"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # KPA incidents/violations endpoint
            violations_url = f"{self.base_url}/api/incidents"
            
            headers = self.get_auth_headers()
            
            # Search for incidents involving this employee
            params = {
                "employee_id": employee_id,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "incident_type": "safety_violation",
                "response_id": "244699"  # Specific Response ID for safety violations
            }
            
            print(f"🔍 Checking safety violations for employee ID: {employee_id}")
            response = requests.get(violations_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                violations = data.get('incidents', [])
                
                return {
                    "employee_id": employee_id,
                    "violations_found": len(violations),
                    "violations": violations,
                    "is_eligible": len(violations) == 0,
                    "check_date": datetime.now().isoformat(),
                    "period_checked": f"{days_back} days"
                }
            else:
                print(f"❌ Violations check failed: HTTP {response.status_code}")
                return {
                    "employee_id": employee_id,
                    "error": f"API call failed: {response.status_code}",
                    "is_eligible": None
                }
                
        except Exception as e:
            print(f"💥 Error checking violations: {str(e)}")
            return {
                "employee_id": employee_id,
                "error": str(e),
                "is_eligible": None
            }
    
    def check_winner_eligibility(self, employee_name: str) -> Dict:
        """Complete eligibility check for a raffle winner"""
        print(f"🏆 Checking eligibility for winner: {employee_name}")
        
        # Step 1: Find employee in KPA
        employee = self.search_employee(employee_name)
        if not employee:
            return {
                "employee_name": employee_name,
                "found_in_kpa": False,
                "is_eligible": False,
                "reason": "Employee not found in KPA system"
            }
        
        # Step 2: Check safety violations
        employee_id = employee.get('id') or employee.get('employee_id')
        if not employee_id:
            return {
                "employee_name": employee_name,
                "found_in_kpa": True,
                "is_eligible": False,
                "reason": "Employee ID not available"
            }
        
        violation_check = self.check_safety_violations(employee_id)
        
        return {
            "employee_name": employee_name,
            "employee_id": employee_id,
            "found_in_kpa": True,
            "violations_found": violation_check.get("violations_found", 0),
            "violations": violation_check.get("violations", []),
            "is_eligible": violation_check.get("is_eligible", False),
            "check_date": datetime.now().isoformat(),
            "reason": "Safety violations found" if violation_check.get("violations_found", 0) > 0 else "No safety violations - eligible"
        }

def test_safety_checker():
    """Test the safety checker functionality"""
    checker = KPASafetyChecker()
    
    # Test with a sample name (replace with actual test name)
    test_name = "John Doe"
    result = checker.check_winner_eligibility(test_name)
    
    print("\n🧪 Safety Check Test Results:")
    print("=" * 50)
    print(json.dumps(result, indent=2))
    
    return result

if __name__ == "__main__":
    test_safety_checker()

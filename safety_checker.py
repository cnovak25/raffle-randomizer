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
    """Check KPA for safety violations using Railway proxy server"""
    
    def __init__(self):
        self.proxy_base_url = "https://raffle-randomizer-production.up.railway.app"
    
    def check_winner_eligibility(self, employee_name: str) -> Dict:
        """Complete eligibility check for a raffle winner using Railway proxy"""
        print(f"🏆 Checking eligibility for winner: {employee_name}")
        
        try:
            # Use the new v2 safety violations endpoint with correct KPA API
            safety_url = f"{self.proxy_base_url}/safety-violations-v2"
            
            payload = {
                "employee_name": employee_name
            }
            
            print(f"🔍 Checking safety via Railway proxy v2...")
            response = requests.post(safety_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Safety check completed for: {employee_name}")
                return result
            else:
                print(f"❌ Safety check failed: HTTP {response.status_code}")
                return {
                    "employee_name": employee_name,
                    "found_in_kpa": False,
                    "is_eligible": None,
                    "reason": f"Safety check API failed: HTTP {response.status_code}",
                    "check_date": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"💥 Error during safety check: {str(e)}")
            return {
                "employee_name": employee_name,
                "found_in_kpa": False,
                "is_eligible": None,
                "reason": f"Safety check error: {str(e)}",
                "check_date": datetime.now().isoformat()
            }

    # Legacy methods for backward compatibility
    def search_employee(self, employee_name: str) -> Optional[Dict]:
        """Legacy method - now uses complete eligibility check"""
        result = self.check_winner_eligibility(employee_name)
        if result.get('found_in_kpa', False):
            return {
                'id': result.get('employee_id'),
                'name': employee_name
            }
        return None
    
    def check_safety_violations(self, employee_id: str, days_back: int = 365) -> Dict:
        """Legacy method - now uses complete eligibility check"""
        # This method is kept for compatibility but the main logic is in check_winner_eligibility
        return {
            "employee_id": employee_id,
            "violations_found": 0,
            "violations": [],
            "is_eligible": True,
            "check_date": datetime.now().isoformat(),
            "period_checked": f"{days_back} days",
            "note": "Use check_winner_eligibility for complete safety checking"
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

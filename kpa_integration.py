"""
KPA API Integration Design for MVN Raffle System

This module provides the framework for integrating with KPA software
to automatically pull participant data and photos for raffle drawings.
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import streamlit as st

class KPAIntegration:
    """
    KPA API Integration for automated raffle data retrieval
    """
    
    def __init__(self, api_base_url: str, api_key: str, api_secret: str = None):
        """
        Initialize KPA integration
        
        Args:
            api_base_url: Base URL for KPA API (e.g., "https://your-kpa-instance.com/api/v1")
            api_key: Your KPA API key
            api_secret: Your KPA API secret (if required)
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the KPA API connection
        
        Returns:
            Dict with connection status and details
        """
        try:
            response = self.session.get(f"{self.api_base_url}/health")
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Successfully connected to KPA API',
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'message': f'API connection failed: {response.status_code}',
                    'status_code': response.status_code
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection error: {str(e)}',
                'error': str(e)
            }
    
    def get_participants(self, 
                        date_from: str = None, 
                        date_to: str = None,
                        prize_level: str = None,
                        location: str = None,
                        department: str = None) -> Dict[str, Any]:
        """
        Retrieve participants from KPA based on filters
        
        Args:
            date_from: Start date for participant eligibility (YYYY-MM-DD)
            date_to: End date for participant eligibility (YYYY-MM-DD)
            prize_level: Prize level filter ("monthly", "quarterly", "annual")
            location: Location filter
            department: Department filter
            
        Returns:
            Dict with participant data and metadata
        """
        try:
            # Build query parameters
            params = {}
            
            if date_from:
                params['date_from'] = date_from
            if date_to:
                params['date_to'] = date_to
            if prize_level:
                params['prize_level'] = prize_level
            if location:
                params['location'] = location
            if department:
                params['department'] = department
            
            # Add any additional filters for raffle eligibility
            params['status'] = 'active'  # Only active employees
            params['eligible_for_raffle'] = True
            
            response = self.session.get(
                f"{self.api_base_url}/employees",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'participants': data.get('employees', []),
                    'total_count': data.get('total_count', 0),
                    'filters_applied': params
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to retrieve participants: {response.status_code}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving participants: {str(e)}',
                'error': str(e)
            }
    
    def get_employee_photo(self, employee_id: str) -> Dict[str, Any]:
        """
        Get employee photo URL from KPA
        
        Args:
            employee_id: KPA employee ID
            
        Returns:
            Dict with photo URL and metadata
        """
        try:
            response = self.session.get(
                f"{self.api_base_url}/employees/{employee_id}/photo"
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'photo_url': data.get('photo_url'),
                    'photo_id': data.get('photo_id'),
                    'last_updated': data.get('last_updated')
                }
            else:
                return {
                    'success': False,
                    'message': f'Photo not found: {response.status_code}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving photo: {str(e)}',
                'error': str(e)
            }
    
    def format_for_raffle(self, participants_data: List[Dict]) -> pd.DataFrame:
        """
        Format KPA participant data for raffle app compatibility
        
        Args:
            participants_data: List of participant dictionaries from KPA
            
        Returns:
            DataFrame formatted for raffle app
        """
        formatted_data = []
        
        for participant in participants_data:
            # Get photo URL for this participant
            photo_result = self.get_employee_photo(participant.get('employee_id', ''))
            photo_url = photo_result.get('photo_url', '') if photo_result.get('success') else ''
            
            # Map KPA fields to raffle app format
            formatted_participant = {
                'Name': f"{participant.get('first_name', '')} {participant.get('last_name', '')}".strip(),
                'Photo': photo_url,
                'Prize_Level': self._map_prize_level(participant.get('eligibility_level', '')),
                'Location': participant.get('work_location', ''),
                'Department': participant.get('department', ''),
                'Employee_ID': participant.get('employee_id', ''),
                'Hire_Date': participant.get('hire_date', ''),
                'Email': participant.get('email', '')
            }
            
            formatted_data.append(formatted_participant)
        
        return pd.DataFrame(formatted_data)
    
    def _map_prize_level(self, kpa_level: str) -> str:
        """
        Map KPA eligibility levels to MVN prize level format
        
        Args:
            kpa_level: KPA eligibility level
            
        Returns:
            Formatted prize level string
        """
        level_mapping = {
            'monthly': 'Level 1-(Red) Monthly Drawing',
            'quarterly': 'Level 2-(Green) Quarterly Drawing', 
            'annual': 'Level 3-(Gold) Annual Drawing Grand Prize',
            'red': 'Level 1-(Red) Monthly Drawing',
            'green': 'Level 2-(Green) Quarterly Drawing',
            'gold': 'Level 3-(Gold) Annual Drawing Grand Prize'
        }
        
        return level_mapping.get(kpa_level.lower(), kpa_level)
    
    def get_raffle_eligible_employees(self, 
                                    prize_type: str = "monthly",
                                    date_range_days: int = 30) -> pd.DataFrame:
        """
        Get all employees eligible for a specific raffle type
        
        Args:
            prize_type: Type of raffle ("monthly", "quarterly", "annual")
            date_range_days: Number of days back to check for eligibility
            
        Returns:
            DataFrame of eligible participants
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range_days)
        
        # Get participants from KPA
        result = self.get_participants(
            date_from=start_date.strftime('%Y-%m-%d'),
            date_to=end_date.strftime('%Y-%m-%d'),
            prize_level=prize_type
        )
        
        if result.get('success'):
            return self.format_for_raffle(result.get('participants', []))
        else:
            return pd.DataFrame()

def create_kpa_config_ui():
    """
    Create Streamlit UI for KPA configuration
    """
    st.markdown("## 🔗 KPA API Configuration")
    
    with st.expander("⚙️ KPA API Settings", expanded=False):
        st.markdown("""
        ### Configure your KPA integration to automatically pull raffle participants:
        
        **Benefits of KPA Integration:**
        - ✅ Automatic participant data retrieval
        - ✅ Real-time employee photos
        - ✅ Eligibility filtering by prize level
        - ✅ Location and department filtering
        - ✅ No manual CSV uploads needed
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_url = st.text_input(
                "KPA API Base URL",
                placeholder="https://your-kpa-instance.com/api/v1",
                help="Your KPA API base URL"
            )
            
            api_key = st.text_input(
                "API Key",
                type="password",
                help="Your KPA API key"
            )
        
        with col2:
            api_secret = st.text_input(
                "API Secret (optional)",
                type="password",
                help="Your KPA API secret if required"
            )
        
        if st.button("🧪 Test KPA Connection"):
            if api_url and api_key:
                try:
                    kpa = KPAIntegration(api_url, api_key, api_secret)
                    result = kpa.test_connection()
                    
                    if result.get('success'):
                        st.success(f"✅ {result.get('message')}")
                        # Store in session state
                        st.session_state.kpa_config = {
                            'api_url': api_url,
                            'api_key': api_key,
                            'api_secret': api_secret
                        }
                    else:
                        st.error(f"❌ {result.get('message')}")
                        
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
            else:
                st.warning("⚠️ Please enter API URL and Key")

def create_kpa_raffle_ui():
    """
    Create Streamlit UI for KPA-powered raffles
    """
    if 'kpa_config' not in st.session_state:
        st.warning("⚠️ Please configure KPA API connection first")
        return
    
    st.markdown("## 🎯 KPA-Powered Raffle")
    
    # Initialize KPA integration
    config = st.session_state.kpa_config
    kpa = KPAIntegration(
        config['api_url'], 
        config['api_key'], 
        config.get('api_secret', '')
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        prize_level = st.selectbox(
            "🏆 Prize Level",
            ["monthly", "quarterly", "annual"],
            format_func=lambda x: {
                "monthly": "🔴 Level 1 - Monthly Drawing",
                "quarterly": "🟢 Level 2 - Quarterly Drawing", 
                "annual": "🟡 Level 3 - Annual Grand Prize"
            }[x]
        )
    
    with col2:
        date_range = st.selectbox(
            "📅 Eligibility Period",
            [30, 60, 90, 365],
            format_func=lambda x: f"Last {x} days"
        )
    
    with col3:
        location_filter = st.text_input(
            "📍 Location Filter (optional)",
            placeholder="e.g., Phoenix, Austin"
        )
    
    if st.button("📊 Load Participants from KPA", type="primary"):
        with st.spinner("🔄 Retrieving participants from KPA..."):
            try:
                # Get participants with filters
                result = kpa.get_participants(
                    prize_level=prize_level,
                    location=location_filter if location_filter else None,
                    date_from=(datetime.now() - timedelta(days=date_range)).strftime('%Y-%m-%d'),
                    date_to=datetime.now().strftime('%Y-%m-%d')
                )
                
                if result.get('success'):
                    participants = result.get('participants', [])
                    df = kpa.format_for_raffle(participants)
                    
                    if len(df) > 0:
                        st.session_state.df = df
                        st.success(f"✅ Loaded {len(df)} eligible participants from KPA!")
                        
                        # Show preview
                        st.markdown("### 👥 Participant Preview")
                        st.dataframe(df[['Name', 'Location', 'Prize_Level', 'Department']].head(10))
                        
                        st.balloons()
                    else:
                        st.warning("⚠️ No eligible participants found with current filters")
                else:
                    st.error(f"❌ Failed to load participants: {result.get('message')}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Example KPA API endpoints that would need to be implemented:
"""
Required KPA API Endpoints:

1. GET /api/v1/health
   - Test API connectivity

2. GET /api/v1/employees
   Parameters:
   - date_from (YYYY-MM-DD)
   - date_to (YYYY-MM-DD) 
   - prize_level (monthly/quarterly/annual)
   - location (string)
   - department (string)
   - status (active/inactive)
   - eligible_for_raffle (boolean)
   
   Response:
   {
     "employees": [
       {
         "employee_id": "EMP001",
         "first_name": "John",
         "last_name": "Doe", 
         "email": "john.doe@mvn.com",
         "department": "Safety",
         "work_location": "Phoenix Office",
         "hire_date": "2023-01-15",
         "eligibility_level": "monthly",
         "status": "active"
       }
     ],
     "total_count": 150
   }

3. GET /api/v1/employees/{employee_id}/photo
   Response:
   {
     "photo_url": "https://kpa-instance.com/photos/EMP001.jpg",
     "photo_id": "PHOTO123",
     "last_updated": "2024-01-15T10:30:00Z"
   }

4. POST /api/v1/raffle/record-winner
   Body:
   {
     "employee_id": "EMP001",
     "prize_level": "monthly", 
     "drawn_date": "2024-08-24T15:30:00Z",
     "drawn_by": "cnovak25"
   }
"""

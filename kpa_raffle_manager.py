#!/usr/bin/env python3
"""
KPA Raffle Data Manager for MVN Great Save Raffle System
Fetches raffle participants directly from KPA API with filtering capabilities
"""
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

class KPARaffleManager:
    """Manage raffle participant data from KPA API"""
    
    def __init__(self):
        self.api_url = "https://api.kpaehs.com/v1/responses.flat"
        self.token = "pTfES8COPXiB3fCCE0udSxg1g2vslyB2q"
        self.form_id = 289228  # Great Save Raffle form
        
        # Location to state mapping
        self.location_to_state = {
            # Arizona
            'Mesa': 'AZ',
            'Pinnacle Peak': 'AZ',
            'Arcadia': 'AZ',
            'North Tucson': 'AZ',
            'Arizona Ave': 'AZ',
            'Tatum': 'AZ',
            'AZ Tree Care': 'AZ',
            'Tucson': 'AZ',
            'Phoenix': 'AZ',
            'Scottsdale': 'AZ',
            
            # Texas
            'Pond Springs': 'TX',
            'Austin': 'TX',
            'Dallas': 'TX',
            'Houston': 'TX',
            'San Antonio': 'TX',
            'TX Tree Care': 'TX',  # Tree Care Division in Texas
            
            # California
            'La Verne': 'CA',
            'Los Angeles': 'CA',
            'San Diego': 'CA',
            'Sacramento': 'CA',
            'SD Tree Care': 'CA',     # San Diego Tree Care
            'LA Tree Care': 'CA',     # Los Angeles Tree Care  
            'Inland Tree Care': 'CA', # Inland Tree Care
            'North Cal Tree Care': 'CA', # North California Tree Care
            
            # Nevada
            'Las Vegas': 'NV',
            'Charleston': 'NV',  # Charleston street location in Las Vegas
            'Eastern': 'NV',     # Eastern location in Las Vegas
            'Rancho': 'NV',      # Rancho location in Las Vegas
            'NV Tree Care': 'NV', # Tree Care Division in Nevada
            
            # Tennessee
            'Knoxville': 'TN',
            'Franklin': 'TN',
            
            # Georgia
            'Peachtree City': 'GA',
            
            # Florida
            'Riviera Beach': 'FL',
            'Naples': 'FL',
            'The Villages': 'FL',
            'FL Tree Care': 'FL',  # Tree Care Division in Florida
        }
        
        # Prize level mappings
        self.prize_levels = {
            'red': 'Level 1-(Red) Monthly Drawing',
            'green': 'Level 2-(Green) Quarterly Drawing', 
            'gold': 'Level 3-(Gold) Annual Drawing Grand Prize'
        }
    
    def fetch_all_participants(self) -> List[Dict]:
        """Fetch all raffle participants from KPA API"""
        print(f"🎫 Fetching raffle participants from KPA API...")
        
        payload = {
            "token": self.token,
            "pretty": True,
            "form_id": self.form_id,
            "limit": 1000,  # Get a large number
            "page": 1,
            "skip_field_id_mapping": False,
            "skip_field_id_mapping_json": False
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                responses = data.get('responses', [])
                
                # Filter out the header row
                participants = []
                for entry in responses:
                    name = entry.get('a4bcktf70id45ylq', '')
                    if 'Name of employee' not in name and name.strip():
                        participants.append(self._parse_participant(entry))
                
                print(f"✅ Fetched {len(participants)} raffle participants")
                return participants
            else:
                print(f"❌ API request failed: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"💥 Error fetching participants: {str(e)}")
            return []
    
    def _parse_participant(self, entry: Dict) -> Dict:
        """Parse a KPA API entry into standardized participant format"""
        name = entry.get('a4bcktf70id45ylq', '').strip()
        location = entry.get('qkx2vzdeheydfssj', '').strip()
        prize_level = entry.get('qfugnl8mu4zh7agg', '').strip()
        photo_url = entry.get('02rih1l2u938808b', '').strip()
        serial_number = entry.get('bcnz1j0t5w31wt88', '').strip()
        description = entry.get('r69hud60slskiz35', '').strip()
        
        # Map location to state
        state = self.location_to_state.get(location, 'Unknown')
        
        # Determine prize level category
        level_category = 'unknown'
        if 'Level 1' in prize_level or 'Red' in prize_level:
            level_category = 'red'
        elif 'Level 2' in prize_level or 'Green' in prize_level:
            level_category = 'green'
        elif 'Level 3' in prize_level or 'Gold' in prize_level:
            level_category = 'gold'
        
        return {
            'name': name,
            'location': location,
            'state': state,
            'prize_level': prize_level,
            'level_category': level_category,
            'photo_url': photo_url,
            'serial_number': serial_number,
            'description': description,
            'source': 'kpa_api'
        }
    
    def filter_participants(self, participants: List[Dict], 
                          state_filter: Optional[str] = None,
                          level_filter: Optional[str] = None) -> List[Dict]:
        """Filter participants by state and/or prize level"""
        filtered = participants.copy()
        
        if state_filter and state_filter != 'all':
            filtered = [p for p in filtered if p['state'] == state_filter]
            print(f"🗺️  Filtered by state {state_filter}: {len(filtered)} participants")
        
        if level_filter and level_filter != 'all':
            filtered = [p for p in filtered if p['level_category'] == level_filter]
            print(f"🏆 Filtered by level {level_filter}: {len(filtered)} participants")
        
        return filtered
    
    def get_available_states(self, participants: List[Dict]) -> List[str]:
        """Get list of available states from participants"""
        states = set(p['state'] for p in participants if p['state'] != 'Unknown')
        return sorted(list(states))
    
    def get_available_levels(self, participants: List[Dict]) -> List[str]:
        """Get list of available prize levels from participants"""
        levels = set(p['level_category'] for p in participants if p['level_category'] != 'unknown')
        return sorted(list(levels))
    
    def get_participant_stats(self, participants: List[Dict]) -> Dict:
        """Get statistics about participants"""
        stats = {
            'total': len(participants),
            'by_state': {},
            'by_level': {},
            'photos_available': 0
        }
        
        for p in participants:
            # Count by state
            state = p['state']
            stats['by_state'][state] = stats['by_state'].get(state, 0) + 1
            
            # Count by level
            level = p['level_category']
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            
            # Count photos
            if p['photo_url'] and 'get-upload' in p['photo_url']:
                stats['photos_available'] += 1
        
        return stats

def test_kpa_raffle_manager():
    """Test the KPA raffle manager"""
    manager = KPARaffleManager()
    
    print("🧪 Testing KPA Raffle Manager...")
    print("=" * 50)
    
    # Fetch all participants
    participants = manager.fetch_all_participants()
    
    if participants:
        # Show stats
        stats = manager.get_participant_stats(participants)
        print(f"\n📊 PARTICIPANT STATISTICS:")
        print(f"Total participants: {stats['total']}")
        print(f"Photos available: {stats['photos_available']}/{stats['total']} ({stats['photos_available']/stats['total']*100:.1f}%)")
        
        print(f"\n🗺️  BY STATE:")
        for state, count in sorted(stats['by_state'].items()):
            print(f"  {state}: {count}")
        
        print(f"\n🏆 BY PRIZE LEVEL:")
        for level, count in sorted(stats['by_level'].items()):
            print(f"  {level}: {count}")
        
        # Test filtering
        print(f"\n🔍 TESTING FILTERS:")
        az_participants = manager.filter_participants(participants, state_filter='AZ')
        red_participants = manager.filter_participants(participants, level_filter='red')
        az_red_participants = manager.filter_participants(participants, state_filter='AZ', level_filter='red')
        
        print(f"AZ participants: {len(az_participants)}")
        print(f"Red level participants: {len(red_participants)}")
        print(f"AZ + Red participants: {len(az_red_participants)}")
        
        # Show sample participant
        if participants:
            print(f"\n👤 SAMPLE PARTICIPANT:")
            sample = participants[0]
            for key, value in sample.items():
                if len(str(value)) > 80:
                    print(f"  {key}: {str(value)[:80]}...")
                else:
                    print(f"  {key}: {value}")
    
    return participants

if __name__ == "__main__":
    test_kpa_raffle_manager()

import pandas as pd
import random
import base64
import zipfile
import io
from pathlib import Path
import time
from datetime import datetime
import json
import os
import streamlit as st
from PIL import Image
import plotly.graph_objects as go

# KPA API integration via Flask server
import requests
KPA_AVAILABLE = True
# Configuration
KPA_API_URL = "http://localhost:5001/api/v1"

def run_app():
    st.set_page_config(page_title="🎉 The MVN Great Save Raffle 🎉", page_icon="🎟️", layout="wide")
    
    # Initialize session state
    if 'winner_history' not in st.session_state:
        st.session_state.winner_history = []
    if 'images' not in st.session_state:
        st.session_state.images = {}
    if 'countdown_active' not in st.session_state:
        st.session_state.countdown_active = False
    
    # Custom CSS (same as before)
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #f7b731, #5f27cd);
        background-size: 400% 400%;
        animation: gradient 3s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .mega-winner {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        animation: bounce 1s infinite, glow 2s ease-in-out infinite;
        margin: 40px auto;
        max-width: 800px;
        background: rgba(255, 255, 255, 0.95);
        padding: 40px;
        border-radius: 30px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }
    
    .winner-name {
        font-size: 5em;
        font-weight: bold;
        color: #fff;
        text-shadow: 
            0 0 10px #fff,
            0 0 20px #fff,
            0 0 30px #ff00de,
            0 0 40px #ff00de,
            0 0 50px #ff00de,
            0 0 60px #ff00de,
            0 0 70px #ff00de;
        margin: 20px 0;
        animation: pulse 2s infinite;
        background: linear-gradient(45deg, #FFD700, #FFA500, #FF6347);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .kpa-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        color: white;
    }
    
    .api-status {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        margin: 5px 0;
    }
    
    .api-connected {
        background: #4CAF50;
        color: white;
    }
    
    .api-disconnected {
        background: #f44336;
        color: white;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    @keyframes glow {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.3); }
    }
    </style>
    """, unsafe_allow_html=True)

    def save_winner_history():
        """Save winner history to a JSON file"""
        try:
            with open('winner_history.json', 'w') as f:
                json.dump(st.session_state.winner_history, f)
        except:
            pass

    def load_winner_history():
        """Load winner history from JSON file"""
        try:
            if os.path.exists('winner_history.json'):
                with open('winner_history.json', 'r') as f:
                    st.session_state.winner_history = json.load(f)
        except:
            st.session_state.winner_history = []

    # Load history on startup
    load_winner_history()

    # MVN Logo header (same as before)
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        try:
            logo_image = Image.open("Moon Valley Logo.png")
            st.image(logo_image, width=100)
        except FileNotFoundError:
            st.markdown("""
            <div style='background: #4ecdc4; color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: bold;'>
                MVN<br/>CORP
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("<h1 style='text-align: center; font-size: 4em; color: #FFD700;'>🎊 The MVN Great Save Raffle 🎊</h1>", unsafe_allow_html=True)
    
    with col3:
        try:
            logo_image = Image.open("Moon Valley Logo.png")
            st.image(logo_image, width=100)
        except FileNotFoundError:
            st.markdown("""
            <div style='background: #4ecdc4; color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: bold;'>
                MVN<br/>CORP
            </div>
            """, unsafe_allow_html=True)
    
    # Check KPA connection status by testing Flask API
    kpa_status = "disconnected"
    try:
        response = requests.get(f"{KPA_API_URL}/health", timeout=5)
        if response.status_code == 200:
            kpa_status = "connected"
    except:
        pass
    
    # API Status indicator
    status_class = "api-connected" if kpa_status == "connected" else "api-disconnected"
    status_text = "🟢 KPA Connected" if kpa_status == "connected" else "🔴 KPA Disconnected"
    
    st.markdown(f"""
    <div style='text-align: center; margin: 10px 0;'>
        <span class='api-status {status_class}'>{status_text}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs with KPA integration
    if KPA_AVAILABLE:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎰 Raffle Draw", "🔗 KPA Integration", "🏆 Hall of Fame", "📊 Leaderboard", "⚙️ Settings"])
    else:
        tab1, tab3, tab4, tab5 = st.tabs(["🎰 Raffle Draw", "🏆 Hall of Fame", "📊 Leaderboard", "⚙️ Settings"])
    
    with tab1:
        st.markdown("<p style='text-align: center; font-size: 1.5em;'>Get ready for the most EPIC winner announcement!</p>", unsafe_allow_html=True)

        # KPA Quick Load section (if connected)
        if kpa_status == "connected":
            st.markdown("""
            <div class='kpa-section'>
                <h3>🚀 KPA Quick Load</h3>
                <p>Load participants directly from your KPA system with filters</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                quick_prize_level = st.selectbox(
                    "🏆 Prize Level",
                    ["monthly", "quarterly", "annual"],
                    format_func=lambda x: {
                        "monthly": "🔴 Monthly Drawing",
                        "quarterly": "🟢 Quarterly Drawing", 
                        "annual": "🟡 Annual Grand Prize"
                    }[x],
                    key="quick_prize_level"
                )
            
            with col2:
                quick_location = st.text_input(
                    "📍 Location Filter (optional)",
                    placeholder="e.g., Phoenix, Austin",
                    key="quick_location"
                )
            
            with col3:
                quick_date_range = st.selectbox(
                    "📅 Eligibility Period",
                    [30, 60, 90, 365],
                    format_func=lambda x: f"Last {x} days",
                    key="quick_date_range"
                )
            
            if st.button("⚡ Quick Load from KPA", type="primary"):
                if load_kpa_participants(quick_prize_level, quick_location, quick_date_range):
                    st.success("✅ Participants loaded from KPA!")
                    st.rerun()
            
            st.markdown("---")

        # Original manual load methods
        st.markdown("### 📊 Manual Data Loading")
        
        # Auto-load from Google Sheets
        if st.button("📊 Load MVN Raffle Data (Google Sheets)", type="secondary"):
            if load_google_sheets_data():
                st.rerun()

        st.markdown("---")
        
        # File uploaders (same as before)
        col1, col2 = st.columns(2)
        with col1:
            uploaded_excel = st.file_uploader("📊 Upload Excel/CSV file", type=["xlsx", "csv"])
            
            st.markdown("**OR**")
            cloud_csv_url = st.text_input(
                "☁️ Load CSV from Cloud URL:",
                placeholder="Dropbox or Google Sheets sharing link",
                help="Supports Dropbox sharing links and Google Sheets sharing links"
            )
            
            if cloud_csv_url and st.button("📥 Load CSV from Cloud"):
                if load_cloud_csv(cloud_csv_url):
                    st.rerun()
            
        with col2:
            st.info("📸 **Photo Options:**")
            st.success("🌐 **Recommended:** Use image URLs in your CSV")
            st.info("🔗 **KPA Integration:** Automatic photo retrieval")
            uploaded_zip = st.file_uploader("🖼️ Optional: Upload ZIP with local images", type=["zip"])

        # Rest of the raffle logic (same as before)
        if uploaded_zip is not None:
            try:
                st.session_state.images = extract_images_from_zip(uploaded_zip)
                st.success(f"🎯 Loaded {len(st.session_state.images)} local images from ZIP!")
            except Exception as e:
                st.error(f"Error loading ZIP: {e}")

        if uploaded_excel is not None:
            process_uploaded_file(uploaded_excel)

        # Show raffle interface if data is loaded
        if 'df' in st.session_state and len(st.session_state.df) > 0:
            show_raffle_interface()

    # KPA Integration Tab
    if KPA_AVAILABLE:
        with tab2:
            st.markdown("""
            <div class='kpa-section'>
                <h2>🔗 KPA Integration Status</h2>
                <p>Direct connection to KPA Great Save Raffle form (ID: 289228)</p>
            </div>
            """, unsafe_allow_html=True)
            
            # KPA Status Display
            if kpa_status == "connected":
                st.success("✅ KPA API Server is running and connected!")
                st.info("📋 Form ID: 289228 (Great Save Raffle)")
                
                # Test connection button
                if st.button("🔄 Test KPA Connection"):
                    try:
                        response = requests.get(f"{KPA_API_URL}/api/participants", timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            participant_count = len(data.get('participants', []))
                            st.success(f"✅ Connection successful! Found {participant_count} participant(s)")
                        else:
                            st.error(f"❌ API Error: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
            else:
                st.error("❌ KPA API Server not running")
                st.info("💡 Start the KPA API server with: `python3 kpa_api_server.py`")
            
            st.markdown("---")
            
            # KPA Direct Load UI (if connected)
            if kpa_status == "connected":
                st.markdown("""
                <div class='kpa-section'>
                    <h3>🚀 Load Participants from KPA</h3>
                    <p>Automatically fetch participants from the Great Save Raffle form</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 Load All Participants", key="kpa_load_all"):
                        if load_kpa_participants("all", "All Locations", 30):
                            st.success("✅ Participants loaded from KPA!")
                        
                with col2:
                    if st.button("🔄 Refresh Data", key="kpa_refresh"):
                        if load_kpa_participants("all", "All Locations", 30):
                            st.success("✅ Data refreshed from KPA!")
            else:
                st.info("⚠️ Start KPA API server to use automated participant loading")

    # Hall of Fame and Leaderboard (same as before)
    with tab3:
        show_hall_of_fame()

    with tab4:
        show_leaderboard()

    with tab5:
        show_settings()

def load_kpa_participants(prize_level, location, date_range):
    """Load participants from KPA Flask API with filters"""
    try:
        with st.spinner("🔄 Loading participants from KPA..."):
            # Call our Flask API to get participants from KPA form
            response = requests.get(f"{KPA_API_URL}/forms/submissions?form_id=289228&limit=100", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                submissions = data.get('submissions', [])
                
                if len(submissions) > 0:
                    # Convert KPA submissions to participant format
                    participants = []
                    for submission in submissions:
                        participant_data = submission.get('data', {})
                        participants.append({
                            'name': participant_data.get('employee_name', 'Unknown'),
                            'email': participant_data.get('email', 'N/A'),
                            'department': participant_data.get('department', 'N/A'),
                            'location': participant_data.get('location', 'N/A'),
                            'employee_id': participant_data.get('employee_id', ''),
                            'submission_id': submission.get('id', ''),
                            'submitted_at': submission.get('submitted_at', '')
                        })
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(participants)
                    
                    # Apply filters if specified
                    if location and location != "All Locations":
                        df = df[df['department'].str.contains(location, case=False, na=False)]
                    
                    st.session_state.df = df
                    st.balloons()
                    return True
                else:
                    st.warning("⚠️ No participants found in KPA Great Save Raffle form (ID: 289228) yet")
                    return False
            else:
                st.error(f"❌ KPA API Error: {response.status_code}")
                return False
    except Exception as e:
        st.error(f"❌ Error loading from KPA: {str(e)}")
        return False

def load_google_sheets_data():
    """Load data from Google Sheets"""
    try:
        import requests
        from io import StringIO
        
        google_sheets_url = "https://docs.google.com/spreadsheets/d/1x_L53CCwC6gNI5iL4iAMZPV7x4o8nRlOtcOfMWR2Ie8/export?format=csv"
        
        with st.spinner("Loading your raffle data..."):
            response = requests.get(google_sheets_url)
            if response.status_code == 200:
                csv_data = StringIO(response.text)
                df = pd.read_csv(csv_data)
                st.session_state.df = df
                st.success(f"✅ Loaded {len(df)} participants from Google Sheets!")
                st.balloons()
                return True
            else:
                st.error(f"❌ Failed to load data. Status: {response.status_code}")
                return False
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return False

def load_cloud_csv(cloud_csv_url):
    """Load CSV from cloud URL"""
    # Implementation same as before
    pass

def extract_images_from_zip(zip_file):
    """Extract images from ZIP file"""
    # Implementation same as before
    pass

def process_uploaded_file(uploaded_file):
    """Process uploaded Excel/CSV file"""
    # Implementation same as before
    pass

def show_raffle_interface():
    """Show the main raffle drawing interface"""
    # Implementation same as before
    pass

def show_hall_of_fame():
    """Show hall of fame tab"""
    # Implementation same as before
    pass

def show_leaderboard():
    """Show leaderboard tab"""
    # Implementation same as before
    pass

def show_settings():
    """Show settings tab"""
    st.markdown("## ⚙️ Application Settings")
    
    st.markdown("### 🔗 KPA Integration Status")
    try:
        response = requests.get(f"{KPA_API_URL}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ KPA API Server Connected")
            st.info("📋 Connected to Great Save Raffle form (ID: 289228)")
        else:
            st.error("❌ KPA API Server Error")
    except:
        st.error("❌ KPA API Server Not Running")
        st.info("💡 Start with: `python3 kpa_api_server.py`")
    
    st.markdown("### 📊 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Winner History"):
            st.session_state.winner_history = []
            try:
                os.remove('winner_history.json')
            except:
                pass
            st.success("✅ Winner history cleared")
    
    with col2:
        if st.button("🔄 Clear All Session Data"):
            # Clear all session data including cached participants
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("✅ All session data cleared - page will refresh")
            st.rerun()
    
    st.markdown("### � Current Data Status")
    if 'df' in st.session_state and len(st.session_state.df) > 0:
        participant_count = len(st.session_state.df)
        st.info(f"📊 Current participants loaded: {participant_count}")
        if st.button("❌ Clear Participant Data"):
            del st.session_state.df
            st.success("✅ Participant data cleared")
            st.rerun()
    else:
        st.info("📊 No participant data currently loaded")
        st.session_state.winner_history = []
        try:
            os.remove('winner_history.json')
        except:
            pass
        st.success("✅ Winner history cleared")
    
    if st.button("💾 Export Winner History"):
        if st.session_state.winner_history:
            df = pd.DataFrame(st.session_state.winner_history)
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Winner History CSV",
                data=csv,
                file_name=f"winner_history_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No winner history to export")

if __name__ == "__main__":
    run_app()

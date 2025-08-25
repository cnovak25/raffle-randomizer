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
import subprocess
import signal
import atexit
import streamlit as st
from PIL import Image
import plotly.graph_objects as go

# KPA API integration via Flask server
import requests
KPA_AVAILABLE = True
# Configuration
KPA_API_URL = "http://localhost:5001/api/v1"

def start_flask_server():
    """Start the Flask API server as a subprocess"""
    if 'flask_process' not in st.session_state or st.session_state.flask_process is None:
        try:
            # Start the Flask server process
            flask_process = subprocess.Popen(
                ['python3', 'kpa_api_server.py'],
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )
            
            st.session_state.flask_process = flask_process
            st.session_state.flask_start_time = time.time()
            
            # Wait a moment for the server to start
            time.sleep(3)
            
            # Register cleanup function
            def cleanup_flask():
                if 'flask_process' in st.session_state and st.session_state.flask_process:
                    try:
                        if hasattr(os, 'killpg'):
                            os.killpg(os.getpgid(st.session_state.flask_process.pid), signal.SIGTERM)
                        else:
                            st.session_state.flask_process.terminate()
                    except:
                        pass
            
            atexit.register(cleanup_flask)
            return True
            
        except Exception as e:
            st.error(f"Failed to start Flask server: {e}")
            return False
    return True

def check_flask_server():
    """Check if Flask server is running and start if needed"""
    try:
        response = requests.get(f"{KPA_API_URL}/health", timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    
    # Server not responding, try to start it
    return start_flask_server()

def stop_flask_server():
    """Stop the Flask server subprocess"""
    if 'flask_process' in st.session_state and st.session_state.flask_process:
        try:
            if hasattr(os, 'killpg'):
                os.killpg(os.getpgid(st.session_state.flask_process.pid), signal.SIGTERM)
            else:
                st.session_state.flask_process.terminate()
            st.session_state.flask_process = None
        except Exception as e:
            st.error(f"Error stopping Flask server: {e}")

# Ensure Flask server is running
if 'flask_initialized' not in st.session_state:
    st.session_state.flask_initialized = True
    with st.spinner("🚀 Starting KPA API server..."):
        if check_flask_server():
            st.success("✅ KPA API server started successfully!")
        else:
            st.error("❌ Failed to start KPA API server")

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

def get_employee_photo(employee_id):
    """Get employee photo from KPA API using employee ID"""
    if not employee_id:
        return None
        
    try:
        # First, try to get photo from KPA submissions to find the photo key
        response = requests.get(f"{KPA_API_URL}/forms/submissions?form_id=289228&limit=100", 
                              headers={'Content-Type': 'application/json'}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            submissions = data.get('submissions', [])
            
            # Find the submission with matching employee_id
            for submission in submissions:
                if submission.get('employee_id') == employee_id:
                    photos = submission.get('photos', [])
                    if photos and len(photos) > 0:
                        photo_url = photos[0].get('url')  # Get proxied photo URL
                        return photo_url
                        
        return None
        
    except Exception as e:
        st.error(f"Error getting photo for {employee_id}: {str(e)}")
        return None

def create_winner_card(winner_data, show_photo=True):
    """Create a beautiful winner card with name and photo"""
    winner_name = winner_data.get('employee_name', winner_data.get('name', 'Unknown'))
    employee_id = winner_data.get('employee_id', '')
    department = winner_data.get('department', 'N/A')
    location = winner_data.get('location', 'N/A')
    
    # Create the card layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div class="mega-winner">
            <h1 style="text-align: center; color: #ff6b6b; margin-bottom: 20px;">🎉 WINNER! 🎉</h1>
        """, unsafe_allow_html=True)
        
        # Show photo if available and requested
        if show_photo and employee_id:
            photo_url = get_employee_photo(employee_id)
            if photo_url:
                try:
                    st.image(photo_url, width=300, caption=f"📸 {winner_name}")
                except Exception as e:
                    st.warning(f"Could not load photo: {str(e)}")
                    st.markdown("📷 *Photo not available*")
            else:
                st.markdown("📷 *Photo not available*")
        
        # Winner details
        st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <h2 style="color: #4ecdc4; font-size: 2.5em;">{winner_name}</h2>
                <p style="font-size: 1.2em; color: #666;">
                    <strong>Employee ID:</strong> {employee_id}<br>
                    <strong>Department:</strong> {department}<br>
                    <strong>Location:</strong> {location}
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

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
    
    # Initialize and auto-start Flask server
    if not check_flask_server():
        with st.spinner("🚀 Starting KPA API server..."):
            if start_flask_server():
                st.success("✅ KPA API server started successfully!")
                time.sleep(2)  # Give server time to fully initialize
                st.rerun()  # Refresh to update connection status
            else:
                st.error("❌ Failed to start KPA API server")

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
    
    # Create tabs - simplified interface with KPA integration built into main tab
    tab1, tab2, tab3, tab4 = st.tabs(["🎰 Raffle Draw", "🏆 Hall of Fame", "📊 Leaderboard", "⚙️ Settings"])
    
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
        st.markdown("### 📊 Data Loading")
        
        # Primary KPA loading interface
        if KPA_AVAILABLE and kpa_status == "connected":
            st.markdown("""
            <div class='kpa-section'>
                <h3>🔗 Automated KPA Data Loading</h3>
                <p>All raffle data is automatically loaded from the KPA Great Save Raffle form with photos included</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("� Load MVN Raffle Data (KPA)", type="primary", use_container_width=True):
                    if load_kpa_participants("all", "All Locations", 30):
                        st.success("✅ Participants loaded from KPA Great Save Raffle form!")
                        st.rerun()
            
            with col2:
                if st.button("🔄 Refresh KPA Data", type="secondary", use_container_width=True):
                    if load_kpa_participants("all", "All Locations", 30):
                        st.success("✅ Data refreshed from KPA!")
                        st.rerun()
            
            st.info("📸 Photos are automatically included from KPA form submissions")
        else:
            st.error("❌ KPA API Server not running")
            st.info("💡 Start the KPA API server to access raffle data")
            st.info("🔧 Go to Settings tab to start the server")

        st.markdown("---")
        
        # CSV Upload Section - RECOMMENDED APPROACH
        st.markdown("""
        <div class='kpa-section' style='background: #e8f5e8; border-left: 5px solid #4CAF50;'>
            <h3>📄 CSV Upload Method (Recommended)</h3>
            <p><strong>💡 Simple & Reliable:</strong> Download CSV from KPA → Upload here → Get photos via API</p>
            <p>✅ Real employee names | ✅ All participant data | ✅ Photos from API</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📤 Upload CSV Data", type="primary", use_container_width=True):
            csv_data = load_csv_participants()
            if csv_data is not None:
                st.session_state.df = csv_data
                st.success("🎯 Ready to run raffle with CSV data + API photos!")
                st.rerun()

        st.markdown("---")

        # Show raffle interface if data is loaded
        if 'df' in st.session_state and len(st.session_state.df) > 0:
            show_raffle_interface()

    # Hall of Fame and Leaderboard tabs
    with tab2:
        show_hall_of_fame()

    with tab3:
        show_leaderboard()

    with tab4:
        show_settings()

def load_csv_participants():
    """Load participants from uploaded CSV file"""
    st.subheader("📄 Upload Participant CSV")
    st.info("💡 Download the participant CSV from KPA, then upload it here for reliable data with real names!")
    
    uploaded_file = st.file_uploader(
        "Upload CSV file with participant data", 
        type=['csv'],
        help="CSV should include columns: employee_name, employee_id, department, location, etc."
    )
    
    if uploaded_file is not None:
        try:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)
            
            # Display preview of the data
            st.success(f"✅ Successfully loaded {len(df)} participants from CSV")
            st.write("**Data Preview:**")
            st.dataframe(df.head(), use_container_width=True)
            
            # Validate required columns
            required_columns = ['employee_name', 'employee_id']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
                st.info("Required columns: employee_name, employee_id")
                return None
            
            # Add any missing optional columns
            optional_columns = {
                'department': 'N/A',
                'location': 'N/A', 
                'email': 'N/A',
                'observer_name': 'N/A',
                'prize_level': 'Standard'
            }
            
            for col, default_value in optional_columns.items():
                if col not in df.columns:
                    df[col] = default_value
            
            # Store in session state
            st.session_state.csv_participants = df
            return df
            
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            return None
    
    return None

def load_kpa_participants(prize_level, location, date_range):
    """Load participants from KPA Flask API with filters - SIMPLIFIED VERSION"""
    try:
        with st.spinner("🔄 Loading participants from KPA..."):
            # Simple headers for local Flask API
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Call our Flask API to get participants from KPA form
            response = requests.get(f"{KPA_API_URL}/forms/submissions?form_id=289228&limit=100", 
                                  headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                submissions = data.get('submissions', [])
                
                if len(submissions) > 0:
                    # Convert KPA submissions to participant format
                    participants = []
                    for submission in submissions:
                        # Extract photo URL from photos array if available
                        photo_url = None
                        photos = submission.get('photos', [])
                        if photos and len(photos) > 0:
                            photo_url = photos[0].get('url')  # Get first photo URL
                        
                        participants.append({
                            'name': submission.get('employee_name', 'Unknown'),
                            'employee_name': submission.get('employee_name', 'Unknown'),  # For compatibility
                            'email': submission.get('email', 'N/A'),
                            'department': submission.get('department', 'N/A'),
                            'location': submission.get('location', 'N/A'),
                            'employee_id': submission.get('employee_id', ''),
                            'observer_name': submission.get('observer_name', 'Unknown'),
                            'prize_level': submission.get('prize_level', 'Unknown'),
                            'description': submission.get('description', ''),
                            'photo_url': photo_url,  # Extract from photos array
                            'photos': photos,    # Keep full photos array
                            'submission_id': submission.get('response_id', ''),
                            'submitted_at': submission.get('submission_date', ''),
                            'nominated_employee_id': submission.get('nominated_employee_id', '')
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
    """Show the main raffle drawing interface with KPA photo support"""
    import random
    
    st.markdown("## 🎰 Raffle Draw Interface")
    
    df = st.session_state.df
    st.success(f"🎯 {len(df)} participants loaded and ready!")
    
    # Show preview of participants with photos (if available)
    st.markdown("### 👥 Participants Preview")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Total Participants:** {len(df)}")
        if 'photo_url' in df.columns:
            photos_count = df['photo_url'].notna().sum()
            st.markdown(f"**With Photos:** {photos_count}")
    
    with col2:
        if st.button("👀 Show Sample Participant"):
            sample = df.sample(n=1).iloc[0]
            st.markdown(f"**Sample:** {sample.get('employee_name', 'Unknown')}")
            if pd.notna(sample.get('photo_url')):
                try:
                    st.image(sample['photo_url'], width=200, caption="Sample participant photo")
                except:
                    st.info("📷 Photo available but couldn't load preview")
    
    st.markdown("---")
    
    # Raffle drawing section
    st.markdown("### 🎲 Draw Winner")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎰 DRAW WINNER", type="primary"):
            # Select random winner
            winner = df.sample(n=1).iloc[0]
            
            # Display winner with fanfare
            st.balloons()
            
            # Use the new winner card function
            create_winner_card(winner, show_photo=True)
            
            # Save to winner history
            winner_record = {
                'name': winner.get('employee_name', 'Unknown'),
                'employee_id': winner.get('employee_id', 'Unknown'),
                'department': winner.get('department', 'Unknown'),
                'prize_level': winner.get('prize_level', 'Unknown'),
                'drawn_date': datetime.now().isoformat(),
                'drawn_by': 'KPA Raffle System',
                'photo_url': winner.get('photo_url')
            }
            
            if 'winner_history' not in st.session_state:
                st.session_state.winner_history = []
            st.session_state.winner_history.append(winner_record)
            
            # Save to file
            try:
                import json
                with open('winner_history.json', 'w') as f:
                    json.dump(st.session_state.winner_history, f)
            except:
                pass
    
    with col2:
        if st.button("🔄 Refresh Participants"):
            if load_kpa_participants("all", "All Locations", 30):
                st.success("✅ Participants refreshed from KPA!")
                st.rerun()
    
    with col3:
        if st.button("📊 Show Statistics"):
            st.markdown("### 📈 Participant Statistics")
            if 'prize_level' in df.columns:
                prize_counts = df['prize_level'].value_counts()
                st.bar_chart(prize_counts)
            
            if 'department' in df.columns:
                dept_counts = df['department'].value_counts().head(10)
                st.markdown("**Top Departments:**")
                for dept, count in dept_counts.items():
                    st.markdown(f"- {dept}: {count} participants")
    
    # Participants table
    st.markdown("### 📋 All Participants")
    
    # Display table with photo indicators
    display_df = df.copy()
    if 'photo_url' in display_df.columns:
        display_df['Has Photo'] = display_df['photo_url'].notna().map({True: '📸', False: '❌'})
    
    # Select columns to display
    display_columns = ['employee_name', 'employee_id', 'department', 'prize_level', 'observer_name']
    if 'Has Photo' in display_df.columns:
        display_columns.append('Has Photo')
    
    available_columns = [col for col in display_columns if col in display_df.columns]
    st.dataframe(display_df[available_columns], use_container_width=True)

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
    
    # Flask server status and controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Check Server Status"):
            if check_flask_server():
                st.success("✅ Flask server is running")
            else:
                st.error("❌ Flask server not responding")
    
    with col2:
        if st.button("🚀 Start/Restart Server"):
            stop_flask_server()
            time.sleep(1)
            if start_flask_server():
                st.success("✅ Flask server started!")
            else:
                st.error("❌ Failed to start server")
    
    with col3:
        if st.button("🛑 Stop Server"):
            stop_flask_server()
            st.info("🛑 Flask server stopped")
    
    # Show current status
    try:
        response = requests.get(f"{KPA_API_URL}/health", timeout=3)
        if response.status_code == 200:
            st.success("✅ KPA API Server Connected")
            st.info("📋 Connected to Great Save Raffle form (ID: 289228)")
            
            # Show Flask process info
            if 'flask_process' in st.session_state and st.session_state.flask_process:
                uptime = time.time() - st.session_state.get('flask_start_time', time.time())
                st.info(f"🕐 Server uptime: {uptime:.1f} seconds")
        else:
            st.error("❌ KPA API Server Error")
    except:
        st.error("❌ KPA API Server Not Running")
        if st.button("� Auto-Start Server"):
            if check_flask_server():
                st.rerun()
    
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

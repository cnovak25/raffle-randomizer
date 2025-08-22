mport pandas as pd
import random
import base64
import zipfile
import io
from pathlib import Path
import time
from datetime import datetime
import json
import os
<<<<<<< HEAD
import streamlit as st
from streamlit_extras.st_autorefresh import st_autorefresh

def run_app():
=======

def run_app():
    import streamlit as st
    from PIL import Image
    import plotly.graph_objects as go
    
>>>>>>> c6fab56fd4a93220ffbde98e024dd2c6ca72533b
    st.set_page_config(page_title="🎉 MEGA Raffle Celebration 🎉", page_icon="🎟️", layout="wide")
    
    # Initialize session state
    if 'winner_history' not in st.session_state:
        st.session_state.winner_history = []
    if 'images' not in st.session_state:
        st.session_state.images = {}
    if 'countdown_active' not in st.session_state:
        st.session_state.countdown_active = False
    
    # Custom CSS for massive celebration
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
    
    .countdown {
        font-size: 10em;
        font-weight: bold;
        color: #FFD700;
        text-shadow: 
            0 0 20px #FFD700,
            0 0 40px #FFA500,
            0 0 60px #FF6347;
        animation: countdown-pulse 1s infinite;
        text-align: center;
        margin: 50px 0;
    }
    
    @keyframes countdown-pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .hall-of-fame {
        background: rgba(255, 215, 0, 0.1);
        border: 3px solid #FFD700;
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    .winner-card {
        background: white;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    
    .winner-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    .leaderboard-entry {
        display: flex;
        align-items: center;
        padding: 10px;
        margin: 5px 0;
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
        transition: all 0.3s;
    }
    
    .leaderboard-entry:hover {
        background: rgba(255,215,0,0.3);
        transform: translateX(10px);
    }
    
    .rank-badge {
        font-size: 2em;
        font-weight: bold;
        margin-right: 20px;
        min-width: 50px;
        text-align: center;
    }
    
    .gold { color: #FFD700; }
    .silver { color: #C0C0C0; }
    .bronze { color: #CD7F32; }
    
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
    
    .confetti {
        position: absolute;
        width: 10px;
        height: 10px;
        background: #f0f;
        animation: confetti-fall 3s linear infinite;
    }
    
    @keyframes confetti-fall {
        to { transform: translateY(100vh) rotate(360deg); }
    }
    
    .trophy {
        font-size: 8em;
        animation: trophy-bounce 1s infinite;
    }
    
    @keyframes trophy-bounce {
        0%, 100% { transform: scale(1) rotate(0deg); }
        25% { transform: scale(1.2) rotate(-5deg); }
        75% { transform: scale(1.2) rotate(5deg); }
    }
    
    .download-button {
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white;
        padding: 15px 30px;
        border-radius: 30px;
        font-size: 1.2em;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .download-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
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

    st.markdown("<h1 style='text-align: center; font-size: 4em; color: #FFD700;'>🎊 MEGA RAFFLE EXTRAVAGANZA 🎊</h1>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🎰 Raffle Draw", "🏆 Hall of Fame", "📊 Leaderboard"])
    
    with tab1:
        st.markdown("<p style='text-align: center; font-size: 1.5em;'>Get ready for the most EPIC winner announcement!</p>", unsafe_allow_html=True)

        # File uploaders
        col1, col2 = st.columns(2)
        with col1:
            uploaded_excel = st.file_uploader("📊 Upload Excel/CSV file", type=["xlsx", "csv"])
        with col2:
            uploaded_zip = st.file_uploader("🖼️ Upload ZIP with images", type=["zip"])

        def play_celebration_sounds():
            sounds = [
                "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3",
                "https://www.soundjay.com/human/sounds/applause-4.mp3"
            ]
            for sound in sounds:
                b64 = base64.b64encode(f'<audio autoplay><source src="{sound}" type="audio/mpeg"></audio>'.encode()).decode()
                st.markdown(f"<iframe src='data:text/html;base64,{b64}' style='display:none;'></iframe>", unsafe_allow_html=True)

        def extract_images_from_zip(zip_file):
            images = {}
            with zipfile.ZipFile(zip_file, 'r') as z:
                for filename in z.namelist():
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                        clean_filename = Path(filename).name
                        if clean_filename:
                            images[clean_filename] = z.read(filename)
            return images

        def create_confetti_rain():
            confetti_html = "<div class='fireworks' style='position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9999;'>"
            colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#FFD700']
            for i in range(100):
                left = random.randint(0, 100)
                delay = random.random() * 3
                color = random.choice(colors)
                size = random.randint(5, 15)
                confetti_html += f"""
                <div class='confetti' style='
                    left: {left}%;
                    background-color: {color};
                    width: {size}px;
                    height: {size}px;
                    animation-delay: {delay}s;
                '></div>
                """
            confetti_html += "</div>"
            st.markdown(confetti_html, unsafe_allow_html=True)

        def create_winner_certificate(winner_name, winner_photo=None):
            """Create a downloadable winner certificate"""
            certificate_html = f"""
            <div id="winner-certificate" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 50px;
                border-radius: 20px;
                text-align: center;
                color: white;
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                max-width: 600px;
                margin: 20px auto;
            ">
                <h1 style="font-size: 3em; margin-bottom: 20px;">🏆 CERTIFICATE OF VICTORY 🏆</h1>
                <p style="font-size: 1.5em;">This certifies that</p>
                <h2 style="font-size: 4em; color: #FFD700; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{winner_name}</h2>
                <p style="font-size: 1.5em;">is the GRAND WINNER of the</p>
                <h3 style="font-size: 2em;">MEGA RAFFLE EXTRAVAGANZA</h3>
                <p style="font-size: 1.2em; margin-top: 30px;">Date: {datetime.now().strftime('%B %d, %Y')}</p>
                <p style="font-size: 1em; margin-top: 20px;">Drawn by: {st.session_state.get('username', 'cnovak25')}</p>
            </div>
            """
            return certificate_html

        # Process ZIP file
        if uploaded_zip is not None:
            try:
                st.session_state.images = extract_images_from_zip(uploaded_zip)
                st.success(f"🎯 Loaded {len(st.session_state.images)} images!")
            except Exception as e:
                st.error(f"Error: {e}")

        # Process Excel/CSV file
        if uploaded_excel is not None:
            try:
                if uploaded_excel.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_excel)
                else:
                    df = pd.read_excel(uploaded_excel)
                
                df.columns = df.columns.str.strip()
                
                if not {"Name", "Photo"}.issubset(df.columns):
                    st.error("Need 'Name' and 'Photo' columns!")
                else:
                    st.success(f"🎪 Loaded {len(df)} participants!")
                    
                    # Countdown settings
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        countdown_seconds = st.slider("⏱️ Countdown Timer (seconds)", 3, 10, 5)
                    
                    # Big shiny button
                    button_col1, button_col2, button_col3 = st.columns([1, 2, 1])
                    with button_col2:
                        if st.button("🎰 SPIN TO WIN! 🎰", type="primary", use_container_width=True):
                            
                            # Countdown
                            countdown_placeholder = st.empty()
                            for i in range(countdown_seconds, 0, -1):
                                countdown_placeholder.markdown(
                                    f"<div class='countdown'>{i}</div>",
                                    unsafe_allow_html=True
                                )
                                time.sleep(1)
                            
                            countdown_placeholder.markdown(
                                "<div class='countdown' style='color: #00FF00;'>GO!</div>",
                                unsafe_allow_html=True
                            )
                            time.sleep(0.5)
                            countdown_placeholder.empty()
                            
                            # Drum roll effect
                            placeholder = st.empty()
                            drum_roll_names = df['Name'].tolist()
                            
                            for i in range(30):
                                random_name = random.choice(drum_roll_names)
                                placeholder.markdown(
                                    f"<h2 style='text-align: center; color: #FFD700;'>🎲 {random_name} 🎲</h2>",
                                    unsafe_allow_html=True
                                )
                                time.sleep(0.05 + (i * 0.005))
                            
                            placeholder.empty()
                            
                            # Select winner
                            winner_row = df.sample(1).iloc[0]
                            winner_name = winner_row['Name']
                            winner_photo = winner_row['Photo']
                            
                            # Add to history
                            winner_entry = {
                                'name': winner_name,
                                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'drawn_by': st.session_state.get('username', 'cnovak25')
                            }
                            st.session_state.winner_history.append(winner_entry)
                            save_winner_history()
                            
                            # MASSIVE CELEBRATION
                            st.balloons()
                            st.snow()
                            play_celebration_sounds()
                            create_confetti_rain()
                            
                            # Trophy animation
                            st.markdown("<div class='trophy' style='text-align: center;'>🏆</div>", unsafe_allow_html=True)
                            
                            # Winner announcement
                            winner_container = st.container()
                            with winner_container:
                                st.markdown(
                                    f"""
                                    <div class='mega-winner'>
                                        <div style='font-size: 2em; color: #FF6347;'>⭐ CONGRATULATIONS! ⭐</div>
                                        <div class='winner-name'>{winner_name}</div>
                                        <div style='font-size: 2em; color: #FF6347;'>🎉 YOU'RE THE WINNER! 🎉</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                # Display photo
                                if pd.notna(winner_photo) and st.session_state.images:
                                    photo_filename = str(winner_photo).strip()
                                    if photo_filename in st.session_state.images:
                                        col1, col2, col3 = st.columns([1, 2, 1])
                                        with col2:
                                            st.image(
                                                st.session_state.images[photo_filename],
                                                use_column_width=True
                                            )
                            
                            # Certificate section
                            st.markdown("---")
                            st.markdown("<h2 style='text-align: center; color: #FFD700;'>🎖️ Winner Certificate 🎖️</h2>", unsafe_allow_html=True)
                            
                            certificate_html = create_winner_certificate(winner_name)
                            st.markdown(certificate_html, unsafe_allow_html=True)
                            
                            # Download button
                            col1, col2, col3 = st.columns([1, 1, 1])
                            with col2:
                                download_html = f"""
                                <html>
                                <head>
                                    <style>
                                        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                                    </style>
                                </head>
                                <body>
                                    {certificate_html}
                                </body>
                                </html>
                                """
                                b64 = base64.b64encode(download_html.encode()).decode()
                                href = f'<a href="data:text/html;base64,{b64}" download="winner_certificate_{winner_name}.html" class="download-button" style="text-decoration: none; display: inline-block;">📥 Download Certificate</a>'
                                st.markdown(href, unsafe_allow_html=True)
                            
            except Exception as e:
                st.error(f"Error: {e}")

    with tab2:
        st.markdown("<h2 style='text-align: center; color: #FFD700;'>🏆 Hall of Fame 🏆</h2>", unsafe_allow_html=True)
        st.markdown("<div class='hall-of-fame'>", unsafe_allow_html=True)
        
        if st.session_state.winner_history:
            # Sort by date (most recent first)
            sorted_history = sorted(st.session_state.winner_history, 
                                  key=lambda x: x['date'], 
                                  reverse=True)
            
            for idx, winner in enumerate(sorted_history[:10]):  # Show last 10 winners
                st.markdown(
                    f"""
                    <div class='winner-card'>
                        <h3 style='color: #FFD700; margin: 0;'>🏆 {winner['name']}</h3>
                        <p style='margin: 5px 0; color: #666;'>Won on: {winner['date']}</p>
                        <p style='margin: 5px 0; color: #888; font-size: 0.9em;'>Drawn by: {winner.get('drawn_by', 'Unknown')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No winners yet! Start your first raffle to see the Hall of Fame.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<h2 style='text-align: center; color: #FFD700;'>📊 Winner Leaderboard 📊</h2>", unsafe_allow_html=True)
        
        if st.session_state.winner_history:
            # Count wins per person
            win_counts = {}
            for winner in st.session_state.winner_history:
                name = winner['name']
                win_counts[name] = win_counts.get(name, 0) + 1
            
            # Sort by win count
            leaderboard = sorted(win_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Display leaderboard
            st.markdown("<div style='max-width: 600px; margin: 0 auto;'>", unsafe_allow_html=True)
            
            for idx, (name, wins) in enumerate(leaderboard[:10]):
                rank = idx + 1
                rank_class = 'gold' if rank == 1 else 'silver' if rank == 2 else 'bronze' if rank == 3 else ''
                medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'#{rank}'
                
                st.markdown(
                    f"""
                    <div class='leaderboard-entry'>
                        <span class='rank-badge {rank_class}'>{medal}</span>
                        <div style='flex-grow: 1;'>
                            <strong style='font-size: 1.2em;'>{name}</strong>
                            <br>
                            <span style='color: #666;'>{wins} win{'s' if wins > 1 else ''}</span>
                        </div>
                        <div style='font-size: 2em;'>{'🏆' * min(wins, 5)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Visualize with a chart
            if len(leaderboard) > 0:
                st.markdown("---")
                names = [item[0] for item in leaderboard[:10]]
                wins = [item[1] for item in leaderboard[:10]]
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=names,
                        y=wins,
                        marker_color=['#FFD700', '#C0C0C0', '#CD7F32'] + ['#4ECDC4'] * 7,
                        text=wins,
                        textposition='auto',
                    )
                ])
                
                fig.update_layout(
                    title="Top 10 Winners",
                    xaxis_title="Winner Name",
                    yaxis_title="Number of Wins",
                    showlegend=False,
                    template="plotly_dark",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No winners yet! Start raffles to see the leaderboard.")
<<<<<<< HEAD

    # Auto-refresh every 5 seconds (5000 ms)
    # st_autorefresh(interval=5000, key="raffle_autorefresh")
=======
>>>>>>> c6fab56fd4a93220ffbde98e024dd2c6ca72533b

if __name__ == "__main__":
    run_app()

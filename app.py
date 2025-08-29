import os, io, time, random, requests, pandas as pd, streamlit as st
from urllib.parse import urlparse, parse_qs, unquote
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import base64
from typing import Optional
from safety_checker import KPASafetyChecker
from kpa_raffle_manager import KPARaffleManager

# Configure page for mobile-first responsive design
st.set_page_config(
    page_title="🎉 MVN Great Save Raffle 🎉",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def fetch_photo_directly(photo_url: str) -> Optional[bytes]:
    """Fetch photo via Railway proxy server"""
    if not photo_url or "get-upload" not in photo_url:
        return None
    
    try:
        # Extract the key from the KPA URL
        if "key=" in photo_url:
            key = photo_url.split("key=")[1].split("&")[0]
            
            # Use Railway proxy (Railway handles port routing automatically)
            proxy_url = f"https://raffle-randomizer-production.up.railway.app/kpa-photo?key={key}"
            
            with st.spinner("📸 Loading winner photo..."):
                response = requests.get(proxy_url, timeout=15)
                if response.status_code == 200:
                    photo_data = response.content
                    st.success("✅ Photo loaded successfully!")
                    return photo_data
                else:
                    st.warning(f"📷 Photo not available (HTTP {response.status_code})")
                    return None
        else:
            st.error("❌ Invalid photo URL format")
            return None
            
    except Exception as e:
        st.error(f"❌ Error loading photo: {str(e)}")
        return None

def fetch_photo_via_proxy(photo_url: str, proxy_base: str = None) -> Optional[bytes]:
    """Legacy proxy method - fallback to direct fetch"""
    return fetch_photo_directly(photo_url)

def check_safety_violations(employee_name: str, proxy_base: str = "https://raffle-randomizer-production.up.railway.app") -> dict:
    """Check if employee has safety violations via Railway proxy"""
    try:
        safety_url = f"{proxy_base}/safety-check?employee_name={employee_name}"
        
        with st.spinner(f"🔍 Checking safety record for {employee_name}..."):
            response = requests.get(safety_url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                st.error(f"❌ Safety check failed (HTTP {response.status_code})")
                return {
                    "employee_name": employee_name,
                    "is_eligible": None,
                    "reason": f"Safety check API failed: HTTP {response.status_code}"
                }
                
    except Exception as e:
        st.error(f"❌ Safety check error: {str(e)}")
        return {
            "employee_name": employee_name,
            "is_eligible": None,
            "reason": f"Safety check error: {str(e)}"
        }

def draw_winner_card(name: str, location: str, level: str, photo_bytes: Optional[bytes]) -> Image.Image:
    """Create winner card with proper photo rendering - LANDSCAPE with ROTATED PHOTO"""
    W, H = 1200, 675  # Back to landscape orientation
    img = Image.new("RGB", (W, H), (20, 24, 28))
    d = ImageDraw.Draw(img)

    # Try to load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        title_font = name_font = info_font = ImageFont.load_default()

    # Header gradient - back to horizontal for landscape
    header_colors = [(255, 107, 107), (78, 205, 196), (69, 183, 209)]
    for i in range(120):  # Back to original header height
        color_ratio = i / 120
        if color_ratio < 0.5:
            ratio = color_ratio * 2
            r = int(header_colors[0][0] * (1 - ratio) + header_colors[1][0] * ratio)
            g = int(header_colors[0][1] * (1 - ratio) + header_colors[1][1] * ratio)
            b = int(header_colors[0][2] * (1 - ratio) + header_colors[1][2] * ratio)
        else:
            ratio = (color_ratio - 0.5) * 2
            r = int(header_colors[1][0] * (1 - ratio) + header_colors[2][0] * ratio)
            g = int(header_colors[1][1] * (1 - ratio) + header_colors[2][1] * ratio)
            b = int(header_colors[1][2] * (1 - ratio) + header_colors[2][2] * ratio)
        d.rectangle([(0, i), (W, i+1)], fill=(r, g, b))

    # Title - back to single line for landscape
    title_text = "GREAT SAVE RAFFLE — WINNER!"
    title_bbox = d.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (W - title_width) // 2
    d.text((title_x + 2, 32), title_text, fill=(0, 0, 0, 128), font=title_font)
    d.text((title_x, 30), title_text, fill="white", font=title_font)
    
    # Date
    date_text = f"MVN {time.strftime('%B %d, %Y')}"
    date_bbox = d.textbbox((0, 0), date_text, font=info_font)
    date_width = date_bbox[2] - date_bbox[0]
    d.text(((W - date_width) // 2, 85), date_text, fill="white", font=info_font)

    # Photo box - back to left side for landscape layout
    box = (50, 150, 350, 450)
    d.rounded_rectangle(box, radius=15, fill=(50, 50, 50), outline=(100, 100, 100), width=3)
    inner_box = (box[0]+4, box[1]+4, box[2]-4, box[3]-4)
    d.rounded_rectangle(inner_box, radius=12, outline=(90, 90, 90), width=2)
    
    # PHOTO PROCESSING - with 90 degree clockwise rotation
    if photo_bytes:
        try:
            p = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
            
            # ROTATE PHOTO 90 DEGREES CLOCKWISE
            p = p.rotate(-90, expand=True)  # -90 degrees = clockwise rotation
            
            # Calculate scaling to fit the box
            bw, bh = inner_box[2] - inner_box[0], inner_box[3] - inner_box[1]
            scale = min(bw / p.width, bh / p.height)
            new_size = (int(p.width * scale), int(p.height * scale))
            p = p.resize(new_size, Image.Resampling.LANCZOS)
            
            # Center the image in the box
            x_offset = (bw - new_size[0]) // 2
            y_offset = (bh - new_size[1]) // 2
            img.paste(p, (inner_box[0] + x_offset, inner_box[1] + y_offset))
            
        except Exception as e:
            d.text((inner_box[0] + 20, inner_box[1] + 20), f"📷 Photo error", fill=(200, 200, 200), font=info_font)
    else:
        d.text((inner_box[0] + 20, inner_box[1] + 20), "📷 No photo available", fill=(200, 200, 200), font=info_font)

    # Winner info - back to right side for landscape layout
    name = (name or "").strip() or "(name missing)"
    location = (location or "").strip() or "(location missing)"
    level = (level or "").strip() or "(level missing)"

    info_x = 400  # Right side of the card
    info_start_y = 180  # Same level as photo

    # Name
    d.text((info_x, info_start_y), "WINNER:", fill="white", font=name_font)
    d.text((info_x, info_start_y + 45), name, fill=(255, 215, 0), font=name_font)
    
    # Location  
    d.text((info_x, info_start_y + 110), "LOCATION:", fill="white", font=info_font)
    d.text((info_x, info_start_y + 140), location, fill=(100, 200, 255), font=info_font)
    
    # Level
    d.text((info_x, info_start_y + 190), "LEVEL:", fill="white", font=info_font)
    d.text((info_x, info_start_y + 220), level, fill=(255, 150, 150), font=info_font)

    return img

def create_analytics_dashboard(df: pd.DataFrame):
    """Create comprehensive analytics dashboard with charts and insights"""
    
    # Use the exact column names from the CSV
    name_col = "Name of employee that earned the Great Save Raffle ticket?"
    location_col = "What MVN location does employee work at?"
    level_col = "What level of ticket was earned?"
    photo_col = "Photo of the employee holding the ticket. (Will be used if drawn))"
    
    st.header("📊 Raffle Analytics Dashboard")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Participants", 
            len(df),
            delta=f"100% Eligible"
        )
    
    with col2:
        locations = df[location_col].nunique() if location_col in df.columns else 0
        st.metric(
            "Locations", 
            locations,
            delta="🏢 Offices"
        )
    
    with col3:
        levels = df[level_col].nunique() if level_col in df.columns else 0
        st.metric(
            "Ticket Levels", 
            levels,
            delta="🎫 Types"
        )
    
    with col4:
        photos = df[photo_col].notna().sum() if photo_col in df.columns else 0
        photo_rate = (photos / len(df)) * 100 if len(df) > 0 else 0
        st.metric(
            "Photo Coverage", 
            f"{photo_rate:.1f}%",
            delta=f"{photos} photos"
        )
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    # Location Distribution Chart
    with col1:
        if location_col in df.columns:
            st.subheader("🏢 Location Distribution")
            location_counts = df[location_col].value_counts()
            
            # Create pie chart
            fig_pie = px.pie(
                values=location_counts.values,
                names=location_counts.index,
                title="Participants by Location",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Location stats table
            st.subheader("📍 Location Breakdown")
            location_df = pd.DataFrame({
                'Location': location_counts.index,
                'Participants': location_counts.values,
                'Percentage': [f"{(count/len(df)*100):.1f}%" for count in location_counts.values]
            })
            st.dataframe(location_df, use_container_width=True)
    
    # Ticket Level Distribution Chart
    with col2:
        if level_col in df.columns:
            st.subheader("🎫 Ticket Level Distribution")
            level_counts = df[level_col].value_counts()
            
            # Create bar chart
            fig_bar = px.bar(
                x=level_counts.index,
                y=level_counts.values,
                title="Participants by Ticket Level",
                labels={'x': 'Ticket Level', 'y': 'Number of Participants'},
                color=level_counts.values,
                color_continuous_scale='viridis'
            )
            fig_bar.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Level stats table
            st.subheader("🎟️ Level Breakdown")
            level_df = pd.DataFrame({
                'Ticket Level': level_counts.index,
                'Participants': level_counts.values,
                'Percentage': [f"{(count/len(df)*100):.1f}%" for count in level_counts.values]
            })
            st.dataframe(level_df, use_container_width=True)
    
    st.markdown("---")
    
    # Combined Analysis
    if location_col in df.columns and level_col in df.columns:
        st.subheader("🔍 Cross-Analysis: Location vs Ticket Level")
        
        # Create heatmap
        cross_table = pd.crosstab(df[location_col], df[level_col], margins=True)
        
        # Remove margins for the heatmap
        heatmap_data = cross_table.iloc[:-1, :-1]
        
        fig_heatmap = px.imshow(
            heatmap_data.values,
            labels=dict(x="Ticket Level", y="Location", color="Count"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale='Blues',
            title="Participant Distribution: Location vs Ticket Level"
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Cross-tabulation table
        st.subheader("📋 Detailed Cross-Tabulation")
        st.dataframe(cross_table, use_container_width=True)
    
    st.markdown("---")
    
    # Photo Analysis
    if photo_col in df.columns:
        st.subheader("📸 Photo Coverage Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Photo availability by location
            if location_col in df.columns:
                photo_by_location = df.groupby(location_col)[photo_col].apply(lambda x: x.notna().sum()).reset_index()
                photo_by_location['Total'] = df.groupby(location_col).size().values
                photo_by_location['Coverage %'] = (photo_by_location[photo_col] / photo_by_location['Total'] * 100).round(1)
                
                fig_photo = px.bar(
                    photo_by_location,
                    x=location_col,
                    y='Coverage %',
                    title="Photo Coverage by Location",
                    labels={'Coverage %': 'Photo Coverage (%)'},
                    color='Coverage %',
                    color_continuous_scale='greens'
                )
                fig_photo.update_layout(height=400)
                st.plotly_chart(fig_photo, use_container_width=True)
        
        with col2:
            # Photo availability by ticket level
            if level_col in df.columns:
                photo_by_level = df.groupby(level_col)[photo_col].apply(lambda x: x.notna().sum()).reset_index()
                photo_by_level['Total'] = df.groupby(level_col).size().values
                photo_by_level['Coverage %'] = (photo_by_level[photo_col] / photo_by_level['Total'] * 100).round(1)
                
                fig_photo_level = px.bar(
                    photo_by_level,
                    x=level_col,
                    y='Coverage %',
                    title="Photo Coverage by Ticket Level",
                    labels={'Coverage %': 'Photo Coverage (%)'},
                    color='Coverage %',
                    color_continuous_scale='oranges'
                )
                fig_photo_level.update_layout(height=400)
                st.plotly_chart(fig_photo_level, use_container_width=True)
    
    st.markdown("---")
    
    # Winner Simulation
    st.subheader("🎲 Winner Probability Simulation")
    st.info("This shows the theoretical probability of winning based on current data distribution.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if location_col in df.columns:
            location_probs = (df[location_col].value_counts() / len(df) * 100).round(2)
            st.write("**🏢 Winning Probability by Location:**")
            for location, prob in location_probs.items():
                st.write(f"• {location}: {prob}%")
    
    with col2:
        if level_col in df.columns:
            level_probs = (df[level_col].value_counts() / len(df) * 100).round(2)
            st.write("**🎫 Winning Probability by Ticket Level:**")
            for level, prob in level_probs.items():
                st.write(f"• {level}: {prob}%")
    
    # Data Quality Report
    st.markdown("---")
    st.subheader("🔍 Data Quality Report")
    
    quality_data = []
    for col in [name_col, location_col, level_col, photo_col]:
        if col in df.columns:
            missing = df[col].isna().sum()
            missing_pct = (missing / len(df)) * 100
            quality_data.append({
                'Field': col.replace('What ', '').replace('Name of employee that earned the Great Save Raffle ticket?', 'Employee Name'),
                'Complete': len(df) - missing,
                'Missing': missing,
                'Completeness': f"{100 - missing_pct:.1f}%"
            })
    
    if quality_data:
        quality_df = pd.DataFrame(quality_data)
        st.dataframe(quality_df, use_container_width=True)

def main():
    # Title with perfectly aligned MVN logos
    st.markdown("""
    <style>
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px 0;
        margin-bottom: 20px;
    }
    .title-text {
        font-size: 3.8rem;
        font-weight: bold;
        color: #1f77b4;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin: 0 40px;
        text-align: center;
        line-height: 1.1;
    }
    .subtitle {
        text-align: center;
        font-size: 1.5rem;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Single centered logo above title - moved right for better alignment
    # Use margin offset to move logo to the right
    try:
        # Use columns with unequal spacing to shift logo right
        col1, col2, col3 = st.columns([2.75, 2, 1.25])
                
        with col2:
            st.image("Moon Valley Logo.png", width=150)
    except:
        st.markdown('<div style="text-align: center; font-size: 5rem; color: #cc0000; margin: 20px 0 20px 80px;">🏢</div>', unsafe_allow_html=True)
    
    # Centered title below logo with RED color to match logo
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <h1 style="
            font-size: 4rem; 
            font-weight: bold; 
            color: #cc0000; 
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            line-height: 1.1;
        ">
            MVN Great Save Raffle
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="subtitle">🎊 Pick your winner and celebrate! 🎊</div>', unsafe_allow_html=True)
    
    # Data source selection
    st.markdown("### 📊 Data Source")
    data_source = st.radio(
        "Choose your data source:",
        ["📁 Upload CSV File", "🔗 Load from KPA API"],
        horizontal=True
    )
    
    df = None
    
    if data_source == "📁 Upload CSV File":
        # File upload
        uploaded_file = st.file_uploader("📁 Upload CSV File", type=['csv'])
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Successfully loaded {len(df)} participants!")
            
            # Use the exact long column names from the CSV
            name_col = "Name of employee that earned the Great Save Raffle ticket?"
            location_col = "What MVN location does employee work at?"
            level_col = "What level of ticket was earned?"
            photo_col = "Photo of the employee holding the ticket. (Will be used if drawn))"
            
            # Check if we have the expected columns
            expected_columns = [name_col, location_col, level_col, photo_col]
            missing_cols = [col for col in expected_columns if col not in df.columns]
            
            if missing_cols:
                st.warning(f"⚠️ Missing expected columns: {len(missing_cols)} out of {len(expected_columns)}")
                st.subheader("Available columns in your CSV:")
                st.write(list(df.columns))
            else:
                st.info("✅ All expected columns found!")
    
    elif data_source == "🔗 Load from KPA API":
        # KPA API integration
        st.markdown("### 🎫 Great Save Raffle - KPA API")
        
        with st.spinner("🔄 Loading participants from KPA API..."):
            kpa_manager = KPARaffleManager()
            participants = kpa_manager.fetch_all_participants()
        
        if participants:
            st.success(f"✅ Successfully loaded {len(participants)} participants from KPA API!")
            
            # Create filter controls
            col1, col2 = st.columns(2)
            
            with col1:
                # State filter
                available_states = kpa_manager.get_available_states(participants)
                state_options = ['all'] + available_states
                selected_state = st.selectbox(
                    "🗺️ Filter by State:",
                    state_options,
                    format_func=lambda x: f"All States ({len([p for p in participants if x == 'all' or p['state'] == x])})" if x == 'all' else f"{x} ({len([p for p in participants if p['state'] == x])})"
                )
            
            with col2:
                # Prize level filter
                available_levels = kpa_manager.get_available_levels(participants)
                level_options = ['all'] + available_levels
                level_labels = {
                    'all': 'All Levels',
                    'red': '🔴 Red (Monthly)',
                    'green': '🟢 Green (Quarterly)', 
                    'gold': '🟡 Gold (Annual)'
                }
                selected_level = st.selectbox(
                    "🏆 Filter by Prize Level:",
                    level_options,
                    format_func=lambda x: f"{level_labels.get(x, x)} ({len([p for p in participants if x == 'all' or p['level_category'] == x])})"
                )
            
            # Apply filters
            filtered_participants = kpa_manager.filter_participants(
                participants, 
                state_filter=selected_state if selected_state != 'all' else None,
                level_filter=selected_level if selected_level != 'all' else None
            )
            
            if filtered_participants:
                st.info(f"� Filtered results: {len(filtered_participants)} participants")
                
                # Convert to DataFrame format for compatibility with existing code
                df_data = []
                for p in filtered_participants:
                    df_data.append({
                        "Name of employee that earned the Great Save Raffle ticket?": p['name'],
                        "What MVN location does employee work at?": p['location'],
                        "What level of ticket was earned?": p['prize_level'],
                        "Photo of the employee holding the ticket. (Will be used if drawn))": p['photo_url'],
                        "State": p['state'],
                        "Level Category": p['level_category'],
                        "Serial Number": p['serial_number']
                    })
                
                df = pd.DataFrame(df_data)
                
                # Set column mappings for compatibility
                name_col = "Name of employee that earned the Great Save Raffle ticket?"
                location_col = "What MVN location does employee work at?"
                level_col = "What level of ticket was earned?"
                photo_col = "Photo of the employee holding the ticket. (Will be used if drawn))"
            else:
                st.warning("❌ No participants match the selected filters.")
        else:
            st.error("❌ Failed to load participants from KPA API.")
    
    # Only show tabs if we have data
    if df is not None and len(df) > 0:
        # Create tabs
        tab1, tab2 = st.tabs(["� Roulette Wheel", "📊 Analytics Dashboard"])
        
        with tab1:
            # Show data preview
            st.subheader("👀 Data Preview")
            st.dataframe(df.head())
            
            # Winner selection
            st.subheader("🎰 Pick Your Winner!")
            
            # Options row
            col1, col2 = st.columns(2)
            with col1:
                use_proxy = st.checkbox("🔗 Use KPA Proxy Server (recommended)", value=True)
            with col2:
                use_safety_check = st.checkbox("🛡️ Check Safety Violations (Response ID 244699)", value=False)
            
            if use_safety_check:
                st.info("ℹ️ Safety check will verify winner has no safety violations before final confirmation.")
            
            if st.button("� Spin the Wheel!", type="primary"):
                # 🎊 CELEBRATORY EFFECTS! 🎊
                st.balloons()
                
                # Create roulette wheel with participant names
                participant_names = df[name_col].tolist()
                winner_idx = random.randint(0, len(participant_names) - 1)
                winner_name = participant_names[winner_idx]
                
                # 🎰 FULL-SCREEN ROULETTE WHEEL ANIMATION! 🎰
                wheel_placeholder = st.empty()
                
                # Generate roulette wheel HTML
                wheel_html = f"""
                <style>
                .roulette-container {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: linear-gradient(135deg, #0f1419, #1a2332);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 9999;
                    font-family: 'Arial', sans-serif;
                }}
                
                .wheel-wrapper {{
                    position: relative;
                    width: 80vmin;
                    height: 80vmin;
                }}
                
                .roulette-wheel {{
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    border: 15px solid #8B4513;
                    position: relative;
                    animation: spin 4s cubic-bezier(0.17, 0.67, 0.12, 0.99) forwards;
                    box-shadow: 0 0 40px rgba(0, 0, 0, 0.8), inset 0 0 30px rgba(139, 69, 19, 0.3);
                    background: conic-gradient(
                        #8B0000 0deg 9.47deg,
                        #000000 9.47deg 18.95deg,
                        #8B0000 18.95deg 28.42deg,
                        #000000 28.42deg 37.89deg,
                        #8B0000 37.89deg 47.37deg,
                        #000000 47.37deg 56.84deg,
                        #8B0000 56.84deg 66.32deg,
                        #000000 66.32deg 75.79deg,
                        #8B0000 75.79deg 85.26deg,
                        #000000 85.26deg 94.74deg,
                        #8B0000 94.74deg 104.21deg,
                        #000000 104.21deg 113.68deg,
                        #8B0000 113.68deg 123.16deg,
                        #000000 123.16deg 132.63deg,
                        #8B0000 132.63deg 142.11deg,
                        #000000 142.11deg 151.58deg,
                        #8B0000 151.58deg 161.05deg,
                        #000000 161.05deg 170.53deg,
                        #8B0000 170.53deg 180deg,
                        #000000 180deg 189.47deg,
                        #8B0000 189.47deg 198.95deg,
                        #000000 198.95deg 208.42deg,
                        #8B0000 208.42deg 217.89deg,
                        #000000 217.89deg 227.37deg,
                        #8B0000 227.37deg 236.84deg,
                        #000000 236.84deg 246.32deg,
                        #8B0000 246.32deg 255.79deg,
                        #000000 255.79deg 265.26deg,
                        #8B0000 265.26deg 274.74deg,
                        #000000 274.74deg 284.21deg,
                        #8B0000 284.21deg 293.68deg,
                        #000000 293.68deg 303.16deg,
                        #8B0000 303.16deg 312.63deg,
                        #000000 312.63deg 322.11deg,
                        #8B0000 322.11deg 331.58deg,
                        #000000 331.58deg 341.05deg,
                        #8B0000 341.05deg 350.53deg,
                        #000000 350.53deg 360deg
                    );
                }}
                
                .wheel-center {{
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 120px;
                    height: 120px;
                    background: radial-gradient(circle, #FFD700, #B8860B);
                    border-radius: 50%;
                    border: 6px solid #8B4513;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 48px;
                    z-index: 100;
                    box-shadow: 0 0 20px rgba(0, 0, 0, 0.6);
                }}
                
                .wheel-pointer {{
                    position: absolute;
                    top: -35px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 0;
                    height: 0;
                    border-left: 35px solid transparent;
                    border-right: 35px solid transparent;
                    border-top: 70px solid #ff4444;
                    z-index: 10000;
                    filter: drop-shadow(0 8px 16px rgba(0,0,0,0.7));
                }}
                
                .winner-announcement {{
                    position: absolute;
                    bottom: 80px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(255, 255, 255, 0.98);
                    padding: 30px 60px;
                    border-radius: 25px;
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #8B0000;
                    text-align: center;
                    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
                    animation: fadeInUp 1s ease-out 4.5s both;
                    border: 4px solid #FFD700;
                }}
                
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate({3600 + random.randint(0, 360)}deg); }}
                }}
                
                @keyframes fadeInUp {{
                    0% {{ opacity: 0; transform: translateX(-50%) translateY(50px); }}
                    100% {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
                }}
                
                .moon-celebration {{
                    position: absolute;
                    font-size: 4rem;
                    animation: moonFloat 2s ease-in-out infinite;
                    z-index: 50;
                }}
                
                @keyframes moonFloat {{
                    0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
                    50% {{ transform: translateY(-30px) rotate(180deg); }}
                }}
                </style>
                
                <div class="roulette-container">
                    <div class="wheel-wrapper">
                        <div class="wheel-pointer"></div>
                        <div class="roulette-wheel">
                            <div class="wheel-center">🌙</div>
                        </div>
                        <div class="winner-announcement">
                            🏆 WINNER: {winner_name}! 🏆
                        </div>
                        <div class="moon-celebration" style="top: 10%; left: 10%;">🌙</div>
                        <div class="moon-celebration" style="top: 15%; right: 10%; animation-delay: 0.5s;">🌛</div>
                        <div class="moon-celebration" style="bottom: 10%; left: 15%; animation-delay: 1s;">🌜</div>
                        <div class="moon-celebration" style="bottom: 15%; right: 15%; animation-delay: 1.5s;">🌙</div>
                    </div>
                </div>
                
                <script>
                setTimeout(() => {{
                    document.querySelector('.roulette-container').style.display = 'none';
                }}, 8000);
                </script>
                """
                
                wheel_placeholder.markdown(wheel_html, unsafe_allow_html=True)
                
                # Wait for wheel animation to complete
                time.sleep(8)
                wheel_placeholder.empty()
                
                # � WINNER ANNOUNCEMENT WITH MOON CELEBRATION! �
                # Beautiful falling moon snowflakes animation
                st.markdown("""
                <style>
                .moon-fall {
                    position: fixed;
                    top: -50px;
                    z-index: 1000;
                    pointer-events: none;
                    font-size: 35px;
                    animation: fall linear infinite;
                }
                
                @keyframes fall {
                    0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
                    100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
                }
                
                .moon-fall:nth-child(1) { left: 5%; animation-duration: 3s; animation-delay: 0s; }
                .moon-fall:nth-child(2) { left: 15%; animation-duration: 3.5s; animation-delay: 0.3s; }
                .moon-fall:nth-child(3) { left: 25%; animation-duration: 4s; animation-delay: 0.6s; }
                .moon-fall:nth-child(4) { left: 35%; animation-duration: 3.2s; animation-delay: 0.9s; }
                .moon-fall:nth-child(5) { left: 45%; animation-duration: 3.8s; animation-delay: 1.2s; }
                .moon-fall:nth-child(6) { left: 55%; animation-duration: 3.3s; animation-delay: 0.2s; }
                .moon-fall:nth-child(7) { left: 65%; animation-duration: 4.2s; animation-delay: 0.5s; }
                .moon-fall:nth-child(8) { left: 75%; animation-duration: 3.6s; animation-delay: 0.8s; }
                .moon-fall:nth-child(9) { left: 85%; animation-duration: 3.9s; animation-delay: 1.1s; }
                .moon-fall:nth-child(10) { left: 95%; animation-duration: 3.4s; animation-delay: 1.4s; }
                .moon-fall:nth-child(11) { left: 10%; animation-duration: 4.1s; animation-delay: 1.7s; }
                .moon-fall:nth-child(12) { left: 20%; animation-duration: 3.7s; animation-delay: 2.0s; }
                .moon-fall:nth-child(13) { left: 30%; animation-duration: 3.1s; animation-delay: 2.3s; }
                .moon-fall:nth-child(14) { left: 40%; animation-duration: 4.3s; animation-delay: 2.6s; }
                .moon-fall:nth-child(15) { left: 50%; animation-duration: 3.9s; animation-delay: 2.9s; }
                </style>
                
                <div class="moon-fall">🌙</div>
                <div class="moon-fall">🌛</div>
                <div class="moon-fall">🌜</div>
                <div class="moon-fall">🌙</div>
                <div class="moon-fall">🌛</div>
                <div class="moon-fall">🌜</div>
                <div class="moon-fall">🌙</div>
                <div class="moon-fall">🌛</div>
                <div class="moon-fall">🌜</div>
                <div class="moon-fall">🌙</div>
                <div class="moon-fall">🌛</div>
                <div class="moon-fall">🌜</div>
                <div class="moon-fall">🌙</div>
                <div class="moon-fall">🌛</div>
                <div class="moon-fall">🌜</div>
                
                <script>
                // Sound effects simulation
                function playWinnerSounds() {
                    // Create audio context for sound effects
                    try {
                        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        
                        // Celebration fanfare
                        function playBeep(frequency, duration, delay = 0) {
                            setTimeout(() => {
                                const oscillator = audioContext.createOscillator();
                                const gainNode = audioContext.createGain();
                                
                                oscillator.connect(gainNode);
                                gainNode.connect(audioContext.destination);
                                
                                oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
                                oscillator.type = 'sine';
                                
                                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
                                
                                oscillator.start(audioContext.currentTime);
                                oscillator.stop(audioContext.currentTime + duration);
                            }, delay);
                        }
                        
                        // Play celebration melody
                        playBeep(523, 0.3, 0);    // C
                        playBeep(659, 0.3, 300);  // E  
                        playBeep(784, 0.3, 600);  // G
                        playBeep(1047, 0.5, 900); // High C
                        
                        console.log("🎉 WINNER SELECTED! 🎉");
                        console.log("🔊 Playing celebration sounds!");
                    } catch (e) {
                        console.log("🎉 WINNER SELECTED! 🎉");
                        console.log("🔇 Audio not available in this environment");
                    }
                }
                
                playWinnerSounds();
                
                // Clean up moon effects after 6 seconds
                setTimeout(() => {
                    document.querySelectorAll('.moon-fall').forEach(el => el.remove());
                }, 6000);
                </script>
                """, unsafe_allow_html=True)
                
                # 🎯 USE WINNER FROM ROULETTE WHEEL! 🎯
                winner = df.iloc[winner_idx]
                
                # Extract winner info
                name = str(winner.get(name_col, "")).strip() if name_col in winner.index else "Unknown"
                location = str(winner.get(location_col, "")).strip() if location_col in winner.index else "Unknown"
                level = str(winner.get(level_col, "")).strip() if level_col in winner.index else "Unknown"
                photo_field = str(winner.get(photo_col, "")).strip() if photo_col in winner.index else ""
                
                st.success(f"🏆 WINNER: {name}! 🏆")
                
                # Safety check if enabled
                safety_eligible = True
                safety_message = ""
                
                if use_safety_check:
                    with st.spinner("🛡️ Performing safety violation check..."):
                        try:
                            safety_checker = KPASafetyChecker()
                            safety_result = safety_checker.check_winner_eligibility(name)
                            
                            if safety_result.get('found_in_kpa', False):
                                violations_count = safety_result.get('violations_found', 0)
                                if violations_count > 0:
                                    safety_eligible = False
                                    safety_message = f"❌ Safety Check Failed: {violations_count} violation(s) found (Response ID 244699)"
                                    st.error(safety_message)
                                    st.warning("🔄 This winner is not eligible. Please select another winner.")
                                    
                                    # Show violation details
                                    with st.expander("📋 View Safety Violation Details"):
                                        st.json(safety_result)
                                else:
                                    safety_message = f"✅ Safety Check Passed: Employee '{name}' found in KPA with no violations"
                                    st.success(safety_message)
                            else:
                                safety_message = f"⚠️ Safety Check: Employee '{name}' not found in KPA system"
                                st.warning(safety_message)
                                st.info("💡 This could be due to name spelling differences or employee not yet in KPA. Winner can proceed.")
                                
                        except Exception as e:
                            safety_message = f"❌ Safety Check Error: {str(e)}"
                            st.error(safety_message)
                            st.info("Proceeding without safety check due to error.")
                
                # Celebratory sound effect simulation
                st.markdown("### 🎺🎺🎺 CONGRATULATIONS! 🎺🎺🎺")
                
                # Display winner info with celebration
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🌟 Winner", name, delta="SELECTED!")
                with col2:
                    st.metric("🏢 Location", location, delta="🎯")
                with col3:
                    st.metric("🎫 Ticket Level", level, delta="🎊")
                with col4:
                    if use_safety_check:
                        safety_status = "✅ ELIGIBLE" if safety_eligible else "❌ NOT ELIGIBLE"
                        safety_delta = "Safe" if safety_eligible else "Violations"
                        st.metric("🛡️ Safety Check", safety_status, delta=safety_delta)
                    else:
                        st.metric("🛡️ Safety Check", "SKIPPED", delta="Not Checked")
                    
                st.info(f"📊 Selected from row {winner_idx + 1} of {len(df)} participants")
                
                # Only proceed with photo and card generation if safety eligible (or safety check disabled)
                if safety_eligible:
                    # Fetch photo (keeping all the proxy functionality UNCHANGED)
                    photo_bytes = None
                    if use_proxy and photo_field:
                        photo_bytes = fetch_photo_via_proxy(photo_field)
                    elif photo_field:
                        st.info("📸 Proxy disabled - skipping photo")
                    else:
                        st.warning("📸 No photo URL provided")
                        
                    # Generate winner card
                    with st.spinner("🎨 Creating winner card..."):
                        card = draw_winner_card(name=name, location=location, level=level, photo_bytes=photo_bytes)
                        
                    st.markdown("### 🎊 Winner Card Generated!")
                    st.image(card, caption=f"🏆 Winner: {name}", use_container_width=True)
                    
                    # More celebration!
                    st.markdown("---")
                    st.markdown("### 🎉 SHARE THE CELEBRATION! 🎉")
                    st.info("Right-click the winner card above to save and share!")
                    
                    # Confetti effect with emojis
                    st.markdown("🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊")
                else:
                    st.markdown("---")
                    st.error("🚫 Winner card not generated due to safety violations. Please select another winner.")
                    st.info("💡 Click 'Random Selection' again to pick a new winner.")
                
                # Show safety message if any
                if safety_message:
                    st.markdown("---")
                    st.markdown(f"**Safety Check Result:** {safety_message}")
        
        with tab2:
            # Analytics Dashboard
            create_analytics_dashboard(df)
            # 🎊 CELEBRATORY EFFECTS! 🎊
            st.balloons()
            
            # 🕐 DRAMATIC 5-SECOND COUNTDOWN! 🕐
            countdown_placeholder = st.empty()
            beep_placeholder = st.empty()
            
            for i in range(5, 0, -1):
                # Big pulsating countdown number
                countdown_placeholder.markdown(f"""
                <div style="
                    text-align: center; 
                    font-size: 8rem; 
                    font-weight: bold; 
                    color: #ff4b4b;
                    text-shadow: 0 0 20px #ff4b4b;
                    animation: pulse 0.5s ease-in-out;
                    margin: 2rem 0;
                ">
                    {i}
                </div>
                <style>
                @keyframes pulse {{
                    0% {{ transform: scale(1); opacity: 0.7; }}
                    50% {{ transform: scale(1.2); opacity: 1; }}
                    100% {{ transform: scale(1); opacity: 0.7; }}
                }}
                </style>
                """, unsafe_allow_html=True)
                
                # Beep sound simulation with visual indicator
                beep_placeholder.markdown(f"""
                <div style="
                    text-align: center; 
                    font-size: 2rem; 
                    color: #ffd700;
                    margin: 1rem 0;
                ">
                    🔊 BEEP! 🔊
                </div>
                """, unsafe_allow_html=True)
                
                time.sleep(1)
                beep_placeholder.empty()
            
            # Clear countdown
            countdown_placeholder.empty()
            
            # WINNER REVEAL WITH FANFARE!
            st.markdown("""
            <div style="
                text-align: center; 
                font-size: 4rem; 
                font-weight: bold; 
                color: #00ff00;
                text-shadow: 0 0 30px #00ff00;
                animation: winner-reveal 2s ease-in-out;
                margin: 2rem 0;
            ">
                🎊 WINNER SELECTED! 🎊
            </div>
            <style>
            @keyframes winner-reveal {
                0% { transform: scale(0); opacity: 0; }
                50% { transform: scale(1.3); opacity: 0.8; }
                100% { transform: scale(1); opacity: 1; }
            }
            </style>
            """, unsafe_allow_html=True)
            
            winner_idx = random.randint(0, len(df) - 1)
            winner = df.iloc[winner_idx]
            
            # Use the exact long column names
            name = str(winner.get(name_col, "")).strip() or "Unknown Employee"
            location = str(winner.get(location_col, "")).strip() or "Unknown Location"
            level = str(winner.get(level_col, "")).strip() or "Unknown Level"
            photo_field = str(winner.get(photo_col, "")).strip()
            
            # 🎉 WINNER ANNOUNCEMENT WITH CELEBRATIONS! 🎉
            st.balloons()
            
            # Add some visual celebration elements
            st.markdown("""
            <div style="text-align: center; font-size: 3rem; animation: pulse 1s infinite;">
                🏆 🎊 🎉 WINNER! 🎉 🎊 🏆
            </div>
            <style>
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            </style>
            <script>
            // Simple celebration sound using Web Audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const playCheer = () => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
                oscillator.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E5
                oscillator.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G5
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.5);
            };
            playCheer();
            </script>
            """, unsafe_allow_html=True)
            
            st.success(f"🏆 WINNER: {name}! 🏆")
            
            # Celebratory sound effect simulation
            st.markdown("### 🎺🎺🎺 CONGRATULATIONS! 🎺🎺🎺")
            
            # Display winner info with celebration
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌟 Winner", name, delta="SELECTED!")
            with col2:
                st.metric("🏢 Location", location, delta="🎯")
            with col3:
                st.metric("🎫 Ticket Level", level, delta="🎊")
                
            st.info(f"📊 Selected from row {winner_idx + 1} of {len(df)} participants")
            
            # Fetch photo (keeping all the proxy functionality)
            photo_bytes = None
            if use_proxy and photo_field:
                photo_bytes = fetch_photo_via_proxy(photo_field)
            elif photo_field:
                st.info("📸 Proxy disabled - skipping photo")
            else:
                st.warning("📸 No photo URL provided")
                
            # Generate winner card
            with st.spinner("🎨 Creating winner card..."):
                card = draw_winner_card(name=name, location=location, level=level, photo_bytes=photo_bytes)
                
            st.markdown("### 🎊 Winner Card Generated!")
            st.image(card, caption=f"🏆 Winner: {name}", use_container_width=True)
            
            # More celebration!
            st.markdown("---")
            st.markdown("### 🎉 SHARE THE CELEBRATION! 🎉")
            st.info("Right-click the winner card above to save and share!")
            
            # Confetti effect with emojis
            st.markdown("🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊")
            
if __name__ == "__main__":
    main()

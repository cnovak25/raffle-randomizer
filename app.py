import os, io, time, random, requests, pandas as pd, streamlit as st
from urllib.parse import urlparse, parse_qs, unquote
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
from datetime import datetime
import base64
from typing import Optional

# Configure page for mobile-first responsive design
st.set_page_config(
    page_title="🎉 MVN Great Save Raffle 🎉",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def fetch_photo_via_proxy(photo_url: str, proxy_base: str = "http://localhost:8000") -> Optional[bytes]:
    """Fetch photo via KPA proxy server"""
    if not photo_url or "get-upload" not in photo_url:
        return None
    
    try:
        # Extract the 'key' parameter from the KPA URL
        if "key=" in photo_url:
            key = photo_url.split("key=")[1].split("&")[0]
            proxy_url = f"{proxy_base}/kpa-photo?key={key}"
            
            with st.spinner("� Loading winner photo..."):
                response = requests.get(proxy_url, timeout=30)
                if response.status_code == 200:
                    photo_data = response.content
                    st.success("✅ Photo loaded successfully!")
                    return photo_data
                else:
                    st.error(f"❌ Could not load photo (HTTP {response.status_code})")
                    return None
        else:
            st.error("❌ Invalid photo URL format")
            return None
            
    except Exception as e:
        st.error(f"❌ Photo loading failed: {str(e)}")
        return None

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
    title_text = "🏆 GREAT SAVE RAFFLE — WINNER! 🏆"
    title_bbox = d.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (W - title_width) // 2
    d.text((title_x + 2, 32), title_text, fill=(0, 0, 0, 128), font=title_font)
    d.text((title_x, 30), title_text, fill="white", font=title_font)
    
    # Date
    date_text = f"🎉 MVN {time.strftime('%B %d, %Y')} 🎉"
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
    d.text((info_x, info_start_y), "🌟 WINNER:", fill="white", font=name_font)
    d.text((info_x, info_start_y + 45), name, fill=(255, 215, 0), font=name_font)
    
    # Location  
    d.text((info_x, info_start_y + 110), "🏢 LOCATION:", fill="white", font=info_font)
    d.text((info_x, info_start_y + 140), location, fill=(100, 200, 255), font=info_font)
    
    # Level
    d.text((info_x, info_start_y + 190), "🎫 LEVEL:", fill="white", font=info_font)
    d.text((info_x, info_start_y + 220), level, fill=(255, 150, 150), font=info_font)

    return img

def main():
    st.title("🎯 MVN Great Save Raffle")
    st.markdown("### 🎊 Pick your winner and celebrate! 🎊")
    
    # File upload
    uploaded_file = st.file_uploader("📁 Upload CSV File", type=['csv'])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Successfully loaded {len(df)} participants!")
        
        # Use standard long column names directly - no mapping needed
        expected_columns = {
            'First Name': 'name',
            'Last Name': 'last_name', 
            'Location': 'location',
            'Ticket Level': 'level',
            'Photo': 'photo'
        }
        
        # Check if we have the expected columns
        missing_cols = [col for col in expected_columns.keys() if col not in df.columns]
        if missing_cols:
            st.warning(f"⚠️ Missing expected columns: {missing_cols}")
            st.info("Expected columns: First Name, Last Name, Location, Ticket Level, Photo")
            st.subheader("Available columns in your CSV:")
            st.write(list(df.columns))
        else:
            st.info("✅ All expected columns found!")
        
        # Show data preview
        st.subheader("👀 Data Preview")
        st.dataframe(df.head())
        
        # Winner selection
        st.subheader("🎰 Pick Your Winner!")
        
        # Photo option
        use_proxy = st.checkbox("🔗 Use KPA Proxy Server (recommended)", value=True)
        
        if st.button("🎲 Random Selection", type="primary"):
            # 🎊 CELEBRATORY EFFECTS! 🎊
            st.balloons()
            
            winner_idx = random.randint(0, len(df) - 1)
            winner = df.iloc[winner_idx]
            
            # Use direct column names (combine first and last name)
            first_name = str(winner.get('First Name', "")).strip()
            last_name = str(winner.get('Last Name', "")).strip()
            name = f"{first_name} {last_name}".strip()
            location = str(winner.get('Location', "")).strip()
            level = str(winner.get('Ticket Level', "")).strip()
            photo_field = str(winner.get('Photo', "")).strip()
            
            # 🎉 WINNER ANNOUNCEMENT WITH SNOW! 🎉
            st.snow()
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

import os, io, time, random, requests, pandas as pd, streamlit as st
from urllib.parse import urlparse, parse_qs, unquote
from PIL import Image, ImageDraw, ImageFont
import plotly.graph_objects as go
from datetime import datetime
import base64
from typing import Optional

# BRAND NEW FILE - NO        # Photo option toggle with proxy server
        photo_option = st.radio(
            "📸 Photo Loading Options:",
            [
                "🚫 Skip photos (fastest)",
                "🔗 Use KPA Proxy Server (recommended)",
                "🔐 Try with session cookies (manual)",
                "🌐 Try direct URLs (will fail)"
            ]
        )
        
        session_cookies = ""
        if photo_option == "🔐 Try with session cookies (manual)":
            st.info("💡 **How to get session cookies:**\n1. Login to KPA in another tab\n2. Open Developer Tools (F12)\n3. Go to Application/Storage → Cookies\n4. Copy the session cookie value")
            session_cookies = st.text_input("🍪 Paste KPA session cookie:", type="password")
        elif photo_option == "🔗 Use KPA Proxy Server (recommended)":
            st.info("🚀 **Using FastAPI proxy server** - handles KPA authentication automatically")- PHOTO FIX
st.success("✅ RUNNING FIXED VERSION - NO MORE API ERRORS!")

# Configure page for mobile-first responsive design
st.set_page_config(
    page_title="🎉 MVN Great Save Raffle 🎉",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# MVN Great Save Raffle System"
    }
)

# Constants
API_BASE = "https://api.kpaehs.com/v1"
PHOTO_PROXY_URL = "http://localhost:5001/photo"

# Column definitions for CSV parsing
COL_NAME = "Employee Name"
COL_LOCATION = "Location" 
COL_LEVEL = "Level"
COL_NOMINATOR = "Your Name"
COL_DATE = "Timestamp"
COL_PHOTO = "Photo"

# Load environment variables
KPA_TOKEN = os.getenv("KPA_TOKEN") or os.getenv("KPA_API_TOKEN")

# Simple photo loading function - NO API CALLS
def fetch_photo_via_proxy(photo_url: str, proxy_base: str = "http://localhost:8000") -> Optional[bytes]:
    """Fetch photo via KPA proxy server"""
    if not photo_url or "get-upload" not in photo_url:
        st.warning("⚠️ Invalid KPA photo URL")
        return None
    
    try:
        # Extract the 'key' parameter from the KPA URL
        if "key=" in photo_url:
            key = photo_url.split("key=")[1].split("&")[0]
            proxy_url = f"{proxy_base}/kpa-photo?key={key}"
            
            st.info(f"🔗 Loading via proxy: {proxy_url[:80]}...")
            
            response = requests.get(proxy_url, timeout=30)
            if response.status_code == 200:
                photo_data = response.content
                cache_status = response.headers.get('X-Cache', 'UNKNOWN')
                st.success(f"📸 Photo loaded via proxy! Size: {len(photo_data):,} bytes (Cache: {cache_status})")
                return photo_data
            else:
                st.error(f"❌ Proxy server returned: HTTP {response.status_code}")
                return None
        else:
            st.error("❌ Could not extract key from KPA URL")
            return None
            
    except Exception as e:
        st.error(f"❌ Proxy fetch error: {str(e)}")
        return None

def fetch_photo_with_session(photo_field: str, session_cookies: str) -> Optional[bytes]:
    """Fetch photo using KPA session cookies"""
    if not photo_field or not photo_field.startswith("http"):
        st.warning("⚠️ No valid photo URL provided")
        return None
    
    try:
        st.info(f"🔗 Loading photo with session: {photo_field[:80]}...")
        
        # Use session cookies to authenticate
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cookie': session_cookies
        }
        
        response = requests.get(photo_field, timeout=15, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            photo_data = response.content
            st.success(f"📸 Photo loaded with session! Size: {len(photo_data):,} bytes")
            
            # Check if we got an image or HTML
            if photo_data.startswith(b'<html') or photo_data.startswith(b'<!doctype'):
                st.error("❌ Still receiving HTML - session may be invalid")
                return None
            elif photo_data.startswith(b'\xff\xd8') or photo_data.startswith(b'\x89PNG'):
                st.success("✅ Valid image format detected with session!")
                return photo_data
            else:
                st.warning(f"⚠️ Unknown format with session. First 20 bytes: {photo_data[:20]}")
                return photo_data
        else:
            st.warning(f"⚠️ Photo URL failed with session: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Photo fetch with session error: {str(e)}")
        return None

def fetch_photo_bytes(photo_field: str) -> Optional[bytes]:
    """Fetch photo directly from URL - SIMPLE AND RELIABLE"""
    if not photo_field or not photo_field.startswith("http"):
        st.warning("⚠️ No valid photo URL provided")
        return None
    
    try:
        st.info(f"🔗 Loading photo from: {photo_field[:80]}...")
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(photo_field, timeout=15, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            photo_data = response.content
            st.success(f"📸 Photo loaded! Size: {len(photo_data):,} bytes")
            
            # Show the actual content type returned
            content_type = response.headers.get('content-type', 'unknown')
            st.info(f"🔍 Content-Type: {content_type}")
            
            # Show first 100 characters as text to see if it's HTML
            try:
                first_100_text = photo_data[:100].decode('utf-8', errors='ignore')
                st.write(f"**First 100 chars as text:** {first_100_text}")
            except:
                st.write("**First 100 bytes:** (binary data)")
            
            # Enhanced format detection
            if photo_data.startswith(b'\xff\xd8'):
                st.info("🖼️ JPEG format detected")
            elif photo_data.startswith(b'\x89PNG'):
                st.info("🖼️ PNG format detected")
            elif photo_data.startswith(b'GIF8'):
                st.info("🖼️ GIF format detected")
            elif photo_data.startswith(b'RIFF') and b'WEBP' in photo_data[:20]:
                st.info("🖼️ WebP format detected")
            elif photo_data.startswith(b'<html') or photo_data.startswith(b'<!doctype') or photo_data.startswith(b'<!DOCTYPE'):
                st.error("❌ Received HTML page instead of image")
                return None
            else:
                st.warning(f"⚠️ Unknown format. First 20 bytes: {photo_data[:20]}")
                st.write(f"Hex: {photo_data[:20].hex()}")
                
            return photo_data
        else:
            st.warning(f"⚠️ Photo URL failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Photo fetch error: {str(e)}")
        return None

def draw_winner_card(name: str, location: str, level: str, photo_bytes: Optional[bytes]) -> Image.Image:
    """Create winner card with proper photo rendering"""
    W, H = 1200, 675
    img = Image.new("RGB", (W, H), (20, 24, 28))
    d = ImageDraw.Draw(img)

    # Try to load fonts
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        title_font = name_font = info_font = ImageFont.load_default()

    # Header gradient
    header_colors = [(255, 107, 107), (78, 205, 196), (69, 183, 209)]
    for i in range(120):
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

    # Title
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

    # Photo box
    box = (50, 150, 350, 450)
    d.rounded_rectangle(box, radius=15, fill=(50, 50, 50), outline=(100, 100, 100), width=3)
    inner_box = (box[0]+4, box[1]+4, box[2]-4, box[3]-4)
    d.rounded_rectangle(inner_box, radius=12, outline=(90, 90, 90), width=2)
    
    # PHOTO PROCESSING - ENHANCED ERROR HANDLING
    if photo_bytes:
        try:
            st.write(f"🖼️ Processing photo: {len(photo_bytes)} bytes")
            
            # Try to detect if it's actually an image
            if photo_bytes.startswith(b'<html') or photo_bytes.startswith(b'<!doctype'):
                st.error("❌ Received HTML page instead of image")
                d.text((inner_box[0] + 20, inner_box[1] + 20), "📷 HTML received instead of image", fill=(200, 200, 200), font=info_font)
            else:
                # Try opening with PIL
                try:
                    p = Image.open(io.BytesIO(photo_bytes))
                    p = p.convert("RGB")  # Ensure RGB format
                    st.write(f"✅ Image loaded: {p.size[0]}x{p.size[1]} pixels, mode: {p.mode}")
                    
                    # Calculate scaling to fit the box
                    bw, bh = inner_box[2] - inner_box[0], inner_box[3] - inner_box[1]
                    scale = min(bw / p.width, bh / p.height)
                    new_size = (int(p.width * scale), int(p.height * scale))
                    p = p.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Center the image in the box
                    x_offset = (bw - new_size[0]) // 2
                    y_offset = (bh - new_size[1]) // 2
                    img.paste(p, (inner_box[0] + x_offset, inner_box[1] + y_offset))
                    st.success("✅ Photo successfully rendered in winner card!")
                    
                except Exception as pil_error:
                    st.error(f"❌ PIL processing failed: {pil_error}")
                    # Show raw data for debugging
                    st.write(f"First 50 bytes: {photo_bytes[:50]}")
                    st.write(f"Last 50 bytes: {photo_bytes[-50:]}")
                    d.text((inner_box[0] + 20, inner_box[1] + 20), f"📷 Image processing error", fill=(200, 200, 200), font=info_font)
                
        except Exception as e:
            st.error(f"❌ Photo processing failed: {e}")
            d.text((inner_box[0] + 20, inner_box[1] + 20), f"📷 Photo error: {str(e)}", fill=(200, 200, 200), font=info_font)
    else:
        st.warning("⚠️ No photo provided for winner card")
        d.text((inner_box[0] + 20, inner_box[1] + 20), "📷 No photo available", fill=(200, 200, 200), font=info_font)

    # Winner info
    name = (name or "").strip() or "(name missing)"
    location = (location or "").strip() or "(location missing)"
    level = (level or "").strip() or "(level missing)"

    info_x = 400
    info_start_y = 180

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
    st.title("🎉 MVN Great Save Raffle - FIXED VERSION")
    
    # File upload
    uploaded_file = st.file_uploader("📁 Upload CSV File", type=['csv'])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Successfully loaded {len(df)} participants!")
        
        # Show actual column names for debugging
        st.subheader("🔍 Column Names in Your CSV")
        st.write("**Available columns:**", list(df.columns))
        
        # Let user map columns
        st.subheader("🔧 Column Mapping")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name_col = st.selectbox("👤 Name Column", df.columns, index=0)
        with col2:
            location_col = st.selectbox("🏢 Location Column", df.columns, index=1 if len(df.columns) > 1 else 0)
        with col3:
            level_col = st.selectbox("🎫 Level Column", df.columns, index=2 if len(df.columns) > 2 else 0)
            
        photo_col = st.selectbox("📸 Photo Column", df.columns, index=len(df.columns)-1)
        
        # Show data preview
        st.subheader("👀 Data Preview")
        st.dataframe(df.head())
        
        # Show what the current mappings are
        st.subheader("✅ Current Column Mappings")
        st.write(f"- **Name:** {name_col}")
        st.write(f"- **Location:** {location_col}")  
        st.write(f"- **Level:** {level_col}")
        st.write(f"- **Photo:** {photo_col}")
        
        # Show a sample row to verify
        st.subheader("🔍 Sample Data Row")
        sample_row = df.iloc[0]
        st.write(f"- Sample Name: '{sample_row.get(name_col, 'NOT FOUND')}'")
        st.write(f"- Sample Location: '{sample_row.get(location_col, 'NOT FOUND')}'")
        st.write(f"- Sample Level: '{sample_row.get(level_col, 'NOT FOUND')}'")
        st.write(f"- Sample Photo: '{str(sample_row.get(photo_col, 'NOT FOUND'))[:100]}...'")
        
        # Winner selection
        st.subheader("🎰 Pick Your Winner!")
        
        # Photo option toggle with new authentication approach
        photo_option = st.radio(
            "📸 Photo Loading Options:",
            [
                "🚫 Skip photos (fastest)",
                "🔐 Try with session cookies (paste your KPA session)",
                "🌐 Try direct URLs (may fail)"
            ]
        )
        
        session_cookies = ""
        if photo_option == "🔐 Try with session cookies (paste your KPA session)":
            st.info("� **How to get session cookies:**\n1. Login to KPA in another tab\n2. Open Developer Tools (F12)\n3. Go to Application/Storage → Cookies\n4. Copy the session cookie value")
            session_cookies = st.text_input("🍪 Paste KPA session cookie:", type="password")
        
        if st.button("🎲 Random Selection"):
            winner_idx = random.randint(0, len(df) - 1)
            winner = df.iloc[winner_idx]
            
            # Use the selected column mappings
            name = str(winner.get(name_col, "")).strip()
            location = str(winner.get(location_col, "")).strip() 
            level = str(winner.get(level_col, "")).strip()
            photo_field = str(winner.get(photo_col, "")).strip()
            
            st.success(f"🏆 WINNER: {name}! 🏆")
            
            # Debug what we extracted
            st.write(f"**Debug Info:**")
            st.write(f"- Name from '{name_col}': '{name}'")
            st.write(f"- Location from '{location_col}': '{location}'")
            st.write(f"- Level from '{level_col}': '{level}'")
            st.write(f"- Photo from '{photo_col}': '{photo_field[:100] if photo_field else 'EMPTY'}...'")
            
            # Display winner info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌟 Winner", name)
            with col2:
                st.metric("🏢 Location", location)
            with col3:
                st.metric("🎫 Ticket Level", level)
                
            st.info(f"📊 Selected from row {winner_idx + 1} of {len(df)} participants")
            
            # Fetch photo based on selected option
            photo_bytes = None
            if photo_option == "🚫 Skip photos (fastest)":
                st.info("📸 Photo loading skipped (disabled)")
            elif photo_option == "🔗 Use KPA Proxy Server (recommended)" and photo_field:
                with st.spinner("🖼️ Fetching winner photo via proxy server..."):
                    photo_bytes = fetch_photo_via_proxy(photo_field)
            elif photo_option == "🌐 Try direct URLs (will fail)" and photo_field:
                with st.spinner("🖼️ Fetching winner photo (direct URL)..."):
                    photo_bytes = fetch_photo_bytes(photo_field)
            elif photo_option == "🔐 Try with session cookies (manual)" and photo_field and session_cookies:
                with st.spinner("🖼️ Fetching winner photo (with session)..."):
                    photo_bytes = fetch_photo_with_session(photo_field, session_cookies)
            elif photo_field:
                st.warning("📸 Photo URL provided but loading method not configured")
            else:
                st.warning("📸 No photo URL provided")
                
            # Generate winner card
            with st.spinner("🎨 Creating winner card..."):
                card = draw_winner_card(name=name, location=location, level=level, photo_bytes=photo_bytes)
                
            st.markdown("### 🎊 Winner Card Generated!")
            st.image(card, caption=f"🏆 Winner: {name}", use_container_width=True)

if __name__ == "__main__":
    main()

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
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Moon Valley Nurseries - Great Save Raffle System"
    }
)

# ── Logo and branding functions ──────────────────────────────────────────────
def load_mvn_logo():
    """Load the MVN logo and convert to base64 for display"""
    try:
        logo_path = "Moon Valley Logo.png"
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_bytes = f.read()
            logo_b64 = base64.b64encode(logo_bytes).decode()
            return logo_b64, logo_bytes
        return None, None
    except Exception as e:
        st.error(f"Could not load MVN logo: {e}")
        return None, None

def display_header_with_logo():
    """Display the app header with MVN logo"""
    logo_b64, _ = load_mvn_logo()
    
    if logo_b64:
        # Header with logo - responsive for mobile
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 2rem; width: 100%;" class="mobile-header-stack">
            <img src="data:image/png;base64,{logo_b64}" style="height: 80px; margin-right: 20px; flex-shrink: 0;" class="header-logo">
            <div style="text-align: center; flex-grow: 1;">
                <h1 class="main-header" style="margin: 0;">🎉 GREAT SAVE RAFFLE 🎉</h1>
                <p class="subtitle" style="margin: 0;">🏆 MVN Employee Recognition Program 🏆</p>
            </div>
            <img src="data:image/png;base64,{logo_b64}" style="height: 80px; margin-left: 20px; flex-shrink: 0;" class="header-logo">
        </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback header without logo
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 class="main-header">🎉 GREAT SAVE RAFFLE 🎉</h1>
            <p class="subtitle">🏆 MVN Employee Recognition Program 🏆</p>
        </div>
        """, unsafe_allow_html=True)

# ── Your column headers (exact) ────────────────────────────────────────────────
COL_LINK = "Link"
COL_DATE = "Date"
COL_OBSERVER = "Observer"
COL_EMP_NAME = "Name of employee that earned the Great Save Raffle ticket?"
COL_TICKET_LEVEL = "What level of ticket was earned?"
COL_LOCATION = "What MVN location does employee work at?"
COL_PHOTO_URL = "Photo of the employee holding the ticket. (Will be used if drawn))"
COL_USER_ID = "id"  # KPA user ID column

# ── KPA API config ────────────────────────────────────────────────────────────
API_BASE = "https://api.kpaehs.com/v1" 
# Try to use local proxy first, fallback to direct API for cloud deployment
PHOTO_PROXY_URL = os.getenv("PHOTO_PROXY_URL", "http://localhost:5001/api/v1/photos/proxy")

# Enhanced token access with detailed debugging
KPA_TOKEN = None
try:
    # Debug: Check Streamlit secrets availability
    st.write("🔍 **Secrets Debug:**")
    
    # Check if secrets are available
    has_secrets_attr = hasattr(st, 'secrets')
    st.write(f"- Secrets attribute available: {has_secrets_attr}")
    
    if has_secrets_attr:
        try:
            # Try to access secrets safely
            secrets_obj = getattr(st, 'secrets', None)
            if secrets_obj is not None:
                st.write("- Secrets object exists")
                
                # Try to get the token
                token_value = None
                if hasattr(secrets_obj, 'get'):
                    token_value = secrets_obj.get("KPA_TOKEN")
                elif hasattr(secrets_obj, '__getitem__'):
                    try:
                        token_value = secrets_obj["KPA_TOKEN"]
                    except (KeyError, TypeError):
                        pass
                
                if token_value:
                    KPA_TOKEN = token_value
                    st.success(f"✅ KPA_TOKEN found (length: {len(KPA_TOKEN)})")
                else:
                    st.warning("⚠️ KPA_TOKEN not found in secrets")
                    # Show available keys for debugging
                    try:
                        if hasattr(secrets_obj, 'keys'):
                            available_keys = list(secrets_obj.keys())
                            st.write(f"- Available keys: {available_keys}")
                    except Exception:
                        pass
            else:
                st.warning("⚠️ Secrets object is None")
        except Exception as e:
            st.error(f"❌ Error accessing secrets: {str(e)}")
    
    # Fallback to environment variable
    if not KPA_TOKEN:
        env_token = os.getenv("KPA_TOKEN")
        if env_token:
            KPA_TOKEN = env_token
            st.info(f"ℹ️ Using environment variable (length: {len(KPA_TOKEN)})")
        else:
            st.error("❌ KPA_TOKEN not found in secrets or environment")
            
except Exception as e:
    st.error(f"❌ Token access error: {str(e)}")
    KPA_TOKEN = None

def test_kpa_integration() -> dict:
    """Test KPA API integration and return status for debugging/monitoring"""
    status = {
        "token_available": bool(KPA_TOKEN),
        "token_length": len(KPA_TOKEN) if KPA_TOKEN else 0,
        "api_base": API_BASE,
        "users_info_available": False,
        "users_list_available": False,
        "error_messages": []
    }
    
    if not KPA_TOKEN:
        status["error_messages"].append("No KPA token configured")
        return status
    
    # Test users.info endpoint
    try:
        test_data = {"token": KPA_TOKEN, "id": "test_user"}
        resp = requests.post(f"{API_BASE}/users.info", json=test_data, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            if "ok" in result:  # Valid KPA response structure
                status["users_info_available"] = True
            else:
                status["error_messages"].append(f"users.info: Invalid response structure")
        else:
            status["error_messages"].append(f"users.info: HTTP {resp.status_code}")
    except Exception as e:
        status["error_messages"].append(f"users.info: {str(e)}")
    
    # Test users.list endpoint (only token parameter supported)
    try:
        test_data = {"token": KPA_TOKEN}
        resp = requests.post(f"{API_BASE}/users.list", json=test_data, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            if "ok" in result:  # Valid KPA response structure
                status["users_list_available"] = True
            else:
                status["error_messages"].append(f"users.list: Invalid response structure")
        else:
            status["error_messages"].append(f"users.list: HTTP {resp.status_code}")
    except Exception as e:
        status["error_messages"].append(f"users.list: {str(e)}")
    
    return status

def extract_user_id(employee_name_or_id: str, photo_field: str) -> Optional[str]:
    """Extract user ID from name, ID, or photo field for KPA API lookup"""
    if not employee_name_or_id and not photo_field:
        return None
    
    # Method 1: If it looks like a KPA ID (24 char hex), return as-is
    if employee_name_or_id and len(employee_name_or_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in employee_name_or_id):
        st.info(f"🔍 Using provided KPA user ID: {employee_name_or_id}")
        return employee_name_or_id
    
    # Method 2: Try to extract from KPA user ID patterns in photo URL
    if photo_field and "kpaehs.com" in photo_field:
        # Look for user ID patterns in the URL or key
        key = extract_key_from_tenant_url(photo_field)
        if key and "/" in key:
            # Extract potential user ID from private path like: private/ytbg74inq29x9bop/image.jpg
            parts = key.split("/")
            if len(parts) >= 2:
                potential_id = parts[1]  # ytbg74inq29x9bop
                if len(potential_id) > 10:  # Reasonable user ID length
                    st.info(f"🔍 Extracted potential user ID from photo: {potential_id}")
                    return potential_id
    
    # Method 3: Try to extract user code from name (like "John Doe (USR001)")
    if employee_name_or_id:
        import re
        # Look for patterns like (USR001), (MVN123), etc.
        user_pattern = r'\(([A-Z]+\d+)\)'
        match = re.search(user_pattern, employee_name)
        if match:
            user_id = match.group(1)
            st.info(f"🔍 Extracted user ID from name: {user_id}")
            return user_id
    
    # Method 3: Use the full name for user search via users.list
    if employee_name:
        # Use the exact name for user search
        st.info(f"🔍 Using full name for user search: {employee_name}")
        return employee_name
    
    return None

def fetch_photo_by_user_id(user_id: str) -> Optional[bytes]:
    """Fetch user photo using KPA users.info endpoint"""
    if not user_id or not KPA_TOKEN:
        return None
    
    try:
        # Try the users.info endpoint to get user details including photo
        data = {"token": KPA_TOKEN, "id": user_id}
        resp = requests.post(f"{API_BASE}/users.info", json=data, timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            st.write(f"🔍 Users.info API Response: {result}")
            
            if result.get('ok'):
                user_data = result.get('user', {})
                
                # Look for photo/avatar URL in the user data
                photo_url = None
                for url_field in ["photo_url", "avatar_url", "profile_photo", "image_url", "photo", "avatar"]:
                    if url_field in user_data:
                        photo_url = user_data[url_field]
                        st.info(f"✅ Found photo URL in field: {url_field}")
                        break
                
                if photo_url:
                    # Download the actual photo
                    img_resp = requests.get(photo_url, timeout=10)
                    if img_resp.status_code == 200:
                        st.success(f"📸 Photo loaded for user ID: {user_id}")
                        return img_resp.content
                    else:
                        st.warning(f"⚠️ Photo download failed: HTTP {img_resp.status_code}")
                else:
                    st.warning("⚠️ No photo URL found in user info response")
                    st.write(f"Available user fields: {list(user_data.keys())}")
            else:
                st.warning(f"⚠️ Users.info API returned ok=False: {result.get('error', 'Unknown error')}")
        else:
            st.warning(f"⚠️ Users.info API error: HTTP {resp.status_code} - {resp.text}")
            
    except Exception as e:
        st.warning(f"⚠️ Users.info API error: {str(e)}")
    
    # Try alternative: users.list to get all users (API doesn't support query/limit)
    try:
        st.info(f"🔍 Trying users.list to find user: {user_id}")
        search_data = {"token": KPA_TOKEN}
        resp = requests.post(f"{API_BASE}/users.list", json=search_data, timeout=10)
        
        if resp.status_code == 200:
            result = resp.json()
            st.write(f"🔍 Users.list API Response: {result}")
            
            if result.get('ok') and result.get('users'):
                users = result.get('users', [])
                if users:
                    # Use the first matching user
                    user_data = users[0]
                    st.info(f"✅ Found user in users.list: {user_data.get('name', 'Unknown')}")
                    
                    # Look for photo URL in the user data
                    photo_url = None
                    for url_field in ["photo_url", "avatar_url", "profile_photo", "image_url", "photo", "avatar"]:
                        if url_field in user_data:
                            photo_url = user_data[url_field]
                            st.info(f"✅ Found photo URL in field: {url_field}")
                            break
                    
                    if photo_url:
                        # Download the actual photo
                        img_resp = requests.get(photo_url, timeout=10)
                        if img_resp.status_code == 200:
                            st.success(f"📸 Photo loaded from users.list for: {user_id}")
                            return img_resp.content
                        else:
                            st.warning(f"⚠️ Photo download failed: HTTP {img_resp.status_code}")
                    else:
                        st.warning("⚠️ No photo URL found in users.list response")
                        st.write(f"Available user fields: {list(user_data.keys())}")
                else:
                    st.warning(f"⚠️ No users found matching: {user_id}")
            else:
                st.warning(f"⚠️ Users.list API returned ok=False: {result.get('error', 'Unknown error')}")
        else:
            st.warning(f"⚠️ Users.list API error: HTTP {resp.status_code} - {resp.text}")
            
    except Exception as e:
        st.warning(f"⚠️ Users.list API error: {str(e)}")
    
    return None

def extract_key_from_tenant_url(url: str) -> Optional[str]:
    """From https://<tenant>.kpaehs.com/get-upload?key=ENCODED → 'private/.../image.jpg'"""
    if not isinstance(url, str) or "get-upload" not in url:
        return None
    try:
        q = parse_qs(urlparse(url).query)
        if "key" not in q or not q["key"]:
            return None
        return unquote(q["key"][0])
    except Exception:
        return None

def fetch_photo_bytes(photo_field: str, employee_name: str = "") -> Optional[bytes]:
    """Fetch photo directly from URL - simplified version"""
    if not photo_field or not photo_field.startswith("http"):
        st.warning("⚠️ No valid photo URL provided")
        return None
    
    try:
        st.info(f"🔗 Loading photo from: {photo_field[:60]}...")
        response = requests.get(photo_field, timeout=15)
        if response.status_code == 200:
            photo_data = response.content
            st.success(f"📸 Photo loaded! Size: {len(photo_data):,} bytes")
            
            # Quick format check
            if photo_data.startswith(b'\xff\xd8') or photo_data.startswith(b'\x89PNG'):
                st.info("🖼️ Valid image format detected")
            else:
                st.warning("⚠️ Unexpected image format - might not display properly")
                
            return photo_data
        else:
            st.warning(f"⚠️ Photo URL failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Photo fetch error: {str(e)}")
        return None

def draw_winner_card(name: str, location: str, level: str, photo_bytes: Optional[bytes]) -> Image.Image:
    W, H = 1200, 675
    img = Image.new("RGB", (W, H), (20, 24, 28))
    d = ImageDraw.Draw(img)

    # Try to load a nice font, fall back to default if not available
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        footer_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        title_font = name_font = info_font = footer_font = ImageFont.load_default()

    # Enhanced gradient header with trophy emoji effect
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

    # Add MVN logo to the header
    _, logo_bytes = load_mvn_logo()
    if logo_bytes:
        try:
            logo_img = Image.open(io.BytesIO(logo_bytes))
            # Resize logo to fit in header
            logo_size = 80
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            # Paste logo on left side of header
            img.paste(logo_img, (20, 20), logo_img if logo_img.mode == 'RGBA' else None)
            # Paste logo on right side of header  
            img.paste(logo_img, (W - logo_size - 20, 20), logo_img if logo_img.mode == 'RGBA' else None)
        except Exception:
            pass  # Continue without logo if there's an error

    # Title with shadow effect - adjusted position for logo
    title_text = "🏆 GREAT SAVE RAFFLE — WINNER! 🏆"
    # Calculate center position accounting for logos
    title_bbox = d.textbbox((0, 0), title_text, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (W - title_width) // 2
    
    # Shadow
    d.text((title_x + 2, 32), title_text, fill=(0, 0, 0, 128), font=title_font)
    # Main text
    d.text((title_x, 30), title_text, fill="white", font=title_font)
    
    # Date with celebration emoji
    date_text = f"🎉 MVN {time.strftime('%B %d, %Y')} 🎉"
    date_bbox = d.textbbox((0, 0), date_text, font=info_font)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = (W - date_width) // 2
    d.text((date_x, 80), date_text, fill="white", font=info_font)

    # Enhanced photo area with sparkle border
    box = (50, 150, 450, 550)
    # Sparkle border effect
    sparkle_color = (255, 215, 0)  # Gold
    d.rounded_rectangle(box, radius=15, outline=sparkle_color, width=4)
    # Inner border
    inner_box = (box[0]+4, box[1]+4, box[2]-4, box[3]-4)
    d.rounded_rectangle(inner_box, radius=12, outline=(90, 90, 90), width=2)
    
    if photo_bytes:
        try:
            # Debug: Check photo data
            print(f"DEBUG: Photo bytes length: {len(photo_bytes)}")
            print(f"DEBUG: Photo starts with: {photo_bytes[:10]}")
            
            p = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
            print(f"DEBUG: Image loaded, size: {p.size}")
            
            # Don't rotate - try without rotation first
            # p = p.rotate(-90, expand=True)
            bw, bh = inner_box[2] - inner_box[0], inner_box[3] - inner_box[1]
            print(f"DEBUG: Box size: {bw}x{bh}")
            
            scale = max(bw / p.width, bh / p.height)
            new_size = (int(p.width * scale), int(p.height * scale))
            print(f"DEBUG: Scaling to: {new_size}")
            
            p = p.resize(new_size)
            x0 = (p.width - bw) // 2
            y0 = (p.height - bh) // 2
            p = p.crop((x0, y0, x0 + bw, y0 + bh))
            print(f"DEBUG: Final crop: {p.size}")
            
            img.paste(p, (inner_box[0], inner_box[1]))
            print("DEBUG: Photo pasted successfully!")
        except Exception as e:
            print(f"DEBUG: Photo processing failed: {e}")
            import traceback
            traceback.print_exc()
            d.text((inner_box[0] + 20, inner_box[1] + 20), f"📷 Photo error: {str(e)}", fill=(200, 200, 200), font=info_font)
    else:
        print("DEBUG: No photo_bytes provided")
        d.text((inner_box[0] + 20, inner_box[1] + 20), "📷 Photo unavailable", fill=(200, 200, 200), font=info_font)

    # Winner info with enhanced styling
    name = (name or "").strip() or "(name missing)"
    loc = (location or "").strip()
    lvl = (level or "").strip()
    
    y = 180
    # Winner label
    d.text((500, y), "🌟 WINNER:", fill=(255, 215, 0), font=info_font)
    y += 40
    
    # Name with shadow effect
    d.text((502, y+2), name, fill=(0, 0, 0, 128), font=name_font)  # Shadow
    d.text((500, y), name, fill="white", font=name_font)
    y += 60
    
    if loc: 
        d.text((500, y), f"🏢 Location: {loc}", fill=(200, 220, 255), font=info_font)
        y += 40
        
    if lvl: 
        d.text((500, y), f"🎫 Ticket Level: {lvl}", fill=(200, 255, 200), font=info_font)
        y += 40
    
    # Congratulations message
    y += 20
    congrats_text = "🎊 CONGRATULATIONS! 🎊"
    d.text((500, y), congrats_text, fill=(255, 215, 0), font=info_font)

    # Enhanced footer with MVN branding
    footer_text = "✨ Moon Valley Nurseries Employee Recognition ✨"
    d.text((W - 40, H - 30), footer_text, fill=(140, 140, 140), anchor="ra", font=footer_font)
    
    return img

# ── UI ────────────────────────────────────────────────────────────────────────
# Enhanced styling and celebration features
def add_celebration_css():
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka+One:wght@400&family=Poppins:wght@300;400;600;700&display=swap');
    
    /* Mobile-first responsive design */
    .main-header {
        font-family: 'Fredoka One', cursive;
        font-size: clamp(2rem, 5vw, 3.5rem);
        text-align: center;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FECA57);
        background-size: 300% 300%;
        animation: rainbow 3s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: 0.1em;
        word-spacing: 0.2em;
        display: block;
        width: 100%;
        line-height: 1.2;
    }
    
    @keyframes rainbow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .subtitle {
        font-family: 'Poppins', sans-serif;
        font-size: clamp(0.9rem, 2.5vw, 1.2rem);
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        line-height: 1.4;
    }
    
    /* Mobile responsive containers */
    @media screen and (max-width: 768px) {
        .main-header {
            font-size: 2.5rem !important;
            line-height: 1.1 !important;
            margin-bottom: 1rem !important;
        }
        
        .subtitle {
            font-size: 1rem !important;
            margin-bottom: 1.5rem !important;
        }
        
        /* Mobile logo adjustments */
        .header-logo {
            height: 60px !important;
            margin: 0 10px !important;
        }
        
        /* Mobile button styling */
        .stButton button {
            width: 100% !important;
            padding: 0.8rem 1rem !important;
            font-size: 1rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* Mobile column adjustments */
        .element-container {
            margin-bottom: 1rem !important;
        }
    }
    
    @media screen and (max-width: 480px) {
        .main-header {
            font-size: 2rem !important;
            letter-spacing: 0.05em !important;
            word-spacing: 0.1em !important;
        }
        
        .subtitle {
            font-size: 0.9rem !important;
        }
        
        .header-logo {
            height: 50px !important;
            margin: 0 5px !important;
        }
        
        /* Stack header elements vertically on very small screens */
        .mobile-header-stack {
            flex-direction: column !important;
            text-align: center !important;
        }
        
        .mobile-header-stack img {
            margin: 10px 0 !important;
        }
    }
    
    .winner-announcement {
        font-family: 'Fredoka One', cursive;
        font-size: 4rem;
        text-align: center;
        color: #FF6B6B;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.3);
        animation: bounce 1s ease infinite alternate;
        margin: 1rem 0;
    }
    
    @keyframes bounce {
        from { transform: translateY(0px); }
        to { transform: translateY(-20px); }
    }
    
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        background: #FF6B6B;
        animation: confetti-fall 3s linear infinite;
        z-index: 1000;
    }
    
    @keyframes confetti-fall {
        to {
            transform: translateY(100vh) rotate(360deg);
        }
    }
    
    .celebration-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .winner-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        text-align: center;
        animation: winner-glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes winner-glow {
        from { box-shadow: 0 10px 30px rgba(255, 107, 107, 0.3); }
        to { box-shadow: 0 20px 40px rgba(255, 107, 107, 0.6); }
    }
    
    .stats-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem 0.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .stats-card h3 {
        font-size: 0.9rem !important;
        margin: 0 0 0.5rem 0 !important;
        line-height: 1.2 !important;
        word-wrap: break-word !important;
    }
    
    .stats-card h1, .stats-card h2 {
        margin: 0 !important;
        line-height: 1 !important;
    }
    
    .fun-button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 25px;
        font-size: 1.2rem;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .sparkle {
        color: #FFD700;
        font-size: 2rem;
        animation: sparkle 1.5s ease-in-out infinite alternate;
    }
    
    @keyframes sparkle {
        from { opacity: 0.4; transform: scale(0.8); }
        to { opacity: 1; transform: scale(1.2); }
    }
    
    .countdown {
        font-size: clamp(4em, 12vw, 8em);
        font-weight: bold;
        color: #FFD700;
        text-shadow: 
            0 0 20px #FFD700,
            0 0 40px #FFA500,
            0 0 60px #FF6347;
        animation: countdown-pulse 1s infinite;
        text-align: center;
        margin: 50px 0;
        z-index: 1000;
        position: relative;
    }
    
    @keyframes countdown-pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .drumroll {
        font-size: clamp(2em, 6vw, 3em);
        font-weight: bold;
        color: #FFD700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        text-align: center;
        margin: 30px 0;
        animation: drumroll-spin 0.1s ease-in-out;
        background: linear-gradient(45deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .mega-winner {
        font-size: clamp(2.5em, 8vw, 4em);
        font-weight: bold;
        text-align: center;
        margin: 30px 0;
        animation: winner-announce 2s ease-in-out;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        background-size: 400% 400%;
        animation: gradient-text 3s ease infinite, winner-bounce 1s ease-in-out;
        line-height: 1.2;
    }
    
    /* Additional mobile responsiveness for stats cards */
    @media screen and (max-width: 768px) {
        .stats-card {
            margin: 0.5rem 0 !important;
            padding: 0.8rem 0.4rem !important;
            min-height: 100px !important;
        }
        
        .stats-card h3 {
            font-size: 0.8rem !important;
        }
        
        .stats-card h1 {
            font-size: 1.8rem !important;
        }
        
        .countdown {
            margin: 30px 0 !important;
        }
        
        .drumroll {
            margin: 20px 0 !important;
        }
        
        .mega-winner {
            margin: 20px 0 !important;
        }
    }
        text-align: center;
        margin: 30px 0;
        animation: drumroll-spin 0.1s ease-in-out;
        background: linear-gradient(45deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    @keyframes drumroll-spin {
        0% { transform: scale(0.9) rotate(-2deg); }
        50% { transform: scale(1.1) rotate(2deg); }
        100% { transform: scale(1) rotate(0deg); }
    }
    
    .mega-winner {
        font-size: 4em;
        font-weight: bold;
        text-align: center;
        margin: 30px 0;
        animation: winner-announce 2s ease-in-out;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        background-size: 400% 400%;
        animation: gradient-text 3s ease infinite, winner-bounce 1s ease-in-out;
    }
    
    @keyframes winner-announce {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.2); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    @keyframes winner-bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-20px); }
        60% { transform: translateY(-10px); }
    }
    
    @keyframes gradient-text {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    </style>
    """, unsafe_allow_html=True)

def show_confetti():
    """Display animated confetti"""
    confetti_html = """
    <div id="confetti-container"></div>
    <script>
    function createConfetti() {
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF'];
        const confettiContainer = document.getElementById('confetti-container');
        
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.top = '-10px';
            confetti.style.width = Math.random() * 10 + 5 + 'px';
            confetti.style.height = Math.random() * 10 + 5 + 'px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0%';
            confetti.style.animation = `confetti-fall ${Math.random() * 3 + 2}s linear infinite`;
            confetti.style.zIndex = '1000';
            confetti.style.pointerEvents = 'none';
            
            confettiContainer.appendChild(confetti);
            
            setTimeout(() => {
                confetti.remove();
            }, 5000);
        }
    }
    
    createConfetti();
    setInterval(createConfetti, 3000);
    </script>
    """
    st.components.v1.html(confetti_html, height=0)

def play_celebration_sound():
    """Add celebration sound effect"""
    st.balloons()
    # Create a simple audio notification
    audio_html = """
    <audio autoplay>
        <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmVvBjiJ0fPNeSsFJHfH8N2QQAoUXrTp66hVFAlGp+PwtmM==" type="audio/wav">
    </audio>
    """
    st.components.v1.html(audio_html, height=0)

def create_stats_chart(df):
    """Create interactive statistics chart"""
    if COL_LOCATION in df.columns:
        location_counts = df[COL_LOCATION].value_counts()
        
        fig = go.Figure(data=[
            go.Bar(
                x=location_counts.index,
                y=location_counts.values,
                marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'][:len(location_counts)],
                text=location_counts.values,
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title={
                'text': "🏢 Participants by Location",
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 18, 'family': 'Fredoka One'}
            },
            xaxis_title="Location",
            yaxis_title="Number of Participants",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Poppins", size=12),
            showlegend=False,
            margin=dict(t=60, b=50, l=50, r=50)
        )
        
        return fig
    return None

def create_ticket_level_chart(df):
    """Create ticket level distribution chart"""
    if COL_TICKET_LEVEL in df.columns:
        level_counts = df[COL_TICKET_LEVEL].value_counts()
        
        fig = go.Figure(data=[
            go.Pie(
                labels=level_counts.index,
                values=level_counts.values,
                hole=0.4,
                marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'][:len(level_counts)],
                textinfo='label+percent',
                textfont_size=14,
            )
        ])
        
        fig.update_layout(
            title={
                'text': "🎫 Ticket Level Distribution",
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 18, 'family': 'Fredoka One'}
            },
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Poppins", size=12),
            showlegend=True,
            margin=dict(t=60, b=50, l=50, r=50)
        )
        
        return fig
    return None

# ── MAIN UI ──────────────────────────────────────────────────────────────────
# Initialize session state
if 'celebration_mode' not in st.session_state:
    st.session_state.celebration_mode = False
if 'winner_announced' not in st.session_state:
    st.session_state.winner_announced = False

# Header with MVN logos
display_header_with_logo()
st.markdown('<p style="text-align: center; color: #666; font-family: Poppins; margin-bottom: 2rem;">📁 Upload CSV • Pick Winner • Create Winner Card • Download PNG</p>', unsafe_allow_html=True)

# KPA Integration Status (for development/debugging)
with st.expander("🔧 KPA Integration Status", expanded=False):
    kpa_status = test_kpa_integration()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if kpa_status["token_available"]:
            st.success(f"✅ Token Available ({kpa_status['token_length']} chars)")
        else:
            st.error("❌ No KPA Token")
    
    with col2:
        if kpa_status["users_info_available"]:
            st.success("✅ users.info endpoint")
        else:
            st.error("❌ users.info unavailable")
    
    with col3:
        if kpa_status["users_list_available"]:
            st.success("✅ users.list endpoint")
        else:
            st.error("❌ users.list unavailable")
    
    if kpa_status["error_messages"]:
        st.warning("⚠️ Issues found:")
        for error in kpa_status["error_messages"]:
            st.write(f"• {error}")
    
    st.info(f"🌐 API Base: {kpa_status['api_base']}")

# Show confetti if in celebration mode
if st.session_state.celebration_mode:
    show_confetti()

csv_file = st.file_uploader("📁 Upload CSV File", type=["csv"], help="Upload your KPA raffle data CSV file")
seed = st.text_input("🎲 Random seed (optional)", value="", help="Enter a seed for reproducible random selection")

if csv_file:
    df = pd.read_csv(csv_file)

    # Validate required columns
    required = [COL_EMP_NAME, COL_PHOTO_URL]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"❌ CSV is missing required column(s): {missing}")
        st.stop()

    # Success message
    st.success(f"✅ Successfully loaded {len(df)} participants!")
    
    # Statistics section
    st.markdown("### 📊 Participant Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>👥 Total Participants</h3>
            <h1>{len(df)}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if COL_LOCATION in df.columns:
            unique_locations = df[COL_LOCATION].nunique()
            st.markdown(f"""
            <div class="stats-card">
                <h3>🏢 Locations</h3>
                <h1>{unique_locations}</h1>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if COL_TICKET_LEVEL in df.columns:
            unique_levels = df[COL_TICKET_LEVEL].nunique()
            st.markdown(f"""
            <div class="stats-card">
                <h3>🎫 Ticket Levels</h3>
                <h1>{unique_levels}</h1>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        if COL_DATE in df.columns:
            date_range = "Today"
            try:
                dates = pd.to_datetime(df[COL_DATE])
                if len(dates.unique()) > 1:
                    date_range = f"{dates.min().strftime('%m/%d')} - {dates.max().strftime('%m/%d')}"
                else:
                    date_range = dates.iloc[0].strftime('%m/%d/%Y')
            except:
                pass
            st.markdown(f"""
            <div class="stats-card">
                <h3>📅 Date Range</h3>
                <h2>{date_range}</h2>
            </div>
            """, unsafe_allow_html=True)

    # Charts section
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        location_chart = create_stats_chart(df)
        if location_chart:
            st.plotly_chart(location_chart, use_container_width=True)
    
    with chart_col2:
        ticket_chart = create_ticket_level_chart(df)
        if ticket_chart:
            st.plotly_chart(ticket_chart, use_container_width=True)

    # Preview section
    st.markdown("### 👀 Data Preview")
    show_cols = [c for c in [COL_LINK, COL_DATE, COL_OBSERVER, COL_EMP_NAME, COL_TICKET_LEVEL, COL_LOCATION, COL_PHOTO_URL] if c in df.columns]
    st.dataframe(df[show_cols].head(15), use_container_width=True)

    # Winner selection section
    st.markdown("### 🎰 Pick Your Winner!")
    
    # Add countdown slider
    countdown_col1, countdown_col2, countdown_col3 = st.columns([1, 2, 1])
    with countdown_col2:
        countdown_seconds = st.slider("⏱️ Countdown Timer (seconds)", 3, 10, 5, help="Duration of countdown before revealing winner")
    
    left, right = st.columns(2)
    with left:
        st.markdown("#### 🎲 Random Selection")
        if st.button("🎊 PICK RANDOM WINNER! 🎊", key="random_winner", help="Click to randomly select a winner!"):
            # Countdown animation
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
            
            # Drumroll effect
            drumroll_placeholder = st.empty()
            participant_names = df[COL_EMP_NAME].tolist()
            
            for i in range(25):
                random_name = random.choice(participant_names)
                drumroll_placeholder.markdown(
                    f"<div class='drumroll'>🎲 {random_name} 🎲</div>",
                    unsafe_allow_html=True
                )
                time.sleep(0.08 + (i * 0.008))  # Gradually slow down
            
            drumroll_placeholder.empty()
            
            # Select winner
            if seed.strip(): 
                random.seed(seed)
            idx = random.randrange(len(df))
            winner_row = df.iloc[idx].to_dict()
            
            # Victory announcement
            victory_placeholder = st.empty()
            victory_placeholder.markdown(
                f"<div class='mega-winner'>🏆 {winner_row[COL_EMP_NAME]} 🏆</div>",
                unsafe_allow_html=True
            )
            time.sleep(2)
            victory_placeholder.empty()
            
            # Set winner and trigger celebration
            st.session_state["winner_row"] = winner_row
            st.session_state["winner_index"] = idx
            st.session_state.celebration_mode = True
            st.session_state.winner_announced = True
            play_celebration_sound()
            st.rerun()
    
    with right:
        st.markdown("#### 🎯 Manual Selection")
        idx_sel = st.number_input("Choose participant index", min_value=0, max_value=max(len(df)-1, 0), value=0, step=1)
        if st.button("✨ PICK SELECTED WINNER! ✨", key="manual_winner"):
            # Shorter celebration for manual selection
            winner_row = df.iloc[int(idx_sel)].to_dict()
            
            # Quick victory announcement
            victory_placeholder = st.empty()
            victory_placeholder.markdown(
                f"<div class='mega-winner'>🏆 {winner_row[COL_EMP_NAME]} 🏆</div>",
                unsafe_allow_html=True
            )
            time.sleep(1.5)
            victory_placeholder.empty()
            
            st.session_state["winner_row"] = winner_row
            st.session_state["winner_index"] = int(idx_sel)
            st.session_state.celebration_mode = True
            st.session_state.winner_announced = True
            play_celebration_sound()
            st.rerun()

    # Winner announcement and card generation
    if "winner_row" in st.session_state and st.session_state.winner_announced:
        w = st.session_state["winner_row"]
        winner_idx = st.session_state.get("winner_index", 0)
        
        # Big winner announcement
        name = str(w.get(COL_EMP_NAME, "")).strip()
        st.markdown(f'<h1 class="winner-announcement">🏆 WINNER: {name}! 🏆</h1>', unsafe_allow_html=True)
        
        # Winner details in celebration container
        st.markdown("""
        <div class="celebration-container">
            <div class="winner-card">
        """, unsafe_allow_html=True)
        
        level = str(w.get(COL_TICKET_LEVEL, "")).strip()
        loc = str(w.get(COL_LOCATION, "")).strip()
        observer = str(w.get(COL_OBSERVER, "")).strip()
        
        # Display winner info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### 🌟 Winner")
            st.markdown(f"**{name}**")
        with col2:
            if loc:
                st.markdown(f"### 🏢 Location")
                st.markdown(f"**{loc}**")
        with col3:
            if level:
                st.markdown(f"### 🎫 Ticket Level")
                st.markdown(f"**{level}**")
        
        if observer:
            st.markdown(f"### 👀 Nominated by: **{observer}**")
        
        st.markdown(f"### 📊 Selected from row **{winner_idx + 1}** of **{len(df)}** participants")
        
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Photo fetching and card generation
        photo_field = str(w.get(COL_PHOTO_URL, "")).strip()
        user_id = str(w.get(COL_USER_ID, "")).strip()  # Get actual user ID from CSV

        # Fetch photo server-side via API token
        with st.spinner("🖼️ Fetching winner photo..."):
            try:
                # Use the actual user ID from CSV instead of employee name
                photo_bytes = fetch_photo_bytes(photo_field, user_id)
                if photo_bytes:
                    st.success(f"✅ Photo loaded successfully! Size: {len(photo_bytes)} bytes")
                    # Debug: Check if it's actually image data
                    if photo_bytes.startswith(b'\xff\xd8') or photo_bytes.startswith(b'\x89PNG'):
                        st.info("🖼️ Valid image format detected")
                    else:
                        st.warning("⚠️ Photo data format might be invalid")
                        st.write(f"First 50 bytes: {photo_bytes[:50]}")
                else:
                    st.warning("⚠️ Could not load photo - will create card without photo")
            except Exception as e:
                st.error(f"❌ Photo fetch failed: {e}")
                photo_bytes = None

        # Generate and display winner card
        with st.spinner("🎨 Creating winner card..."):
            card = draw_winner_card(name=name, location=loc, level=level, photo_bytes=photo_bytes)
            
        st.markdown("### 🎊 Winner Card Generated!")
        st.image(card, caption=f"🏆 Winner: {name}", use_container_width=True)
        
        # Download section
        buf = io.BytesIO()
        card.save(buf, format="PNG")
        st.download_button(
            "📥 Download Winner Card (PNG)",
            buf.getvalue(),
            file_name=f"winner_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png",
            help="Click to download the winner card as a PNG file"
        )
        
        # Reset celebration button
        if st.button("🔄 Pick Another Winner", key="reset_winner"):
            st.session_state.celebration_mode = False
            st.session_state.winner_announced = False
            if "winner_row" in st.session_state:
                del st.session_state["winner_row"]
            if "winner_index" in st.session_state:
                del st.session_state["winner_index"]
            st.rerun()

# Footer with MVN branding
st.markdown("---")
logo_b64, _ = load_mvn_logo()
if logo_b64:
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-family: 'Poppins', sans-serif;">
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
            <img src="data:image/png;base64,{logo_b64}" style="height: 40px; margin-right: 15px;">
            <div>
                <p style="margin: 0;"><strong>Moon Valley Nurseries</strong></p>
                <p style="margin: 0; font-size: 0.9rem;">Great Save Raffle System</p>
            </div>
            <img src="data:image/png;base64,{logo_b64}" style="height: 40px; margin-left: 15px;">
        </div>
        <p>🎯 Simple • 🎨 Beautiful • 🚀 Fast</p>
        <p>Made with ❤️ using Streamlit + KPA API</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; color: #666; font-family: 'Poppins', sans-serif;">
        <p>✨ <strong>Moon Valley Nurseries - Great Save Raffle System</strong> ✨</p>
        <p>🎯 Simple • 🎨 Beautiful • 🚀 Fast</p>
        <p>Made with ❤️ using Streamlit + KPA API</p>
    </div>
    """, unsafe_allow_html=True)

# 🎉 MVN Great Save Raffle System - Public Deployment

## 🌟 Quick Start

### Option 1: Use the Startup Script
```bash
./start_raffle_system.sh
```

### Option 2: Manual Startup
```bash
# Start KPA API Server
python3 kpa_api_server.py &

# Start Streamlit App with external access
streamlit run streamlit_csv_raffle.py --server.address 0.0.0.0 --server.port 8502
```

## 🌐 Access URLs

### For Public Access:
- **Primary External URL**: `http://172.182.200.128:8502`
- **Network URL**: `http://10.0.0.175:8502`
- **Local URL**: `http://localhost:8502`

### For Development:
- **KPA API Server**: `http://localhost:5001`

## 📱 Mobile Features

### ✅ Responsive Design
- **Adaptive text sizing**: Uses `clamp()` for perfect scaling
- **Mobile-first CSS**: Optimized for phones and tablets
- **Touch-friendly buttons**: Large, easy-to-tap interface
- **Flexible layouts**: Columns stack on small screens

### ✅ Mobile Optimizations
- **Viewport meta tag**: Proper mobile scaling
- **Simplified navigation**: Minimal UI for mobile
- **Fast loading**: Optimized assets and code
- **Cross-platform**: Works on iOS, Android, desktop

## 🎯 Key Features

### 🎪 Core Functionality
- **CSV Upload**: Drag & drop participant data
- **Random Winner Selection**: With countdown & drumroll
- **Photo Integration**: Automatic employee photos via KPA API
- **Winner Cards**: Beautiful PNG downloads with MVN branding
- **Statistics Dashboard**: Real-time participant analytics

### 🎨 User Experience
- **Celebration Animations**: Countdown, drumroll, confetti
- **MVN Branding**: Dual logos and corporate colors
- **Mobile Responsive**: Perfect on any device
- **Public Access**: Share via web link

## 🛠️ Technical Stack

- **Frontend**: Streamlit with custom CSS/HTML
- **Backend**: Flask API server for photo proxy
- **Integration**: KPA API for employee photos
- **Styling**: Mobile-first responsive design
- **Deployment**: Docker container ready

## 🔧 Configuration

### Streamlit Config (`.streamlit/config.toml`)
```toml
[server]
headless = true
port = 8502
address = "0.0.0.0"
enableCORS = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
```

### KPA API Configuration
- **Token**: Configured in `.streamlit/secrets.toml`
- **Proxy Server**: Handles photo requests on port 5001
- **CORS Enabled**: For cross-origin requests

## 📋 Usage Instructions

### For End Users:
1. **Visit the public URL**: `http://172.182.200.128:8502`
2. **Upload CSV file**: Drag & drop your participant data
3. **Review statistics**: Check participant counts and charts
4. **Pick winner**: Click "PICK RANDOM WINNER!" for full experience
5. **Download card**: Get the winner card as PNG

### For Administrators:
1. **Monitor logs**: Check server output for issues
2. **Update data**: Replace CSV files as needed
3. **Restart services**: Use `./start_raffle_system.sh`
4. **Access controls**: Configure as needed for security

## 🛑 Stopping Services

```bash
# Stop all raffle services
pkill -f "streamlit|kpa_api_server"

# Or stop individual services
pkill -f streamlit
pkill -f kpa_api_server
```

## 🔒 Security Notes

- **Public Access**: App is accessible to anyone with the URL
- **No Authentication**: Currently open access (as requested)
- **Photo Proxy**: KPA credentials stored securely in secrets
- **File Uploads**: Limited to CSV files, 200MB max

## 📞 Support

For technical issues or questions:
- **Check logs**: Server output for error messages
- **Restart services**: Often resolves temporary issues
- **Verify URLs**: Ensure correct external access URLs
- **Test mobile**: Verify responsive design on actual devices

---

**Made with ❤️ for Moon Valley Nurseries**

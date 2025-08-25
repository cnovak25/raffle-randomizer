#!/bin/bash

# MVN Great Save Raffle - Public Deployment Script
echo "🎉 Starting MVN Great Save Raffle System..."

# Kill any existing processes
echo "🔄 Stopping existing services..."
pkill -f "streamlit\|kpa_api_server" 2>/dev/null || true
fuser -k 5001/tcp 2>/dev/null || true
sleep 3

# Start KPA API Server
echo "🚀 Starting KPA Photo Server on port 5001..."
cd /workspaces/raffle-randomizer
python3 kpa_api_server.py &
KPA_PID=$!
sleep 3

# Start Streamlit App with external access
echo "🎪 Starting Raffle App on port 8502..."
streamlit run streamlit_csv_raffle.py \
    --server.address 0.0.0.0 \
    --server.port 8502 \
    --server.headless true \
    --browser.gatherUsageStats false &
STREAMLIT_PID=$!

# Display access information
echo ""
echo "🌟 ==============================================="
echo "🎉 MVN GREAT SAVE RAFFLE IS NOW LIVE!"
echo "🌟 ==============================================="
echo ""
echo "📱 MOBILE-FRIENDLY URLS:"
echo "   Local:    http://localhost:8502"
echo "   Network:  http://$(hostname -I | cut -d' ' -f1):8502"
echo "   External: http://172.182.200.128:8502"
echo ""
echo "🛠️  API Server: http://localhost:5001"
echo ""
echo "📋 FEATURES:"
echo "   ✅ Mobile responsive design"
echo "   ✅ External web access"
echo "   ✅ CSV upload & processing"
echo "   ✅ Photo integration with KPA"
echo "   ✅ Countdown & celebration animations"
echo "   ✅ MVN branding & logos"
echo ""
echo "🔧 Process IDs:"
echo "   KPA Server: $KPA_PID"
echo "   Streamlit:  $STREAMLIT_PID"
echo ""
echo "🛑 To stop: pkill -f 'streamlit|kpa_api_server'"
echo "🌟 ==============================================="

# Wait for processes
wait

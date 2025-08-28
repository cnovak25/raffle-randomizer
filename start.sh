#!/bin/bash
export PORT=${PORT:-8000}
echo "🚀 Starting KPA Photo Proxy on port $PORT"
echo "Working directory: $(pwd)"
echo "Python path: $(which python)"
echo "Checking if kpa_photo_proxy_railway.py exists:"
ls -la kpa_photo_proxy_railway.py

echo "Starting uvicorn..."
python -m uvicorn kpa_photo_proxy_railway:app --host 0.0.0.0 --port $PORT --log-level info

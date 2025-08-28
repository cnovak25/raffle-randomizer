#!/bin/bash
PORT=${PORT:-8000}
echo "🚀 Starting KPA Photo Proxy on port $PORT"
python -m uvicorn kpa_photo_proxy_railway:app --host 0.0.0.0 --port $PORT

#!/bin/bash
export PORT=${PORT:-8000}
echo "🚀 Starting FastAPI KPA Photo Proxy on port $PORT"
echo "Working directory: $(pwd)"
echo "Environment variables:"
env | grep -E "(PORT|KPA)" || echo "No PORT/KPA vars found"
echo "Starting FastAPI app..."
python -m uvicorn kpa_photo_proxy_railway:app --host 0.0.0.0 --port $PORT --log-level info

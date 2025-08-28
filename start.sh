#!/bin/bash
export PORT=${PORT:-8000}
echo "🚀 Starting Simple KPA Photo Proxy on port $PORT"
echo "Working directory: $(pwd)"
echo "Environment variables:"
env | grep -E "(PORT|KPA)" || echo "No PORT/KPA vars found"
echo "Starting Flask app..."
python simple_proxy.py

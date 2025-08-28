#!/bin/bash
export PORT=${PORT:-8000}
echo "🚀 Starting Simple KPA Photo Proxy on port $PORT"
echo "Working directory: $(pwd)"
python simple_proxy.py

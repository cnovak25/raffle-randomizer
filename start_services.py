#!/usr/bin/env python3
"""
Railway deployment script - starts both FastAPI proxy and Streamlit app
"""
import os
import subprocess
import threading
import time
import signal
import sys

def start_fastapi():
    """Start the FastAPI proxy server"""
    print("🚀 Starting FastAPI proxy server on port 8000...")
    try:
        # Run FastAPI in background
        process = subprocess.Popen([
            "python", "-m", "uvicorn", 
            "kpa_photo_proxy_railway:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
        return process
    except Exception as e:
        print(f"❌ FastAPI failed to start: {e}")
        return None

def start_streamlit():
    """Start the Streamlit app"""
    # Use Railway's PORT environment variable if available
    port = os.environ.get('PORT', '8501')
    print(f"🎯 Starting Streamlit app on port {port}...")
    try:
        # This will be the main process
        subprocess.run([
            "python", "-m", "streamlit", "run", "app.py", 
            "--server.port", port,
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--server.enableCORS", "false"
        ])
    except Exception as e:
        print(f"❌ Streamlit failed to start: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down services...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🎊 Starting MVN Great Save Raffle services...")
    
    # Start FastAPI proxy in background
    fastapi_process = start_fastapi()
    
    # Give FastAPI time to start
    time.sleep(3)
    
    # Start Streamlit in main thread
    start_streamlit()

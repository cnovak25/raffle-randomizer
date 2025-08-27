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
    """Start the FastAPI proxy server in background"""
    print("🚀 Starting FastAPI proxy server on port 8000...")
    try:
        # Start FastAPI in background using Popen (non-blocking)
        process = subprocess.Popen([
            "python", "-m", "uvicorn", 
            "kpa_photo_proxy_railway:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ FastAPI proxy started in background")
        return process
    except Exception as e:
        print(f"❌ FastAPI failed to start: {e}")
        return None

def start_streamlit():
    """Start the Streamlit app as main process"""
    # Use Railway's PORT environment variable if available
    port = os.environ.get('PORT', '8501')
    print(f"🎯 Starting Streamlit app on port {port}...")
    try:
        # This runs as the main process and blocks
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
    
    if fastapi_process:
        # Give FastAPI time to start
        print("⏱️  Waiting for FastAPI to initialize...")
        time.sleep(5)
        
        # Start Streamlit as main process (this will block and keep container alive)
        print("🎭 Starting Streamlit as primary service...")
        start_streamlit()
    else:
        print("❌ Failed to start FastAPI - exiting")
        sys.exit(1)

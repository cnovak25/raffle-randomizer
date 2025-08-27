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
    subprocess.run([
        "python", "-m", "uvicorn", 
        "kpa_photo_proxy_railway:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ])

def start_streamlit():
    """Start the Streamlit app"""
    print("🎯 Starting Streamlit app on port 8501...")
    subprocess.run([
        "streamlit", "run", "app.py", 
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false"
    ])

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down services...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🎊 Starting MVN Great Save Raffle services...")
    
    # Start FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Give FastAPI time to start
    time.sleep(3)
    
    # Start Streamlit in main thread
    start_streamlit()

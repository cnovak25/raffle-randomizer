#!/usr/bin/env python3
"""
Simple Railway startup script for Streamlit
"""
import os
import subprocess
import sys

def main():
    port = os.environ.get('PORT', '8501')
    print(f"🚀 Starting Streamlit on port {port}")
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'test_app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false'
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()

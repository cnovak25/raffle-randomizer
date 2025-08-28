#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    # Get the port from Railway
    port = os.environ.get('PORT', '8501')
    print(f"Starting Streamlit on port {port}")
    
    # Simple, direct command
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == '__main__':
    main()

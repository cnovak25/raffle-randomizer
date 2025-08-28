#!/usr/bin/env python3
import os
import subprocess
import sys

# Use Railway's PORT directly - this is where Railway expects the service to respond
port = os.environ.get('PORT', '8501')
print(f"Railway PORT: {port}")
print(f"Starting Streamlit on Railway's expected port: {port}")

# Run streamlit on Railway's assigned port
cmd = [
    sys.executable, '-m', 'streamlit', 'run', 'minimal_test.py',
    '--server.port', str(port),
    '--server.address', '0.0.0.0',
    '--server.headless', 'true',
    '--server.enableCORS', 'false'
]

print(f"Running: {' '.join(cmd)}")
subprocess.run(cmd)

#!/usr/bin/env python3
import os
import subprocess
import sys

# Get port from environment or default to 8501
port = os.environ.get('PORT', '8501')
print(f"Railway PORT: {port}")
print(f"All env vars with PORT: {[k for k in os.environ.keys() if 'PORT' in k]}")

# Run streamlit with explicit port
cmd = [
    sys.executable, '-m', 'streamlit', 'run', 'minimal_test.py',
    '--server.port', str(port),
    '--server.address', '0.0.0.0',
    '--server.headless', 'true',
    '--server.enableCORS', 'false'
]

print(f"Running: {' '.join(cmd)}")
subprocess.run(cmd)

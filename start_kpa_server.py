#!/usr/bin/env python3
"""
KPA API Server Startup Script
Simplified startup to avoid import issues
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, '/workspaces/raffle-randomizer')

# Ensure user site-packages are in the path
import site
site.addsitedir('/home/vscode/.local/lib/python3.11/site-packages')

try:
    # Now import and run the KPA API server
    print("🚀 Starting KPA API Server...")
    print("📦 Loading dependencies...")
    
    from flask import Flask, request, jsonify, g
    from flask_cors import CORS
    import sqlite3
    import json
    import requests
    from dotenv import load_dotenv
    
    print("✅ Dependencies loaded successfully")
    print("🔧 Starting server...")
    
    # Load the server code
    exec(open('/workspaces/raffle-randomizer/kpa_api_server.py').read())
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("📝 Please install missing dependencies with: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Server Error: {e}")
    sys.exit(1)

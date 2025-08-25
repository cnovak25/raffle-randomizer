#!/usr/bin/env python3
"""
Simple test server to verify Flask functionality
"""

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "status": "success",
        "message": "Flask server is working correctly",
        "kpa_ready": True
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    print("🚀 Starting simple test server...")
    app.run(host='0.0.0.0', port=5001, debug=False)

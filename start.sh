#!/bin/bash
echo "🚀 Railway Start Script"
echo "PORT environment variable: $PORT"
echo "All PORT-related env vars:"
env | grep -i port || echo "No PORT env vars found"
echo "Starting with Python script..."
python run_minimal.py

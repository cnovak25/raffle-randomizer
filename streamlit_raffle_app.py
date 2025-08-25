#!/usr/bin/env python3
"""
Streamlit Raffle App with KPA Integration
Automatically pulls data from KPA's Great Save Raffle form
"""

import streamlit as st
import requests
import json
import pandas as pd
import random
from datetime import datetime
import os

# KPA API Configuration
KPA_API_TOKEN = "pTfES8COPXiB3fCCE0udSxg1g2vslyB2q"
KPA_BASE_URL = "https://api.kpaehs.com/v1"
GREAT_SAVE_RAFFLE_FORM_ID = "289228"

def get_kpa_responses():
    """Get raffle submissions from KPA API"""
    try:
        url = f'{KPA_BASE_URL}/responses.list'
        payload = {
            'token': KPA_API_TOKEN,
            'form_id': GREAT_SAVE_RAFFLE_FORM_ID
        }
        
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('responses', [])
        else:
            st.error(f"Error getting KPA data: {response.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to KPA API: {str(e)}")
        return []

def get_response_details(response_id):
    """Get detailed information for a specific response"""
    try:
        url = f'{KPA_BASE_URL}/responses.info'
        payload = {
            'token': KPA_API_TOKEN,
            'response_id': response_id
        }
        
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error getting response details: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="Great Save Raffle",
        page_icon="🎯",
        layout="wide"
    )
    
    st.title("🎯 Great Save Raffle")
    st.subheader("Powered by KPA API Integration")
    
    # Sidebar with KPA integration status
    with st.sidebar:
        st.header("🔗 KPA Integration")
        
        # Test KPA connectivity
        if st.button("Test KPA Connection"):
            with st.spinner("Testing KPA API..."):
                responses = get_kpa_responses()
                if responses is not None:
                    st.success(f"✅ Connected! Found {len(responses)} submissions")
                else:
                    st.error("❌ Connection failed")
        
        st.info(f"Form ID: {GREAT_SAVE_RAFFLE_FORM_ID}")
        st.info("API: KPA v1")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Current Submissions")
        
        # Get current submissions
        with st.spinner("Loading submissions from KPA..."):
            responses = get_kpa_responses()
        
        if responses:
            # Create DataFrame for display
            submission_data = []
            for i, response in enumerate(responses):
                submission_data.append({
                    'Entry #': i + 1,
                    'Response ID': response.get('id', 'N/A'),
                    'Date Submitted': response.get('date_created', 'N/A'),
                    'Status': response.get('status', 'Active')
                })
            
            df = pd.DataFrame(submission_data)
            st.dataframe(df, use_container_width=True)
            
            # Show detailed view for selected response
            if st.checkbox("Show detailed view"):
                selected_idx = st.selectbox(
                    "Select submission to view details:",
                    range(len(responses)),
                    format_func=lambda x: f"Entry #{x+1} - {responses[x].get('id')}"
                )
                
                if selected_idx is not None:
                    response_id = responses[selected_idx].get('id')
                    details = get_response_details(response_id)
                    
                    if details:
                        st.subheader("📋 Submission Details")
                        st.json(details)
        else:
            st.info("No submissions found yet. The form is ready to receive entries!")
            
            # Show sample data for demonstration
            st.subheader("📊 Sample Data (for testing)")
            sample_data = [
                {'Name': 'John Doe', 'Department': 'Operations', 'Email': 'john.doe@mvncorp.com'},
                {'Name': 'Jane Smith', 'Department': 'Safety', 'Email': 'jane.smith@mvncorp.com'},
                {'Name': 'Mike Johnson', 'Department': 'Maintenance', 'Email': 'mike.johnson@mvncorp.com'},
            ]
            st.dataframe(pd.DataFrame(sample_data))
    
    with col2:
        st.header("🎰 Raffle Controls")
        
        if responses:
            st.success(f"**{len(responses)}** entries ready")
            
            if st.button("🎯 Draw Winner!", type="primary", use_container_width=True):
                if responses:
                    winner = random.choice(responses)
                    
                    st.balloons()
                    st.success("🎉 We have a winner!")
                    
                    # Get winner details
                    details = get_response_details(winner.get('id'))
                    if details:
                        st.write(f"**Winner:** {details.get('employee_name', 'N/A')}")
                        st.write(f"**Department:** {details.get('department', 'N/A')}")
                        st.write(f"**Email:** {details.get('email', 'N/A')}")
                    else:
                        st.write(f"**Response ID:** {winner.get('id')}")
                    
                    st.write(f"**Drawn at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.warning("No entries available yet")
            st.info("Waiting for form submissions...")
        
        # Manual refresh
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🔗 **Connected to KPA API** | "
        f"Form: Great Save Raffle ({GREAT_SAVE_RAFFLE_FORM_ID}) | "
        "🏢 Moon Valley Nurseries"
    )

if __name__ == "__main__":
    main()

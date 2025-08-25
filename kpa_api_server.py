"""
KPA API Endpoints for MVN Raffle Integration
==========================================

This file contains the complete Flask/FastAPI implementation for the 4 required endpoints.
Choose the framework you prefer (Flask or FastAPI) and we'll customize it for your KPA system.

REQUIRED INFORMATION FROM KPA TEAM:
- Database connection details
- Employee table schema
- Photo storage system details
- Preferred Python framework (Flask/FastAPI/Django)
- API authentication method you're using
"""

# =============================================================================
# OPTION 1: FLASK IMPLEMENTATION
# =============================================================================

from flask import Flask, request, jsonify, g, Response
from flask_cors import CORS
import sqlite3
import os
import json
import requests
from datetime import datetime, timedelta
import hashlib
import hmac
import time
from functools import wraps
from threading import Lock
import logging
from dotenv import load_dotenv

# Load environment variables from secrets folder
load_dotenv('secrets/.env')

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting state (in production, use Redis or database)
rate_limit_state = {
    'requests': [],
    'lock': Lock(),
    'blocked_until': None
}

# Configuration
class Config:
    # KPA API configuration
    KPA_API_TOKEN = os.getenv('KPA_API_TOKEN')
    KPA_BASE_URL = os.getenv('KPA_BASE_URL', 'https://api.kpaehs.com/v1')
    
    # Rate limiting (KPA Flex API: ~80 requests per minute)
    KPA_RATE_LIMIT_PER_MINUTE = int(os.getenv('KPA_RATE_LIMIT_PER_MINUTE', 75))  # Set to 75 for safety margin
    KPA_RATE_LIMIT_WINDOW = int(os.getenv('KPA_RATE_LIMIT_WINDOW', 60))
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///kpa_raffle.db')
    
    # Photo storage configuration  
    PHOTO_SECRET_KEY = os.getenv('PHOTO_SECRET_KEY', 'default_secret_key')
    PHOTO_EXPIRY_HOURS = 1
    
    # Flask configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_flask_secret')

app.config.from_object(Config)

# Rate limiting functions for KPA Flex API
def check_rate_limit():
    """
    Check if we're within KPA Flex API rate limits
    Returns (allowed: bool, wait_time: int)
    """
    with rate_limit_state['lock']:
        now = time.time()
        
        # Check if we're currently blocked
        if rate_limit_state['blocked_until'] and now < rate_limit_state['blocked_until']:
            wait_time = int(rate_limit_state['blocked_until'] - now)
            return False, wait_time
        
        # Clean up old requests (older than rate limit window)
        cutoff_time = now - Config.KPA_RATE_LIMIT_WINDOW
        rate_limit_state['requests'] = [req_time for req_time in rate_limit_state['requests'] if req_time > cutoff_time]
        
        # Check if we're at the limit
        if len(rate_limit_state['requests']) >= Config.KPA_RATE_LIMIT_PER_MINUTE:
            return False, Config.KPA_RATE_LIMIT_WINDOW
        
        return True, 0

def record_api_request():
    """Record an API request for rate limiting"""
    with rate_limit_state['lock']:
        rate_limit_state['requests'].append(time.time())

def handle_kpa_rate_limit_error():
    """Handle rate limit exceeded response from KPA"""
    with rate_limit_state['lock']:
        # Block requests for 60 seconds as mentioned in KPA documentation
        rate_limit_state['blocked_until'] = time.time() + 60
        logger.warning("KPA API rate limit exceeded. Blocking requests for 60 seconds.")

def make_kpa_request(method, endpoint, **kwargs):
    """
    Make a request to KPA API with rate limiting and authentication
    KPA API uses token in POST body, not headers
    """
    # Check rate limit before making request
    allowed, wait_time = check_rate_limit()
    if not allowed:
        return {
            'error': 'rate_limit_exceeded',
            'message': f'Rate limit exceeded. Try again in {wait_time} seconds.',
            'wait_time': wait_time,
            'ok': False
        }, 429
    
    # Record this request
    record_api_request()
    
    # KPA API uses token in POST body, not headers
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Ensure we have a valid token
    if not Config.KPA_API_TOKEN or Config.KPA_API_TOKEN == 'your-token-here':
        return {
            'error': 'no_authentication',
            'message': 'No valid KPA API token configured. Please set KPA_API_TOKEN in .env file',
            'ok': False
        }, 401
    
    # Add token to the request body for KPA API
    if 'json' in kwargs:
        kwargs['json']['token'] = Config.KPA_API_TOKEN
        kwargs['json']['pretty'] = True
    else:
        kwargs['json'] = {
            'token': Config.KPA_API_TOKEN,
            'pretty': True
        }
    
    url = f"{Config.KPA_BASE_URL}/{endpoint}"
    
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        
        # Check for KPA rate limit error
        if response.status_code == 429:
            handle_kpa_rate_limit_error()
            return {
                'error': 'rate_limit_exceeded',
                'message': 'KPA API rate limit exceeded. Requests blocked for 60 seconds.',
                'ok': False
            }, 429
        
        # Check for authentication issues
        if response.status_code == 401:
            return {
                'error': 'authentication_failed',
                'message': 'KPA API token invalid or expired',
                'ok': False
            }, 401
        
        # Try to parse JSON response
        try:
            return response.json(), response.status_code
        except ValueError:
            # If not JSON, return text response
            return {
                'error': 'invalid_response',
                'message': f'KPA API returned non-JSON response: {response.text[:200]}',
                'ok': False
            }, response.status_code
        
    except requests.RequestException as e:
        logger.error(f"KPA API request failed: {str(e)}")
        return {
            'error': 'kpa_api_error',
            'message': f'Failed to connect to KPA API: {str(e)}',
            'ok': False
        }, 500

def lookup_employee_name(user_id):
    """
    Look up employee name using KPA web interface autocomplete API.
    This uses the actual endpoint that the KPA web interface uses.
    """
    try:
        # Use the KPA web interface endpoint for employee lookup
        url = f"https://mvncorp.kpaehs.com/spa-api/autocomplete/data-list-items/135212"
        
        # Get session info from environment
        session_cookie = os.getenv('KPA_SESSION_COOKIE', '')
        csrf_token = os.getenv('KPA_CSRF_TOKEN', '')
        
        headers = {
            'Content-Type': 'application/json',
            'Cookie': session_cookie,
            'isc-csrf-token': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://mvncorp.kpaehs.com',
            'Referer': 'https://mvncorp.kpaehs.com/forms/analyze/289228',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        # Search payload - this searches for the user ID in the employee data list
        payload = {
            "search": user_id,
            "limit": 10,
            "offset": 0
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Look for a matching employee in the results
            if 'items' in data and data['items']:
                for item in data['items']:
                    # Check if this item contains our user ID
                    if 'value' in item and user_id in str(item.get('value', '')):
                        # Extract the display name
                        display_name = item.get('label', item.get('text', ''))
                        # Filter out meaningless responses
                        if display_name and display_name != user_id and not any(bad_phrase in display_name.lower() for bad_phrase in ['does not qualify', 'not qualify', 'unknown', 'invalid']):
                            logger.info(f"Found employee name for {user_id}: {display_name}")
                            return display_name
                            
                # If no exact match, try the first result but be more selective
                if data['items']:
                    first_item = data['items'][0]
                    display_name = first_item.get('label', first_item.get('text', ''))
                    # Only use it if it looks like a real name, not system data
                    if display_name and not any(bad_phrase in display_name.lower() for bad_phrase in ['does not qualify', 'not qualify', 'unknown', 'invalid', 'system', 'error']):
                        logger.info(f"Using filtered result for {user_id}: {display_name}")
                        return display_name
        
        logger.warning(f"No valid employee name found for user ID: {user_id}")
        return "Unknown"
        
    except Exception as e:
        logger.error(f"Error looking up employee name for {user_id}: {e}")
        return "Unknown"

# Simple authentication - remove this decorator since we're using direct KPA API access
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # No authentication required for local API server
        return f(*args, **kwargs)
    
    return decorated_function

# Database helper functions
def get_db_connection():
    """Get database connection - UPDATE THIS FOR YOUR DATABASE"""
    # Example for PostgreSQL:
    # import psycopg2
    # return psycopg2.connect(Config.DATABASE_URL)
    
    # Example for SQLite (for testing):
    conn = sqlite3.connect('kpa_test.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_test_database():
    """Initialize test database with sample data - REMOVE IN PRODUCTION"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            department TEXT,
            work_location TEXT,
            hire_date DATE,
            eligibility_level TEXT DEFAULT 'monthly',
            status TEXT DEFAULT 'active',
            raffle_eligible BOOLEAN DEFAULT 1,
            last_raffle_win TIMESTAMP,
            raffle_wins_count INTEGER DEFAULT 0,
            photo_path TEXT
        )
    ''')
    
    # Create employee name mapping table (code → name resolution)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_name_cache (
            employee_code TEXT PRIMARY KEY,  -- MVN00245, etc.
            employee_name TEXT NOT NULL,     -- Real name like "John Smith"
            kpa_user_id TEXT,               -- 664fb5de8c63e90b736e22b3
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT DEFAULT 'kpa_lookup'  -- How we got this name
        )
    ''')
    
    # Create raffle_winners table  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raffle_winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            prize_level TEXT NOT NULL,
            prize_description TEXT,
            drawn_date TIMESTAMP NOT NULL,
            drawn_by TEXT NOT NULL,
            raffle_session_id TEXT,
            location TEXT,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample employees
    sample_employees = [
        ('EMP001', 'John', 'Doe', 'john.doe@mvn.com', 'Safety', 'Phoenix Office', '2023-01-15', 'monthly', 'active', 1, None, 0, 'photos/john_doe.jpg'),
        ('EMP002', 'Jane', 'Smith', 'jane.smith@mvn.com', 'Operations', 'Austin Office', '2023-06-20', 'quarterly', 'active', 1, None, 0, 'photos/jane_smith.jpg'),
        ('EMP003', 'Bob', 'Johnson', 'bob.johnson@mvn.com', 'Management', 'Phoenix Office', '2022-03-10', 'annual', 'active', 1, None, 1, 'photos/bob_johnson.jpg')
    ]
    
    cursor.executemany('''
        INSERT OR REPLACE INTO employees 
        (employee_id, first_name, last_name, email, department, work_location, hire_date, eligibility_level, status, raffle_eligible, last_raffle_win, raffle_wins_count, photo_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_employees)
    
    conn.commit()
    conn.close()

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test local database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        conn.close()
        database_status = "connected"
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        database_status = f"error: {str(e)}"

    # Test KPA API connection using direct token
    kpa_status = "unknown"
    if Config.KPA_API_TOKEN and Config.KPA_API_TOKEN != 'your-token-here':
        try:
            # Test a simple KPA API call
            result, status_code = make_kpa_request('POST', 'responses.list', json={
                'form_id': 289228,  # Use integer, not string
                'limit': 1,
                'latest': True,
                'pretty': True
            })
            if status_code == 200:
                kpa_status = "connected"
            elif status_code == 429:
                kpa_status = "rate_limited"
            elif status_code == 401:
                kpa_status = "authentication_failed"
            else:
                kpa_status = f"error: {result.get('message', 'unknown error')}"
        except Exception as e:
            kpa_status = f"error: {str(e)}"
    else:
        kpa_status = "no_token_configured"

    # Check current rate limit status
    allowed, wait_time = check_rate_limit()
    rate_limit_status = {
        "requests_allowed": allowed,
        "wait_time_seconds": wait_time if not allowed else 0,
        "requests_in_window": len(rate_limit_state['requests']),
        "limit_per_minute": Config.KPA_RATE_LIMIT_PER_MINUTE
    }

    overall_status = "healthy"
    if database_status != "connected" or kpa_status not in ["connected", "rate_limited"]:
        overall_status = "degraded"

    return jsonify({
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": database_status,
            "kpa_api": kpa_status,
            "rate_limiting": rate_limit_status
        }
    })

@app.route('/api/v1/employees', methods=['GET'])
@require_api_key
def get_employees():
    """Get filtered list of employees for raffle from KPA Flex API"""
    try:
        # Parse query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        prize_level = request.args.get('prize_level')
        location = request.args.get('location')
        department = request.args.get('department')
        status = request.args.get('status', 'active')
        eligible_for_raffle = request.args.get('eligible_for_raffle', 'true').lower() == 'true'
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build KPA API request parameters
        kpa_params = {
            'limit': limit,
            'offset': offset
        }
        
        # Add filters to KPA request
        if status != 'all':
            kpa_params['status'] = status
        if date_from:
            kpa_params['hire_date_from'] = date_from
        if date_to:
            kpa_params['hire_date_to'] = date_to
        if location:
            kpa_params['location'] = location
        if department:
            kpa_params['department'] = department
        if eligible_for_raffle:
            kpa_params['raffle_eligible'] = True
        
        # Make request to KPA Flex API
        result, status_code = make_kpa_request('GET', '/employees', params=kpa_params)
        
        if status_code == 429:
            return jsonify({
                "error": "rate_limit_exceeded",
                "message": "KPA API rate limit exceeded. Please try again later.",
                "wait_time": result.get('wait_time', 60),
                "ok": False
            }), 429
        
        if status_code != 200:
            return jsonify({
                "error": "kpa_api_error",
                "message": result.get('message', 'Failed to retrieve employees from KPA'),
                "ok": False
            }), status_code
        
        # Process KPA response and format for raffle app
        employees_data = result.get('employees', [])
        total_count = result.get('total_count', len(employees_data))
        
        # Filter by prize level if specified (may need to be done locally if KPA doesn't support this filter)
        if prize_level:
            employees_data = [emp for emp in employees_data if emp.get('eligibility_level') == prize_level]
        
        # Format response for raffle app compatibility
        employee_list = []
        for emp in employees_data:
            employee_list.append({
                "employee_id": emp.get('employee_id', emp.get('id')),
                "first_name": emp.get('first_name', ''),
                "last_name": emp.get('last_name', ''),
                "email": emp.get('email', ''),
                "department": emp.get('department', ''),
                "work_location": emp.get('work_location', emp.get('location', '')),
                "hire_date": emp.get('hire_date', ''),
                "eligibility_level": emp.get('eligibility_level', prize_level or 'monthly'),
                "status": emp.get('status', 'active'),
                "raffle_eligible": emp.get('raffle_eligible', True),
                "last_raffle_win": emp.get('last_raffle_win'),
                "raffle_wins_count": emp.get('raffle_wins_count', 0)
            })
        
        return jsonify({
            "employees": employee_list,
            "total_count": total_count,
            "page": (offset // limit) + 1,
            "limit": limit,
            "filters_applied": {
                "date_from": date_from,
                "date_to": date_to,
                "prize_level": prize_level,
                "location": location,
                "department": department,
                "status": status,
                "eligible_for_raffle": eligible_for_raffle
            },
            "ok": True
        })
        
    except Exception as e:
        logger.error(f"Error in get_employees: {str(e)}")
        return jsonify({
            "error": "internal_error",
            "message": f"Internal server error: {str(e)}",
            "ok": False
        }), 500

@app.route('/api/v1/forms/submissions', methods=['GET'])
@require_api_key  
def get_form_submissions():
    """
    Get Great Save Raffle form submissions from KPA using responses.list
    
    Query Parameters:
    - form_id: Form ID (defaults to 289228 for Great Save Raffle)
    - date_from: Start date for submissions (ISO format)
    - date_to: End date for submissions (ISO format) 
    - limit: Number of results (default: 100)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Parse query parameters - default to Great Save Raffle form
        form_id = int(request.args.get('form_id', 289228))  # Great Save Raffle form ID as integer
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = min(int(request.args.get('limit', 100)), 500)  # Max 500 for performance
        offset = int(request.args.get('offset', 0))
        
        # Build KPA API request payload for responses.list
        request_payload = {
            'form_id': form_id,  # Must be integer, not string
            'limit': limit,
            'latest': True,  # Include actual response data
            'pretty': True   # Include whitespace for readability
        }
        
        # Add page parameter (KPA uses page, not offset)
        if offset > 0:
            page = (offset // limit) + 1
            request_payload['page'] = page
        
        if date_from:
            request_payload['after'] = date_from  # Use 'after' parameter for KPA API
        if date_to:
            request_payload['before'] = date_to   # Use 'before' parameter for KPA API
            
        # Make request to KPA responses.list endpoint
        result, status_code = make_kpa_request('POST', 'responses.list', json=request_payload)
        
        if status_code != 200:
            return jsonify({
                "error": "kpa_api_error",
                "message": f"KPA API error: {result.get('message', 'Unknown error')}",
                "ok": False,
                "kpa_status_code": status_code
            }), status_code
            
        # Process and format Great Save Raffle form submissions
        formatted_submissions = []
        
        for response in result.get('responses', []):
            # Get detailed response information using responses.info
            response_id = response.get('id')
            if response_id:
                detail_result, detail_status = make_kpa_request('POST', 'responses.info', json={
                    'response_id': response_id
                })
                
                if detail_status == 200 and detail_result.get('ok'):
                    response_data = detail_result.get('response', {})
                    latest = response_data.get('latest', {})
                    responses_data = latest.get('responses', {})
                    
                    # Map KPA form fields to our format based on actual form structure
                    # Field mappings discovered from form analysis:
                    # a4bcktf70id45ylq = "Name of employee that earned the Great Save Raffle ticket?" (user ID)
                    # km7d8el3bnzsjc3n = Observer name (person filling out form)
                    # bcnz1j0t5w31wt88 = Employee ID/Number
                    # qfugnl8mu4zh7agg = Prize level selection
                    # qkx2vzdeheydfssj = Department/Location code
                    # r69hud60slskiz35 = Description/reason
                    
                    nominated_employee_id = responses_data.get('a4bcktf70id45ylq', {}).get('value', {}).get('values', [''])[0] if responses_data.get('a4bcktf70id45ylq', {}).get('value', {}).get('values') else ''
                    observer_name = responses_data.get('km7d8el3bnzsjc3n', {}).get('value', {}).get('text', 'Unknown')
                    employee_id = responses_data.get('bcnz1j0t5w31wt88', {}).get('value', {}).get('text', '')
                    prize_level = responses_data.get('qfugnl8mu4zh7agg', {}).get('value', {}).get('values', [''])[0] if responses_data.get('qfugnl8mu4zh7agg', {}).get('value', {}).get('values') else ''
                    department_code = responses_data.get('qkx2vzdeheydfssj', {}).get('value', {}).get('values', [''])[0] if responses_data.get('qkx2vzdeheydfssj', {}).get('value', {}).get('values') else ''
                    description = responses_data.get('r69hud60slskiz35', {}).get('value', {}).get('text', '')
                    
                    # Extract photo attachments from form fields
                    # Photo fields: 02rih1l2u938808b and riggypq53qwmtqah contain attachments
                    photo_attachments = []
                    for field_id in ['02rih1l2u938808b', 'riggypq53qwmtqah']:
                        field_data = responses_data.get(field_id, {}).get('value', {})
                        attachments = field_data.get('attachments', [])
                        for attachment in attachments:
                            if attachment.get('key'):
                                # Create proxied photo URL through our Flask server
                                photo_url = f"http://localhost:5001/api/v1/photos/proxy?key={attachment['key']}"
                                photo_attachments.append({
                                    'key': attachment['key'],
                                    'url': photo_url,
                                    'original_url': f"https://mvncorp.kpaehs.com/get-upload?key={attachment['key']}"
                                })
                    
                    # Try to resolve nominated employee name from user ID
                    nominated_employee_name = "Unknown"
                    if nominated_employee_id:
                        try:
                            # Look up employee details using KPA web interface autocomplete
                            employee_name = lookup_employee_name(nominated_employee_id)
                            if employee_name and employee_name != "Unknown" and "Does Not Qualify" not in employee_name:
                                nominated_employee_name = employee_name
                            elif employee_id and employee_id != "Unknown":
                                # Use the employee ID to create a readable name
                                if " – " in employee_id:  # Format like "508-L1 – L2"
                                    emp_code = employee_id.split(" – ")[0]
                                    nominated_employee_name = f"Employee {emp_code}"
                                else:
                                    nominated_employee_name = f"Employee {employee_id}"
                            else:
                                # Fallback to shortened user ID
                                nominated_employee_name = f"Employee {nominated_employee_id[:8]}..."
                        except Exception as e:
                            logger.warning(f"Failed to lookup employee {nominated_employee_id}: {e}")
                            if employee_id and employee_id != "Unknown":
                                nominated_employee_name = f"Employee {employee_id}"
                            else:
                                nominated_employee_name = f"Employee {nominated_employee_id[:8]}..."
                    
                    formatted_submission = {
                        'response_id': response_id,
                        'form_id': form_id,
                        'submission_date': response.get('created'),
                        'employee_name': nominated_employee_name,  # The person who earned the ticket
                        'observer_name': observer_name,  # The person who filled out the form
                        'employee_id': employee_id,
                        'nominated_employee_id': nominated_employee_id,  # Raw user ID
                        'email': '',  # Not available in this form
                        'department': department_code,
                        'location': department_code,  # Using department code as location
                        'prize_level': prize_level,
                        'description': description,
                        'photos': photo_attachments,  # Add photo URLs for automatic retrieval
                        'photo_url': photo_attachments[0]['url'] if photo_attachments else None,  # Primary photo for easy access
                        'raw_response': response_data  # Include full response for debugging
                    }
                    formatted_submissions.append(formatted_submission)
        
        return jsonify({
            "submissions": formatted_submissions,
            "total": result.get('paging', {}).get('total', len(formatted_submissions)),
            "count": len(formatted_submissions),
            "limit": limit,
            "offset": offset,
            "form_id": form_id,
            "description": result.get('description', ''),
            "ok": True
        })
        
    except ValueError as e:
        logger.error(f"Invalid query parameters: {str(e)}")
        return jsonify({
            "error": "invalid_parameters",
            "message": f"Invalid query parameters: {str(e)}",
            "ok": False
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error in get_form_submissions: {str(e)}")
        return jsonify({
            "error": "internal_error",
            "message": f"Internal server error: {str(e)}",
            "ok": False
        }), 500


@app.route('/api/v1/forms/responses/<response_id>/info', methods=['GET'])
@require_api_key  
def get_response_info(response_id):
    """
    Get detailed information for a specific form response using KPA responses.info endpoint
    
    Path Parameters:
    - response_id: The ID of the form response to retrieve
    """
    try:
        # Validate response_id
        if not response_id:
            return jsonify({
                "error": "missing_response_id",
                "message": "Response ID is required",
                "ok": False
            }), 400
        
        # Build KPA API request payload for responses.info
        request_payload = {
            'response_id': response_id
        }
        
        # Make request to KPA responses.info endpoint
        result, status_code = make_kpa_request('POST', 'responses.info', json=request_payload)
        
        if status_code != 200:
            return jsonify({
                "error": "kpa_api_error", 
                "message": f"KPA API error: {result.get('message', 'Unknown error')}",
                "ok": False,
                "kpa_status_code": status_code
            }), status_code
            
        # Return the detailed response information
        response_info = result.get('response', {})
        
        return jsonify({
            "response_info": response_info,
            "response_id": response_id,
            "ok": True
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in get_response_info: {str(e)}")
        return jsonify({
            "error": "internal_error",
            "message": f"Internal server error: {str(e)}",
            "ok": False
        }), 500


@app.route('/api/v1/forms/submissions', methods=['POST'])
@require_api_key  
def submit_form():
    """
    PLACEHOLDER: Submit a new Great Save Raffle form entry to KPA
    
    Note: This endpoint is not yet implemented as we don't have the exact
    KPA API endpoint for form submissions. We currently support:
    - responses.list (get form responses)
    - responses.info (get detailed response data)
    
    For form submissions, users should submit directly through KPA's web interface.
    """
    return jsonify({
        "error": "not_implemented",
        "message": "Form submission endpoint not yet implemented. Please submit forms through KPA's web interface.",
        "available_endpoints": [
            "GET /api/v1/forms/submissions - Get form responses using responses.list",
            "GET /api/v1/forms/responses/<response_id>/info - Get detailed response using responses.info"
        ],
        "ok": False
    }), 501

@app.route('/api/v1/forms/great-save-raffle/info', methods=['GET'])
@require_api_key  
def get_great_save_raffle_info():
    """
    Get information about the Great Save Raffle form
    
    Returns form structure, fields, and current status
    """
    try:
        # Make request to KPA Forms API to get form details
        result, status_code = make_kpa_request('GET', '/v1/forms/Great Save Raffle/info')
        
        if status_code != 200:
            # Return default form info if KPA API unavailable
            return jsonify({
                "ok": True,
                "form_info": {
                    "form_name": "Great Save Raffle",
                    "description": "Monthly raffle for Great Save employees",
                    "auto_populate_fields": [
                        "employee_id",
                        "employee_name", 
                        "email",
                        "department",
                        "work_location",
                        "job_title",
                        "hire_date",
                        "manager_name"
                    ],
                    "user_input_fields": [
                        "photo_upload",
                        "consent_to_photo_use",
                        "emergency_contact",
                        "additional_notes"
                    ],
                    "required_fields": [
                        "photo_upload",
                        "consent_to_photo_use"
                    ]
                },
                "source": "default_config"
            })
        
        return jsonify({
            "ok": True,
            "form_info": result,
            "source": "kpa_api"
        })
        
    except Exception as e:
        logger.error(f"Error in get_great_save_raffle_info: {str(e)}")
        return jsonify({
            "error": "internal_error",
            "message": f"Internal server error: {str(e)}",
            "ok": False
        }), 500

@app.route('/api/v1/employees/<employee_id>/photo', methods=['GET'])
@require_api_key  
def get_employee_photo(employee_id):
    """Get employee photo URL from KPA Flex API"""
    try:
        # Make request to KPA Flex API for employee photo
        result, status_code = make_kpa_request('GET', f'/employees/{employee_id}/photo')
        
        if status_code == 429:
            return jsonify({
                "error": "rate_limit_exceeded",
                "message": "KPA API rate limit exceeded. Please try again later.",
                "wait_time": result.get('wait_time', 60),
                "ok": False
            }), 429
        
        if status_code == 404:
            return jsonify({
                "error": "photo_not_found",
                "message": "Photo not found for this employee",
                "ok": False
            }), 404
        
        if status_code != 200:
            return jsonify({
                "error": "kpa_api_error", 
                "message": result.get('message', 'Failed to retrieve photo from KPA'),
                "ok": False
            }), status_code
        
        # KPA should return photo URL or photo data
        photo_url = result.get('photo_url')
        if not photo_url:
            # If KPA returns photo data instead of URL, we might need to create a temporary URL
            photo_data = result.get('photo_data')
            if photo_data:
                # In a real implementation, you'd store this temporarily and return a URL
                # For now, return an error asking for URL-based photos
                return jsonify({
                    "error": "photo_format_unsupported",
                    "message": "Photo data format not supported. Please configure KPA to return photo URLs.",
                    "ok": False
                }), 400
        
        # Generate secure, time-limited photo URL if needed
        # If KPA already provides secure URLs, use them directly
        if photo_url.startswith('http'):
            secure_photo_url = photo_url
        else:
            # Generate secure URL for local photo paths
            expiry = int(time.time()) + (Config.PHOTO_EXPIRY_HOURS * 3600)
            message = f"{photo_url}:{expiry}"
            signature = hmac.new(
                Config.PHOTO_SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            secure_photo_url = f"{Config.PHOTO_BASE_URL}/{photo_url}?expires={expiry}&signature={signature}"
        
        return jsonify({
            "photo_url": secure_photo_url,
            "photo_id": result.get('photo_id', f"PHOTO_{employee_id}"),
            "last_updated": result.get('last_updated', datetime.now().isoformat()),
            "content_type": result.get('content_type', 'image/jpeg'),
            "ok": True
        })
        
    except Exception as e:
        logger.error(f"Error in get_employee_photo: {str(e)}")
        return jsonify({
            "error": "internal_error",
            "message": f"Internal server error: {str(e)}",
            "ok": False
        }), 500

@app.route('/api/v1/photos/proxy', methods=['GET'])
@require_api_key
def proxy_kpa_photo():
    """
    Proxy KPA photos using the web interface with session authentication
    Since the KPA API doesn't have upload endpoints, we use the web interface
    """
    try:
        photo_key = request.args.get('key')
        if not photo_key:
            return jsonify({
                "error": "missing_parameter",
                "message": "Photo key parameter is required",
                "ok": False
            }), 400
        
        # Construct the KPA photo URL (web interface)
        kpa_photo_url = f"https://mvncorp.kpaehs.com/get-upload?key={photo_key}"
        
        # Get session info from environment for authenticated requests
        session_cookie = os.getenv('KPA_SESSION_COOKIE', '')
        csrf_token = os.getenv('KPA_CSRF_TOKEN', '')
        
        if not session_cookie:
            return jsonify({
                "error": "no_session",
                "message": "KPA session cookie not configured",
                "ok": False
            }), 500
        
        headers = {
            'Cookie': session_cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Referer': 'https://mvncorp.kpaehs.com/forms/analyze/289228',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        if csrf_token:
            headers['isc-csrf-token'] = csrf_token
        
        # Fetch the photo from KPA web interface
        import requests as photo_requests
        try:
            logger.info(f"Fetching photo from KPA: {photo_key}")
            response = photo_requests.get(kpa_photo_url, headers=headers, timeout=30, stream=True)
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched photo for key: {photo_key}")
                
                # Determine content type
                content_type = response.headers.get('content-type', 'image/jpeg')
                
                # Stream the photo data back to the client
                def generate():
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
                
                return Response(
                    generate(),
                    mimetype=content_type,
                    headers={
                        'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                        'Content-Disposition': f'inline; filename="photo_{photo_key[-20:]}.jpg"'
                    }
                )
            
            else:
                logger.warning(f"Failed to fetch photo {photo_key}: HTTP {response.status_code}")
                return jsonify({
                    "error": "photo_fetch_failed",
                    "message": f"Failed to fetch photo from KPA (status: {response.status_code})",
                    "status_code": response.status_code,
                    "ok": False
                }), response.status_code
                
        except photo_requests.exceptions.Timeout:
            logger.error(f"Timeout fetching photo: {photo_key}")
            return jsonify({
                "error": "photo_timeout",
                "message": "Timeout while fetching photo from KPA",
                "ok": False
            }), 408
            
        except photo_requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching photo {photo_key}: {e}")
            return jsonify({
                "error": "photo_request_failed",
                "message": f"Failed to request photo from KPA: {str(e)}",
                "ok": False
            }), 502
        
    except Exception as e:
        logger.error(f"Error in proxy_kpa_photo: {str(e)}")
        return jsonify({
            "error": "internal_error",
            "message": f"Internal server error: {str(e)}",
            "ok": False
        }), 500

@app.route('/api/v1/raffle/winners', methods=['POST'])
@require_api_key
def record_raffle_winner():
    """Record a raffle winner to both local database and KPA Flex API"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['employee_id', 'prize_level', 'drawn_date', 'drawn_by']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": "validation_error",
                    "message": f"Missing required field: {field}",
                    "ok": False
                }), 400
        
        # Prepare winner data for KPA API
        winner_data = {
            "employee_id": data['employee_id'],
            "prize_level": data['prize_level'],
            "prize_description": data.get('prize_description', ''),
            "drawn_date": data['drawn_date'],
            "drawn_by": data['drawn_by'],
            "raffle_session_id": data.get('raffle_session_id', ''),
            "notes": data.get('notes', '')
        }
        
        # Record winner to KPA Flex API first
        result, status_code = make_kpa_request('POST', '/raffle/winners', json=winner_data)
        
        if status_code == 429:
            return jsonify({
                "error": "rate_limit_exceeded",
                "message": "KPA API rate limit exceeded. Winner not recorded. Please try again later.",
                "wait_time": result.get('wait_time', 60),
                "ok": False
            }), 429
        
        if status_code not in [200, 201]:
            # Log the error but still try to record locally
            logger.error(f"Failed to record winner to KPA API: {result}")
        
        # Also record to local database for backup/caching
        try:
            # Get employee info for local record
            employee_result, emp_status = make_kpa_request('GET', f'/employees/{data["employee_id"]}')
            
            if emp_status == 200:
                employee = employee_result
                employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
                location = employee.get('work_location', '')
                department = employee.get('department', '')
            else:
                # Fallback if we can't get employee details
                employee_name = f"Employee {data['employee_id']}"
                location = ''
                department = ''
            
            # Store in local database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO raffle_winners 
                (employee_id, employee_name, prize_level, prize_description, drawn_date, drawn_by, raffle_session_id, location, department)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['employee_id'],
                employee_name,
                data['prize_level'],
                data.get('prize_description', ''),
                data['drawn_date'],
                data['drawn_by'],
                data.get('raffle_session_id', ''),
                location,
                department
            ))
            
            local_winner_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
        except Exception as local_error:
            logger.error(f"Failed to record winner locally: {str(local_error)}")
            local_winner_id = None
        
        # Determine response based on KPA API result
        if status_code in [200, 201]:
            return jsonify({
                "success": True,
                "winner_record_id": result.get('winner_record_id', local_winner_id),
                "message": "Winner recorded successfully to KPA and local database",
                "kpa_response": result,
                "ok": True
            })
        else:
            return jsonify({
                "success": False,
                "winner_record_id": local_winner_id,
                "message": "Winner recorded locally but failed to record to KPA API",
                "kpa_error": result,
                "ok": False
            }), 207  # Multi-status: partial success
        
    except Exception as e:
        logger.error(f"Error in record_raffle_winner: {str(e)}")
        return jsonify({
            "error": "internal_error",
            "message": f"Internal server error: {str(e)}",
            "ok": False
        }), 500

# =============================================================================
# RATE LIMITING MONITORING ENDPOINTS
# =============================================================================

@app.route('/api/v1/rate-limit/status', methods=['GET'])
@require_api_key
def get_rate_limit_status():
    """Get current rate limit status"""
    allowed, wait_time = check_rate_limit()
    
    with rate_limit_state['lock']:
        return jsonify({
            "rate_limit": {
                "allowed": allowed,
                "wait_time_seconds": wait_time if not allowed else 0,
                "requests_in_current_window": len(rate_limit_state['requests']),
                "limit_per_minute": Config.KPA_RATE_LIMIT_PER_MINUTE,
                "window_size_seconds": Config.KPA_RATE_LIMIT_WINDOW,
                "blocked_until": rate_limit_state['blocked_until'],
                "current_time": time.time()
            },
            "ok": True
        })

@app.route('/api/v1/rate-limit/reset', methods=['POST'])
@require_api_key  
def reset_rate_limit():
    """Reset rate limit state (for testing or emergency use)"""
    with rate_limit_state['lock']:
        rate_limit_state['requests'] = []
        rate_limit_state['blocked_until'] = None
        
    return jsonify({
        "message": "Rate limit state reset successfully",
        "ok": True
    })

# =============================================================================
# TESTING ENDPOINTS (REMOVE IN PRODUCTION)
# =============================================================================

@app.route('/api/v1/test/setup', methods=['POST'])
def setup_test_data():
    """Setup test data - REMOVE IN PRODUCTION"""
    try:
        init_test_database()
        return jsonify({"message": "Test database initialized successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/test/winners', methods=['GET'])
def get_test_winners():
    """Get all winners - FOR TESTING ONLY"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM raffle_winners ORDER BY created_at DESC')
        winners = cursor.fetchall()
        conn.close()
        
        winner_list = []
        for winner in winners:
            winner_list.append({
                "id": winner[0],
                "employee_id": winner[1],
                "employee_name": winner[2],
                "prize_level": winner[3],
                "drawn_date": winner[5],
                "drawn_by": winner[6]
            })
        
        return jsonify({"winners": winner_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize test database
    init_test_database()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=False)

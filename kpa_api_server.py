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

from flask import Flask, request, jsonify, g
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
    KPA_BASE_URL = os.getenv('KPA_BASE_URL', 'https://your-kpa-instance.com/api')
    
    # Rate limiting (KPA Flex API: ~80 requests per minute)
    KPA_RATE_LIMIT_PER_MINUTE = int(os.getenv('KPA_RATE_LIMIT_PER_MINUTE', 75))  # Set to 75 for safety margin
    KPA_RATE_LIMIT_WINDOW = int(os.getenv('KPA_RATE_LIMIT_WINDOW', 60))
    
    # Database configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///kpa_raffle.db')
    
    # API Security - MVN Raffle App authentication
    API_KEYS = {
        "mvn_raffle_key": {
            "name": "MVN Raffle App",
            "permissions": ["read_employees", "read_photos", "write_winners"],
            "active": True
        },
        "test-token-for-api-testing": {
            "name": "Test API Key",
            "permissions": ["read_employees", "read_photos", "write_winners", "read_forms"],
            "active": True
        }
    }
    
    # Photo storage configuration
    PHOTO_BASE_URL = f"{KPA_BASE_URL}/photos"
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
    if not Config.KPA_API_TOKEN or Config.KPA_API_TOKEN == 'pTfES8COPXiB3fCCE0udSxg1g2vslyB2q':
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

def get_okta_token():
    """
    Get OKTA access token for KPA API authentication
    Supports both service-to-service and user credential flows
    """
    okta_domain = os.getenv('OKTA_DOMAIN')
    okta_client_id = os.getenv('OKTA_CLIENT_ID') 
    okta_client_secret = os.getenv('OKTA_CLIENT_SECRET')
    okta_scope = os.getenv('OKTA_SCOPE', 'kpa_api_access')
    
    # User credentials for personal SSO login
    okta_username = os.getenv('OKTA_USERNAME')
    okta_password = os.getenv('OKTA_PASSWORD')
    
    if not okta_domain:
        logger.error("OKTA_DOMAIN not configured")
        return None
    
    try:
        # Method 1: User credentials flow (Resource Owner Password Credentials)
        if okta_username and okta_password:
            logger.info("Using OKTA user credentials authentication")
            token_url = f"https://{okta_domain}/oauth2/default/v1/token"
            
            auth_data = {
                'grant_type': 'password',
                'username': okta_username,
                'password': okta_password,
                'scope': okta_scope
            }
            
            auth_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            # Use client credentials if available, otherwise basic auth
            if okta_client_id and okta_client_secret:
                auth = (okta_client_id, okta_client_secret)
            else:
                auth = None
                auth_data['client_id'] = okta_client_id if okta_client_id else 'default'
            
            response = requests.post(
                token_url,
                data=auth_data,
                headers=auth_headers,
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                logger.info("Successfully obtained OKTA access token via user credentials")
                return access_token
            else:
                logger.error(f"OKTA user credentials authentication failed: {response.status_code} - {response.text}")
        
        # Method 2: Client credentials flow (service-to-service)
        elif okta_client_id and okta_client_secret:
            logger.info("Using OKTA client credentials authentication")
            token_url = f"https://{okta_domain}/oauth2/default/v1/token"
            
            auth_data = {
                'grant_type': 'client_credentials',
                'scope': okta_scope
            }
            
            auth_headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                token_url,
                data=auth_data,
                headers=auth_headers,
                auth=(okta_client_id, okta_client_secret),
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                logger.info("Successfully obtained OKTA access token via client credentials")
                return access_token
            else:
                logger.error(f"OKTA client credentials authentication failed: {response.status_code} - {response.text}")
        
        else:
            logger.error("Neither OKTA user credentials nor client credentials are configured")
            
        return None
            
    except Exception as e:
        logger.error(f"Error getting OKTA token: {str(e)}")
        return None

# Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authorization header must start with 'Bearer '"}), 401
        
        api_key = auth_header.replace('Bearer ', '')
        
        if api_key not in Config.API_KEYS:
            return jsonify({"error": "Invalid API key"}), 401
        
        if not Config.API_KEYS[api_key]["active"]:
            return jsonify({"error": "API key is inactive"}), 401
        
        g.api_key_info = Config.API_KEYS[api_key]
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
    
    # Test OKTA authentication
    okta_status = "unknown"
    okta_method = "none"
    okta_domain = os.getenv('OKTA_DOMAIN')
    okta_username = os.getenv('OKTA_USERNAME')
    okta_client_id = os.getenv('OKTA_CLIENT_ID')
    
    if okta_domain and okta_domain != 'your-company.okta.com':
        try:
            okta_token = get_okta_token()
            if okta_token:
                if okta_username:
                    okta_status = "connected_user_credentials"
                    okta_method = f"user: {okta_username}"
                elif okta_client_id:
                    okta_status = "connected_client_credentials"  
                    okta_method = f"client: {okta_client_id}"
                else:
                    okta_status = "connected_unknown_method"
            else:
                if okta_username:
                    okta_status = "user_authentication_failed"
                    okta_method = f"user: {okta_username}"
                else:
                    okta_status = "client_authentication_failed"
        except Exception as e:
            okta_status = f"error: {str(e)}"
    else:
        okta_status = "not_configured"
    
    # Test KPA session authentication  
    kpa_session_cookie = os.getenv('KPA_SESSION_COOKIE')
    kpa_csrf_token = os.getenv('KPA_CSRF_TOKEN')
    session_auth_status = "not_configured"
    
    if kpa_session_cookie and kpa_csrf_token:
        session_auth_status = "configured"
        if len(kpa_session_cookie) > 20 and len(kpa_csrf_token) > 10:
            session_auth_status = "session_available"
    
    # Test KPA API connection (with session authentication)  
    kpa_status = "unknown"
    if session_auth_status == "session_available":
        # Try multiple potential endpoints to find what works
        test_endpoints = ['/api/health', '/health', '/v1/health', '/api/v1/health', '/status']
        for endpoint in test_endpoints:
            result, status_code = make_kpa_request('GET', endpoint)
            if status_code == 200:
                kpa_status = f"connected_session (using {endpoint})"
                break
            elif status_code == 429:
                kpa_status = "rate_limited"
                break
            elif status_code == 401 or status_code == 403:
                kpa_status = "session_expired"
                break
        else:
            # If no endpoint worked, show the last error
            kpa_status = f"error: {result.get('message', 'unknown error')} (status: {status_code})"
    elif okta_status.startswith("connected"):
        result, status_code = make_kpa_request('GET', '/health')
        if status_code == 200:
            kpa_status = "connected"
        elif status_code == 429:
            kpa_status = "rate_limited"
        elif status_code == 401:
            kpa_status = "okta_authentication_failed"
        else:
            kpa_status = f"error: {result.get('message', 'unknown error')}"
    elif okta_status == "not_configured":
        # Fallback to direct token if OKTA not configured
        if Config.KPA_API_TOKEN:
            result, status_code = make_kpa_request('GET', '/health')
            if status_code == 200:
                kpa_status = "connected_direct_token"
            else:
                kpa_status = f"error: {result.get('message', 'unknown error')}"
        else:
            kpa_status = "no_authentication_configured"
    else:
        kpa_status = f"okta_issue: {okta_status}"
    
    # Check current rate limit status
    allowed, wait_time = check_rate_limit()
    rate_limit_status = {
        "requests_allowed": allowed,
        "wait_time_seconds": wait_time if not allowed else 0,
        "requests_in_window": len(rate_limit_state['requests']),
        "limit_per_minute": Config.KPA_RATE_LIMIT_PER_MINUTE
    }
    
    overall_status = "healthy"
    if database_status != "connected" or kpa_status not in ["connected", "connected_direct_token", "connected_session", "rate_limited"]:
        overall_status = "degraded"
    
    return jsonify({
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": database_status,
            "okta_sso": {
                "status": okta_status,
                "method": okta_method
            },
            "kpa_session": {
                "status": session_auth_status,
                "has_cookie": bool(kpa_session_cookie),
                "has_csrf_token": bool(kpa_csrf_token)
            },
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
        form_id = request.args.get('form_id', '289228')  # Great Save Raffle form ID
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        limit = min(int(request.args.get('limit', 100)), 500)  # Max 500 for performance
        offset = int(request.args.get('offset', 0))
        
        # Build KPA API request payload for responses.list
        request_payload = {
            'form_id': form_id,
            'limit': limit,
            'offset': offset
        }
        
        if date_from:
            request_payload['date_from'] = date_from
        if date_to:
            request_payload['date_to'] = date_to
            
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
        
        for submission in result.get('responses', []):
            # Extract key information from form submission
            formatted_submission = {
                'response_id': submission.get('response_id'),
                'form_id': submission.get('form_id'),
                'employee_id': submission.get('employee_id'),
                'submission_date': submission.get('date_created'),
                'employee': {
                    'full_name': submission.get('employee_name'),
                    'email': submission.get('employee_email'),
                    'employee_id': submission.get('employee_id')
                },
                'submission_data': submission.get('submission_data', {}),
                'raw_response': submission  # Include full response for debugging
            }
            formatted_submissions.append(formatted_submission)
        
        return jsonify({
            "submissions": formatted_submissions,
            "total": result.get('total', len(formatted_submissions)),
            "count": len(formatted_submissions),
            "limit": limit,
            "offset": offset,
            "form_id": form_id,
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

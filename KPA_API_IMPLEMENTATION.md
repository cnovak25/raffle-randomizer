# KPA API Implementation Checklist
# This file shows exactly what KPA needs to implement for the raffle integration

## Required KPA Database Schema Changes

### 1. Employee Table Additions
```sql
ALTER TABLE employees ADD COLUMN raffle_eligible BOOLEAN DEFAULT true;
ALTER TABLE employees ADD COLUMN eligibility_level VARCHAR(20) DEFAULT 'monthly';
ALTER TABLE employees ADD COLUMN last_raffle_participation TIMESTAMP;
ALTER TABLE employees ADD COLUMN raffle_wins_count INTEGER DEFAULT 0;
```

### 2. New Raffle Winners Table
```sql
CREATE TABLE raffle_winners (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    prize_level VARCHAR(50) NOT NULL,
    prize_description VARCHAR(255),
    drawn_date TIMESTAMP NOT NULL,
    drawn_by VARCHAR(100) NOT NULL,
    raffle_session_id VARCHAR(100),
    location VARCHAR(255),
    department VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
```

## API Endpoint Specifications

### 1. Health Check Endpoint
```python
# GET /api/v1/health
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0", 
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",
            "photo_storage": "available"
        }
    }
```

### 2. Employee List Endpoint
```python
# GET /api/v1/employees
@app.route('/api/v1/employees', methods=['GET'])
@require_api_key
def get_employees():
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
    
    # Build SQL query with filters
    query = """
        SELECT 
            employee_id,
            first_name,
            last_name, 
            email,
            department,
            work_location,
            hire_date,
            eligibility_level,
            status,
            raffle_eligible,
            last_raffle_participation,
            raffle_wins_count
        FROM employees 
        WHERE 1=1
    """
    
    params = []
    
    if status != 'all':
        query += " AND status = %s"
        params.append(status)
    
    if eligible_for_raffle:
        query += " AND raffle_eligible = true"
    
    if date_from:
        query += " AND hire_date >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND hire_date <= %s" 
        params.append(date_to)
        
    if prize_level:
        query += " AND eligibility_level = %s"
        params.append(prize_level)
        
    if location:
        query += " AND work_location ILIKE %s"
        params.append(f"%{location}%")
        
    if department:
        query += " AND department ILIKE %s"
        params.append(f"%{department}%")
    
    query += f" ORDER BY last_name, first_name LIMIT {limit} OFFSET {offset}"
    
    # Execute query
    employees = execute_query(query, params)
    total_count = get_total_count(query.replace('SELECT employee_id...', 'SELECT COUNT(*)'), params[:-2])
    
    return {
        "employees": [
            {
                "employee_id": emp.employee_id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "email": emp.email,
                "department": emp.department,
                "work_location": emp.work_location,
                "hire_date": emp.hire_date.isoformat(),
                "eligibility_level": emp.eligibility_level,
                "status": emp.status,
                "raffle_eligible": emp.raffle_eligible,
                "last_raffle_win": emp.last_raffle_participation.isoformat() if emp.last_raffle_participation else None
            }
            for emp in employees
        ],
        "total_count": total_count,
        "page": (offset // limit) + 1,
        "limit": limit
    }
```

### 3. Employee Photo Endpoint  
```python
# GET /api/v1/employees/{employee_id}/photo
@app.route('/api/v1/employees/<employee_id>/photo', methods=['GET'])
@require_api_key
def get_employee_photo(employee_id):
    # Get employee photo info from database
    photo_info = get_employee_photo_info(employee_id)
    
    if not photo_info:
        return {"error": "Photo not found"}, 404
    
    # Generate secure photo URL (valid for 1 hour)
    photo_url = generate_secure_photo_url(
        photo_info.photo_path,
        expiry_hours=1
    )
    
    return {
        "photo_url": photo_url,
        "photo_id": photo_info.photo_id,
        "last_updated": photo_info.last_updated.isoformat(),
        "content_type": "image/jpeg"
    }

def generate_secure_photo_url(photo_path, expiry_hours=1):
    """Generate time-limited signed URL for photo access"""
    import hmac
    import hashlib
    from urllib.parse import urlencode
    
    expiry = int(time.time()) + (expiry_hours * 3600)
    
    # Create signature
    message = f"{photo_path}:{expiry}"
    signature = hmac.new(
        PHOTO_SECRET_KEY.encode(),
        message.encode(), 
        hashlib.sha256
    ).hexdigest()
    
    # Build signed URL
    params = {
        'expires': expiry,
        'signature': signature
    }
    
    return f"{PHOTO_BASE_URL}/{photo_path}?{urlencode(params)}"
```

### 4. Record Winner Endpoint
```python
# POST /api/v1/raffle/winners
@app.route('/api/v1/raffle/winners', methods=['POST'])
@require_api_key
def record_raffle_winner():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['employee_id', 'prize_level', 'drawn_date', 'drawn_by']
    for field in required_fields:
        if field not in data:
            return {"error": f"Missing required field: {field}"}, 400
    
    # Get employee info
    employee = get_employee_by_id(data['employee_id'])
    if not employee:
        return {"error": "Employee not found"}, 404
    
    # Create winner record
    winner_record = {
        'employee_id': data['employee_id'],
        'employee_name': f"{employee.first_name} {employee.last_name}",
        'prize_level': data['prize_level'],
        'prize_description': data.get('prize_description', ''),
        'drawn_date': data['drawn_date'],
        'drawn_by': data['drawn_by'],
        'raffle_session_id': data.get('raffle_session_id', ''),
        'location': employee.work_location,
        'department': employee.department
    }
    
    # Insert into database
    winner_id = insert_raffle_winner(winner_record)
    
    # Update employee raffle stats
    update_employee_raffle_stats(
        data['employee_id'], 
        data['drawn_date']
    )
    
    return {
        "success": True,
        "winner_record_id": winner_id,
        "message": "Winner recorded successfully"
    }

def update_employee_raffle_stats(employee_id, drawn_date):
    """Update employee's raffle participation stats"""
    query = """
        UPDATE employees 
        SET 
            last_raffle_participation = %s,
            raffle_wins_count = raffle_wins_count + 1
        WHERE employee_id = %s
    """
    execute_query(query, [drawn_date, employee_id])
```

### 5. Authentication Middleware
```python
def require_api_key(f):
    """Decorator to require valid API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not api_key:
            return {"error": "API key required"}, 401
            
        if not validate_api_key(api_key):
            return {"error": "Invalid API key"}, 401
            
        return f(*args, **kwargs)
    return decorated_function

def validate_api_key(api_key):
    """Validate API key against database"""
    # Check if API key exists and is active
    key_info = get_api_key_info(api_key)
    return key_info and key_info.is_active
```

## Configuration Settings for KPA

### 1. API Keys Table
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    permissions TEXT[], -- e.g., ['read_employees', 'read_photos', 'write_winners']
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Insert raffle app API key
INSERT INTO api_keys (key_name, api_key, permissions, created_by) VALUES 
('MVN Raffle App', 'mvn_raffle_api_key_2024', 
 ARRAY['read_employees', 'read_photos', 'write_winners'], 'admin');
```

### 2. Rate Limiting Configuration
```python
# Rate limiting: 100 requests per minute per API key
RATE_LIMITS = {
    'read_employees': 30,  # per minute
    'read_photos': 100,    # per minute  
    'write_winners': 10    # per minute
}
```

### 3. Photo Storage Configuration
```python
# Photo storage settings
PHOTO_STORAGE = {
    'base_url': 'https://your-kpa-instance.com/api/v1/photos',
    'storage_path': '/var/kpa/photos/',
    'allowed_formats': ['jpg', 'jpeg', 'png'],
    'max_file_size': 5 * 1024 * 1024,  # 5MB
    'url_expiry_hours': 1
}
```

## Testing Endpoints

### Test with curl:
```bash
# 1. Health check
curl -H "Authorization: Bearer mvn_raffle_api_key_2024" \
     https://your-kpa-instance.com/api/v1/health

# 2. Get employees  
curl -H "Authorization: Bearer mvn_raffle_api_key_2024" \
     "https://your-kpa-instance.com/api/v1/employees?prize_level=monthly&limit=10"

# 3. Get employee photo
curl -H "Authorization: Bearer mvn_raffle_api_key_2024" \
     https://your-kpa-instance.com/api/v1/employees/EMP001/photo

# 4. Record winner
curl -X POST \
     -H "Authorization: Bearer mvn_raffle_api_key_2024" \
     -H "Content-Type: application/json" \
     -d '{"employee_id":"EMP001","prize_level":"monthly","drawn_date":"2024-08-24T15:30:00Z","drawn_by":"cnovak25"}' \
     https://your-kpa-instance.com/api/v1/raffle/winners
```

## Deployment Checklist

### ✅ Database Changes
- [ ] Add raffle fields to employees table
- [ ] Create raffle_winners table
- [ ] Create api_keys table
- [ ] Set up database indexes for performance

### ✅ API Implementation  
- [ ] Implement health check endpoint
- [ ] Implement employee list endpoint with filtering
- [ ] Implement photo URL endpoint with security
- [ ] Implement winner recording endpoint
- [ ] Add API key authentication

### ✅ Security & Performance
- [ ] Set up rate limiting
- [ ] Implement secure photo URLs
- [ ] Add request logging
- [ ] Set up monitoring/alerts

### ✅ Testing
- [ ] Unit tests for all endpoints
- [ ] Integration tests with raffle app
- [ ] Load testing for employee queries
- [ ] Security testing for API keys

### ✅ Documentation
- [ ] API documentation for raffle team
- [ ] Error code reference
- [ ] Rate limiting guidelines
- [ ] Security best practices

This implementation will give you a production-ready KPA API that seamlessly integrates with the raffle system! 🚀

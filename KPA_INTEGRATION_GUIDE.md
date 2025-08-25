# KPA API Integration for MVN Raffle System

## 🎯 Overview

This document outlines the complete KPA API integration design for the MVN Great Save Raffle system. The integration eliminates manual CSV uploads and provides real-time access to employee data and photos.

## 🌟 Benefits

### ✅ **Automated Data Retrieval**
- No more manual CSV uploads
- Real-time employee eligibility checking
- Automatic photo retrieval from KPA profiles

### ✅ **Smart Filtering**
- **Date Range**: Employees hired within specified timeframe
- **Prize Level**: Filter by monthly/quarterly/annual eligibility
- **Location**: Filter by work location or office
- **Department**: Filter by department or team
- **Status**: Only active employees

### ✅ **Enhanced User Experience**
- One-click participant loading
- Real-time data synchronization
- Automatic winner recording back to KPA

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit     │────▶│   KPA API       │────▶│   KPA Database  │
│   Raffle App    │     │   Integration   │     │   (Employee     │
│                 │◀────│                 │◀────│    Data)        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 📡 Required KPA API Endpoints

### 1. **Health Check Endpoint**
```
GET /api/v1/health
```
**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-08-24T15:30:00Z"
}
```

### 2. **Employee List Endpoint**
```
GET /api/v1/employees
```

**Query Parameters:**
- `date_from` (YYYY-MM-DD): Start date for eligibility filter
- `date_to` (YYYY-MM-DD): End date for eligibility filter  
- `prize_level` (string): "monthly", "quarterly", "annual"
- `location` (string): Work location filter
- `department` (string): Department filter
- `status` (string): "active", "inactive", "all"
- `eligible_for_raffle` (boolean): Only raffle-eligible employees
- `limit` (integer): Number of results per page
- `offset` (integer): Pagination offset

**Response:**
```json
{
  "employees": [
    {
      "employee_id": "EMP001",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@mvn.com",
      "department": "Safety Department", 
      "work_location": "Phoenix Office",
      "hire_date": "2023-01-15",
      "eligibility_level": "monthly",
      "status": "active",
      "raffle_eligible": true,
      "last_raffle_win": "2024-06-15T10:30:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "limit": 50
}
```

### 3. **Employee Photo Endpoint**
```
GET /api/v1/employees/{employee_id}/photo
```

**Response:**
```json
{
  "photo_url": "https://kpa-instance.com/api/v1/photos/EMP001.jpg",
  "photo_id": "PHOTO123",
  "last_updated": "2024-01-15T10:30:00Z",
  "content_type": "image/jpeg"
}
```

### 4. **Record Winner Endpoint**
```
POST /api/v1/raffle/winners
```

**Request Body:**
```json
{
  "employee_id": "EMP001",
  "prize_level": "monthly",
  "prize_description": "Level 1-(Red) Monthly Drawing",
  "drawn_date": "2024-08-24T15:30:00Z",
  "drawn_by": "cnovak25",
  "raffle_session_id": "RAFFLE_2024_08_24_001"
}
```

**Response:**
```json
{
  "success": true,
  "winner_record_id": "WIN001",
  "message": "Winner recorded successfully"
}
```

## 🔐 Authentication

### API Key Authentication (Recommended)
```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### OAuth 2.0 (Alternative)
```http
Authorization: Bearer ACCESS_TOKEN
Content-Type: application/json
```

## 📝 Implementation Steps

### Phase 1: Basic Integration (Week 1)
1. ✅ Set up KPA API credentials
2. ✅ Implement health check endpoint
3. ✅ Create employee list retrieval
4. ✅ Add basic error handling

### Phase 2: Photo Integration (Week 2)
1. ✅ Implement photo URL retrieval
2. ✅ Add photo fallback handling
3. ✅ Optimize image loading performance

### Phase 3: Advanced Features (Week 3)
1. ✅ Add winner recording to KPA
2. ✅ Implement advanced filtering
3. ✅ Add data validation and caching

### Phase 4: Production Ready (Week 4)
1. ✅ Add comprehensive error handling
2. ✅ Implement rate limiting
3. ✅ Add logging and monitoring
4. ✅ Performance optimization

## 🎛️ Configuration UI

The raffle app includes a user-friendly configuration interface:

### KPA Settings Panel
```python
# Configuration stored in Streamlit session state
{
  "api_url": "https://your-kpa-instance.com/api/v1",
  "api_key": "your_api_key_here", 
  "api_secret": "optional_secret",
  "connection_status": "connected",
  "last_sync": "2024-08-24T15:30:00Z"
}
```

### Quick Filters
- **Prize Level Selector**: Monthly/Quarterly/Annual
- **Date Range**: Last 30/60/90/365 days
- **Location Filter**: Text input for office/location
- **Department Filter**: Dropdown with available departments

## 🚀 Usage Flow

### 1. **Setup KPA Connection**
```python
# In Streamlit app
kpa = KPAIntegration(
    api_base_url="https://your-kpa.com/api/v1",
    api_key="your_api_key",
    api_secret="optional_secret"  
)

# Test connection
result = kpa.test_connection()
if result['success']:
    st.success("✅ KPA Connected!")
```

### 2. **Load Participants**
```python
# Get filtered participants
participants = kpa.get_participants(
    prize_level="monthly",
    location="Phoenix Office", 
    date_from="2024-07-01",
    date_to="2024-08-24"
)

# Format for raffle
df = kpa.format_for_raffle(participants['employees'])
```

### 3. **Run Raffle with KPA Data**
```python
# Raffle drawing (same process)
winner = df.sample(1).iloc[0]

# Record winner back to KPA
kpa.record_winner(
    employee_id=winner['Employee_ID'],
    prize_level="monthly",
    drawn_by="cnovak25"
)
```

## 📊 Data Mapping

### KPA ➡️ Raffle App Format
```python
KPA_FIELD               RAFFLE_APP_FIELD
────────────           ─────────────────
first_name + last_name  → Name
photo_url              → Photo  
eligibility_level      → Prize_Level
work_location          → Location
department             → Department
employee_id            → Employee_ID
hire_date              → Hire_Date
email                  → Email
```

### Prize Level Mapping
```python
KPA_LEVEL    MVN_FORMAT
─────────    ──────────────────────────────────
"monthly"    → "Level 1-(Red) Monthly Drawing"
"quarterly"  → "Level 2-(Green) Quarterly Drawing"  
"annual"     → "Level 3-(Gold) Annual Drawing Grand Prize"
```

## 🔧 Error Handling

### Connection Errors
```python
{
  "success": False,
  "error_type": "connection_error",
  "message": "Unable to connect to KPA API",
  "retry_after": 30
}
```

### Authentication Errors
```python
{
  "success": False, 
  "error_type": "auth_error",
  "message": "Invalid API key or permissions",
  "error_code": 401
}
```

### Data Errors
```python
{
  "success": False,
  "error_type": "data_error", 
  "message": "No employees found matching criteria",
  "filters_applied": {...}
}
```

## 🎯 Next Steps

### For KPA Development Team:
1. **Implement Required Endpoints**: Create the 4 core API endpoints
2. **Set Up Authentication**: Configure API key or OAuth system
3. **Employee Data Model**: Ensure employee records include raffle eligibility fields
4. **Photo Storage**: Implement secure photo URL generation
5. **Winner Tracking**: Add raffle winner recording capability

### For MVN Raffle Team:
1. **API Credentials**: Obtain KPA API access credentials
2. **Testing Environment**: Set up staging environment for testing
3. **User Training**: Train raffle operators on new KPA integration
4. **Rollout Plan**: Plan gradual rollout from manual CSV to automated KPA

## 💡 Benefits Summary

| Feature | Manual CSV | KPA Integration |
|---------|------------|-----------------|
| Setup Time | 5-10 minutes | 30 seconds |
| Data Accuracy | Manual entry errors | Real-time, accurate |
| Photo Loading | Manual ZIP upload | Automatic from KPA |
| Eligibility Checking | Manual filtering | Automated rules |
| Winner Recording | Manual tracking | Automatic logging |
| Scalability | Limited | Unlimited |

## 🔄 Migration Path

### Week 1: Parallel Operation
- Keep existing CSV method
- Add KPA integration as option
- Test with small groups

### Week 2: Primary KPA
- Make KPA the primary method
- Keep CSV as backup
- Train all operators

### Week 3: KPA Only  
- Remove CSV upload option
- Full KPA integration
- Monitor and optimize

### Week 4: Enhancement
- Add advanced KPA features
- Implement winner analytics
- Optimize performance

This KPA integration will transform the raffle system from a manual process to a fully automated, real-time employee engagement platform! 🚀

# KPA Forms Integration for Raffle System

## Overview

You're absolutely right! The raffle submissions should be handled through KPA's forms system rather than just pulling employee data. This approach is much more aligned with how KPA actually works, where raffle participants submit their information (including photos) through a KPA form.

## How It Should Work

### 1. **Form Creation in KPA**
The KPA team would create a raffle submission form with fields like:
- Employee ID (auto-populated if logged in)
- Employee Name 
- Email
- Department
- Location/Office
- Photo Upload
- Consent to use photo
- Emergency contact information
- Any other raffle-specific questions

### 2. **Form Submissions Flow**
```
Employee fills out raffle form → Form submitted to KPA → Our API pulls submissions → Raffle app processes entries
```

### 3. **API Endpoints Added**

#### GET `/api/v1/forms/submissions`
Retrieve raffle form submissions from KPA
```json
{
  "form_id": "raffle-form-2024",
  "date_from": "2024-01-01",
  "date_to": "2024-12-31",
  "status": "submitted",
  "limit": 100,
  "offset": 0
}
```

Response includes:
- Submission ID
- Employee information
- Form responses (all field data)
- Photo information
- Submission date
- Status

#### POST `/api/v1/forms/submissions`
Submit new raffle entry (if needed for manual entries)
```json
{
  "form_id": "raffle-form-2024",
  "employee_id": "12345",
  "form_data": {
    "employee_name": "John Doe",
    "email": "john.doe@company.com",
    "department": "Engineering", 
    "location": "Main Office",
    "photo": "uploaded_photo_data",
    "consent_to_photo_use": true
  }
}
```

## Benefits of Forms-Based Approach

### ✅ **Proper Data Flow**
- Follows KPA's natural workflow
- Employees use familiar KPA interface
- Form validation built into KPA
- Audit trail of submissions

### ✅ **Better Photo Management**
- Photos uploaded directly to KPA
- Proper permissions and consent handling
- KPA handles image processing/storage
- Consistent with other KPA workflows

### ✅ **Enhanced Data Collection**
- Can collect additional raffle-specific info
- Consent forms and legal requirements
- Custom questions per raffle
- Better data validation

### ✅ **Administrative Control**
- KPA admins can review submissions
- Form can be enabled/disabled per raffle
- Better tracking and reporting
- Integration with KPA's permission system

## Implementation Notes

### For KPA Team
1. **Create the raffle form** in KPA with all necessary fields
2. **Configure form permissions** (who can submit, when)
3. **Set up photo upload** with appropriate size/format limits
4. **Enable API access** to the forms endpoints
5. **Provide form ID** to the raffle app team

### For Raffle App
1. **Use forms endpoints** instead of just employee endpoints
2. **Filter by form ID** to get only raffle submissions
3. **Handle photo URLs** from form submissions
4. **Process form responses** for raffle logic
5. **Track submission IDs** for winner recording

## Migration Path

If currently using CSV uploads:
1. Create KPA form matching current CSV structure
2. Import existing data as form submissions (if needed)
3. Switch raffle app to use forms API
4. Train users on new KPA form process
5. Disable CSV upload feature

This approach is much more sustainable and follows KPA's intended usage patterns!

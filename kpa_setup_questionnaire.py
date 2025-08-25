"""
KPA API Configuration Questionnaire
==================================

Please provide the following information so I can customize the API endpoints for your KPA system:

STEP 1: BASIC SETUP
==================
1. What's your API token that you generated? 
   → We'll use this as the Bearer token for authentication

2. What Python web framework do you prefer?
   a) Flask (simple, lightweight)
   b) FastAPI (modern, automatic docs)
   c) Django (full framework)
   d) Other (specify)

3. What database system does KPA use?
   a) PostgreSQL
   b) MySQL/MariaDB  
   c) SQL Server
   d) Oracle
   e) SQLite (for testing)
   f) Other (specify)

STEP 2: DATABASE SCHEMA
======================
4. What's your employee table called?
   → Common names: "employees", "users", "staff", "personnel"

5. What are the column names in your employee table?
   → We need to map these fields:
   - Employee ID (e.g., "employee_id", "emp_id", "id")
   - First Name (e.g., "first_name", "fname", "given_name")
   - Last Name (e.g., "last_name", "lname", "surname")
   - Email (e.g., "email", "email_address")
   - Department (e.g., "department", "dept", "division")
   - Location (e.g., "location", "office", "work_location")
   - Hire Date (e.g., "hire_date", "start_date", "date_hired")
   - Status (e.g., "status", "active", "employment_status")

6. Do you have existing fields for raffle eligibility?
   → If not, we'll need to add:
   - raffle_eligible (boolean)
   - eligibility_level (text: monthly/quarterly/annual)
   - last_raffle_win (datetime)
   - raffle_wins_count (integer)

STEP 3: PHOTO STORAGE
====================
7. How are employee photos stored in your system?
   a) File paths in database (e.g., "/photos/employee123.jpg")
   b) URLs in database (e.g., "https://photos.kpa.com/emp123.jpg")
   c) Separate photo service/API
   d) Cloud storage (AWS S3, Azure Blob, etc.)
   e) Local file system

8. What's your photo storage base URL?
   → Example: "https://your-kpa-instance.com/photos"

STEP 4: DEPLOYMENT
=================
9. Where will you deploy the API?
   a) Same server as main KPA application
   b) Separate server/container
   c) Cloud service (AWS, Azure, GCP)
   d) Docker container

10. What port should the API run on?
    → Common choices: 5000, 8000, 8080, 3000

STEP 5: SECURITY
===============
11. Do you want to use your existing API token as-is, or should we create a new API key system?

12. Should we add rate limiting?
    → Recommended: 100 requests per minute per API key

QUICK START OPTION
=================
If you want to test immediately, I can set up a working demo with:
- SQLite database (for testing)
- Sample employee data
- Your API token
- Flask web server on port 5000

Just provide your API token and we can have it running in 5 minutes!

NEXT STEPS
=========
Once you provide this information, I'll:
1. Customize the API code for your specific system
2. Provide database migration scripts
3. Set up testing endpoints
4. Create deployment instructions
5. Test the integration with the raffle app
"""

print("KPA API Configuration Helper")
print("=" * 50)
print()
print("Hi KPA Team! 👋")
print()
print("I'm ready to help you set up the API endpoints for the MVN raffle integration.")
print("Please provide the information requested in the configuration file above.")
print()
print("For a QUICK START demo, just tell me:")
print("1. Your API token")
print("2. Your preferred database (or SQLite for testing)")
print("3. Any specific requirements")
print()
print("And I'll have a working API server running for you to test!")
print()
print("Let's make this raffle integration happen! 🚀")

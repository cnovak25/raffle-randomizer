#!/usr/bin/env python3
"""
KPA Authentication Manager - Automated Cookie Refresh
Handles automatic authentication with KPA to maintain valid session cookies
"""
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KPAAuthManager:
    def __init__(self):
        self.base_url = "https://mvncorp.kpaehs.com"
        self.driver = None
        
    def setup_driver(self):
        """Setup headless Chrome driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return False
    
    def authenticate_with_okta(self, username, password):
        """Authenticate with OKTA and get KPA session cookies"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return None
            
            logger.info("Starting OKTA authentication...")
            
            # Navigate to KPA login page
            self.driver.get(f"{self.base_url}/signin")
            
            # Wait for OKTA redirect and login form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "okta-signin-username"))
            )
            
            # Fill in credentials
            username_field = self.driver.find_element(By.ID, "okta-signin-username")
            password_field = self.driver.find_element(By.ID, "okta-signin-password")
            
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit login
            submit_button = self.driver.find_element(By.ID, "okta-signin-submit")
            submit_button.click()
            
            # Wait for potential MFA or successful login
            WebDriverWait(self.driver, 30).until(
                lambda driver: "mvncorp.kpaehs.com" in driver.current_url and "/signin" not in driver.current_url
            )
            
            logger.info("Authentication successful, extracting cookies...")
            
            # Extract cookies
            cookies = self.driver.get_cookies()
            return self.extract_kpa_cookies(cookies)
            
        except TimeoutException:
            logger.error("Authentication timed out")
            return None
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def extract_kpa_cookies(self, cookies):
        """Extract the relevant KPA authentication cookies"""
        session_cookie = None
        subdomain_cookie = None
        
        for cookie in cookies:
            if cookie['name'] == '6Pphk3dbK4Y-mvncorp':
                session_cookie = cookie['value']
            elif cookie['name'] == 'last-subdomain':
                subdomain_cookie = cookie['value']
        
        if session_cookie and subdomain_cookie:
            logger.info("Successfully extracted KPA cookies")
            return {
                'session_cookie': session_cookie,
                'subdomain_cookie': subdomain_cookie
            }
        else:
            logger.error("Failed to extract required cookies")
            return None
    
    def test_cookies(self, session_cookie, subdomain_cookie):
        """Test if the extracted cookies work for photo access"""
        try:
            test_url = f"{self.base_url}/get-upload?key=test"
            headers = {
                'Cookie': f'6Pphk3dbK4Y-mvncorp={session_cookie}; last-subdomain={subdomain_cookie}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(test_url, headers=headers, timeout=10, allow_redirects=False)
            
            # If we get a redirect to S3 or a 404 (not signin), cookies are working
            if response.status_code in [302, 404] and 'signin' not in response.headers.get('location', ''):
                logger.info("Cookie test successful")
                return True
            else:
                logger.warning(f"Cookie test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Cookie test error: {e}")
            return False
    
    def refresh_cookies(self, username=None, password=None):
        """Main method to refresh KPA authentication cookies"""
        try:
            # Get credentials from environment if not provided
            username = username or os.environ.get('KPA_USERNAME')
            password = password or os.environ.get('KPA_PASSWORD')
            
            if not username or not password:
                logger.error("KPA credentials not provided")
                return None
            
            # Authenticate and get new cookies
            cookies = self.authenticate_with_okta(username, password)
            
            if cookies:
                # Test the cookies
                if self.test_cookies(cookies['session_cookie'], cookies['subdomain_cookie']):
                    logger.info("Cookie refresh successful")
                    return cookies
                else:
                    logger.error("New cookies failed validation")
                    return None
            else:
                logger.error("Failed to get new cookies")
                return None
                
        except Exception as e:
            logger.error(f"Cookie refresh failed: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def update_railway_environment(self, cookies):
        """Update Railway environment variables with new cookies"""
        # This would require Railway API access or webhook
        # For now, we'll return the cookies for manual update
        logger.info("New cookies ready for Railway update:")
        logger.info(f"KPA_SESSION_COOKIE={cookies['session_cookie']}")
        logger.info(f"KPA_SUBDOMAIN_COOKIE={cookies['subdomain_cookie']}")
        return cookies

# Standalone function for Railway integration
def refresh_kpa_authentication():
    """Standalone function to refresh KPA authentication"""
    manager = KPAAuthManager()
    return manager.refresh_cookies()

if __name__ == "__main__":
    # Command line usage
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python kpa_auth_manager.py <username> <password>")
        sys.exit(1)
    
    username, password = sys.argv[1], sys.argv[2]
    
    manager = KPAAuthManager()
    cookies = manager.refresh_cookies(username, password)
    
    if cookies:
        print("Cookie refresh successful!")
        print(f"KPA_SESSION_COOKIE={cookies['session_cookie']}")
        print(f"KPA_SUBDOMAIN_COOKIE={cookies['subdomain_cookie']}")
    else:
        print("Cookie refresh failed!")
        sys.exit(1)

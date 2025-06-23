"""
Hub XP Token Extraction Service
Migrated from renovar_token_simplified.py
"""
import os
import json
import logging
import platform
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from typing import Dict, Any, Optional, Tuple
from database.connection import execute_query
from models.hub_token import TokenExtractionResult

logger = logging.getLogger(__name__)


class HubTokenService:
    """Hub XP Token Extraction Service"""

    def __init__(self):
        self.environment = self._detect_environment()
        self.driver: Optional[webdriver.Chrome] = None

    def _detect_environment(self) -> str:
        """Detect running environment"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            if "microsoft" in platform.release().lower():
                return "wsl"
            return "linux"
        return "unknown"

    def _get_chrome_binary_path(self) -> Optional[str]:
        """Get Chrome binary path for different environments"""
        if self.environment == "windows":
            paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
        else:  # Linux/WSL
            paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium"
            ]

        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def _get_chromedriver_path(self) -> Optional[str]:
        """Get ChromeDriver path"""
        if self.environment == "windows":
            paths = [
                os.path.join(os.getcwd(), "chromedriver.exe"),
                "chromedriver.exe"
            ]
        else:
            paths = [
                os.path.join(os.getcwd(), "chromedriver"),
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver"
            ]

        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def _setup_webdriver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()

        # Anti-detection and stealth options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")

        # User agent to look like regular browser
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

        # Anti-bot detection
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")

        # Additional stealth options
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")

        # WSL specific options
        if self.environment in ["linux", "wsl"]:
            # chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")

        # Set Chrome binary path
        chrome_binary = self._get_chrome_binary_path()
        if chrome_binary:
            chrome_options.binary_location = chrome_binary

        # Setup ChromeDriver service with logging
        chromedriver_path = self._get_chromedriver_path()
        service = Service(
            chromedriver_path,
            log_level='INFO',
            service_args=['--verbose']
        ) if chromedriver_path else None

        try:
            if service:
                driver = webdriver.Chrome(
                    service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)

            # Set timeouts
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(10)

            # Execute stealth JavaScript to hide automation
            stealth_js = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                window.chrome = {
                    runtime: {}
                };
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en'],
                });
                
                const originalQuery = window.navigator.permissions.query;
                return window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """

            try:
                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': stealth_js
                })
            except Exception as e:
                logger.warning(f"Could not add stealth script: {e}")

            logger.info(f"WebDriver setup successful on {self.environment}")
            return driver

        except Exception as e:
            logger.error(f"WebDriver setup failed: {e}")
            raise

    def _perform_login(self, user_login: str, password: str, mfa_code: Optional[str] = None) -> bool:
        """Perform Hub XP login with enhanced error handling"""
        try:
            logger.info(f"Starting login for user: {user_login}")

            # Navigate to Hub XP
            logger.info("Navigating to Hub XP...")
            self.driver.get("https://hub.xpi.com.br/")

            # Wait for page load
            wait = WebDriverWait(self.driver, 60)

            # Check for blocked access
            page_title = self.driver.title.lower()
            logger.info(f"Page title: {self.driver.title}")

            if "bloqueado" in page_title or "blocked" in page_title:
                logger.error(
                    "Access blocked by Hub XP - anti-bot protection detected")
                raise Exception(
                    "Hub XP blocked access - try again later or use different approach")

            logger.info("Waiting for login form...")

            # Try multiple selectors for username field
            username_selectors = [
                (By.ID, "username"),
                (By.NAME, "username"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[placeholder*='email']"),
                (By.CSS_SELECTOR, "input[placeholder*='usuário']"),
                (By.XPATH, "//input[@type='text' or @type='email']")
            ]

            username_field = None
            for selector in username_selectors:
                try:
                    wait_short = WebDriverWait(self.driver, 5)
                    username_field = wait_short.until(
                        EC.presence_of_element_located(selector))
                    logger.info(
                        f"Username field found with selector: {selector}")
                    break
                except TimeoutException:
                    continue

            if not username_field:
                # Get page source for debugging
                logger.error("Username field not found. Page source:")
                logger.error(self.driver.page_source[:1000])
                raise Exception("Username field not found with any selector")

            # Enter username
            logger.info("Entering username...")
            username_field.clear()
            username_field.send_keys(user_login)

            # Try multiple selectors for password field
            password_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@type='password']")
            ]

            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(*selector)
                    logger.info(
                        f"Password field found with selector: {selector}")
                    break
                except:
                    continue

            if not password_field:
                raise Exception("Password field not found")

            # Enter password
            logger.info("Entering password...")
            password_field.clear()
            password_field.send_keys(password)

            # Try multiple selectors for login button
            login_selectors = [
                (By.XPATH, "//button[@type='submit']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Entrar')]"),
                (By.XPATH, "//button[contains(text(), 'Login')]"),
                (By.XPATH, "//input[@type='submit']"),
                (By.CSS_SELECTOR, ".btn-login"),
                (By.CSS_SELECTOR, ".login-button")
            ]

            login_button = None
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(*selector)
                    logger.info(
                        f"Login button found with selector: {selector}")
                    break
                except:
                    continue

            if not login_button:
                raise Exception("Login button not found")

            # Click login button
            logger.info("Clicking login button...")
            login_button.click()

            # Wait and check for results
            import time
            time.sleep(5)

            # Check current URL for success indicators
            current_url = self.driver.current_url
            logger.info(f"Current URL after login attempt: {current_url}")

            # Success patterns
            success_patterns = [
                "dashboard", "home", "main", "portal", "app"
            ]

            if any(pattern in current_url.lower() for pattern in success_patterns):
                logger.info("Login successful - URL indicates success")
                return True

            # Check for error messages
            error_selectors = [
                (By.CSS_SELECTOR, ".error"),
                (By.CSS_SELECTOR, ".alert-danger"),
                (By.XPATH, "//*[contains(text(), 'erro')]"),
                (By.XPATH, "//*[contains(text(), 'inválid')]")
            ]

            for selector in error_selectors:
                try:
                    error_element = self.driver.find_element(*selector)
                    if error_element.is_displayed():
                        logger.error(
                            f"Login error found: {error_element.text}")
                        return False
                except:
                    continue

            # If we're still on login page, it might be waiting for MFA or failed
            if "login" in current_url.lower():
                logger.warning(
                    "Still on login page - might need MFA or login failed")

                # Check for MFA requirement
                mfa_selectors = [
                    (By.ID, "mfa-token"),
                    (By.NAME, "mfa"),
                    (By.CSS_SELECTOR, "input[placeholder*='código']"),
                    (By.XPATH, "//input[contains(@placeholder, 'código')]")
                ]

                mfa_field = None
                for selector in mfa_selectors:
                    try:
                        mfa_field = self.driver.find_element(*selector)
                        if mfa_field.is_displayed():
                            logger.info(
                                f"MFA field found with selector: {selector}")
                            break
                    except:
                        continue

                if mfa_field:
                    if not mfa_code:
                        raise Exception("MFA code required but not provided")

                    logger.info("Entering MFA code...")
                    mfa_field.clear()
                    mfa_field.send_keys(mfa_code)

                    # Find and click MFA submit button
                    mfa_button = None
                    for selector in login_selectors:
                        try:
                            mfa_button = self.driver.find_element(*selector)
                            break
                        except:
                            continue

                    if mfa_button:
                        logger.info("Clicking MFA submit button...")
                        mfa_button.click()
                        time.sleep(5)

                        current_url = self.driver.current_url
                        logger.info(f"URL after MFA: {current_url}")

                        if any(pattern in current_url.lower() for pattern in success_patterns):
                            logger.info("Login with MFA successful")
                            return True

            # Final check - if we're not on login page anymore, assume success
            final_url = self.driver.current_url
            if "login" not in final_url.lower():
                logger.info("Login appears successful - not on login page")
                return True

            logger.error("Login failed - still on login page")
            return False

        except Exception as e:
            logger.error(f"Login failed with exception: {e}")
            # Log page source for debugging
            try:
                logger.error(f"Current URL: {self.driver.current_url}")
                logger.error(f"Page title: {self.driver.title}")
            except:
                pass
            return False

    def _extract_token_from_browser(self) -> Optional[Dict[str, Any]]:
        """Extract token from browser localStorage and sessionStorage"""
        try:
            logger.info("Extracting token from browser storage")

            # Enhanced token extraction script for Auth0 and various storage locations
            token_script = """
            // Helper function to search all storages
            function findTokens() {
                var results = {
                    localStorage: {},
                    sessionStorage: {},
                    cookies: {},
                    auth0: {}
                };
                
                // Check localStorage
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    try {
                        var value = localStorage.getItem(key);
                        if (key.toLowerCase().includes('token') || 
                            key.toLowerCase().includes('auth') ||
                            key.toLowerCase().includes('jwt') ||
                            key.toLowerCase().includes('access')) {
                            results.localStorage[key] = value;
                        }
                    } catch(e) {}
                }
                
                // Check sessionStorage
                for (var i = 0; i < sessionStorage.length; i++) {
                    var key = sessionStorage.key(i);
                    try {
                        var value = sessionStorage.getItem(key);
                        if (key.toLowerCase().includes('token') || 
                            key.toLowerCase().includes('auth') ||
                            key.toLowerCase().includes('jwt') ||
                            key.toLowerCase().includes('access')) {
                            results.sessionStorage[key] = value;
                        }
                    } catch(e) {}
                }
                
                // Check cookies
                document.cookie.split(';').forEach(function(cookie) {
                    var parts = cookie.trim().split('=');
                    if (parts.length === 2) {
                        var key = parts[0];
                        if (key.toLowerCase().includes('token') || 
                            key.toLowerCase().includes('auth') ||
                            key.toLowerCase().includes('jwt') ||
                            key.toLowerCase().includes('access')) {
                            results.cookies[key] = parts[1];
                        }
                    }
                });
                
                // Check Auth0 specific patterns
                var auth0Keys = [
                    'auth0.is.authenticated',
                    'auth0.ssodata',
                    'com.auth0.auth',
                    'a0-access_token',
                    'a0-id_token'
                ];
                
                auth0Keys.forEach(function(key) {
                    var value = localStorage.getItem(key) || sessionStorage.getItem(key);
                    if (value) {
                        results.auth0[key] = value;
                    }
                });
                
                return results;
            }
            
            // Execute search
            return findTokens();
            """

            all_tokens = self.driver.execute_script(token_script)
            logger.info(f"Token search results: {all_tokens}")

            if not all_tokens:
                logger.error("No token data found in any storage")
                return None
            
            # Try to find the actual token in the results
            token = None
            token_source = None
            
            # Check localStorage first
            for key, value in all_tokens.get('localStorage', {}).items():
                if value and len(str(value)) > 10:  # Tokens are usually longer
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(value) if isinstance(value, str) and value.startswith('{') else value
                        if isinstance(parsed, dict):
                            if 'access_token' in parsed:
                                token = parsed['access_token']
                                token_source = f"localStorage.{key}.access_token"
                                break
                            elif 'token' in parsed:
                                token = parsed['token']
                                token_source = f"localStorage.{key}.token"
                                break
                        else:
                            # Direct token value
                            token = str(value)
                            token_source = f"localStorage.{key}"
                            break
                    except:
                        # Use raw value
                        token = str(value)
                        token_source = f"localStorage.{key}"
                        break
            
            # Check sessionStorage if no token found
            if not token:
                for key, value in all_tokens.get('sessionStorage', {}).items():
                    if value and len(str(value)) > 10:
                        try:
                            parsed = json.loads(value) if isinstance(value, str) and value.startswith('{') else value
                            if isinstance(parsed, dict):
                                if 'access_token' in parsed:
                                    token = parsed['access_token']
                                    token_source = f"sessionStorage.{key}.access_token"
                                    break
                                elif 'token' in parsed:
                                    token = parsed['token']
                                    token_source = f"sessionStorage.{key}.token"
                                    break
                            else:
                                token = str(value)
                                token_source = f"sessionStorage.{key}"
                                break
                        except:
                            token = str(value)
                            token_source = f"sessionStorage.{key}"
                            break
            
            # Check Auth0 specific locations
            if not token:
                for key, value in all_tokens.get('auth0', {}).items():
                    if value and len(str(value)) > 10:
                        token = str(value)
                        token_source = f"auth0.{key}"
                        break
            
            # Check cookies as last resort
            if not token:
                for key, value in all_tokens.get('cookies', {}).items():
                    if value and len(str(value)) > 10:
                        token = str(value)
                        token_source = f"cookies.{key}"
                        break

            if not token:
                logger.error("No valid token found in any storage location")
                logger.info("Available storage data for debugging:")
                for storage_type, storage_data in all_tokens.items():
                    if storage_data:
                        logger.info(f"{storage_type}: {list(storage_data.keys())}")
                return None

            logger.info(f"Token found in: {token_source}")
            logger.info(f"Token preview: {token[:50]}..." if len(token) > 50 else f"Token: {token}")

            # For now, assume 24-hour expiry since we might not have expiry info
            expires_at = datetime.now() + timedelta(hours=24)

            logger.info("Token extracted successfully")
            return {
                'token': token,
                'expires_at': expires_at,
                'extracted_at': datetime.now(),
                'source': token_source
            }

        except Exception as e:
            logger.error(f"Token extraction failed: {e}")
            return None

    def _save_token_to_database(self, user_login: str, token_data: Dict[str, Any]) -> Optional[int]:
        """Save token to database"""
        try:
            # Delete old tokens for this user
            delete_query = "DELETE FROM hub_tokens WHERE user_login = %s"
            execute_query(delete_query, (user_login,))

            # Insert new token
            insert_query = """
            INSERT INTO hub_tokens (user_login, token, expires_at, extracted_at, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """

            params = (
                user_login,
                token_data['token'],
                token_data['expires_at'],
                token_data['extracted_at'],
                datetime.now()
            )

            result = execute_query(insert_query, params)

            # Get the inserted ID
            id_query = "SELECT LAST_INSERT_ID() as id"
            id_result = execute_query(id_query, fetch=True)
            token_id = id_result[0]['id'] if id_result else None

            logger.info(f"Token saved to database with ID: {token_id}")
            return token_id

        except Exception as e:
            logger.error(f"Failed to save token to database: {e}")
            return None

    async def extract_token(self, user_login: str, password: str, mfa_code: Optional[str] = None) -> TokenExtractionResult:
        """
        Main method to extract Hub XP token
        """
        try:
            logger.info(f"Starting token extraction for user: {user_login}")

            # Setup WebDriver
            self.driver = self._setup_webdriver()

            # Perform login
            login_success = self._perform_login(user_login, password, mfa_code)
            if not login_success:
                return TokenExtractionResult(
                    success=False,
                    message="Login failed",
                    user_login=user_login,
                    error_details="Unable to authenticate with Hub XP"
                )

            # Extract token
            token_data = self._extract_token_from_browser()
            if not token_data:
                return TokenExtractionResult(
                    success=False,
                    message="Token extraction failed",
                    user_login=user_login,
                    error_details="Unable to extract token from browser"
                )

            # Save to database
            token_id = self._save_token_to_database(user_login, token_data)
            if not token_id:
                return TokenExtractionResult(
                    success=False,
                    message="Database save failed",
                    user_login=user_login,
                    error_details="Unable to save token to database"
                )

            logger.info(
                f"Token extraction completed successfully for user: {user_login}")
            return TokenExtractionResult(
                success=True,
                message="Token extracted successfully",
                token_id=token_id,
                user_login=user_login,
                expires_at=token_data['expires_at']
            )

        except Exception as e:
            logger.error(f"Token extraction failed with exception: {e}")
            return TokenExtractionResult(
                success=False,
                message="Extraction failed with error",
                user_login=user_login,
                error_details=str(e)
            )

        finally:
            # Cleanup WebDriver
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                except:
                    pass

    async def get_token_status(self, user_login: str) -> Dict[str, Any]:
        """Get current token status for user"""
        try:
            query = """
            SELECT token, expires_at, extracted_at, created_at
            FROM hub_tokens 
            WHERE user_login = %s 
            ORDER BY created_at DESC 
            LIMIT 1
            """

            result = execute_query(query, (user_login,), fetch=True)

            if not result:
                return {
                    "user_login": user_login,
                    "has_valid_token": False,
                    "message": "No token found"
                }

            token_data = result[0]
            expires_at = token_data['expires_at']
            now = datetime.now()

            is_valid = expires_at > now if expires_at else False

            return {
                "user_login": user_login,
                "has_valid_token": is_valid,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "extracted_at": token_data['extracted_at'].isoformat(),
                "time_until_expiry": str(expires_at - now) if is_valid else "Expired"
            }

        except Exception as e:
            logger.error(f"Failed to get token status: {e}")
            return {
                "user_login": user_login,
                "has_valid_token": False,
                "error": str(e)
            }

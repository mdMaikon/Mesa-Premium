"""
Hub XP Token Extraction Service
Migrated from renovar_token_simplified.py
"""
import os
import json
import logging
from utils.log_sanitizer import get_sanitized_logger, mask_sensitive_data
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

logger = get_sanitized_logger(__name__)


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
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")

        # WSL specific options
        if self.environment in ["linux", "wsl"]:
            chrome_options.add_argument("--headless")
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
            masked_user = user_login[:2] + '***' + \
                user_login[-2:] if len(user_login) > 4 else '***'
            logger.info(f"Starting login for user: {masked_user}")

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

            # Try multiple selectors for username field - Hub XP uses name="account"
            username_selectors = [
                (By.NAME, "account"),  # Hub XP specific
                (By.CSS_SELECTOR, "input[placeholder*='account']"),
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

            # Try multiple selectors for password field - Hub XP uses name="password"
            password_selectors = [
                (By.NAME, "password"),  # Hub XP specific
                (By.ID, "password"),
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

            # Try multiple selectors for login button - Hub XP uses aria-label='Continuar'
            login_selectors = [
                # Hub XP specific
                (By.CSS_SELECTOR, "button[aria-label='Continuar']"),
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

            # Wait for page to load after clicking login
            import time
            time.sleep(5)

            # MFA - SEMPRE aguarda aparecer os campos (exactly like renovar_token_simplified.py)
            # Hub XP sempre requer MFA após login inicial
            logger.info("Looking for MFA fields after login...")
            logger.info("DEBUG: MFA code provided: [MASKED]")
            logger.info(f"DEBUG: MFA code type: {type(mfa_code)}")
            logger.info(
                f"DEBUG: MFA code length: {len(mfa_code) if mfa_code else 'None'}")

            try:
                mfa_fields = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "input[class='G7DrImLjomaOopqdA6D6dA==']"))
                )

                logger.info(f"DEBUG: Found {len(mfa_fields)} MFA fields")

                if not mfa_code:
                    raise Exception("MFA code required but not provided")

                # Garantir que mfa_code é string
                mfa_code = str(mfa_code).strip()
                logger.info(
                    f"DEBUG: MFA code after conversion: '[MASKED]' (length: {len(mfa_code)})")

                if len(mfa_code) != 6:
                    raise Exception(
                        f"MFA code must be 6 digits, got {len(mfa_code)}")

                logger.info(
                    f"Entering MFA code in {len(mfa_fields)} fields...")
                # Preenche cada campo com um dígito do MFA
                for i, campo in enumerate(mfa_fields):
                    if i < len(mfa_code):
                        digit = mfa_code[i]
                        logger.info(
                            f"DEBUG: Filling field {i} with digit '[MASKED]'")
                        campo.clear()
                        campo.send_keys(digit)
                        # Verificar se foi preenchido
                        filled_value = campo.get_attribute('value')
                        logger.info(
                            f"DEBUG: Field {i} value after filling: '[MASKED]'")

                # Find MFA submit button (exactly like renovar_token_simplified.py)
                try:
                    mfa_submit = self.driver.find_element(
                        By.CSS_SELECTOR, "button[aria-label='Confirmar e acessar conta']")
                except:
                    mfa_submit = self.driver.find_element(
                        By.CSS_SELECTOR, "soma-button[type='submit']")

                mfa_submit.click()

                # Aguarda autenticação (exactly like renovar_token_simplified.py)
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "header"))
                )

                logger.info("Login with MFA successful")
                return True

            except TimeoutException:
                logger.error("MFA fields not found or timeout during MFA")
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
        """Extract token from localStorage - exactly like renovar_token_simplified.py"""
        try:
            logger.info("Extracting token from browser storage")

            local_storage_keys = self.driver.execute_script(
                "return Object.keys(window.localStorage);")
            oidc_key = next(
                (k for k in local_storage_keys if k.startswith("oidc.user:")), None)

            if not oidc_key:
                logger.error("Chave OIDC não encontrada")
                return None

            oidc_data_raw = self.driver.execute_script(
                f"return window.localStorage.getItem('{oidc_key}');")
            oidc_data = json.loads(oidc_data_raw)

            token = oidc_data.get("access_token")
            expires_at = oidc_data.get("expires_at")

            if not token:
                logger.error("Token não encontrado")
                return None

            return {
                'token': token,
                'expires_at': datetime.fromtimestamp(expires_at) if expires_at else datetime.now() + timedelta(hours=8),
                'extracted_at': datetime.now()
            }

        except Exception as e:
            logger.error(f"Erro ao extrair token: {e}")
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

            # Execute insert and get the connection to retrieve last insert ID
            from database.connection import get_database_connection

            with get_database_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(insert_query, params)
                token_id = cursor.lastrowid  # Get the auto-increment ID
                connection.commit()
                cursor.close()

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
            masked_user = user_login[:2] + '***' + \
                user_login[-2:] if len(user_login) > 4 else '***'
            logger.info(f"Starting token extraction for user: {masked_user}")

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
            if token_id is None:
                return TokenExtractionResult(
                    success=False,
                    message="Database save failed",
                    user_login=user_login,
                    error_details="Unable to save token to database"
                )

            masked_user = user_login[:2] + '***' + \
                user_login[-2:] if len(user_login) > 4 else '***'
            logger.info(
                f"Token extraction completed successfully for user: {masked_user}")
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

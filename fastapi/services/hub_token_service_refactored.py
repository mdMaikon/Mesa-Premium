"""
Refactored Hub XP Token Extraction Service
Implements Single Responsibility Principle and reduces cyclomatic complexity
"""

import asyncio
import functools
import json
import os
import platform
import shutil
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any

from database.connection import execute_query
from models.hub_token import TokenExtractionResult
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils.crypto_utils import (
    generate_user_hash,
    prepare_token_for_storage,
    prepare_token_from_storage,
    validate_crypto_environment,
)
from utils.log_sanitizer import get_sanitized_logger, mask_username

logger = get_sanitized_logger(__name__)


class HubXPCustomExceptions:
    """Custom exceptions for Hub XP operations"""

    class HubXPException(Exception):
        """Base exception for Hub XP operations"""

        pass

    class EnvironmentDetectionError(HubXPException):
        """Error detecting environment"""

        pass

    class WebDriverSetupError(HubXPException):
        """Error setting up WebDriver"""

        pass

    class LoginError(HubXPException):
        """Error during login process"""

        pass

    class MFAError(LoginError):
        """Error during MFA authentication"""

        pass

    class TokenExtractionError(HubXPException):
        """Error extracting token"""

        pass

    class BlockedAccessError(LoginError):
        """Access blocked by Hub XP"""

        pass


class EnvironmentDetector:
    """Detects and configures environment-specific settings"""

    @staticmethod
    def detect_environment() -> str:
        """Detect running environment"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            if "microsoft" in platform.release().lower():
                return "wsl"
            return "linux"
        return "unknown"

    @staticmethod
    def get_chrome_binary_path(environment: str) -> str | None:
        """Get Chrome binary path for different environments"""
        if environment == "windows":
            windows_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(
                    r"~\AppData\Local\Google\Chrome\Application\chrome.exe"
                ),
            ]
            return next(
                (path for path in windows_paths if os.path.exists(path)), None
            )

        elif environment in ["linux", "wsl"]:
            linux_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium",
            ]
            return next(
                (path for path in linux_paths if os.path.exists(path)), None
            )

        return None


class WebDriverManager:
    """Manages WebDriver setup and configuration"""

    def __init__(self, environment: str):
        self.environment = environment

    def create_webdriver(self) -> webdriver.Chrome:
        """Create configured WebDriver instance"""
        try:
            chrome_options = self._get_chrome_options()
            binary_path = EnvironmentDetector.get_chrome_binary_path(
                self.environment
            )

            if binary_path:
                chrome_options.binary_location = binary_path
                logger.info(f"Using Chrome binary: {binary_path}")

            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Configure timeouts
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(60)

            # Apply advanced stealth measures
            self._apply_stealth_measures(driver)

            logger.info(f"WebDriver setup successful on {self.environment}")
            return driver

        except Exception as e:
            logger.error(f"WebDriver setup failed: {e}")
            raise HubXPCustomExceptions.WebDriverSetupError(
                f"Failed to setup WebDriver: {e}"
            ) from e

    def _get_chrome_options(self) -> Options:
        """Get Chrome options based on environment with anti-bot detection measures"""
        options = Options()

        # Critical anti-bot detection measures
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Security and SSL options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--ignore-certificate-errors-spki-list")

        # Docker/Production specific options - Environment-aware approach
        if (
            self.environment in ["linux"]
            and os.getenv("ENVIRONMENT") == "production"
        ):
            # Docker production mode - approach radical para resolver conflitos persistentes
            timestamp = int(time.time() * 1000)
            process_id = os.getpid()
            unique_id = f"{timestamp}_{process_id}_{uuid.uuid4().hex[:8]}"

            # Usar /tmp que sabemos que funciona no container
            user_data_dir = f"/tmp/chrome_prod_{unique_id}"  # nosec B108

            # Limpeza forçada se existir
            if os.path.exists(user_data_dir):
                shutil.rmtree(user_data_dir, ignore_errors=True)

            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument("--remote-debugging-port=0")
            # REMOVER --single-process e --no-zygote que causam crashes
            # options.add_argument("--single-process")  # Pode causar instabilidade
            # options.add_argument("--no-zygote")  # Pode causar crashes

            # Configuração mais estável para Docker
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-sync")
            options.add_argument("--disk-cache-size=0")
            options.add_argument("--disable-dev-tools")  # Desabilita DevTools
            options.add_argument("--disable-logging")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-features=AudioServiceOutOfProcess")
            options.add_argument(
                "--force-gpu-mem-available-mb=512"
            )  # Reduzir uso de memória
            options.add_argument(
                "--max-old-space-size=2048"
            )  # Reduzir uso de memória
            options.add_argument("--memory-pressure-off")
            options.add_argument("--disable-ipc-flooding-protection")
        else:
            # Desenvolvimento/local - usar configuração padrão que funciona
            temp_dir = tempfile.gettempdir()
            unique_user_data_dir = os.path.join(
                temp_dir, f"chrome_user_data_{uuid.uuid4().hex[:8]}"
            )
            options.add_argument(f"--user-data-dir={unique_user_data_dir}")
            options.add_argument("--remote-debugging-port=0")

        # Performance optimizations
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-logging")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")

        # Environment-specific options - always use headless for Linux/WSL
        if self.environment in ["linux", "wsl"]:
            options.add_argument("--headless")
            options.add_argument("--disable-features=VizDisplayCompositor")

        # Critical automation detection bypass
        # Fixed: was 'enable-logging'
        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option("useAutomationExtension", False)

        # Additional stealth measures
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")

        return options

    def _apply_stealth_measures(self, driver: webdriver.Chrome) -> None:
        """Apply advanced JavaScript stealth measures to bypass bot detection"""
        try:
            # Advanced stealth JavaScript injection from original working version
            stealth_js = """
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Add chrome runtime object
                window.chrome = {
                    runtime: {}
                };

                // Fake plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // Set proper languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en'],
                });

                // Override permissions query
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Remove automation indicators
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            """

            # Execute stealth measures using CDP
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js}
            )

            logger.info("Advanced stealth measures applied successfully")

        except Exception as e:
            logger.warning(f"Failed to apply some stealth measures: {e}")
            # Continue anyway as basic options may still work


class HubXPAuthenticator:
    """Handles Hub XP authentication logic"""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, 60)

    def perform_login(
        self, user_login: str, password: str, mfa_code: str | None = None
    ) -> bool:
        """
        Perform Hub XP login with MFA

        Args:
            user_login: User login credentials
            password: User password
            mfa_code: Optional MFA code (required for successful login)

        Returns:
            bool: True if login successful, False otherwise

        Raises:
            BlockedAccessError: If access is blocked by Hub XP
            LoginError: If login fails for other reasons
            MFAError: If MFA authentication fails
        """
        try:
            masked_user = mask_username(user_login)
            logger.info(f"Starting login for user: {masked_user}")

            # Navigate and check for blocks
            self._navigate_to_hub()
            self._check_access_blocked()

            # Perform login steps
            self._fill_login_form(user_login, password)
            self._submit_login_form()

            # Handle MFA
            if not self._handle_mfa_authentication(mfa_code):
                raise HubXPCustomExceptions.MFAError(
                    "MFA authentication failed"
                )

            logger.info("Login with MFA successful")
            return True

        except HubXPCustomExceptions.HubXPException:
            raise
        except Exception as e:
            logger.error(f"Login failed with exception: {e}")
            self._log_debugging_info()
            raise HubXPCustomExceptions.LoginError(f"Login failed: {e}") from e

    def _navigate_to_hub(self) -> None:
        """Navigate to Hub XP homepage"""
        logger.info("Navigating to Hub XP...")
        self.driver.get("https://hub.xpi.com.br/")

    def _check_access_blocked(self) -> None:
        """Check if access is blocked by Hub XP"""
        page_title = self.driver.title.lower()
        logger.info(f"Page title: {self.driver.title}")

        if "bloqueado" in page_title or "blocked" in page_title:
            logger.error(
                "Access blocked by Hub XP - anti-bot protection detected"
            )
            raise HubXPCustomExceptions.BlockedAccessError(
                "Hub XP blocked access - try again later or use different approach"
            )

    def _fill_login_form(self, user_login: str, password: str) -> None:
        """Fill in login form fields"""
        logger.info("Waiting for login form...")

        # Find and fill username
        username_field = self._find_username_field()
        logger.info("Entering username...")
        username_field.clear()
        username_field.send_keys(user_login)

        # Find and fill password
        password_field = self._find_password_field()
        logger.info("Entering password...")
        password_field.clear()
        password_field.send_keys(password)

    def _find_username_field(self):
        """Find username field using multiple selectors"""
        selectors = [
            (By.NAME, "account"),  # Hub XP specific
            (By.CSS_SELECTOR, "input[placeholder*='account']"),
            (By.XPATH, "//input[@type='text' or @type='email']"),
        ]

        for selector in selectors:
            try:
                wait_short = WebDriverWait(self.driver, 5)
                field = wait_short.until(
                    EC.presence_of_element_located(selector)
                )
                logger.info(f"Username field found with selector: {selector}")
                return field
            except TimeoutException:
                continue

        logger.error("Username field not found. Page source:")
        logger.error(self.driver.page_source[:1000])
        raise HubXPCustomExceptions.LoginError(
            "Username field not found with any selector"
        )

    def _find_password_field(self):
        """Find password field using multiple selectors"""
        selectors = [
            (By.NAME, "password"),  # Hub XP specific
            (By.ID, "password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[@type='password']"),
        ]

        for selector in selectors:
            try:
                field = self.driver.find_element(*selector)
                logger.info(f"Password field found with selector: {selector}")
                return field
            except Exception:
                continue

        raise HubXPCustomExceptions.LoginError("Password field not found")

    def _submit_login_form(self) -> None:
        """Submit the login form"""
        login_button = self._find_login_button()
        logger.info("Clicking login button...")
        login_button.click()

        # Wait for form submission and page load
        logger.info("Waiting for page to load after login...")
        time.sleep(3)  # Otimizado: reduzido de 8 para 3 segundos

    def _find_login_button(self):
        """Find login button using multiple selectors"""
        selectors = [
            # Hub XP specific
            (By.CSS_SELECTOR, "button[aria-label='Continuar']"),
            (By.XPATH, "//button[@type='submit']"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Entrar')]"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//input[@type='submit']"),
            (By.CSS_SELECTOR, ".btn-login"),
            (By.CSS_SELECTOR, ".login-button"),
        ]

        for selector in selectors:
            try:
                button = self.driver.find_element(*selector)
                logger.info(f"Login button found with selector: {selector}")
                return button
            except Exception:
                continue

        raise HubXPCustomExceptions.LoginError("Login button not found")

    def _handle_mfa_authentication(self, mfa_code: str | None) -> bool:
        """
        Handle MFA authentication with connection stability

        Args:
            mfa_code: 6-digit MFA code

        Returns:
            bool: True if MFA successful, False otherwise
        """
        logger.info("Looking for MFA fields after login...")

        if not mfa_code:
            raise HubXPCustomExceptions.MFAError(
                "MFA code required but not provided"
            )

        try:
            # Verificar se a conexão está ativa antes de continuar
            try:
                current_url = self.driver.current_url
                logger.info(f"Current URL before MFA: {current_url[:50]}...")

                # Verificação adicional de estabilidade
                page_title = self.driver.title
                logger.info(f"Page title before MFA: {page_title}")

                # Pequena pausa para estabilidade
                time.sleep(2)

            except Exception as e:
                logger.error(f"Driver connection lost before MFA: {e}")
                raise HubXPCustomExceptions.MFAError(
                    "Browser connection lost"
                ) from e

            # Find MFA fields com timeout reduzido para detectar problemas mais cedo
            mfa_fields = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (
                        By.CSS_SELECTOR,
                        "input[class='G7DrImLjomaOopqdA6D6dA==']",
                    )
                )
            )

            logger.info(f"DEBUG: Found {len(mfa_fields)} MFA fields")

            # Validate MFA code
            mfa_code = str(mfa_code).strip()
            if len(mfa_code) != 6:
                raise HubXPCustomExceptions.MFAError(
                    f"MFA code must be 6 digits, got {len(mfa_code)}"
                )

            # Fill MFA fields with connection checks
            self._fill_mfa_fields_safe(mfa_fields, mfa_code)

            # Submit MFA with connection check
            self._submit_mfa_form_safe()

            # Wait for authentication success with shorter timeout
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "header"))
            )

            return True

        except TimeoutException:
            logger.error("MFA fields not found or timeout during MFA")
            return False
        except Exception as e:
            logger.error(f"MFA authentication error: {e}")
            return False

    def _fill_mfa_fields_safe(self, mfa_fields: list, mfa_code: str) -> None:
        """Fill MFA fields with code digits safely"""
        logger.info(f"Entering MFA code in {len(mfa_fields)} fields...")

        for i, field in enumerate(mfa_fields):
            if i < len(mfa_code):
                try:
                    # Verificar se o campo ainda está disponível
                    if not field.is_enabled():
                        logger.warning(f"Field {i} is not enabled, skipping")
                        continue

                    digit = mfa_code[i]
                    logger.info(
                        f"DEBUG: Filling field {i} with digit '[MASKED]'"
                    )
                    field.clear()
                    field.send_keys(digit)

                    # Pequena pausa entre campos para estabilidade
                    time.sleep(0.2)

                except Exception as e:
                    logger.error(f"Error filling MFA field {i}: {e}")
                    # Continue com os outros campos mesmo se um falhar
                    continue

    def _fill_mfa_fields(self, mfa_fields: list, mfa_code: str) -> None:
        """Fill MFA fields with code digits (legacy method)"""
        return self._fill_mfa_fields_safe(mfa_fields, mfa_code)

    def _submit_mfa_form_safe(self) -> None:
        """Submit MFA form safely with connection checks"""
        try:
            # Verificar conexão antes de submeter
            try:
                _ = self.driver.page_source[:100]  # Connection check
                logger.info("Connection check passed before MFA submit")
            except Exception as e:
                logger.error(f"Connection lost before MFA submit: {e}")
                raise HubXPCustomExceptions.MFAError(
                    "Browser disconnected before submit"
                ) from e

            # Tentar encontrar botão de submit
            try:
                mfa_submit = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "button[aria-label='Confirmar e acessar conta']",
                )
                logger.info("Found primary MFA submit button")
            except Exception:
                try:
                    mfa_submit = self.driver.find_element(
                        By.CSS_SELECTOR, "soma-button[type='submit']"
                    )
                    logger.info("Found secondary MFA submit button")
                except Exception as e:
                    logger.error(f"No MFA submit button found: {e}")
                    raise HubXPCustomExceptions.MFAError(
                        "Submit button not found"
                    ) from e

            # Click com verificação
            mfa_submit.click()
            logger.info("MFA form submitted successfully")

            # Pequena pausa após submit
            time.sleep(1)

        except Exception as e:
            logger.error(f"Error submitting MFA form: {e}")
            raise

    def _submit_mfa_form(self) -> None:
        """Submit MFA form (legacy method)"""
        return self._submit_mfa_form_safe()

    def _log_debugging_info(self) -> None:
        """Log safe debugging information"""
        try:
            current_url = self.driver.current_url
            # Remove query parameters to avoid exposing sensitive data
            safe_url = (
                current_url.split("?")[0]
                if "?" in current_url
                else current_url
            )
            logger.error(f"Current URL (safe): {safe_url}")

            page_title = self.driver.title
            # Truncate title to avoid potential sensitive data exposure
            safe_title = (
                page_title[:100] + "..."
                if len(page_title) > 100
                else page_title
            )
            logger.error(f"Page title (safe): {safe_title}")
        except Exception:
            logger.error("Unable to retrieve page debugging information")


class TokenExtractor:
    """Handles token extraction from browser storage"""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver

    def extract_token_from_browser(self) -> dict[str, Any] | None:
        """
        Extract token from browser localStorage

        Returns:
            Optional[Dict]: Token data with token, expires_at, extracted_at

        Raises:
            TokenExtractionError: If token extraction fails
        """
        try:
            logger.info("Extracting token from browser storage")

            # Get localStorage keys
            local_storage_keys = self.driver.execute_script(
                "return Object.keys(window.localStorage);"
            )

            # Find OIDC key
            oidc_key = next(
                (k for k in local_storage_keys if k.startswith("oidc.user:")),
                None,
            )

            if not oidc_key:
                logger.error("OIDC key not found")
                raise HubXPCustomExceptions.TokenExtractionError(
                    "OIDC key not found"
                )

            # Extract OIDC data
            oidc_data_raw = self.driver.execute_script(
                f"return window.localStorage.getItem('{oidc_key}');"
            )
            oidc_data = json.loads(oidc_data_raw)

            # Extract token and expiration
            token = oidc_data.get("access_token")
            expires_at = oidc_data.get("expires_at")

            if not token:
                logger.error("Token not found in OIDC data")
                raise HubXPCustomExceptions.TokenExtractionError(
                    "Token not found"
                )

            return {
                "token": token,
                "expires_at": datetime.fromtimestamp(expires_at)
                if expires_at
                else datetime.now() + timedelta(hours=8),
                "extracted_at": datetime.now(),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing OIDC data: {e}")
            raise HubXPCustomExceptions.TokenExtractionError(
                f"Error parsing OIDC data: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Error extracting token: {e}")
            raise HubXPCustomExceptions.TokenExtractionError(
                f"Error extracting token: {e}"
            ) from e


class TokenRepository:
    """Handles token persistence in database with encryption support"""

    @staticmethod
    def save_token(user_login: str, token_data: dict[str, Any]) -> bool:
        """
        Save token to database with encryption

        Args:
            user_login: User login
            token_data: Token data dictionary

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate crypto environment
            if not validate_crypto_environment():
                logger.error("Crypto environment validation failed")
                return False

            # Prepare encrypted data for storage
            storage_data = prepare_token_for_storage(user_login, token_data)

            # Delete existing tokens for user using hash
            user_hash = generate_user_hash(user_login)
            delete_query = "DELETE FROM hub_tokens WHERE user_login_hash = %s"
            execute_query(delete_query, (user_hash,))

            # Insert new encrypted token
            insert_query = """
                INSERT INTO hub_tokens (user_login, user_login_hash, token, expires_at, extracted_at, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """

            execute_query(
                insert_query,
                (
                    storage_data["user_login"],
                    storage_data["user_login_hash"],
                    storage_data["token"],
                    storage_data["expires_at"],
                    storage_data["extracted_at"],
                ),
            )

            logger.info(
                f"Encrypted token saved successfully for user: {mask_username(user_login)}"
            )
            return True

        except Exception as e:
            logger.error(f"Error saving encrypted token: {e}")
            return False

    @staticmethod
    def get_token_status(user_login: str) -> dict[str, Any] | None:
        """
        Get token status from database with decryption

        Args:
            user_login: User login

        Returns:
            Optional[Dict]: Token status data
        """
        try:
            # Validate crypto environment
            if not validate_crypto_environment():
                logger.error("Crypto environment validation failed")
                return None

            # Generate search hash for user
            user_hash = generate_user_hash(user_login)

            query = """
                SELECT user_login, token, expires_at, extracted_at, created_at
                FROM hub_tokens
                WHERE user_login_hash = %s
                ORDER BY created_at DESC
                LIMIT 1
            """

            result = execute_query(query, (user_hash,), fetch=True)
            if result:
                encrypted_data = result[0]

                # Prepare decrypted data
                token_data = prepare_token_from_storage(encrypted_data)

                return {
                    "user_login": mask_username(user_login),
                    "has_token": True,
                    "expires_at": token_data["expires_at"],
                    "extracted_at": token_data["extracted_at"],
                    "created_at": token_data["created_at"],
                    "is_valid": token_data["expires_at"] > datetime.now()
                    if token_data["expires_at"]
                    else False,
                }

            return {
                "user_login": mask_username(user_login),
                "has_token": False,
                "expires_at": None,
                "extracted_at": None,
                "created_at": None,
                "is_valid": False,
            }

        except Exception as e:
            logger.error(f"Error getting encrypted token status: {e}")
            return None

    @staticmethod
    def get_valid_token(user_login: str) -> str | None:
        """
        Get valid decrypted token from database

        Args:
            user_login: User login

        Returns:
            Optional[str]: Valid token or None
        """
        try:
            token_status = TokenRepository.get_token_status(user_login)

            if token_status and token_status.get("is_valid"):
                # Get decrypted token
                user_hash = generate_user_hash(user_login)
                query = """
                    SELECT user_login, token, expires_at, extracted_at, created_at
                    FROM hub_tokens
                    WHERE user_login_hash = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """

                result = execute_query(query, (user_hash,), fetch=True)
                if result:
                    encrypted_data = result[0]
                    token_data = prepare_token_from_storage(encrypted_data)
                    logger.info(
                        f"Valid token retrieved for user: {mask_username(user_login)}"
                    )
                    return token_data["token"]

            return None

        except Exception as e:
            logger.error(f"Error getting valid token: {e}")
            return None

    @staticmethod
    def get_any_valid_token() -> tuple[str, str] | None:
        """
        Get any valid token from database without requiring specific user_login

        This method searches for valid tokens by checking expiration dates
        and tries to decrypt them. Returns the first valid token found.

        Returns:
            Optional[Tuple[str, str]]: (user_login, token) or None if no valid token found
        """
        try:
            # Validate crypto environment
            if not validate_crypto_environment():
                logger.error("Crypto environment validation failed")
                return None

            # Get all tokens that might be valid (not expired by date)
            query = """
                SELECT user_login, user_login_hash, token, expires_at, extracted_at, created_at
                FROM hub_tokens
                WHERE expires_at > NOW()
                ORDER BY created_at DESC
            """

            results = execute_query(query, fetch=True)
            if not results:
                logger.warning("No unexpired tokens found in database")
                return None

            logger.info(
                f"Found {len(results)} unexpired token(s), checking validity..."
            )

            # Try to decrypt each token until we find a valid one
            for encrypted_data in results:
                try:
                    # Attempt to decrypt the token data
                    token_data = prepare_token_from_storage(encrypted_data)

                    if token_data and token_data.get("token"):
                        # Double-check expiration after decryption
                        if token_data["expires_at"] > datetime.now():
                            logger.info(
                                f"Valid token found for user: {mask_username(token_data['user_login'])}"
                            )
                            return token_data["user_login"], token_data[
                                "token"
                            ]

                except Exception as e:
                    # This token couldn't be decrypted, try the next one
                    logger.debug(f"Could not decrypt token: {e}")
                    continue

            logger.warning("No valid decryptable tokens found")
            return None

        except Exception as e:
            logger.error(f"Error getting any valid token: {e}")
            return None


class RefactoredHubTokenService:
    """
    Refactored Hub XP Token Service with Single Responsibility Principle

    This service orchestrates the token extraction process using specialized classes:
    - EnvironmentDetector: Detects environment and configurations
    - WebDriverManager: Manages WebDriver setup
    - HubXPAuthenticator: Handles authentication logic
    - TokenExtractor: Extracts tokens from browser
    - TokenRepository: Manages token persistence
    """

    def __init__(self):
        self.environment = EnvironmentDetector.detect_environment()
        self.webdriver_manager = WebDriverManager(self.environment)
        self._executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="webdriver"
        )

    async def extract_token(
        self, user_login: str, password: str, mfa_code: str | None = None
    ) -> TokenExtractionResult:
        """
        Extract Hub XP token using async WebDriver execution

        Args:
            user_login: User login credentials
            password: User password
            mfa_code: Optional MFA code

        Returns:
            TokenExtractionResult: Result of token extraction
        """
        loop = asyncio.get_event_loop()

        try:
            # Run WebDriver operations in thread pool
            result = await loop.run_in_executor(
                self._executor,
                functools.partial(
                    self._extract_token_sync, user_login, password, mfa_code
                ),
            )

            return result

        except Exception as e:
            logger.error(f"Async token extraction failed: {e}")
            return TokenExtractionResult(
                success=False,
                message=str(e),
                user_login=mask_username(user_login),
            )

    def _extract_token_sync(
        self, user_login: str, password: str, mfa_code: str | None = None
    ) -> TokenExtractionResult:
        """
        Synchronous token extraction using specialized classes

        Args:
            user_login: User login credentials
            password: User password
            mfa_code: Optional MFA code

        Returns:
            TokenExtractionResult: Result of token extraction
        """
        driver = None

        try:
            # Setup WebDriver
            driver = self.webdriver_manager.create_webdriver()

            # Perform authentication
            authenticator = HubXPAuthenticator(driver)
            login_success = authenticator.perform_login(
                user_login, password, mfa_code
            )

            if not login_success:
                return TokenExtractionResult(
                    success=False,
                    message="Login failed",
                    user_login=mask_username(user_login),
                )

            # Extract token
            token_extractor = TokenExtractor(driver)
            token_data = token_extractor.extract_token_from_browser()

            if not token_data:
                return TokenExtractionResult(
                    success=False,
                    message="Token extraction failed",
                    user_login=mask_username(user_login),
                )

            # Save token
            save_success = TokenRepository.save_token(user_login, token_data)

            if not save_success:
                return TokenExtractionResult(
                    success=False,
                    message="Token save failed",
                    user_login=mask_username(user_login),
                )

            return TokenExtractionResult(
                success=True,
                message="Token extracted successfully",
                user_login=mask_username(user_login),
                expires_at=token_data["expires_at"],
            )

        except HubXPCustomExceptions.HubXPException as e:
            logger.error(f"Hub XP specific error: {e}")
            return TokenExtractionResult(
                success=False,
                message=str(e),
                user_login=mask_username(user_login),
            )
        except Exception as e:
            logger.error(f"Unexpected error during token extraction: {e}")
            return TokenExtractionResult(
                success=False,
                message=f"Unexpected error: {e}",
                user_login=mask_username(user_login),
            )
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    def get_token_status(self, user_login: str) -> dict[str, Any] | None:
        """
        Get token status for user

        Args:
            user_login: User login

        Returns:
            Optional[Dict]: Token status data
        """
        return TokenRepository.get_token_status(user_login)

    def __del__(self):
        """Cleanup thread pool on destruction"""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)

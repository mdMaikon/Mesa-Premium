"""
Mock implementations for Selenium WebDriver automation
"""

import time
from unittest.mock import Mock

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By


class MockWebElement:
    """Mock WebElement for Selenium testing"""

    def __init__(self, tag_name="div", text="", attributes=None):
        self.tag_name = tag_name
        self.text = text
        self.attributes = attributes or {}
        self._value = ""

    def click(self):
        """Mock click action"""
        pass

    def send_keys(self, keys):
        """Mock send_keys action"""
        self._value += str(keys)

    def clear(self):
        """Mock clear action"""
        self._value = ""

    def get_attribute(self, name):
        """Mock get_attribute"""
        if name == "value":
            return self._value
        return self.attributes.get(name, "")

    def is_displayed(self):
        """Mock is_displayed"""
        return True

    def is_enabled(self):
        """Mock is_enabled"""
        return True


class MockWebDriver:
    """Mock WebDriver for Selenium testing"""

    def __init__(self, simulate_success=True, simulate_mfa=True):
        self.simulate_success = simulate_success
        self.simulate_mfa = simulate_mfa
        self.current_url = "https://hub.xpi.com.br/login"
        self._page_source = ""
        self._elements = {}
        self._setup_mock_elements()

    def _setup_mock_elements(self):
        """Setup mock elements for different scenarios"""
        # Login form elements
        self._elements["username"] = MockWebElement(
            "input", attributes={"name": "account"}
        )
        self._elements["password"] = MockWebElement(
            "input", attributes={"name": "password"}
        )
        self._elements["login_button"] = MockWebElement("button")

        # MFA elements
        self._elements["mfa_fields"] = [
            MockWebElement(
                "input", attributes={"class": "G7DrImLjomaOopqdA6D6dA=="}
            )
            for _ in range(6)
        ]

        # Dashboard elements
        self._elements["dashboard"] = MockWebElement("div", text="Dashboard")

    def get(self, url):
        """Mock get method"""
        self.current_url = url
        time.sleep(0.1)  # Simulate page load

    def find_element(self, by, value):
        """Mock find_element"""
        if by == By.NAME:
            if value == "account":
                return self._elements["username"]
            elif value == "password":
                return self._elements["password"]

        if by == By.XPATH and "button" in value.lower():
            return self._elements["login_button"]

        if "dashboard" in value.lower():
            if self.simulate_success:
                self.current_url = "https://hub.xpi.com.br/dashboard"
                return self._elements["dashboard"]
            else:
                raise NoSuchElementException("Dashboard not found")

        # Default element
        return MockWebElement()

    def find_elements(self, by, value):
        """Mock find_elements"""
        if "G7DrImLjomaOopqdA6D6dA==" in value:
            return self._elements["mfa_fields"]

        return []

    def execute_script(self, script):
        """Mock execute_script"""
        if "localStorage" in script and "token" in script:
            if self.simulate_success:
                return "mock_hub_token_12345_abcdef"
            else:
                return None

        return None

    def quit(self):
        """Mock quit method"""
        pass

    def close(self):
        """Mock close method"""
        pass

    @property
    def page_source(self):
        """Mock page_source property"""
        if "dashboard" in self.current_url:
            return "<html><body><div>Dashboard Content</div></body></html>"
        return "<html><body><div>Login Page</div></body></html>"


class MockWebDriverWait:
    """Mock WebDriverWait for testing"""

    def __init__(self, driver, timeout):
        self.driver = driver
        self.timeout = timeout

    def until(self, condition):
        """Mock until method"""
        # Simulate waiting
        time.sleep(0.1)

        # Try to call the condition function
        try:
            result = condition(self.driver)
            if result:
                return result
        except Exception:
            pass

        # For certain conditions, simulate success or failure
        if hasattr(condition, "locator"):
            if "dashboard" in str(condition.locator):
                if self.driver.simulate_success:
                    return MockWebElement("div", text="Dashboard")
                else:
                    raise TimeoutException("Dashboard not found")

        # Default successful wait
        return MockWebElement()


class MockChrome:
    """Mock Chrome WebDriver constructor"""

    def __init__(
        self,
        options=None,
        service=None,
        simulate_success=True,
        simulate_mfa=True,
    ):
        self.options = options
        self.service = service
        self.simulate_success = simulate_success
        self.simulate_mfa = simulate_mfa

    def __call__(self, *args, **kwargs):
        return MockWebDriver(
            simulate_success=self.simulate_success,
            simulate_mfa=self.simulate_mfa,
        )


class HubXPMockScenarios:
    """Predefined mock scenarios for Hub XP testing"""

    @staticmethod
    def successful_login():
        """Mock successful login scenario"""
        return MockWebDriver(simulate_success=True, simulate_mfa=True)

    @staticmethod
    def failed_login():
        """Mock failed login scenario"""
        return MockWebDriver(simulate_success=False, simulate_mfa=False)

    @staticmethod
    def mfa_timeout():
        """Mock MFA timeout scenario"""
        driver = MockWebDriver(simulate_success=True, simulate_mfa=False)

        # Override find_elements to return empty MFA fields
        original_find_elements = driver.find_elements

        def mock_find_elements(by, value):
            if "G7DrImLjomaOopqdA6D6dA==" in value:
                return []  # No MFA fields found
            return original_find_elements(by, value)

        driver.find_elements = mock_find_elements
        return driver

    @staticmethod
    def network_error():
        """Mock network error scenario"""
        driver = MockWebDriver()

        # Override get method to simulate network error
        def mock_get(url):
            raise Exception("Network error: Connection timeout")

        driver.get = mock_get
        return driver

    @staticmethod
    def token_extraction_failed():
        """Mock token extraction failure"""
        driver = MockWebDriver(simulate_success=True, simulate_mfa=True)

        # Override execute_script to return None for token
        def mock_execute_script(script):
            if "localStorage" in script and "token" in script:
                return None  # No token found
            return None

        driver.execute_script = mock_execute_script
        return driver

    @staticmethod
    def partial_mfa_entry():
        """Mock partial MFA entry scenario"""
        driver = MockWebDriver(simulate_success=True, simulate_mfa=True)

        # Mock MFA fields with partial values
        mfa_fields = []
        for i in range(6):
            element = MockWebElement(
                "input", attributes={"class": "G7DrImLjomaOopqdA6D6dA=="}
            )
            # Fill only first 3 fields
            if i < 3:
                element._value = str(i + 1)
            mfa_fields.append(element)

        driver._elements["mfa_fields"] = mfa_fields
        return driver


class SeleniumMockFactory:
    """Factory for creating Selenium mocks with different behaviors"""

    @staticmethod
    def create_hub_xp_mock(scenario="success", **kwargs):
        """
        Create Hub XP specific mock based on scenario

        Args:
            scenario: Type of scenario (success, failure, mfa_timeout, etc.)
            **kwargs: Additional parameters for mock configuration

        Returns:
            Mock WebDriver configured for the scenario
        """
        scenario_map = {
            "success": HubXPMockScenarios.successful_login,
            "failure": HubXPMockScenarios.failed_login,
            "mfa_timeout": HubXPMockScenarios.mfa_timeout,
            "network_error": HubXPMockScenarios.network_error,
            "token_failed": HubXPMockScenarios.token_extraction_failed,
            "partial_mfa": HubXPMockScenarios.partial_mfa_entry,
        }

        if scenario not in scenario_map:
            raise ValueError(f"Unknown scenario: {scenario}")

        return scenario_map[scenario]()

    @staticmethod
    def create_webdriver_wait_mock(timeout_scenario=False):
        """Create WebDriverWait mock"""
        if timeout_scenario:

            def mock_until(condition):
                time.sleep(0.1)
                raise TimeoutException("Timed out waiting for condition")

            wait_mock = Mock()
            wait_mock.until = mock_until
            return wait_mock

        return MockWebDriverWait(MockWebDriver(), 10)


# Pytest fixtures for Selenium mocks
def pytest_selenium_fixtures():
    """Helper function to create pytest fixtures"""
    import pytest

    @pytest.fixture
    def mock_successful_webdriver():
        return HubXPMockScenarios.successful_login()

    @pytest.fixture
    def mock_failed_webdriver():
        return HubXPMockScenarios.failed_login()

    @pytest.fixture
    def mock_webdriver_factory():
        return SeleniumMockFactory()

    return {
        "mock_successful_webdriver": mock_successful_webdriver,
        "mock_failed_webdriver": mock_failed_webdriver,
        "mock_webdriver_factory": mock_webdriver_factory,
    }

#!/usr/bin/env python3
"""
Deployment Script for MenuAutomacoes FastAPI
Handles deployment to different environments with proper configuration

Usage:
    python scripts/deploy.py [environment] [options]

Environments:
    development (default)
    staging
    production

Options:
    --check-dependencies    Run security audit before deployment
    --update-dependencies   Update vulnerable dependencies
    --run-tests            Run test suite before deployment
    --backup               Create backup before deployment
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Import secure subprocess utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.secure_subprocess import (
    SecureSubprocessError,
    run_pytest,
    run_python_script,
)


class Deployer:
    """Deployment manager for different environments"""

    def __init__(self, environment: str = "development"):
        self.environment = environment.lower()
        self.project_root = Path(__file__).parent.parent
        self.env_files = {
            "development": None,  # Use default .env
            "staging": ".env.staging",
            "production": ".env.production",
        }

        # Validate environment
        if self.environment not in self.env_files:
            raise ValueError(f"Invalid environment: {environment}")

    def setup_environment_config(self) -> bool:
        """Setup environment-specific configuration"""
        env_file = self.env_files[self.environment]

        if env_file:
            source_file = self.project_root / env_file
            target_file = self.project_root / ".env"

            if not source_file.exists():
                print(f"❌ Environment file not found: {source_file}")
                print(
                    f"💡 Create {source_file} with appropriate configuration"
                )
                return False

            # Backup existing .env if it exists
            if target_file.exists():
                backup_file = target_file.with_suffix(
                    f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                shutil.copy2(target_file, backup_file)
                print(f"💾 Backed up existing .env to: {backup_file}")

            # Copy environment-specific config
            shutil.copy2(source_file, target_file)
            print(f"✅ Environment configuration set: {env_file} → .env")
        else:
            print(f"ℹ️  Using existing .env for {self.environment}")

        return True

    def check_dependencies(self) -> bool:
        """Run security audit on dependencies"""
        print("🔍 Running dependency security audit...")

        try:
            # Run security audit script using secure subprocess
            audit_script = self.project_root / "scripts" / "security_audit.py"
            if not audit_script.exists():
                print("⚠️  Security audit script not found, skipping...")
                return True

            result = run_python_script(
                audit_script,
                args=["--ci"],
                working_dir=self.project_root,
                timeout=300,
            )

            if result.returncode == 0:
                print("✅ Security audit passed - no critical vulnerabilities")
                return True
            elif result.returncode == 1:
                print("⚠️  Security audit found high-severity vulnerabilities")
                print("Consider updating dependencies before deployment")
                return (
                    self.environment == "development"
                )  # Allow in dev, block in prod/staging
            else:
                print("🚨 Security audit found critical vulnerabilities")
                print(result.stdout)
                return False

        except FileNotFoundError:
            print("⚠️  Security audit script not found, skipping...")
            return True
        except (
            SecureSubprocessError,
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
        ) as e:
            print(f"⚠️  Security audit failed: {e}")
            return self.environment == "development"
        except Exception as e:
            print(f"⚠️  Unexpected error in security audit: {e}")
            return self.environment == "development"

    def update_dependencies(self) -> bool:
        """Update vulnerable dependencies"""
        print("📦 Updating vulnerable dependencies...")

        try:
            # Validate script exists before execution
            update_script = (
                self.project_root / "scripts" / "update_dependencies.py"
            )
            if not update_script.exists():
                print("⚠️  Dependency update script not found, skipping...")
                return True

            result = run_python_script(
                update_script,
                args=["--force"],
                working_dir=self.project_root,
                timeout=600,
            )

            if result.returncode == 0:
                print("✅ Dependencies updated successfully")
                return True
            else:
                print(f"❌ Dependency update failed: {result.stderr}")
                return False

        except FileNotFoundError:
            print("⚠️  Dependency update script not found, skipping...")
            return True
        except Exception as e:
            print(f"⚠️  Dependency update failed: {e}")
            return False

    def run_tests(self) -> bool:
        """Run test suite to ensure application stability"""
        print("🧪 Running test suite...")

        try:
            # Validate test files exist before execution
            test_files = [
                "tests/unit/test_state_manager.py",
                "tests/integration/test_api_endpoints.py",
            ]

            existing_test_files = []
            for test_file in test_files:
                test_path = self.project_root / test_file
                if test_path.exists():
                    existing_test_files.append(
                        test_file
                    )  # Keep relative paths

            if not existing_test_files:
                print("⚠️  No test files found, skipping...")
                return True

            # Build test arguments
            pytest_args = ["-v", "--tb=short"]

            # Add specific test selections if files exist
            if (
                "tests/integration/test_api_endpoints.py"
                in existing_test_files
            ):
                existing_test_files.extend(
                    [
                        "tests/integration/test_api_endpoints.py::TestHealthEndpoints::test_health_check_success",
                        "tests/integration/test_api_endpoints.py::TestAutomationEndpoints::test_list_automations",
                    ]
                )

            result = run_pytest(
                test_paths=existing_test_files,
                args=pytest_args,
                working_dir=self.project_root,
                timeout=120,
            )

            if result.returncode == 0:
                print("✅ Core tests passed - application is stable")
                return True
            else:
                print("❌ Tests failed:")
                print(result.stdout)
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("⚠️  Tests timed out")
            return False
        except FileNotFoundError:
            print("⚠️  pytest not found, skipping tests...")
            return True
        except Exception as e:
            print(f"⚠️  Test execution failed: {e}")
            return self.environment == "development"

    def validate_environment(self) -> bool:
        """Validate environment-specific requirements"""
        print(f"🔍 Validating {self.environment} environment...")

        # Check required environment variables
        required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]

        if self.environment in ["staging", "production"]:
            required_vars.extend(["HUB_XP_API_KEY", "ALLOWED_ORIGINS"])

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(
                f"❌ Missing required environment variables: {', '.join(missing_vars)}"
            )
            return False

        # Environment-specific checks
        if self.environment == "production":
            # Production-specific validations
            if os.getenv("ENVIRONMENT") != "production":
                print("❌ ENVIRONMENT variable must be set to 'production'")
                return False

            if os.getenv("LOG_LEVEL", "").lower() not in ["warning", "error"]:
                print(
                    "⚠️  Consider using WARNING or ERROR log level in production"
                )

        print(f"✅ {self.environment.title()} environment validation passed")
        return True

    def install_dependencies(self) -> bool:
        """Install/update Python dependencies"""
        print("📦 Checking Python dependencies...")

        try:
            # Validate requirements file exists and is safe
            requirements_files = [
                "requirements-secure.txt",
                "requirements.txt",
            ]
            requirements_file = None

            for req_file in requirements_files:
                req_path = self.project_root / req_file
                if req_path.exists():
                    requirements_file = str(req_path)
                    break

            if not requirements_file:
                print("⚠️  No requirements file found, skipping...")
                return True

            # In development, skip actual installation due to externally managed environment
            if self.environment == "development":
                print("ℹ️  Development mode: Skipping package installation")
                print(
                    "💡 Dependencies should be installed in virtual environment or with --break-system-packages"
                )
                print(f"📋 Requirements file: {requirements_file}")
                return True

            # For staging/production, attempt installation with secure subprocess
            from utils.secure_subprocess import run_pip_command

            result = run_pip_command(
                args=[
                    "install",
                    "-r",
                    requirements_file,
                    "--break-system-packages",
                ],
                working_dir=self.project_root,
                timeout=900,
            )

            if result.returncode == 0:
                print(f"✅ Dependencies installed from {requirements_file}")
                return True
            else:
                print(f"❌ Failed to install dependencies: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Dependency installation failed: {e}")
            return False

    def deploy(
        self,
        check_deps: bool = False,
        update_deps: bool = False,
        run_tests: bool = False,
        backup: bool = False,
    ) -> bool:
        """Execute deployment process"""
        print(f"🚀 Starting deployment to {self.environment} environment...")
        print("=" * 60)

        # Step 1: Setup environment configuration
        if not self.setup_environment_config():
            return False

        # Step 2: Validate environment
        if not self.validate_environment():
            return False

        # Step 3: Install dependencies
        if not self.install_dependencies():
            return False

        # Step 4: Check dependencies for vulnerabilities (if requested)
        if check_deps and not self.check_dependencies():
            print("🛑 Deployment blocked due to security issues")
            return False

        # Step 5: Update vulnerable dependencies (if requested)
        if update_deps and not self.update_dependencies():
            print("🛑 Deployment blocked due to dependency update failure")
            return False

        # Step 6: Run tests (if requested)
        if run_tests and not self.run_tests():
            print("🛑 Deployment blocked due to test failures")
            return False

        # Step 7: Display deployment summary
        self.display_deployment_summary()

        print("=" * 60)
        print(f"✅ Deployment to {self.environment} completed successfully!")

        return True

    def display_deployment_summary(self):
        """Display deployment configuration summary"""
        print("\n📋 DEPLOYMENT SUMMARY")
        print("-" * 25)
        print(f"Environment: {self.environment}")
        print(f"Host: {os.getenv('HOST', '0.0.0.0')}")
        print(f"Port: {os.getenv('PORT', '8000')}")
        print(f"Log Level: {os.getenv('LOG_LEVEL', 'info')}")

        if self.environment != "development":
            print(f"Workers: {os.getenv('WORKERS', 'N/A')}")

        print(f"Database: {os.getenv('DB_NAME', 'N/A')}")
        print(
            f"Rate Limiting: {'Disabled' if os.getenv('DISABLE_RATE_LIMITING') == 'true' else 'Enabled'}"
        )

        print("\n🎯 NEXT STEPS")
        print("-" * 15)

        if self.environment == "development":
            print("1. Start development server: python main.py")
            print("2. Access API docs: http://localhost:8000/docs")
            print("3. Run tests: pytest tests/")
        elif self.environment == "staging":
            print("1. Start staging server: python main.py")
            print("2. Run integration tests against staging")
            print("3. Verify all endpoints are working")
        else:  # production
            print(
                "1. Start production server with process manager (PM2, systemd, etc.)"
            )
            print("2. Configure reverse proxy (nginx, Apache)")
            print("3. Setup monitoring and alerting")
            print("4. Configure SSL/TLS certificates")
            print("5. Setup log aggregation")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Deploy MenuAutomacoes to different environments"
    )
    parser.add_argument(
        "environment",
        nargs="?",
        default="development",
        choices=["development", "staging", "production"],
        help="Target environment (default: development)",
    )
    parser.add_argument(
        "--check-dependencies",
        action="store_true",
        help="Run security audit before deployment",
    )
    parser.add_argument(
        "--update-dependencies",
        action="store_true",
        help="Update vulnerable dependencies",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run test suite before deployment",
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before deployment"
    )

    args = parser.parse_args()

    try:
        # Create deployer and run deployment
        deployer = Deployer(args.environment)
        success = deployer.deploy(
            check_deps=args.check_dependencies,
            update_deps=args.update_dependencies,
            run_tests=args.run_tests,
            backup=args.backup,
        )

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

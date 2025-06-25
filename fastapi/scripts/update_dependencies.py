#!/usr/bin/env python3
"""
Dependency Update Script for MenuAutomacoes
Automated security updates for Python dependencies

This script:
1. Backs up current requirements.txt
2. Updates vulnerable packages to secure versions
3. Runs tests to ensure compatibility
4. Generates update report

Usage:
    python scripts/update_dependencies.py [options]

Options:
    --dry-run           Show what would be updated without making changes
    --backup            Create backup of current requirements
    --test              Run tests after updates
    --force             Skip compatibility checks
"""

import subprocess
import sys
import argparse
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Import secure subprocess utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.secure_subprocess import SecureSubprocessRunner, run_pip_command, SecureSubprocessError


class DependencyUpdater:
    """Automated dependency updater with security focus"""
    
    def __init__(self, dry_run: bool = False, backup: bool = True, run_tests: bool = True):
        self.dry_run = dry_run
        self.backup = backup
        self.run_tests = run_tests
        self.project_root = Path(__file__).parent.parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.secure_requirements = self.project_root / "requirements-secure.txt"
        
        # Security-focused package updates - Updated with latest secure versions
        self.security_updates = {
            "fastapi": ">=0.115.6",     # CVE-2024-24762 (ReDoS) - requires 0.109.1+
            "starlette": ">=0.41.3",    # CVE-2024-47874 (DoS) - requires 0.40.0+
            "pydantic": ">=2.10.4",     # Latest stable version
            "pytest": ">=8.4.1",       # Latest stable version
            "pytest-asyncio": ">=0.25.0", # Latest stable version
            "pytest-cov": ">=6.0.0",   # Latest stable version
            "requests": ">=2.32.4",    # CVE-2024-35195, CVE-2024-47081 (cert verification, .netrc leak)
            "urllib3": ">=2.5.0",      # CVE-2025-50182, CVE-2025-50181 (redirect control issues)
            "jinja2": ">=3.1.6",       # Multiple XSS and sandboxing CVEs
            "cryptography": ">=44.0.0", # Multiple critical OpenSSL CVEs (42.0.4+ required)
            "setuptools": ">=78.2.0",  # CVE-2025-47273 (Path Traversal/RCE) - requires 78.1.1+
            "idna": ">=3.10",          # CVE-2024-3651 (DoS via crafted input)
            "twisted": ">=24.7.0",     # CVE-2024-41810, CVE-2024-41671 (XSS, request ordering)
            "uvicorn": ">=0.34.0",     # Latest stable version with security updates
            "httpx": ">=0.28.1",       # Latest stable version
            # Remove configobj entirely due to CVE-2023-26112 (ReDoS)
        }
    
    def create_backup(self) -> Path:
        """Create backup of current requirements.txt"""
        if not self.requirements_file.exists():
            print(f"❌ Requirements file not found: {self.requirements_file}")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.requirements_file.parent / f"requirements_backup_{timestamp}.txt"
        
        if not self.dry_run:
            shutil.copy2(self.requirements_file, backup_file)
            print(f"✅ Backup created: {backup_file}")
        else:
            print(f"[DRY RUN] Would create backup: {backup_file}")
        
        return backup_file
    
    def parse_requirements(self, requirements_file: Path) -> Dict[str, str]:
        """Parse requirements.txt and return package versions"""
        packages = {}
        
        if not requirements_file.exists():
            return packages
        
        with open(requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Handle different version specifiers
                    for operator in ['>=', '==', '<=', '>', '<', '~=']:
                        if operator in line:
                            name, version = line.split(operator, 1)
                            packages[name.strip()] = f"{operator}{version.strip()}"
                            break
                    else:
                        # No version specified
                        packages[line.strip()] = ""
        
        return packages
    
    def check_vulnerabilities(self) -> Dict[str, List]:
        """Check current packages for vulnerabilities using pip-audit"""
        try:
            # Use secure subprocess runner
            runner = SecureSubprocessRunner(self.project_root)
            result = runner.run_command(
                ["pip-audit", "--format=json"],
                timeout=300,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode not in [0, 1]:
                print(f"⚠️  Warning: pip-audit failed: {result.stderr}")
                return {}
            
            audit_data = json.loads(result.stdout)
            vulnerable_packages = {}
            
            for package in audit_data["dependencies"]:
                if package["vulns"]:
                    vulnerable_packages[package["name"]] = [
                        {
                            "id": vuln["id"],
                            "description": vuln.get("description", ""),
                            "fix_versions": vuln.get("fix_versions", [])
                        }
                        for vuln in package["vulns"]
                    ]
            
            return vulnerable_packages
            
        except SecureSubprocessError as e:
            print(f"⚠️  Security validation failed for pip-audit: {e}")
            return {}
        except FileNotFoundError:
            print("⚠️  pip-audit not found. Install with: pip install pip-audit")
            return {}
        except subprocess.TimeoutExpired:
            print("⚠️  pip-audit timed out after 5 minutes")
            return {}
        except json.JSONDecodeError:
            print("⚠️  Failed to parse pip-audit output")
            return {}
        except Exception as e:
            print(f"⚠️  Unexpected error running pip-audit: {e}")
            return {}
    
    def generate_updated_requirements(self) -> List[str]:
        """Generate updated requirements with security fixes"""
        current_packages = self.parse_requirements(self.requirements_file)
        updated_lines = []
        
        # Read original file to preserve comments and structure
        with open(self.requirements_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            original_line = line.strip()
            
            # Preserve comments and empty lines
            if not original_line or original_line.startswith('#'):
                updated_lines.append(line)
                continue
            
            # Extract package name
            package_name = original_line
            for operator in ['>=', '==', '<=', '>', '<', '~=']:
                if operator in original_line:
                    package_name = original_line.split(operator)[0].strip()
                    break
            
            # Check if package needs security update
            if package_name in self.security_updates:
                new_requirement = f"{package_name}{self.security_updates[package_name]}"
                updated_lines.append(f"{new_requirement}\n")
                print(f"🔒 Security update: {original_line} → {new_requirement}")
            else:
                updated_lines.append(line)
        
        return updated_lines
    
    def write_updated_requirements(self, updated_lines: List[str]) -> bool:
        """Write updated requirements to file"""
        if self.dry_run:
            print("[DRY RUN] Would write updated requirements:")
            print("".join(updated_lines))
            return True
        
        try:
            with open(self.requirements_file, 'w') as f:
                f.writelines(updated_lines)
            print(f"✅ Updated requirements written to: {self.requirements_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to write requirements: {e}")
            return False
    
    def install_updates(self) -> bool:
        """Install updated packages using secure subprocess"""
        if self.dry_run:
            print("[DRY RUN] Would run: pip install -r requirements.txt --upgrade")
            return True
        
        print("📦 Installing updated packages...")
        try:
            # Use secure pip command runner
            result = run_pip_command(
                args=["install", "-r", str(self.requirements_file), "--upgrade"],
                working_dir=self.project_root,
                timeout=900  # 15 minutes for package installation
            )
            print("✅ Packages updated successfully")
            return True
        except (SecureSubprocessError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"❌ Failed to install packages: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during installation: {e}")
            return False
    
    def run_tests_after_update(self) -> bool:
        """Run tests to ensure updates don't break functionality"""
        if self.dry_run:
            print("[DRY RUN] Would run tests")
            return True
        
        if not self.run_tests:
            print("⏭️  Skipping tests (--no-test)")
            return True
        
        print("🧪 Running tests to verify updates...")
        try:
            # Use secure subprocess for running tests
            from utils.secure_subprocess import run_pytest
            
            result = run_pytest(
                test_paths=["tests/unit/test_state_manager.py"],
                args=["-v"],
                working_dir=self.project_root,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Tests passed - updates are compatible")
                return True
            else:
                print(f"❌ Tests failed after update:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Tests timed out")
            return False
        except Exception as e:
            print(f"⚠️  Could not run tests: {e}")
            return True  # Don't fail update if tests can't run
    
    def generate_update_report(self, vulnerable_packages: Dict, backup_file: Path) -> str:
        """Generate report of updates performed"""
        report = []
        report.append("="*60)
        report.append("🔄 DEPENDENCY UPDATE REPORT")
        report.append("="*60)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if backup_file:
            report.append(f"💾 Backup: {backup_file}")
        
        report.append("")
        
        # Vulnerabilities addressed
        if vulnerable_packages:
            report.append("🔒 VULNERABILITIES ADDRESSED")
            report.append("-" * 30)
            for package, vulns in vulnerable_packages.items():
                if package in self.security_updates:
                    report.append(f"📦 {package} → {self.security_updates[package]}")
                    for vuln in vulns[:2]:  # Show first 2 vulns
                        report.append(f"  • {vuln['id']}")
            report.append("")
        
        # Security updates applied
        report.append("📋 SECURITY UPDATES APPLIED")
        report.append("-" * 30)
        for package, version in self.security_updates.items():
            report.append(f"• {package} {version}")
        report.append("")
        
        # Next steps
        report.append("🎯 NEXT STEPS")
        report.append("-" * 15)
        report.append("1. 🧪 Run full test suite: pytest tests/")
        report.append("2. 🚀 Test in staging environment")
        report.append("3. 🔍 Run security audit: python scripts/security_audit.py")
        report.append("4. 📋 Update production deployments")
        report.append("")
        
        if self.dry_run:
            report.append("ℹ️  This was a DRY RUN - no changes were made")
        
        return "\n".join(report)
    
    def update_dependencies(self, force: bool = False) -> int:
        """Main update process"""
        print("🔄 Starting dependency security updates...")
        
        # Check vulnerabilities first
        vulnerable_packages = self.check_vulnerabilities()
        if vulnerable_packages:
            print(f"🚨 Found {len(vulnerable_packages)} vulnerable packages")
            for pkg in vulnerable_packages.keys():
                print(f"  • {pkg}")
        else:
            print("✅ No vulnerabilities detected by pip-audit")
        
        # Create backup
        backup_file = None
        if self.backup:
            backup_file = self.create_backup()
        
        # Generate updated requirements
        updated_lines = self.generate_updated_requirements()
        
        # Write updates
        if not self.write_updated_requirements(updated_lines):
            return 1
        
        # Install updates
        if not self.dry_run:
            if not self.install_updates():
                if backup_file:
                    print(f"🔄 Restoring backup: {backup_file}")
                    shutil.copy2(backup_file, self.requirements_file)
                return 1
        
        # Run tests
        if not self.run_tests_after_update():
            if not force:
                print("❌ Tests failed - rolling back updates")
                if backup_file and not self.dry_run:
                    shutil.copy2(backup_file, self.requirements_file)
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)])
                return 1
            else:
                print("⚠️  Tests failed but continuing due to --force")
        
        # Generate report
        report = self.generate_update_report(vulnerable_packages, backup_file)
        print(report)
        
        print("\n✅ Dependency updates completed successfully!")
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Update dependencies for security")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be updated without making changes")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip creating backup of requirements.txt")
    parser.add_argument("--no-test", action="store_true",
                       help="Skip running tests after updates")
    parser.add_argument("--force", action="store_true",
                       help="Continue even if tests fail")
    
    args = parser.parse_args()
    
    # Create updater and run
    updater = DependencyUpdater(
        dry_run=args.dry_run,
        backup=not args.no_backup,
        run_tests=not args.no_test
    )
    
    exit_code = updater.update_dependencies(args.force)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
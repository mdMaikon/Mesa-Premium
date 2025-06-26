#!/usr/bin/env python3
"""
Automated Security Update Pipeline for MenuAutomacoes
Continuous dependency monitoring and automated security updates

This script implements the automated update pipeline recommended in CHECK.md:
1. Daily vulnerability scanning
2. Automated security updates for critical vulnerabilities
3. Integration with CI/CD for continuous monitoring
4. Alert generation for manual review requirements

Usage:
    python scripts/automated_security_updates.py [options]

Options:
    --mode [scan|update|full]    Operation mode (default: full)
    --severity [critical|high|medium|low]  Minimum severity to process
    --schedule                   Run in scheduled mode (non-interactive)
    --notify                     Send notifications on findings
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Import project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.secure_subprocess import SecureSubprocessRunner

from scripts.security_audit import SecurityAuditor
from scripts.update_dependencies import DependencyUpdater


class AutomatedSecurityPipeline:
    """Automated security update pipeline with CI/CD integration"""

    def __init__(
        self,
        mode: str = "full",
        min_severity: str = "high",
        schedule_mode: bool = False,
        notify: bool = False,
    ):
        self.mode = mode
        self.min_severity = min_severity
        self.schedule_mode = schedule_mode
        self.notify = notify
        self.project_root = Path(__file__).parent.parent

        # Severity hierarchy for decision making
        self.severity_levels = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
        }

        # Auto-update rules based on severity
        self.auto_update_rules = {
            "critical": True,  # Always auto-update critical vulnerabilities
            "high": True,  # Auto-update high severity if tests pass
            "medium": False,  # Require manual review
            "low": False,  # Require manual review
        }

        # Initialize components
        self.runner = SecureSubprocessRunner(self.project_root)
        self.auditor = SecurityAuditor(output_format="json")
        self.updater = DependencyUpdater(
            dry_run=False, backup=True, run_tests=True
        )

    def scan_vulnerabilities(self) -> dict:
        """Scan for vulnerabilities and return structured results"""
        print("🔍 Scanning for security vulnerabilities...")

        try:
            # Run comprehensive security audit
            audit_data = self.auditor.run_pip_audit()
            analysis = self.auditor.analyze_vulnerabilities(audit_data)

            # Categorize findings by severity
            findings = {
                "critical": [],
                "high": [],
                "medium": [],
                "low": [],
                "total_vulnerabilities": analysis["total_vulnerabilities"],
                "vulnerable_packages": analysis["vulnerable_packages"],
                "scan_timestamp": datetime.now().isoformat(),
            }

            # Process vulnerabilities and assign severity
            for package in audit_data["dependencies"]:
                if package.get("vulns"):
                    for vuln in package["vulns"]:
                        severity = self._determine_vulnerability_severity(vuln)

                        vuln_info = {
                            "package": package["name"],
                            "version": package["version"],
                            "vulnerability_id": vuln["id"],
                            "description": vuln.get("description", ""),
                            "fix_versions": vuln.get("fix_versions", []),
                            "aliases": vuln.get("aliases", []),
                        }

                        findings[severity].append(vuln_info)

            return findings

        except Exception as e:
            print(f"❌ Vulnerability scan failed: {e}")
            return {"error": str(e)}

    def _determine_vulnerability_severity(self, vuln: dict) -> str:
        """Determine vulnerability severity based on description and CVE data"""
        description = vuln.get("description", "").lower()
        # vuln_id is available but not currently used in severity determination
        _vuln_id = vuln.get("id", "").lower()

        # Critical indicators
        critical_keywords = [
            "remote code execution",
            "rce",
            "arbitrary code execution",
            "privilege escalation",
            "authentication bypass",
            "sql injection",
            "command injection",
            "path traversal",
            "directory traversal",
        ]

        # High severity indicators
        high_keywords = [
            "cross-site scripting",
            "xss",
            "csrf",
            "session hijacking",
            "denial of service",
            "dos",
            "buffer overflow",
            "memory corruption",
            "information disclosure",
            "data exposure",
        ]

        # Medium severity indicators
        medium_keywords = [
            "redos",
            "regular expression denial",
            "resource exhaustion",
            "timeout",
            "redirect",
            "validation bypass",
        ]

        # Check for critical vulnerabilities
        if any(keyword in description for keyword in critical_keywords):
            return "critical"

        # Check for high severity
        if any(keyword in description for keyword in high_keywords):
            return "high"

        # Check for medium severity
        if any(keyword in description for keyword in medium_keywords):
            return "medium"

        # Default to low if no clear indicators
        return "low"

    def should_auto_update(self, findings: dict) -> tuple[bool, str]:
        """Determine if auto-update should proceed based on findings"""
        if not findings or "error" in findings:
            return False, "Scan failed or no data available"

        critical_count = len(findings.get("critical", []))
        high_count = len(findings.get("high", []))
        medium_count = len(findings.get("medium", []))

        # Always update critical vulnerabilities
        if critical_count > 0:
            return (
                True,
                f"Found {critical_count} critical vulnerabilities requiring immediate update",
            )

        # Update high severity if within threshold and in auto-update mode
        if high_count > 0 and self.auto_update_rules["high"]:
            severity_threshold = self.severity_levels.get(self.min_severity, 3)
            if self.severity_levels["high"] >= severity_threshold:
                return (
                    True,
                    f"Found {high_count} high-severity vulnerabilities approved for auto-update",
                )

        # Require manual review for medium/low
        if medium_count > 0:
            return (
                False,
                f"Found {medium_count} medium-severity vulnerabilities requiring manual review",
            )

        return False, "No vulnerabilities requiring automatic updates"

    def perform_automated_updates(self, findings: dict) -> dict:
        """Perform automated security updates based on findings"""
        update_results = {
            "attempted": False,
            "successful": False,
            "packages_updated": [],
            "test_results": "not_run",
            "rollback_performed": False,
            "error": None,
        }

        should_update, reason = self.should_auto_update(findings)

        if not should_update:
            update_results["error"] = f"Auto-update not performed: {reason}"
            return update_results

        print(f"🔄 Proceeding with automated updates: {reason}")
        update_results["attempted"] = True

        try:
            # Create backup first
            backup_file = self.updater.create_backup()

            # Generate and apply updates
            updated_lines = self.updater.generate_updated_requirements()

            if self.updater.write_updated_requirements(updated_lines):
                print("✅ Requirements file updated")

                # Install updates
                if self.updater.install_updates():
                    print("✅ Packages installed successfully")
                    update_results["packages_updated"] = list(
                        self.updater.security_updates.keys()
                    )

                    # Run tests to validate updates
                    if self.updater.run_tests_after_update():
                        print("✅ Tests passed - updates validated")
                        update_results["successful"] = True
                        update_results["test_results"] = "passed"
                    else:
                        print("❌ Tests failed - rolling back updates")
                        if backup_file:
                            self._rollback_updates(backup_file)
                            update_results["rollback_performed"] = True
                        update_results["test_results"] = "failed"
                        update_results["error"] = "Tests failed after update"
                else:
                    update_results["error"] = "Package installation failed"
            else:
                update_results["error"] = (
                    "Failed to write updated requirements"
                )

        except Exception as e:
            update_results["error"] = f"Update process failed: {e}"
            print(f"❌ Update process failed: {e}")

        return update_results

    def _rollback_updates(self, backup_file: Path) -> bool:
        """Rollback updates using backup file"""
        try:
            import shutil

            shutil.copy2(backup_file, self.updater.requirements_file)

            # Reinstall from backup
            _result = self.runner.run_command(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(self.updater.requirements_file),
                ],
                timeout=600,
            )

            print(f"🔄 Successfully rolled back to: {backup_file}")
            return True

        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False

    def generate_security_report(
        self, findings: dict, update_results: dict
    ) -> str:
        """Generate comprehensive security report"""
        report = []
        report.append("=" * 70)
        report.append("🔒 AUTOMATED SECURITY UPDATE REPORT")
        report.append("=" * 70)
        report.append(
            f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report.append(f"🔍 Scan Mode: {self.mode}")
        report.append(f"⚠️  Min Severity: {self.min_severity}")
        report.append("")

        # Vulnerability summary
        if "error" not in findings:
            report.append("📊 VULNERABILITY SUMMARY")
            report.append("-" * 25)
            report.append(f"🔴 Critical: {len(findings.get('critical', []))}")
            report.append(f"🟠 High: {len(findings.get('high', []))}")
            report.append(f"🟡 Medium: {len(findings.get('medium', []))}")
            report.append(f"🟢 Low: {len(findings.get('low', []))}")
            report.append(
                f"📦 Total Vulnerable Packages: {findings.get('vulnerable_packages', 0)}"
            )
            report.append("")

            # Critical vulnerabilities details
            if findings.get("critical"):
                report.append(
                    "🚨 CRITICAL VULNERABILITIES (IMMEDIATE ACTION REQUIRED)"
                )
                report.append("-" * 55)
                for vuln in findings["critical"]:
                    report.append(f"📦 {vuln['package']} {vuln['version']}")
                    report.append(f"  🆔 {vuln['vulnerability_id']}")
                    if vuln["fix_versions"]:
                        report.append(
                            f"  🔧 Fix: {', '.join(vuln['fix_versions'])}"
                        )
                    report.append(f"  📝 {vuln['description'][:100]}...")
                    report.append("")

        # Update results
        if update_results["attempted"]:
            report.append("🔄 UPDATE RESULTS")
            report.append("-" * 20)
            if update_results["successful"]:
                report.append("✅ Updates applied successfully")
                report.append(
                    f"📦 Packages updated: {len(update_results['packages_updated'])}"
                )
                for pkg in update_results["packages_updated"]:
                    report.append(f"  • {pkg}")
            else:
                report.append("❌ Updates failed")
                if update_results["error"]:
                    report.append(f"💥 Error: {update_results['error']}")
                if update_results["rollback_performed"]:
                    report.append("🔄 Rollback performed")
            report.append("")

        # Recommendations
        report.append("🎯 RECOMMENDATIONS")
        report.append("-" * 20)

        if findings.get("critical") or findings.get("high"):
            if not update_results["successful"]:
                report.append(
                    "1. 🚨 URGENT: Manually review and update critical/high vulnerabilities"
                )
            report.append("2. 🧪 Run full test suite after any manual updates")
            report.append(
                "3. 🚀 Deploy updates to staging environment for validation"
            )

        if findings.get("medium") or findings.get("low"):
            report.append(
                "4. 📋 Schedule manual review for medium/low severity vulnerabilities"
            )

        report.append("5. 🔄 Configure automated daily vulnerability scanning")
        report.append("6. 📧 Set up security alerts for critical findings")
        report.append("")

        # Next scan
        next_scan = datetime.now() + timedelta(days=1)
        report.append(
            f"⏰ Next automated scan: {next_scan.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        return "\n".join(report)

    def send_notification(self, report: str, findings: dict):
        """Send notification if critical vulnerabilities found"""
        if not self.notify:
            return

        critical_count = len(findings.get("critical", []))
        high_count = len(findings.get("high", []))

        if critical_count == 0 and high_count == 0:
            return  # No urgent notifications needed

        # In a real implementation, this would send email/Slack/Teams notifications
        print("📧 Security notification would be sent:")
        print(f"   Critical vulnerabilities: {critical_count}")
        print(f"   High severity vulnerabilities: {high_count}")
        print("   (Configure SMTP settings in production)")

    def run_pipeline(self) -> int:
        """Run the complete automated security pipeline"""
        print("🚀 Starting automated security update pipeline...")

        try:
            # Step 1: Scan for vulnerabilities
            if self.mode in ["scan", "full"]:
                findings = self.scan_vulnerabilities()

                if "error" in findings:
                    print(f"❌ Pipeline failed: {findings['error']}")
                    return 1
            else:
                findings = {"total_vulnerabilities": 0}

            # Step 2: Perform automated updates
            update_results = {"attempted": False}
            if self.mode in ["update", "full"]:
                update_results = self.perform_automated_updates(findings)

            # Step 3: Generate report
            report = self.generate_security_report(findings, update_results)
            print(report)

            # Step 4: Send notifications if needed
            self.send_notification(report, findings)

            # Step 5: Save report for CI/CD integration
            report_file = self.project_root / "security_update_report.txt"
            with open(report_file, "w") as f:
                f.write(report)
            print(f"📄 Report saved: {report_file}")

            # Determine exit code
            if findings.get("critical") and not update_results.get(
                "successful"
            ):
                print(
                    "🚨 Exiting with error code due to unresolved critical vulnerabilities"
                )
                return 2  # Critical vulnerabilities not resolved
            elif findings.get("high") and not update_results.get("successful"):
                print(
                    "⚠️ Exiting with warning due to unresolved high-severity vulnerabilities"
                )
                return 1  # High severity vulnerabilities not resolved
            else:
                print("✅ Security pipeline completed successfully")
                return 0

        except Exception as e:
            print(f"❌ Pipeline failed with unexpected error: {e}")
            return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Automated security update pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["scan", "update", "full"],
        default="full",
        help="Operation mode (default: full)",
    )
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low"],
        default="high",
        help="Minimum severity to process",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run in scheduled mode (non-interactive)",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send notifications on critical findings",
    )

    args = parser.parse_args()

    # Create and run pipeline
    pipeline = AutomatedSecurityPipeline(
        mode=args.mode,
        min_severity=args.severity,
        schedule_mode=args.schedule,
        notify=args.notify,
    )

    exit_code = pipeline.run_pipeline()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

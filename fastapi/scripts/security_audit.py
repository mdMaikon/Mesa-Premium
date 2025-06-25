#!/usr/bin/env python3
"""
Security Audit Script for MenuAutomacoes
Automated dependency vulnerability scanning using pip-audit

This script performs:
1. Vulnerability scanning of all installed packages
2. Generation of detailed security reports
3. Suggestions for package updates
4. Integration with CI/CD workflows

Usage:
    python scripts/security_audit.py [options]

Options:
    --format json|html|text    Output format (default: text)
    --output FILE             Output file (default: stdout)
    --fix                     Suggest fixes for vulnerabilities
    --ci                      Exit with non-zero code if vulnerabilities found
"""

import subprocess
import json
import sys
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import secure subprocess utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.secure_subprocess import SecureSubprocessRunner, SecureSubprocessError


class SecurityAuditor:
    """Automated security auditor for Python dependencies"""
    
    def __init__(self, output_format: str = "text", output_file: str = None):
        self.output_format = output_format
        self.output_file = output_file
        self.vulnerabilities_found = 0
        self.critical_vulns = 0
        self.high_vulns = 0
        self.medium_vulns = 0
        self.low_vulns = 0
    
    def run_pip_audit(self) -> Dict[str, Any]:
        """Run pip-audit and return parsed results"""
        try:
            # Use secure subprocess runner for pip-audit
            runner = SecureSubprocessRunner()
            
            result = runner.run_command(
                command=["pip-audit", "--format=json"],
                timeout=300,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode not in [0, 1]:  # 1 is expected when vulns found
                raise RuntimeError(f"pip-audit failed: {result.stderr}")
            
            return json.loads(result.stdout)
        
        except SecureSubprocessError as e:
            print(f"ERROR: Security validation failed: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("ERROR: pip-audit not found. Install with: pip install pip-audit")
            sys.exit(1)
        except subprocess.TimeoutExpired:
            print("ERROR: pip-audit timed out after 5 minutes")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse pip-audit output: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: Unexpected error running pip-audit: {e}")
            sys.exit(1)
    
    def analyze_vulnerabilities(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze vulnerabilities and categorize by severity"""
        analysis = {
            "total_packages": len(audit_data["dependencies"]),
            "vulnerable_packages": 0,
            "total_vulnerabilities": 0,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "critical_packages": [],
            "recommended_updates": {},
            "summary": ""
        }
        
        for package in audit_data["dependencies"]:
            # Handle different formats - pip-audit can return vulns as list or empty
            vulns = package.get("vulns", [])
            if vulns:
                analysis["vulnerable_packages"] += 1
                package_vulns = len(vulns)
                analysis["total_vulnerabilities"] += package_vulns
                
                # Determine highest severity for this package
                highest_severity = self._get_package_severity(vulns)
                analysis["by_severity"][highest_severity] += 1
                
                # Track critical packages
                if highest_severity == "critical":
                    analysis["critical_packages"].append({
                        "name": package["name"],
                        "version": package["version"],
                        "vulns": package_vulns
                    })
                
                # Get recommended fix versions
                fix_versions = self._get_fix_versions(vulns)
                if fix_versions:
                    analysis["recommended_updates"][package["name"]] = {
                        "current": package["version"],
                        "recommended": max(fix_versions),  # Latest fix version
                        "all_fixes": fix_versions
                    }
        
        # Update instance counters
        self.vulnerabilities_found = analysis["total_vulnerabilities"]
        self.critical_vulns = analysis["by_severity"]["critical"]
        self.high_vulns = analysis["by_severity"]["high"]
        self.medium_vulns = analysis["by_severity"]["medium"]
        self.low_vulns = analysis["by_severity"]["low"]
        
        return analysis
    
    def _get_package_severity(self, vulns: List[Dict]) -> str:
        """Determine highest severity level for package vulnerabilities"""
        # Simple heuristic based on CVE keywords and vulnerability descriptions
        severity_keywords = {
            "critical": ["remote code execution", "rce", "arbitrary code", "privilege escalation"],
            "high": ["xss", "csrf", "sql injection", "authentication bypass", "dos", "denial of service"],
            "medium": ["information disclosure", "path traversal", "redirect"],
            "low": ["deprecation", "minor"]
        }
        
        highest = "low"
        for vuln in vulns:
            description = vuln.get("description", "").lower()
            
            for severity, keywords in severity_keywords.items():
                if any(keyword in description for keyword in keywords):
                    if severity == "critical":
                        return "critical"
                    elif severity == "high" and highest != "critical":
                        highest = "high"
                    elif severity == "medium" and highest not in ["critical", "high"]:
                        highest = "medium"
        
        return highest
    
    def _get_fix_versions(self, vulns: List[Dict]) -> List[str]:
        """Extract recommended fix versions from vulnerabilities"""
        fix_versions = set()
        for vuln in vulns:
            if "fix_versions" in vuln and vuln["fix_versions"]:
                fix_versions.update(vuln["fix_versions"])
        return sorted(list(fix_versions))
    
    def generate_report(self, audit_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate security report in specified format"""
        if self.output_format == "json":
            return self._generate_json_report(audit_data, analysis)
        elif self.output_format == "html":
            return self._generate_html_report(audit_data, analysis)
        else:
            return self._generate_text_report(audit_data, analysis)
    
    def _generate_text_report(self, audit_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate human-readable text report"""
        report = []
        report.append("="*60)
        report.append("🔒 SECURITY AUDIT REPORT")
        report.append("="*60)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"🔍 Tool: pip-audit")
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 20)
        report.append(f"Total packages scanned: {analysis['total_packages']}")
        report.append(f"Vulnerable packages: {analysis['vulnerable_packages']}")
        report.append(f"Total vulnerabilities: {analysis['total_vulnerabilities']}")
        report.append("")
        
        # Severity breakdown
        report.append("⚠️  SEVERITY BREAKDOWN")
        report.append("-" * 20)
        report.append(f"🔴 Critical: {analysis['by_severity']['critical']} packages")
        report.append(f"🟠 High: {analysis['by_severity']['high']} packages")
        report.append(f"🟡 Medium: {analysis['by_severity']['medium']} packages")
        report.append(f"🟢 Low: {analysis['by_severity']['low']} packages")
        report.append("")
        
        # Critical packages (if any)
        if analysis["critical_packages"]:
            report.append("🚨 CRITICAL PACKAGES (IMMEDIATE ACTION REQUIRED)")
            report.append("-" * 50)
            for pkg in analysis["critical_packages"]:
                report.append(f"• {pkg['name']} {pkg['version']} ({pkg['vulns']} vulnerabilities)")
            report.append("")
        
        # Vulnerable packages details
        if analysis["vulnerable_packages"] > 0:
            report.append("📋 VULNERABLE PACKAGES DETAILS")
            report.append("-" * 30)
            
            for package in audit_data["dependencies"]:
                vulns = package.get("vulns", [])
                if vulns:
                    report.append(f"\n📦 {package['name']} {package['version']}")
                    for vuln in vulns:
                        report.append(f"  • {vuln['id']}")
                        if vuln.get("aliases"):
                            report.append(f"    Aliases: {', '.join(vuln['aliases'])}")
                        if vuln.get("fix_versions"):
                            report.append(f"    Fix available: {', '.join(vuln['fix_versions'])}")
                        if vuln.get("description"):
                            # Truncate long descriptions
                            desc = vuln["description"][:200] + "..." if len(vuln["description"]) > 200 else vuln["description"]
                            report.append(f"    Description: {desc}")
        
        # Recommendations
        if analysis["recommended_updates"]:
            report.append("\n💡 RECOMMENDED UPDATES")
            report.append("-" * 25)
            for pkg, update in analysis["recommended_updates"].items():
                report.append(f"• {pkg}: {update['current']} → {update['recommended']}")
            
            report.append("\n📝 UPDATE COMMANDS")
            report.append("-" * 20)
            report.append("# Update individual packages:")
            for pkg, update in analysis["recommended_updates"].items():
                report.append(f"pip install {pkg}>={update['recommended']}")
            
            report.append("\n# Or update requirements.txt and run:")
            report.append("pip install -r requirements.txt --upgrade")
        
        # Action items
        report.append("\n🎯 NEXT ACTIONS")
        report.append("-" * 15)
        if analysis["by_severity"]["critical"] > 0:
            report.append("1. 🚨 URGENT: Update critical packages immediately")
        if analysis["by_severity"]["high"] > 0:
            report.append("2. ⚡ HIGH: Schedule high-severity updates within 24-48h")
        if analysis["by_severity"]["medium"] > 0:
            report.append("3. 📅 MEDIUM: Plan medium-severity updates in next sprint")
        if analysis["total_vulnerabilities"] == 0:
            report.append("✅ No vulnerabilities found - great job!")
        
        report.append(f"\n4. 🔄 Schedule regular audits (weekly/monthly)")
        report.append(f"5. 📋 Review and update dependency management policies")
        
        return "\n".join(report)
    
    def _generate_json_report(self, audit_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate JSON report for programmatic consumption"""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool": "pip-audit",
                "format_version": "1.0"
            },
            "summary": analysis,
            "raw_audit_data": audit_data
        }
        return json.dumps(report, indent=2)
    
    def _generate_html_report(self, audit_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate HTML report for web viewing"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Security Audit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .critical {{ color: #dc3545; }}
        .high {{ color: #fd7e14; }}
        .medium {{ color: #ffc107; }}
        .low {{ color: #28a745; }}
        .package {{ border: 1px solid #dee2e6; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .vulnerability {{ background: #f8f9fa; margin: 5px 0; padding: 10px; border-radius: 3px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #dee2e6; padding: 8px; text-align: left; }}
        th {{ background: #e9ecef; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Security Audit Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h2>📊 Summary</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total Packages</td><td>{analysis['total_packages']}</td></tr>
        <tr><td>Vulnerable Packages</td><td>{analysis['vulnerable_packages']}</td></tr>
        <tr><td>Total Vulnerabilities</td><td>{analysis['total_vulnerabilities']}</td></tr>
        <tr><td class="critical">Critical</td><td>{analysis['by_severity']['critical']}</td></tr>
        <tr><td class="high">High</td><td>{analysis['by_severity']['high']}</td></tr>
        <tr><td class="medium">Medium</td><td>{analysis['by_severity']['medium']}</td></tr>
        <tr><td class="low">Low</td><td>{analysis['by_severity']['low']}</td></tr>
    </table>
"""
        
        # Add vulnerable packages
        if analysis["vulnerable_packages"] > 0:
            html += "<h2>📋 Vulnerable Packages</h2>"
            for package in audit_data["dependencies"]:
                vulns = package.get("vulns", [])
                if vulns:
                    html += f"""<div class="package">
                        <h3>📦 {package['name']} {package['version']}</h3>"""
                    for vuln in vulns:
                        html += f"""<div class="vulnerability">
                            <strong>{vuln['id']}</strong><br>
                            {vuln.get('description', 'No description available')[:300]}...
                        </div>"""
                    html += "</div>"
        
        html += "</body></html>"
        return html
    
    def save_report(self, report: str):
        """Save report to file or print to stdout"""
        if self.output_file:
            Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to: {self.output_file}")
        else:
            print(report)
    
    def run_audit(self, ci_mode: bool = False, suggest_fixes: bool = False) -> int:
        """Run complete security audit"""
        print("🔍 Running security audit...")
        
        # Run pip-audit
        audit_data = self.run_pip_audit()
        
        # Analyze results
        analysis = self.analyze_vulnerabilities(audit_data)
        
        # Generate report
        report = self.generate_report(audit_data, analysis)
        
        # Save/display report
        self.save_report(report)
        
        # Print quick summary
        if self.output_format != "json":
            print(f"\n🎯 Quick Summary: {analysis['vulnerable_packages']} vulnerable packages, {analysis['total_vulnerabilities']} total vulnerabilities")
            if analysis["by_severity"]["critical"] > 0:
                print(f"🚨 CRITICAL: {analysis['by_severity']['critical']} packages need immediate attention!")
        
        # Suggest fixes if requested
        if suggest_fixes and analysis["recommended_updates"]:
            print("\n💡 Suggested update commands:")
            for pkg, update in analysis["recommended_updates"].items():
                print(f"pip install '{pkg}>={update['recommended']}'")
        
        # Return appropriate exit code for CI
        if ci_mode:
            if analysis["by_severity"]["critical"] > 0:
                return 2  # Critical vulnerabilities
            elif analysis["by_severity"]["high"] > 0:
                return 1  # High vulnerabilities
            else:
                return 0  # No critical/high vulnerabilities
        
        return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Security audit for Python dependencies")
    parser.add_argument("--format", choices=["text", "json", "html"], default="text",
                       help="Output format (default: text)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--fix", action="store_true", help="Suggest fixes for vulnerabilities")
    parser.add_argument("--ci", action="store_true", help="CI mode - exit with error code if vulnerabilities found")
    
    args = parser.parse_args()
    
    # Create auditor and run
    auditor = SecurityAuditor(args.format, args.output)
    exit_code = auditor.run_audit(args.ci, args.fix)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
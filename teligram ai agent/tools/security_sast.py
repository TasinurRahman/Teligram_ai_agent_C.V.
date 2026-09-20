import re
import os
import logging

logger = logging.getLogger(__name__)

class SecuritySASTTool:
    """
    Static Application Security Testing (SAST) Scanner:
    Inspects source code for common OWASP Top 10 security vulnerabilities:
    - Hardcoded credentials / API keys
    - SQL Injection patterns
    - Unsanitized XSS reflections
    - Insecure CORS / Eval calls
    """

    PATTERNS = {
        "Hardcoded API Key / Secret": r"(?i)(api_key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
        "Potential SQL Injection": r"(?i)(select|insert|update|delete)\s+.*\s+from\s+.*(%s|\+)",
        "Unsafe JavaScript Eval": r"eval\s*\(",
        "Insecure InnerHTML Injection (XSS Risk)": r"\.innerHTML\s*="
    }

    def scan_code_snippet(self, code: str) -> list:
        """Scans a single string of code for security vulnerabilities."""
        vulnerabilities = []
        for vuln_name, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, code)
            if matches:
                vulnerabilities.append({
                    "rule": vuln_name,
                    "severity": "HIGH" if "Key" in vuln_name or "SQL" in vuln_name else "MEDIUM",
                    "occurrences": len(matches)
                })
        return vulnerabilities

    def scan_directory(self, dir_path: str) -> dict:
        """Scans all source code files in a target directory."""
        report = {}
        if not os.path.exists(dir_path):
            return {"error": f"Path '{dir_path}' does not exist."}

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith((".py", ".js", ".html", ".php")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        vulns = self.scan_code_snippet(content)
                        if vulns:
                            report[file_path] = vulns
                    except Exception as e:
                        logger.error(f"Error scanning file {file_path}: {e}")
        return report

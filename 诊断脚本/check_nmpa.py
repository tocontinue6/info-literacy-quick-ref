# -*- coding: utf-8 -*-
"""Verify the old vs new NMPA data-query URL before changing anything."""
import ssl, urllib.request, urllib.error, socket

CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

TARGETS = [
    ("旧地址", "https://www.nmpa.gov.cn/datasearch/home-index.html"),
    ("新地址", "https://datasearch.nmpa.gov.cn/datasearch/home-index.html"),
    ("新地址根", "https://datasearch.nmpa.gov.cn/"),
    ("旧站点根", "https://www.nmpa.gov.cn/"),
]

for label, u in TARGETS:
    try:
        req = urllib.request.Request(u, headers={
            "User-Agent": UA, "Accept": "text/html,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9"})
        with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
            body = r.read(400)
            print(f"{label:8s} {r.status}  final={r.geturl()}")
            print(f"         server={r.headers.get('Server')} len={r.headers.get('Content-Length')}")
    except urllib.error.HTTPError as e:
        print(f"{label:8s} HTTP {e.code} {e.reason}   final={e.url if hasattr(e,'url') else ''}")
    except Exception as e:
        print(f"{label:8s} {type(e).__name__}: {str(e)[:110]}")

print()
# DNS resolution tells us whether the new hostname actually exists
for h in ("www.nmpa.gov.cn", "datasearch.nmpa.gov.cn"):
    try:
        infos = socket.getaddrinfo(h, 443, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos})
        print(f"DNS {h:26s} -> {ips}")
    except Exception as e:
        print(f"DNS {h:26s} -> FAIL {type(e).__name__}: {e}")

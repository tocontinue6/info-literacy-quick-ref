# -*- coding: utf-8 -*-
"""Wide byte-scan for the external-link confirmation dialog across DSH install + profile."""
import os

ROOTS = [
    r"C:\Users\Lenovo\AppData\Local\Programs\DSH NEXT",
    r"C:\Users\Lenovo\.dsh",
]
FRAGMENTS = ["即将访问", "访问外部链接", "相关内容与服务", "外部链接，", "由第三方提供",
             "即将离开", "打开第三方", "离开当前"]

SKIP_EXT = {".exe", ".dll", ".node", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
            ".woff", ".woff2", ".ttf", ".otf", ".zip", ".gz", ".7z", ".mp4", ".pdf",
            ".pyc", ".so", ".dylib", ".bin", ".pak", ".asar"}

needles = [(f, f.encode("utf-8")) for f in FRAGMENTS]
needles += [(f, f.encode("utf-16-le")) for f in FRAGMENTS]

hits = []
scanned = 0
skipped = 0
for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("Cache", "Code Cache", "GPUCache")]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_EXT:
                skipped += 1
                continue
            try:
                if os.path.getsize(p) > 120 * 1024 * 1024:
                    skipped += 1
                    continue
                blob = open(p, "rb").read()
            except OSError:
                continue
            scanned += 1
            for frag, b in needles:
                if b in blob:
                    enc = "utf-16" if b[:2] == frag.encode("utf-16-le")[:2] and len(b) != len(frag.encode("utf-8")) else "utf-8"
                    hits.append((frag, p, blob.find(b)))

print(f"scanned={scanned} skipped={skipped}")
print("=== HITS ===")
for frag, p, off in hits:
    print(f"  {frag!r}  @{off}  {p}")
if not hits:
    print("  (none)")

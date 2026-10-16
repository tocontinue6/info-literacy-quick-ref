# -*- coding: utf-8 -*-
"""Byte-level search for a UI string across DSH resources."""
import os, sys

NEEDLES = ["即将访问外部链接", "第三方提供", "相关内容与服务"]
# also a control string that must exist somewhere, to prove the method works
CONTROL = ["DSH", "present"]

ROOTS = [
    r"C:\Users\Lenovo\AppData\Local\Programs\DSH NEXT\resources\app.asar",
    r"C:\Users\Lenovo\AppData\Local\Programs\DSH NEXT\resources\app.asar.unpacked",
]


def variants(s):
    out = []
    for enc in ("utf-8", "utf-16-le", "utf-16-be"):
        try:
            out.append((enc, s.encode(enc)))
        except Exception:
            pass
    return out


def scan_bytes(path, needles):
    hits = []
    try:
        size = os.path.getsize(path)
    except OSError as e:
        return [(n, "STAT-FAIL", str(e)) for n, _ in needles]
    with open(path, "rb") as f:
        chunk = f.read()
    for name, enc, b in needles:
        if b in chunk:
            hits.append((name, enc, chunk.find(b)))
    return hits


def walk(root):
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            yield os.path.join(dirpath, fn)


needles = []
for s in NEEDLES:
    for enc, b in variants(s):
        needles.append((s, enc, b))
control = []
for s in CONTROL:
    for enc, b in variants(s):
        control.append((s, enc, b))

print("=== control strings (must be found) ===")
found_control = False
files = []
for root in ROOTS:
    files.extend(walk(root))
print("files to scan:", len(files))

for f in files:
    if os.path.getsize(f) > 300 * 1024 * 1024:
        print("  skip (too big):", f)
        continue
    try:
        data = open(f, "rb").read()
    except OSError:
        continue
    for name, enc, b in control:
        if b in data:
            print(f"  control {name!r} [{enc}] FOUND in {os.path.basename(f)} @ {data.find(b)}")
            found_control = True
    for name, enc, b in needles:
        if b in data:
            print(f"  *** TARGET {name!r} [{enc}] FOUND in {f} @ {data.find(b)}")

print("\ncontrol method works:", found_control)
print("done")

# -*- coding: utf-8 -*-
"""Locate the dialog string inside app.asar: which bundled file, and what triggers it."""
import json, struct, os, re, sys

ASAR = r"C:\Users\Lenovo\AppData\Local\Programs\DSH NEXT\resources\app.asar"
data = open(ASAR, "rb").read()
print("asar bytes:", len(data))

# --- parse asar header ---
# header: [u32 4][u32 header_size][u32 json_size][u32 json_len][json...]
(_, hdr_size, json_size, json_len) = struct.unpack_from("<4I", data, 0)
header = json.loads(data[16:16 + json_len].decode("utf-8"))
base_offset = 8 + hdr_size
print("header parsed, base offset:", base_offset)

entries = []  # (name, offset_abs, size)


def walk(node, path):
    for name, meta in (node.get("files") or {}).items():
        p = path + "/" + name
        if "files" in meta:
            walk(meta, p)
        else:
            off = meta.get("offset")
            if off is not None:
                entries.append((p, base_offset + int(off), int(meta.get("size", 0))))


walk(header, "")
print("files in asar:", len(entries))
entries.sort(key=lambda e: e[1])

NEEDLES = ["第三方提供", "即将访问外部链接", "相关内容与服务", "外部链接"]
for needle in NEEDLES:
    b = needle.encode("utf-8")
    idx = data.find(b)
    where = []
    while idx != -1 and len(where) < 6:
        # find containing entry
        lo, hi = 0, len(entries) - 1
        hit = None
        for name, off, size in entries:
            if off <= idx < off + size:
                hit = (name, off, size)
                break
        where.append((idx, hit[0] if hit else "?"))
        idx = data.find(b, idx + 1)
    print(f"\nneedle {needle!r}: {len(where)} hit(s) -> {where}")

# --- dump context around the found offset ---
b = "第三方提供".encode("utf-8")
off = data.find(b)
if off != -1:
    ctx = data[off - 1600:off + 600].decode("utf-8", "replace")
    open("out/asar_context.txt", "w", encoding="utf-8").write(ctx)
    print("\ncontext written to out/asar_context.txt")
    print(ctx[-1400:])

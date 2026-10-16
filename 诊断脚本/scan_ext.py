# -*- coding: utf-8 -*-
"""Scan installed browser extensions for the external-link confirmation text."""
import os, json, glob

PROFILES = [
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
    os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles"),
    os.path.expandvars(r"%LOCALAPPDATA%\360Chrome\Chrome\User Data"),
    os.path.expandvars(r"%APPDATA%\Tencent\QQBrowser\User Data"),
]
FRAGMENTS = ["即将访问外部链接", "第三方提供", "访问外部链接", "即将离开", "外部链接"]
EXT_OK = {".js", ".json", ".html", ".css", ".txt", ".md"}

for prof in PROFILES:
    if not os.path.isdir(prof):
        print(f"[skip] not present: {prof}")
        continue
    print(f"\n=== {prof} ===")
    exts = {}
    for pat in ("*/Extensions/*/*/manifest.json", "Extensions/*/manifest.json"):
        for man in glob.glob(os.path.join(prof, pat)):
            exts[os.path.dirname(man)] = man
    # Firefox
    for man in glob.glob(os.path.join(prof, "*", "extensions.json")):
        exts[man] = man
    print(f"  extensions found: {len(exts)}")
    for d in sorted(exts):
        try:
            m = json.load(open(exts[d], encoding="utf-8"))
        except Exception:
            m = {}
        name = m.get("name", "?")
        print(f"   - {name}   ({os.path.basename(d)})")
    # scan extension contents
    hits = 0
    for d in exts:
        root = d if os.path.isdir(d) else os.path.dirname(d)
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if os.path.splitext(fn)[1].lower() not in EXT_OK:
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(p) > 20 * 1024 * 1024:
                        continue
                    blob = open(p, "rb").read()
                except OSError:
                    continue
                for f in FRAGMENTS:
                    if f.encode("utf-8") in blob:
                        print(f"   *** {f!r} in {p}")
                        hits += 1
    print(f"  fragment hits: {hits}")

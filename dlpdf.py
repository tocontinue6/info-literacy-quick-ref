import json, urllib.request, ssl, os, hashlib, urllib.parse, time

CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

d = json.load(open("out/knowledge_raw.json", encoding="utf-8"))
os.makedirs("pdf", exist_ok=True)
log = open("out/pdf_download.log", "w", encoding="utf-8")

# collect every pdf-ish url from anchors AND bare urls
cands = {}
for l in d["links"]:
    u = l["href"]
    if ".pdf" in u.lower().split("?")[0]:
        cands[u] = ("anchor", l["item_title"], l["label"])
for b in d["bare_urls"]:
    u = b["url"]
    if ".pdf" in u.lower().split("?")[0]:
        cands.setdefault(u, ("text", b["item_title"], ""))

for u, (src, title, label) in cands.items():
    base = os.path.basename(urllib.parse.urlparse(u).path)
    base = urllib.parse.unquote(base) or hashlib.md5(u.encode()).hexdigest()[:10]
    for ch in '\\/:*?"<>|':
        base = base.replace(ch, "_")
    if not base.lower().endswith(".pdf"):
        base += ".pdf"
    dest = os.path.join("pdf", base)
    try:
        r = urllib.request.Request(u, headers={"User-Agent": UA, "Referer": "https://csc.xxsuyang.com/"})
        with urllib.request.urlopen(r, timeout=90, context=CTX) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        ok = data[:4] == b"%PDF"
        line = f"OK   status={resp.status} bytes={len(data)} pdf_magic={ok} src={src} item='{title}'\n     url={u}\n     dest={dest}"
        print(line)
        print(line, file=log)
    except Exception as e:
        line = f"FAIL {type(e).__name__}: {e}\n     url={u}\n     item='{title}'"
        print(line)
        print(line, file=log)
    time.sleep(1)
log.close()

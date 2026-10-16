"""Check reachability of every distinct URL referenced by the Knowledge page."""
import os, json, ssl, urllib.request, urllib.error, urllib.parse, collections, sys, re
from concurrent.futures import ThreadPoolExecutor
import url_fixes

CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

d = json.load(open("out/knowledge_raw.json", encoding="utf-8"))
url_fixes.apply_all(d)          # 应用网址勘误（旧地址已被官方迁移）

TRAIL = "）。，、；：！？》】”’…;:,.)\"'"
def clean(u):
    u = urllib.parse.unquote(u) if False else u
    return u.rstrip(TRAIL)

urls = {}
for l in d["links"]:
    u = clean(l["href"])
    urls.setdefault(u, {"sources": [], "labels": set()})
    urls[u]["sources"].append(f"{l['category']} / {l['item_title']}")
    urls[u]["labels"].add(l["label"])
for b in d["bare_urls"]:
    u = clean(b["url"])
    if not u.startswith("http"):
        continue
    urls.setdefault(u, {"sources": [], "labels": set()})
    urls[u]["sources"].append(f"{b['category']} / {b['item_title']} (正文)")

print(f"distinct urls to check: {len(urls)}", file=sys.stderr)


def check(u):
    if u.startswith("file:") or not u.startswith(("http://", "https://")):
        return u, "SKIP/local-or-invalid", ""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(u, method=method, headers={
                "User-Agent": UA, "Accept": "*/*", "Accept-Language": "zh-CN,zh;q=0.9",
                "Referer": "https://csc.xxsuyang.com/"})
            with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
                return u, f"{r.status}", r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if method == "GET":
                return u, f"HTTP {e.code}", ""
            continue
        except Exception as e:
            if method == "GET":
                return u, f"ERR {type(e).__name__}: {str(e)[:90]}", ""
            continue
    return u, "UNKNOWN", ""


CACHE = "out/linkcheck_cache.jsonl"
results = {}
if os.path.exists(CACHE):
    for line in open(CACHE, encoding="utf-8"):
        try:
            o = json.loads(line)
            results[o["url"]] = o
        except Exception:
            pass

todo = [u for u in urls if u not in results]
print(f"cached={len(results)} todo={len(todo)}", file=sys.stderr)
cache_fh = open(CACHE, "a", encoding="utf-8")
with ThreadPoolExecutor(max_workers=12) as ex:
    for i, (u, st, ct) in enumerate(ex.map(check, todo)):
        rec = {"url": u, "status": st, "content_type": ct,
               "meta": {"sources": urls[u]["sources"], "labels": sorted(urls[u]["labels"])}}
        results[u] = rec
        cache_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        cache_fh.flush()
        if (i + 1) % 25 == 0:
            print(f"  checked {i+1}/{len(todo)}", file=sys.stderr)
cache_fh.close()

json.dump(results, open("out/linkcheck.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

buckets = collections.Counter(v["status"].split(":")[0].split(" ")[0] for v in results.values())
print("status buckets:", dict(buckets))

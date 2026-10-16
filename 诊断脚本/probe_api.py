import sys, json, urllib.request, urllib.parse, ssl, itertools

CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
BASE = "https://jsgateway.zhixinst.com"

paths = [
    "/SCC/Website/GetKnowledge",
    "/SCC/Website/GetKnowledgeCategory",
    "/SCC/Website/GetKnowledgeType",
    "/SCC/Website/GetKnowledgeClass",
    "/SCC/Website/GetKnowledgeClassList",
    "/SCC/Website/GetKnowledgeCategoryList",
    "/SCC/Website/GetCategory",
    "/SCC/Website/GetCategoryList",
]
params = [
    {},
    {"kind": "csc2025"},
    {"kind": "csc2025", "type": "1"},
    {"kind": "csc2025", "ismain": "true"},
    {"kind": "csc2025", "pageindex": "1", "pagesize": "100"},
]

def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=25, context=CTX) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except Exception as e:
        return None, f"ERR {type(e).__name__} {e}"

for p in paths:
    for q in params:
        url = BASE + p + ("?" + urllib.parse.urlencode(q) if q else "")
        st, body = get(url)
        if st is None:
            print(f"{st} {url} -> {body[:100]}")
            continue
        try:
            j = json.loads(body)
            d = j.get("data")
            desc = f"list[{len(d)}]" if isinstance(d, list) else repr(d)[:120]
            if isinstance(d, list) and d:
                desc += " keys=" + ",".join(list(d[0].keys())[:12])
        except Exception:
            desc = body[:120]
        print(f"{st} {url}\n     -> {desc}")

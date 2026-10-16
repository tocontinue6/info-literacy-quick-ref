"""Extract all resources from the CSC Knowledge API data."""
import json, re, os, html, collections, urllib.parse

RAW = "raw"
OUT = "out"
os.makedirs(OUT, exist_ok=True)

parents = json.load(open(f"{RAW}/api_parentlist.json", encoding="utf-8"))["data"]
# The list endpoint returns only 50 rows; paginate defensively below.
items = json.load(open(f"{RAW}/probe__kind_csc2025.json", encoding="utf-8"))["data"]

cat_name = {c["id"]: c["name"] for c in parents}
cat_sort = {c["id"]: c["sort"] for c in parents}

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"[ \t\u00a0]+")
NL = re.compile(r"\n{3,}")


def to_text(h):
    if not h:
        return ""
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</(p|div|li|tr|h[1-6]|table|section)>", "\n", h)
    h = re.sub(r"(?i)<li[^>]*>", "  - ", h)
    h = re.sub(r"(?i)<(p|div|tr|h[1-6])[^>]*>", "", h)
    h = TAG.sub("", h)
    h = html.unescape(h)
    h = h.replace("\u200b", "")
    lines = [WS.sub(" ", ln).strip() for ln in h.split("\n")]
    txt = "\n".join(ln for ln in lines)
    return NL.sub("\n\n", txt).strip()


A_HREF = re.compile(r"""(?is)<a\b[^>]*?href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))[^>]*>(.*?)</a>""")
# exclude CJK ideographs, CJK punctuation/fullwidth forms and general punctuation
ANY_URL = re.compile(r"(?i)https?://[^\s\"'<>()\[\]{}\u2000-\u206f\u3000-\u303f"
                     r"\u4e00-\u9fff\uff00-\uffef，、；：！？。]+")
SRC_ATTR = re.compile(r"""(?is)<(?:img|iframe|source|video|embed)\b[^>]*?(?:src|data-src)\s*=\s*(?:"([^"]*)"|'([^']*)')""")

TRAIL = ").,;:!?'\"…。，、；：！？）》】”’"


def clean_url(u):
    u = html.unescape(u or "").strip()
    while u and u[-1] in TRAIL:
        u = u[:-1]
    return u

INTERNAL_HOSTS = {"csc.xxsuyang.com", "xxsuyang.com", "www.xxsuyang.com",
                  "ai.xxsuyang.com", "2024csc.xxsuyang.com"}

links = []          # every <a href> occurrence
bare_urls = []      # plain-text URLs inside content
assets = []         # img/iframe src


def norm(u):
    u = html.unescape(u or "").strip()
    return u


for it in items:
    iid = it["id"]
    cid = it.get("categoryid")
    cname = cat_name.get(cid, "(未分类)")
    title = (it.get("title") or "").strip()
    content = it.get("content") or ""
    text = to_text(content)

    for m in A_HREF.finditer(content):
        href = clean_url(norm(m.group(1) or m.group(2) or m.group(3)))
        if not href or href.lower().startswith(("javascript:", "#", "mailto:")):
            continue
        label = to_text(m.group(4)) or href
        links.append({"item_id": iid, "item_title": title, "category": cname,
                      "href": href, "label": label})

    for m in ANY_URL.finditer(text):
        bare_urls.append({"item_id": iid, "item_title": title, "category": cname,
                          "url": clean_url(m.group(0))})

    for m in SRC_ATTR.finditer(content):
        src = norm(m.group(1) or m.group(2))
        if src and not src.startswith("data:"):
            assets.append({"item_id": iid, "item_title": title, "category": cname, "src": src})

    it["_text"] = text
    it["_category"] = cname
    it["_sort"] = cat_sort.get(cid, 99)

items.sort(key=lambda x: (x["_sort"], x.get("sort") or 0, x["title"]))


def kind_of(u):
    ul = u.lower()
    if ul.startswith("/") or ul.startswith("./") or ul.startswith("../"):
        return "internal-relative"
    if ul.startswith("http"):
        host = urllib.parse.urlparse(ul).netloc.lower()
        if host.endswith("xxsuyang.com"):
            return "internal-site"
        return "external"
    return "other"


# ---- aggregate -------------------------------------------------------------
uniq = {}
for l in links:
    u = l["href"]
    key = (l["item_id"], u)
    uniq.setdefault(key, l)
all_links = list(uniq.values())

pdf_links = [l for l in all_links if ".pdf" in l["href"].lower().split("?")[0]]
ext_links = [l for l in all_links if kind_of(l["href"]) == "external"]
site_links = [l for l in all_links if kind_of(l["href"]) == "internal-site"]
rel_links = [l for l in all_links if kind_of(l["href"]) == "internal-relative"]


def hosts(ls):
    c = collections.Counter()
    for l in ls:
        c[urllib.parse.urlparse(l["href"]).netloc.lower()] += 1
    return c


summary = {
    "categories": len(parents),
    "items": len(items),
    "total_anchor_links": len(all_links),
    "pdf_links": len(pdf_links),
    "external_links": len(ext_links),
    "site_links": len(site_links),
    "relative_links": len(rel_links),
    "bare_urls": len(bare_urls),
    "assets": len(assets),
    "external_hosts": hosts(ext_links).most_common(),
    "pdf_hosts": hosts(pdf_links).most_common(),
}

json.dump({"summary": summary, "categories": parents, "items": items,
           "links": all_links, "pdf_links": pdf_links, "external_links": ext_links,
           "bare_urls": bare_urls, "assets": assets},
          open(f"{OUT}/knowledge_raw.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# console summary in ASCII-safe form
print("== SUMMARY ==")
for k, v in summary.items():
    print(k, "=", v)
print()
print("== CATEGORIES (id | sort) ==")
for c in parents:
    n = sum(1 for i in items if i.get("categoryid") == c["id"])
    print(f"  {c['name']}  sort={c['sort']}  items={n}")
print()
print("== ITEMS (title | category | content_chars) ==")
for i in items:
    print(f"  {i['title']} | {i['_category']} | {len(i['_text'])}")

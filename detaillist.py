import json, collections, urllib.parse, sys
import url_fixes

d = json.load(open("out/knowledge_raw.json", encoding="utf-8"))
url_fixes.apply_all(d)          # 应用网址勘误（旧地址已被官方迁移）
out = open("out/details.txt", "w", encoding="utf-8")
P = lambda *a: print(*a, file=out)

P("=== CATEGORIES ===")
for c in sorted(d["categories"], key=lambda x: x["sort"]):
    n = sum(1 for i in d["items"] if i.get("categoryid") == c["id"])
    P(f"{c['sort']}. {c['name']}  (id={c['id']})  modules={n}")

P("\n=== PDF LINKS ===")
for l in d["pdf_links"]:
    P(f"* [{l['category']}] {l['item_title']}\n    label: {l['label']}\n    url  : {l['href']}")

P("\n=== EXTERNAL LINK HOST TOTALS ===")
h = collections.Counter(urllib.parse.urlparse(l["href"]).netloc.lower() for l in d["external_links"])
for k, v in h.most_common():
    P(f"  {v:3d}  {k}")
P(f"TOTAL external-link rows: {len(d['external_links'])}  distinct URLs: {len({l['href'] for l in d['external_links']})}")

P("\n=== BARE URLS (in visible text) ===")
bu = collections.Counter(b["url"] for b in d["bare_urls"])
for k, v in bu.most_common():
    P(f"  {v:3d}  {k}")
P(f"TOTAL bare url rows: {len(d['bare_urls'])}  distinct: {len(bu)}")

P("\n=== ASSETS ===")
for a in d["assets"]:
    P(f"  [{a['category']}] {a['item_title']}\n    {a['src']}")

P("\n=== ALL ITEMS WITH LINKS ===")
by_item = collections.defaultdict(list)
for l in d["links"]:
    by_item[l["item_id"]].append(l)
for i in d["items"]:
    P(f"\n--- [{i['_category']}] {i['title']}  (id={i['id']})")
    P(f"    createtime={i.get('createtime')}  author={i.get('author')}  type={i.get('type')}")
    for l in by_item.get(i["id"], []):
        P(f"      - {l['label']}  ->  {l['href']}")
out.close()

# also dump plain text of all items
with open("out/items_text.md", "w", encoding="utf-8") as f:
    for i in d["items"]:
        f.write(f"\n\n## [{i['_category']}] {i['title']}\n")
        f.write(f"- id: `{i['id']}`\n- createtime: {i.get('createtime')}\n\n")
        f.write(i["_text"] + "\n")
print("written")

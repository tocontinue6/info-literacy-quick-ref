import json, sys, collections

p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
print("top-level keys:", list(d.keys()))
print("code:", d.get("code"), "msg-ok:", d.get("msg") is not None)
data = d.get("data")
print("data type:", type(data).__name__)
if isinstance(data, list):
    print("len:", len(data))
    if data:
        print("first item keys:", list(data[0].keys()))
        print("first item:", json.dumps(data[0], ensure_ascii=False)[:1200])
        # key frequency
        c = collections.Counter()
        for it in data:
            if isinstance(it, dict):
                c.update(it.keys())
        print("key freq:", dict(c))
        # distinct values for small-cardinality keys
        for k in (c or {}):
            vals = {str(it.get(k))[:80] for it in data if isinstance(it, dict)}
            if len(vals) <= 12:
                print(f"  {k}: {sorted(vals)}")

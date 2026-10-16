# -*- coding: utf-8 -*-
import re, json, sys, os

p = "考点速查手册.html"
s = open(p, encoding="utf-8").read()
m = re.search(r"<script>\n?(.*?)\n?</script>", s, re.S)
js = m.group(1)
os.makedirs("out", exist_ok=True)
open("out/_check.js", "w", encoding="utf-8").write(js)
print("html chars:", len(s), "| script chars:", len(js))

# pull the embedded JSON out and re-parse it as a sanity check
mm = re.search(r"const DATA = (\{.*?\});\nconst MODS", js, re.S)
raw = mm.group(1).replace("<\\/", "</")
d = json.loads(raw)
print("data ok -> modules:", len(d["modules"]), "uses:", len(d["uses"]),
      "platforms:", len(d["platforms"]))
print("modules w/o links:", [m["no"] for m in d["modules"] if not m["links"]])
print("modules w/o req:", [m["no"] for m in d["modules"] if not m["req"]])
print("uses missing modules:",
      [u["id"] for u in d["uses"] if len(u["nos"]) != u["count"]])
print("total links:", sum(len(m["links"]) for m in d["modules"]))
print("supp links:", sum(1 for m in d["modules"] for l in m["links"] if l.get("src") == "supp"))
print("questions:", sum(len(m["questions"]) for m in d["modules"]))
print("questions w/o answer:", sum(1 for m in d["modules"] for q in m["questions"] if not q["answer"]))
print("platforms w/o url:", [p["name"] for p in d["platforms"] if not p.get("url")])
print("external resource refs:", s.count('href="http'))
print("uses list:")
for u in d["uses"]:
    print("  ", u["id"], u["name"], u["count"])

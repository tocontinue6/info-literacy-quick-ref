# -*- coding: utf-8 -*-
"""诊断：为什么模块49的“学习指导及备赛建议”标题泄漏进了具体要求列表。"""
import json, re

SEC = re.compile(r"^☆\s*([^：:]{1,20})[：:]?\s*(.*)$")

raw = json.load(open("out/knowledge_raw.json", encoding="utf-8"))
it = [x for x in raw["items"] if x["title"].endswith("数据可视化工具")][0]
lines = it["_text"].split("\n")

print("module:", it["title"])
for i, ln in enumerate(lines):
    s = ln.strip()
    if "☆" not in s:
        continue
    m = SEC.match(s)
    print(f"line {i:>2}  match={bool(m)}  group1={m.group(1)!r}" if m else f"line {i:>2}  match=False  {s!r}")

print("\n--- 逐行看 8..16 ---")
for i in range(8, min(17, len(lines))):
    print(i, repr(lines[i]))

# 看看实际生成的 req
app = json.load(open("out/app_data.json", encoding="utf-8"))
m49 = [x for x in app["modules"] if x["no"] == 49][0]
print("\n--- app_data 模块49 req ---")
for x in m49["req"]:
    print("  ", repr(x))

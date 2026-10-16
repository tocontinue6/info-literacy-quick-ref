# -*- coding: utf-8 -*-
"""统计各模块使用的“学习指导”小节标题写法，确认解析器漏配的范围。"""
import json, re, collections

SEC = re.compile(r"^☆\s*([^：:]{1,20})[：:]?\s*(.*)$")
raw = json.load(open("out/knowledge_raw.json", encoding="utf-8"))

variants = collections.Counter()
affected = []
for it in raw["items"]:
    heads = []
    for ln in it["_text"].split("\n"):
        s = ln.strip()
        m = SEC.match(s)
        if m and m.group(1).startswith("学习指导"):
            heads.append(m.group(1))
    for h in heads:
        variants[h] += 1
    if any("与" in h for h in heads):
        affected.append((it["title"], heads))

print("=== “学习指导”标题的写法分布 ===")
for k, v in variants.most_common():
    print(f"  {k}  ×{v}")

print(f"\n=== 使用“与”写法（解析器漏配）的模块：{len(affected)} 个 ===")
for t, h in affected:
    print("  ", t, h)

# 这些模块的“具体要求”是否因此被污染
app = json.load(open("out/app_data.json", encoding="utf-8"))
bad = []
for m in app["modules"]:
    if any(x.startswith("☆") for x in m["req"] + m["explore"]):
        bad.append(m["no"])
print("\n=== app_data 中“学习要点/实践任务”里残留 ☆ 标题行的模块 ===")
print("  ", bad if bad else "无")

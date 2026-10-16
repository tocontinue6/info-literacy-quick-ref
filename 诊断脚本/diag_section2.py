# -*- coding: utf-8 -*-
"""精确诊断：打印 split_sections 的分段结果与关键字符的码点。"""
import json, re, importlib.util, sys

SEC = re.compile(r"^☆\s*([^：:]{1,20})[：:]?\s*(.*)$")

raw = json.load(open("out/knowledge_raw.json", encoding="utf-8"))
it = [x for x in raw["items"] if x["title"].endswith("数据可视化工具")][0]
text = it["_text"]

# 复刻 build_data.split_sections
def split_sections(text):
    out, cur, buf = [], None, []
    for ln in text.split("\n"):
        s = ln.strip()
        m = SEC.match(s)
        if m and (m.group(1) in ("具体要求", "学习指导及备赛建议", "参考资源")
                  or m.group(1).startswith("样题")):
            if cur is not None:
                out.append((cur, buf))
            cur = m.group(1) + (("：" + m.group(2)) if m.group(2).strip() else "")
            buf = []
        else:
            if cur is None:
                if s:
                    cur, buf = "(前言)", [ln]
            else:
                buf.append(ln)
    if cur is not None:
        out.append((cur, buf))
    return out

print("=== split_sections 结果 ===")
for title, body in split_sections(text):
    print(f"  小节 {title!r}  行数={len(body)}")

print("\n=== 目标字符串码点比对 ===")
target_in_code = "学习指导及备赛建议"          # build_data.py 里的字面量
line12 = [l.strip() for l in text.split("\n") if l.strip().startswith("☆")][1]
m = SEC.match(line12)
got = m.group(1)
print("  字面量      :", [hex(ord(c)) for c in target_in_code])
print("  实际 group1 :", [hex(ord(c)) for c in got])
print("  相等?       :", got == target_in_code)
print("  长度        :", len(target_in_code), len(got))

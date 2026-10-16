# -*- coding: utf-8 -*-
"""成品自检：离线性、无 window.open 可执行调用、数据完整性。"""
import re, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
p = os.path.join(ROOT, "信息素养与科研工具速查手册.html")
s = open(p, encoding="utf-8").read()

ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', s)
print("外部资源引用 (src/href):", len(ext), ext[:3] if ext else "")

# strip HTML comments, then JS block comments, then // line comments
no_html = re.sub(r"<!--[\s\S]*?-->", "", s)
no_block = re.sub(r"/\*[\s\S]*?\*/", "", no_html)
no_line = re.sub(r"^\s*//.*$", "", no_block, flags=re.M)
calls = re.findall(r"window\.open\s*\(", no_line)
print("window.open 可执行调用:", len(calls), calls[:3] if calls else "")
print("文件大小: %.1f KB" % (len(s.encode("utf-8")) / 1024))

# embedded data integrity
m = re.search(r"const DATA = (\{.*?\});\nconst MODS", s, re.S)
d = json.loads(m.group(1).replace("<\\/", "</"))
print("数据: %d 模块 / %d 用途 / %d 平台 / %d 样题"
      % (len(d["modules"]), len(d["uses"]), len(d["platforms"]),
         sum(len(x["questions"]) for x in d["modules"])))
print("每模块都有链接:", all(x["links"] for x in d["modules"]))
print("每模块都有考点:", all(x["req"] for x in d["modules"]))

for token in ["打开方式：", "id=\"btn-mode\"", "id=\"toast\"", "openerAnchor", "location.assign"]:
    print(f"  含 {token!r}:", token in s)

# -*- coding: utf-8 -*-
"""Make temp copies of the built manual with a panel/module open, for screenshots."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
latest = "信息素养与科研工具速查手册.html"
print("target:", latest)

s = open(os.path.join(ROOT, latest), encoding="utf-8").read()
anchor = "selectMod(S.sel, true);"
assert anchor in s

open(os.path.join(HERE, "_shot_module14.html"), "w", encoding="utf-8").write(
    s.replace(anchor, "selectMod(14, true);"))
open(os.path.join(HERE, "_shot_toast.html"), "w", encoding="utf-8").write(
    s.replace(anchor, anchor + "\ntoast('已在新标签页打开：https://www.cnki.net/','https://www.cnki.net/');"
                              "\nclearTimeout(_toastT);"))
open(os.path.join(HERE, "_shot_plat.html"), "w", encoding="utf-8").write(
    s.replace(anchor, anchor + "\ndocument.getElementById('mask-plat').classList.add('on');"
                              "\ndocument.getElementById('platq').value='药品';\nrenderPlats();"))
print("prepared shot files")

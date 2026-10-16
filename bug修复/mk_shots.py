# -*- coding: utf-8 -*-
"""Make temporary copies that boot with a panel already open (for screenshots)."""
s = open("考点速查手册.html", encoding="utf-8").read()
anchor = "selectMod(S.sel, true);"
assert anchor in s, "anchor not found"

open("out/_plat.html", "w", encoding="utf-8").write(
    s.replace(anchor, anchor + "\ndocument.getElementById('mask-plat').classList.add('on'); renderPlats();"))
open("out/_help.html", "w", encoding="utf-8").write(
    s.replace(anchor, anchor + "\ndocument.getElementById('mask-help').classList.add('on');"))
open("out/_search.html", "w", encoding="utf-8").write(
    s.replace(anchor, anchor + "\nsearch('cnki'); renderResults();"))
print("prepared _plat.html / _help.html / _search.html")

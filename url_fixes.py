# -*- coding: utf-8 -*-
"""网址勘误表 —— 官方页面上的旧地址已被站点自身改版/迁移。

为什么单独放一个文件：
    这些地址出现在**抓取到的原始内容**里（`out/knowledge_raw.json`）。
    如果只在生成好的 HTML / Markdown 里改，下次重新生成就会被覆盖回去。
    因此所有下游脚本（build_data / report / linkcheck）在读取原始数据后
    统一调用 `apply_all()`，保证每次重新生成都带上勘误。

新增勘误请只改 `URL_FIXES`，并在 `REASONS` 里写清依据与核实日期。
"""

# 旧地址 -> 新地址
URL_FIXES = {
    "https://www.nmpa.gov.cn/datasearch/home-index.html":
        "https://datasearch.nmpa.gov.cn/datasearch/home-index.html",
}

# 勘误依据（便于日后复核，不会输出到成品）
REASONS = {
    "https://www.nmpa.gov.cn/datasearch/home-index.html": {
        "date": "2026-10-16",
        "source": "用户反馈 + 实测验证",
        "evidence": (
            "实测旧地址返回 HTTP 412，但被服务端 302 到 "
            "https://datasearch.nmpa.gov.cn/datasearch/url_change.html"
            "（即官方自己的“网址已变更”提示页）；新域名 datasearch.nmpa.gov.cn "
            "解析正常（39.96.250.10）并正常响应。"
        ),
    },
}

# 平台名（新域名不在原 KNOWN 表里，需补一个显示名）
HOST_NAMES = {
    "datasearch.nmpa.gov.cn": "国家药品监督管理局数据查询",
}


def fix_url(u):
    """修正单个网址（含带参数/末尾标点的情形）。"""
    if not u:
        return u
    return URL_FIXES.get(u, URL_FIXES.get(u.strip(), u))


def fix_text(s):
    """修正任意文本中出现的旧网址（正文里是以纯文本形式内嵌的）。"""
    if not s:
        return s
    for old, new in URL_FIXES.items():
        if old in s:
            s = s.replace(old, new)
    return s


def apply_all(d):
    """就地把 knowledge_raw.json 载入的字典里的旧网址全部替换掉。"""
    if not d:
        return d
    for it in d.get("items", []):
        for k in ("content", "_text"):
            if it.get(k):
                it[k] = fix_text(it[k])
    for l in d.get("links", []):
        if l.get("href"):
            l["href"] = fix_url(l["href"])
        if l.get("label"):
            l["label"] = fix_text(l["label"])
    for b in d.get("bare_urls", []):
        if b.get("url"):
            b["url"] = fix_url(b["url"])
    return d


def summary():
    lines = []
    for old, new in URL_FIXES.items():
        r = REASONS.get(old, {})
        lines.append(f"  {old}\n    -> {new}\n    [{r.get('date','?')}] {r.get('source','')}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(f"勘误条数: {len(URL_FIXES)}")
    print(summary())

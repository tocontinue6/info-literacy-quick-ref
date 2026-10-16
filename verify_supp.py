# -*- coding: utf-8 -*-
"""Verify candidate supplementary platform URLs before including them."""
import json, ssl, urllib.request, urllib.error, sys
from concurrent.futures import ThreadPoolExecutor

CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

CAND = [
    # 常见 AI 工具（页面多处以文字提到但未给链接）
    ("DeepSeek", "https://www.deepseek.com/"),
    ("Kimi（月之暗面）", "https://kimi.moonshot.cn/"),
    ("智谱清言", "https://chatglm.cn/"),
    ("文心一言", "https://yiyan.baidu.com/"),
    ("讯飞星火", "https://xinghuo.xfyun.cn/"),
    ("纳米AI", "https://www.n.cn/"),
    ("秘塔AI搜索", "https://metaso.cn/"),
    ("AMiner", "https://www.aminer.cn/"),
    ("腾讯元宝", "https://yuanbao.tencent.com/"),
    ("豆包", "https://www.doubao.com/chat/"),
    ("通义千问", "https://www.qianwen.com/"),
    # 数据 / 统计
    ("国家统计局", "https://www.stats.gov.cn/"),
    ("中国统计年鉴", "https://www.stats.gov.cn/sj/ndsj/"),
    ("中国经济社会大数据研究平台", "https://data.cnki.net/"),
    ("EPS 数据平台", "https://www.epsnet.com.cn/"),
    # 图书馆 / 馆藏
    ("四川大学图书馆", "https://lib.scu.edu.cn/"),
    ("国家图书馆联机公共目录", "http://opac.nlc.cn/"),
    ("读秀学术搜索", "https://www.duxiu.com/"),
    ("超星发现", "https://www.chaoxing.com/"),
    # 截屏录屏 / 办公
    ("LICEcap（GIF 录屏）", "https://www.cockos.com/licecap/"),
    ("Snipaste（截图贴图）", "https://zh.snipaste.com/"),
    ("WPS Office", "https://www.wps.cn/"),
    ("石墨文档", "https://shimo.im/"),
    ("ProcessOn（在线思维导图）", "https://www.processon.com/"),
    ("XMind", "https://xmind.cn/"),
    ("幕布", "https://mubu.com/"),
    # 数据处理与可视化
    ("微词云", "https://www.weiciyun.com/"),
    ("Apache ECharts", "https://echarts.apache.org/zh/index.html"),
    ("Tableau Public", "https://public.tableau.com/"),
    ("镝数图表", "https://dycharts.com/"),
    ("花火 Hanabi", "https://hanabi.cn/"),
    # 文献管理
    ("Mendeley", "https://www.mendeley.com/"),
    ("Zotero", "https://www.zotero.org/"),
    ("EndNote", "https://endnote.com/"),
    ("NoteExpress", "https://www.inoteexpress.com/"),
    # 检索 / 学术
    ("百度学术", "https://xueshu.baidu.com/"),
    ("谷歌学术", "https://scholar.google.com/"),
    ("中国大学MOOC", "https://www.icourse163.org/"),
    ("国家哲学社会科学文献中心", "https://www.ncpssd.cn/"),
    ("国家科技图书文献中心", "https://www.nstl.gov.cn/"),
    ("Sci-Hub", "https://sci-hub.se/"),
]


def check(item):
    name, u = item
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(u, method=method, headers={
                "User-Agent": UA, "Accept": "*/*", "Accept-Language": "zh-CN,zh;q=0.9"})
            with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
                return name, u, r.status, r.geturl()
        except urllib.error.HTTPError as e:
            if method == "GET":
                return name, u, f"HTTP {e.code}", ""
        except Exception as e:
            if method == "GET":
                return name, u, f"ERR {type(e).__name__}", ""
    return name, u, "?", ""


ok, bad = [], []
with ThreadPoolExecutor(max_workers=10) as ex:
    for name, u, st, final in ex.map(check, CAND):
        line = f"{st}\t{name}\t{u}" + (f"\t-> {final}" if final and final.rstrip('/') != u.rstrip('/') else "")
        print(line)
        (ok if st == 200 else bad).append((name, u, st))

json.dump({"ok": ok, "bad": bad}, open("out/supp_verify.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\nOK={len(ok)} BAD={len(bad)}")

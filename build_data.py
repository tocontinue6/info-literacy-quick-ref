# -*- coding: utf-8 -*-
"""Build the structured dataset for the exam-day quick-reference app."""
import json, re, os, html, collections, urllib.parse
import url_fixes

RAW = "out/knowledge_raw.json"
LC = "out/linkcheck.json"
OUT = "out/app_data.json"

d = json.load(open(RAW, encoding="utf-8"))
url_fixes.apply_all(d)          # 应用网址勘误（旧地址已被官方迁移）
lc = json.load(open(LC, encoding="utf-8"))
items = d["items"]
TRAIL = ").,;:!?'\"…。，、；：！？）》】”’"


def clean(u):
    return (u or "").strip().rstrip(TRAIL)


def host(u):
    return urllib.parse.urlparse(u).netloc.lower()


# ---------------------------------------------------------------- 用途分类
# 按“你打算做什么”划分，而不是按学科领域。
USES = [
    ("U1", "AI 工具实操", "打开某个 AI 产品，查找功能、生成内容或完成操作",
     [2, 3, 4, 5, 6, 7]),
    ("U2", "AI 政策法规与伦理", "查阅 AI 相关法律法规、规范性文件的名称、条款与适用范围",
     [1]),
    ("U3", "法律法规 · 标准 · 知识产权", "查阅法律条文、判例、国家标准、商标、专利、地理标志",
     [10, 11, 12, 13]),
    ("U4", "政府公开信息与事实核查", "查阅统计数据、年鉴、开放数据、医卫／文教／证书资质等事实性信息",
     [8, 9, 14, 15, 16]),
    ("U5", "学术文献检索", "在各类学术数据库中检索期刊、会议、学位论文并获取全文",
     [21, 22, 23, 24, 25]),
    ("U6", "检索系统与搜索工具", "使用学术搜索、图片搜索、网址导航、网络指数、馆藏系统",
     [26, 27, 28, 29, 30]),
    ("U7", "检索语法与策略", "布尔逻辑、截词、字段限定、精确／模糊匹配、结果筛选等检索技术",
     [31, 32, 33, 34, 35, 36, 37]),
    ("U8", "图书 · 课程 · 学习资源", "查找电子书、开放课程、慕课、国家图书馆数字资源",
     [17, 18, 19, 20]),
    ("U9", "文献管理 · 写作 · 排版", "文献管理软件、参考文献著录、投稿选刊、学术伦理、论文排版",
     [42, 43, 44, 45, 46, 47]),
    ("U10", "通用工具与知识管理", "思维导图、笔记、插件、截图录屏、PDF、数据处理与可视化",
     [38, 39, 40, 41, 48, 49, 50]),
]

mod_no = {}          # module id -> 序号 1..50
use_of = {}          # module id -> use id
for uid, uname, udesc, nos in USES:
    for n in nos:
        use_of[n] = uid

# ---------------------------------------------------------------- 解析工具
SEC = re.compile(r"^☆\s*([^：:]{1,20})[：:]?\s*(.*)$")
QTYPE = re.compile(r"样题\s*\d*\s*[（(]([^）)]*)[）)]?")


def split_sections(text):
    out, cur, buf = [], None, []
    for ln in text.split("\n"):
        s = ln.strip()
        m = SEC.match(s)
        # 注意：原始页面里这一节有两种写法——“学习指导及备赛建议”与“学习指导与备赛建议”，
        # 模块49 用的是“与”。这里按前缀匹配，避免漏配导致该节内容并进上一节。
        if m and (m.group(1) in ("具体要求", "参考资源")
                  or m.group(1).startswith(("学习指导", "样题"))):
            if cur is not None:
                out.append((cur, buf))
            cur = m.group(1) + (("：" + m.group(2)) if m.group(2).strip() else "")
            buf = []
        else:
            if cur is None:
                if s:
                    cur, buf = "(前言)", [ln]
            elif s:
                # 防御：任何漏网的小节标题行都不要混进正文
                if not s.startswith("☆"):
                    buf.append(ln)
    if cur is not None:
        out.append((cur, buf))
    return out


def take_options(s, q):
    marks = [mm.start() for mm in re.finditer(r"(?:^|\s)([A-DＡ-Ｄ])\s*[、.．]\s*", s)]
    if not marks:
        return False
    if len(marks) == 1:
        mm = re.match(r"^\s*([A-DＡ-Ｄ])\s*[、.．]\s*(.*)$", s)
        if mm:
            q["options"].append([mm.group(1), mm.group(2).strip()])
            return True
        return False
    marks.append(len(s))
    for a, b in zip(marks, marks[1:]):
        mm = re.match(r"^([A-DＡ-Ｄ])\s*[、.．]\s*(.*)$", s[a:b].strip())
        if mm:
            q["options"].append([mm.group(1), mm.group(2).strip()])
    return True


def parse_question(title, body):
    q = {"type": "", "stem": [], "options": [], "answer": "", "explain": []}
    m = QTYPE.search(title)
    if m:
        q["type"] = m.group(1)
    mode = "stem"
    for ln in body:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("答案解析"):
            mode = "explain"
            q["explain"].append(re.sub(r"^答案解析\s*[：:]\s*", "", s).strip())
            continue
        if s.startswith("参考答案") or s.startswith("正确答案"):
            mode = "answer"
            q["answer"] = re.sub(r"^(参考答案|正确答案)\s*[：:]\s*", "", s).strip()
            continue
        if mode in ("stem", "options") and take_options(s, q):
            mode = "options"
            continue
        (q["stem"] if mode == "stem" else q["explain"]).append(s)
    q["stem"] = " ".join(q["stem"]).strip()
    q["explain"] = " ".join(q["explain"]).strip()
    return q


# ---------------------------------------------------------------- 链接与平台
LOGIN_HOSTS = {
    "www.cnki.net", "cnki.net", "ai.cnki.net", "chkd.cnki.net", "k.cnki.net", "x.cnki.net",
    "navi.cnki.net", "conf.cnki.net", "lawpro.cnki.net", "image.cnki.net",
    "www.wanfangdata.com.cn", "video.wanfangdata.com.cn", "cx.wanfangdata.com.cn",
    "www.cqvip.com", "www.sciencedirect.com", "eci.elsevier.cn",
    "onlinelibrary.wiley.com", "www.tandfonline.com", "dl.acm.org", "ieeexplore.ieee.org",
    "www.jstor.org", "bioone.org", "www.spiedigitallibrary.org", "iopscience.iop.org",
    "asmedigitalcollection.asme.org",
}
MIXED_HOSTS = {"www.cambridge.org", "academic.oup.com", "www.nature.com", "www.cell.com",
               "www.science.org", "www.ieee.org"}


def access_note(u):
    h = host(u)
    if h in LOGIN_HOSTS or h.endswith(("cnki.net", "wanfangdata.com.cn", "cqvip.com")):
        return "login"
    if h in MIXED_HOSTS:
        return "mixed"
    if h.endswith((".gov.cn", ".edu.cn", ".org.cn")):
        return "gov"
    return "open"


by_item = collections.defaultdict(list)
for l in d["links"]:
    by_item[l["item_id"]].append(l)

modules = []
platform_map = collections.OrderedDict()

def reg_platform(u, label, title):
    """Register a URL in the platform index. Non-HTTP (e.g. file:///) links are ignored."""
    if not u.startswith(("http://", "https://")):
        return
    h = host(u)
    if not h:
        return
    p = platform_map.setdefault(h, {"host": h, "names": collections.Counter(),
                                    "urls": collections.OrderedDict(), "mods": []})
    if label and not label.startswith("http") and "." not in label[:40]:
        p["names"][label] += 2
    p["urls"][u] = p["urls"].get(u, 0) + 1
    if title not in p["mods"]:
        p["mods"].append(title)


for idx, it in enumerate(items, 1):
    mod_no[it["id"]] = idx
    text = it["_text"]
    secs = split_sections(text)
    req, guide, questions = [], [], []
    for title, body in secs:
        if title.startswith("具体要求"):
            req = [l.strip() for l in body if l.strip()]
        elif title.startswith("学习指导"):
            guide = [l.strip() for l in body if l.strip()]
        elif title.startswith("样题"):
            questions.append(parse_question(title, body))

    seen, explore = set(), []
    for l in guide + req:
        if "探索" in l and l not in seen:
            seen.add(l)
            explore.append(l)

    # links: anchor links first (they carry labels), then bare urls not already present
    links, seenu = [], set()
    for l in by_item.get(it["id"], []):
        u = clean(l["href"])
        if u in seenu:
            continue
        seenu.add(u)
        label = (l["label"] or "").strip()
        links.append({"u": u, "label": label, "host": host(u), "access": access_note(u)})
        reg_platform(u, label, it["title"])

    for b in d["bare_urls"]:
        if b["item_id"] != it["id"]:
            continue
        u = clean(b["url"])
        if u in seenu or not u.startswith("http"):
            continue
        seenu.add(u)
        links.append({"u": u, "label": "", "host": host(u), "access": access_note(u)})
        reg_platform(u, "", it["title"])

    # 学习要点关键词：从官方要求里抽出的重点对象（平台名、文件名、术语）
    kw = set()
    for s in req + explore:
        for m in re.finditer(r"《([^》]{2,40})》", s):
            kw.add(m.group(1))
        for m in re.finditer(r"[A-Za-z][A-Za-z0-9&\.\-]{2,30}", s):
            kw.add(m.group(0))
    kws = sorted(kw, key=lambda x: (-len(x), x))[:18]

    modules.append({
        "no": idx,
        "id": it["id"],
        "title": it["title"],
        "use": use_of.get(idx, "U10"),
        "legacy": it["_category"],
        "detail": f"https://csc.xxsuyang.com/detail?id={it['id']}",
        "req": req,
        "explore": explore,
        "questions": questions,
        "links": links,
        "kw": kws,
    })

# ---------------------------------------------------------------- 平台速查
KNOWN = {
    "www.cnki.net": "中国知网 CNKI", "k.cnki.net": "CNKI 在线教学平台",
    "ai.cnki.net": "CNKI AI 学术研究助手", "chkd.cnki.net": "中国医院知识总库 CHKD",
    "x.cnki.net": "知网研学", "navi.cnki.net": "CNKI 期刊导航",
    "conf.cnki.net": "CNKI 中国学术会议网", "lawpro.cnki.net": "中国法律知识资源总库",
    "image.cnki.net": "CNKI 学术图片库", "publishmedia.cbpt.cnki.net": "CNKI 出版平台",
    "www.wanfangdata.com.cn": "万方数据知识服务平台", "video.wanfangdata.com.cn": "万方视频",
    "cx.wanfangdata.com.cn": "万方创新助手", "www.cqvip.com": "维普期刊资源整合服务平台",
    "www.sciencedirect.com": "ScienceDirect（爱思唯尔）", "eci.elsevier.cn": "爱思唯尔 LeapSpace",
    "onlinelibrary.wiley.com": "Wiley Online Library", "www.tandfonline.com": "Taylor & Francis",
    "dl.acm.org": "ACM Digital Library", "ieeexplore.ieee.org": "IEEE Xplore",
    "www.jstor.org": "JSTOR", "bioone.org": "BioOne",
    "www.spiedigitallibrary.org": "SPIE Digital Library", "iopscience.iop.org": "IOPscience",
    "asmedigitalcollection.asme.org": "ASME Digital Collection",
    "www.cambridge.org": "Cambridge Core", "academic.oup.com": "Oxford Academic",
    "www.nature.com": "Nature", "www.cell.com": "Cell Press", "www.science.org": "Science",
    "www.ncbi.nlm.nih.gov": "NCBI（PubMed/Bookshelf）", "pubmed.ncbi.nlm.nih.gov": "PubMed",
    "pubmed.gov": "PubMed", "arxiv.org": "arXiv", "www.chinaxiv.org": "中国预印本平台 ChinaXiv",
    "www.medrxiv.org": "medRxiv", "doaj.org": "DOAJ 开放获取期刊目录",
    "www.oalib.com": "OA 图书馆", "dspace.mit.edu": "MIT DSpace（学位论文）",
    "suyang.zxhnzq.com": "高校信息素养教育数据库",
    "www.go.cn": "", "www.gov.cn": "中国政府网", "www.cac.gov.cn": "国家互联网信息办公室",
    "www.cas.cn": "中国科学院", "www.sjtu.edu.cn": "上海交通大学",
    "research.bjmu.edu.cn": "北京大学医学部科研处", "aisg.tongji.edu.cn": "同济大学 AI 安全治理",
    "unesdoc.unesco.org": "UNESCO 数字图书馆", "flk.npc.gov.cn": "国家法律法规数据库",
    "xzfg.moj.gov.cn": "司法部行政法规库", "www.moj.gov.cn": "司法部",
    "rmfyalk.court.gov.cn": "人民法院案例库", "gongbao.court.gov.cn": "最高人民法院公报",
    "zxgk.court.gov.cn": "中国执行信息公开网", "tingshen.court.gov.cn": "中国庭审公开网",
    "wenshu.court.gov.cn": "中国裁判文书网",
    "openstd.samr.gov.cn": "国家标准全文公开系统", "std.samr.gov.cn": "全国标准信息公共服务平台",
    "sppt.cfsa.net.cn:8086": "食品安全国家标准数据库", "gb2760.cfsa.net.cn": "GB 2760 食品添加剂查询",
    "sppt.cfsa.net.cn:8087": "食品安全国家标准数据库（新版）",
    "www.mee.gov.cn": "生态环境部", "www.mohurd.gov.cn": "住房和城乡建设部",
    "sbj.cnipa.gov.cn": "国家知识产权局商标局", "epub.cnipa.gov.cn": "中国专利公布公告",
    "pss-system.cponline.cnipa.gov.cn": "专利检索及分析系统", "www.uspto.gov": "USPTO 美国专利商标局",
    "ie.espacenet.com": "Espacenet 全球专利库", "patentscope2.wipo.int": "WIPO PATENTSCOPE",
    "www.cnipa.gov.cn": "国家知识产权局", "ggfw.cnipa.gov.cn": "地理标志产品查询",
    "www.piyao.org.cn": "中国互联网联合辟谣平台", "www.nhc.gov.cn": "国家卫生健康委员会",
    "datasearch.nmpa.gov.cn": "国家药品监督管理局数据查询",
    "www.nmpa.gov.cn": "国家药品监督管理局", "www.neea.edu.cn": "中国教育考试网",
    "yz.chsi.com.cn": "中国研究生招生信息网（研招网）", "www.chsi.com.cn": "中国高等教育学生信息网（学信网）",
    "www.ncss.cn": "国家大学生就业服务平台", "gj.ncss.cn": "高校毕业生到国际组织实习任职信息平台",
    "cy.ncss.cn": "全国大学生创业服务网", "gs.sac.net.cn": "中国证券业协会",
    "www.amac.org.cn": "中国证券投资基金业协会", "www.china-cba.net": "中国银行业协会",
    "cmis.cicpa.org.cn": "中国注册会计师协会", "credit.acla.org.cn": "全国律师执业诚信信息公示平台",
    "press.nppa.gov.cn": "国家新闻出版署", "www.nppa.gov.cn": "国家新闻出版署",
    "www.icourse163.org": "中国大学 MOOC", "www.xuetangx.com": "学堂在线",
    "www.zhihuishu.com": "智慧树", "www.xueyinonline.com": "学银在线",
    "higher.smartedu.cn": "国家高等教育智慧教育平台", "vocational.smartedu.cn": "国家职业教育智慧教育平台",
    "lifelong.smartedu.cn": "国家终身教育智慧教育平台", "basic.smartedu.cn": "国家中小学智慧教育平台",
    "www.ilab-x.com": "iLAB-X 虚拟仿真实验平台", "www.icourses.cn": "爱课程",
    "open.163.com": "网易公开课", "www.xuexi.cn": "学习强国", "www.yixi.tv": "一席",
    "www.ted.com": "TED", "www.xiaohongshu.com": "小红书", "www.bilibili.com": "哔哩哔哩",
    "www.zhihu.com": "知乎", "zhida.zhihu.com": "知乎直答",
    "www.nlc.cn": "中国国家图书馆", "read.nlc.cn": "国家图书馆·中华古籍资源库",
    "www.loc.gov": "美国国会图书馆", "www.modernhistory.org.cn": "抗日战争与近代中日关系文献数据平台",
    "www.ncpssd.cn": "国家哲学社会科学文献中心", "fz.people.com.cn": "国家社科基金项目数据库",
    "kd.nsfc.cn": "国家自然科学基金大数据知识管理服务门户",
    "xueshu.baidu.com": "百度学术", "pubscholar.cn": "PubScholar 公益学术平台",
    "www.nstl.gov.cn": "国家科技图书文献中心 NSTL",
    "www.iconfont.cn": "Iconfont", "unsplash.com": "Unsplash", "pixabay.com": "Pixabay",
    "scidraw.io": "SciDraw", "smart.servier.com": "Servier Medical Art",
    "image.baidu.com": "百度图片", "pic.sogou.com": "搜狗图片", "image.so.com": "360 图片",
    "hao.uisdc.com": "优设导航", "www.hippter.com": "HiPPTER",
    "www.wenxianxue.cn": "文献学", "ai-bot.cn": "AI 工具集", "index.baidu.com": "百度指数",
    "trendinsight.oceanengine.com": "抖音指数（巨量算数）", "www.baidu.com": "百度",
    "docs.qq.com": "腾讯文档", "www.wps.cn": "WPS", "note.youdao.com": "有道云笔记",
    "www.qianwen.com": "通义千问", "www.wjx.cn": "问卷星", "gw.xkonglong.com": "小恐龙公文排版助手",
    "www.yuketang.cn": "雨课堂", "www.office-ai.cn": "OfficeAI 助手", "www.yunzhan365.com": "云展网",
    "echarts.apache.org": "Apache ECharts", "www.weiciyun.com": "微词云",
    "www.citexs.com": "Citexs 赛特新思", "www.doubao.com": "豆包",
    "yuanbao.tencent.com": "腾讯元宝", "paper.iflytek.com": "星火科研助手",
    "developer.aliyun.com": "阿里云开发者社区", "www.aidaxue.com": "科大讯飞 AI 大学堂",
    "ascend.developer.huaweicloud.com": "华为昇腾 AI 专区", "zh.d2l.ai": "动手学深度学习",
    "www.elementsofai.com": "Elements of AI", "www.lib.szu.edu.cn": "深圳大学图书馆",
    "github.com": "GitHub", "docs.github.com": "GitHub 文档", "modelscope.cn": "魔搭 ModelScope",
    "aistudio.baidu.com": "百度 AI Studio 飞桨星河社区", "www.heywhale.com": "和鲸社区 HeyWhale",
    "tianchi.aliyun.com": "阿里云天池", "www.datafountain.cn": "DataFountain",
    "opendatalab.com": "OpenDataLab", "www.openml.org": "OpenML",
    "archive.ics.uci.edu": "UCI 机器学习库", "archive-beta.ics.uci.edu": "UCI 机器学习库（新版）",
    "data.stats.gov.cn": "国家统计局数据查询", "www.escience.org.cn": "中国科技资源共享网",
    "www.scidb.cn": "科学数据银行 ScienceDB", "data.worldbank.org": "世界银行开放数据",
    "mp.weixin.qq.com": "微信公众号文章", "jhsjk.people.cn": "习近平系列重要讲话数据库",
    "www.12371.cn": "共产党员网", "xhsz.news.cn": "新华社思政资源",
    "www.cell.com": "Cell Press", "www.sciencedirect.com": "ScienceDirect",
}

platforms = []
for h, p in platform_map.items():
    name = KNOWN.get(h) or (p["names"].most_common(1)[0][0] if p["names"] else h)
    best = max(p["urls"].items(), key=lambda kv: (".pdf" not in kv[0].lower(), kv[1]))[0]
    platforms.append({
        "host": h, "name": name, "url": best,
        "urls": list(p["urls"].keys()),
        "mods": p["mods"][:8],
        "access": access_note(best),
        "src": "page",
    })

# ---------------------------------------------------------------- 补充平台
# 页面文字提到、但没有给出可点链接的平台。每一项都经过 HTTP 可达性实测
# （见 out/supp_verify.json）；403/不可达者已剔除，最终地址取实测跳转后的地址。
SUPP = {
    "DeepSeek": "https://www.deepseek.com/",
    "Kimi（月之暗面）": "https://www.kimi.com/",
    "智谱清言": "https://chatglm.cn/",
    "文心一言": "https://wenxin.baidu.com/?enter_type=yiyan_site",
    "讯飞星火": "https://xinghuo.xfyun.cn/",
    "纳米AI": "https://www.n.cn/",
    "秘塔AI搜索": "https://metaso.cn/",
    "AMiner": "https://www.aminer.cn/",
    "国家统计局": "https://www.stats.gov.cn/",
    "中国统计年鉴": "https://www.stats.gov.cn/sj/ndsj/",
    "中国经济社会大数据研究平台（CNKI）": "https://data.cnki.net/",
    "EPS数据平台": "https://www.epsnet.com.cn/index.html",
    "四川大学图书馆": "https://lib.scu.edu.cn/",
    "国家图书馆联机公共目录": "http://opac.nlc.cn/",
    "读秀学术搜索": "https://www.duxiu.com/",
    "超星发现": "https://www.chaoxing.com/",
    "LICEcap（GIF 录屏）": "https://www.cockos.com/licecap/",
    "Snipaste（截图 / 贴图）": "https://zh.snipaste.com/",
    "WPS Office": "https://www.wps.cn/",
    "石墨文档": "https://shimo.im/",
    "ProcessOn（在线思维导图）": "https://www.processon.com/",
    "XMind": "https://xmind.cn/",
    "幕布": "https://mubu.com/home",
    "微词云": "https://www.weiciyun.com/",
    "Apache ECharts": "https://echarts.apache.org/zh/index.html",
    "Tableau Public": "https://public.tableau.com/app",
    "镝数图表": "https://dycharts.com/",
    "花火 Hanabi": "https://hanabi.cn/",
    "Zotero": "https://www.zotero.org/",
    "Mendeley": "https://www.mendeley.com/",
    "EndNote": "https://endnote.com/",
    "NoteExpress": "https://www.inoteexpress.com/",
    "百度学术": "https://xueshu.baidu.com/",
    "中国大学 MOOC": "https://www.icourse163.org/",
    "国家哲学社会科学文献中心": "https://www.ncpssd.cn/",
    "国家科技图书文献中心 NSTL": "https://www.nstl.gov.cn/",
    "中国知网 CNKI": "https://www.cnki.net/",
    "ACM Digital Library": "https://dl.acm.org/",
}

# 官方页面未给链接的模块 → 按模块要点补齐（仍标注为“补充”）
MOD_SUPP = {
    4: ["Kimi（月之暗面）", "智谱清言", "文心一言", "讯飞星火", "DeepSeek", "纳米AI",
        "秘塔AI搜索"],
    30: ["四川大学图书馆", "国家图书馆联机公共目录", "读秀学术搜索", "超星发现"],
    34: ["中国知网 CNKI", "ACM Digital Library"],
    40: ["LICEcap（GIF 录屏）", "Snipaste（截图 / 贴图）"],
    45: ["WPS Office", "石墨文档"],
    48: ["EPS数据平台", "Tableau Public", "微词云", "Apache ECharts"],
}

for m in modules:
    for nm in MOD_SUPP.get(m["no"], []):
        u = SUPP.get(nm)
        if not u:
            continue
        m["links"].append({"u": u, "label": nm, "host": host(u),
                           "access": access_note(u), "src": "supp"})

for m in modules:
    for l in m["links"]:
        l.setdefault("src", "page")

for nm, u in SUPP.items():
    platforms.append({
        "host": host(u), "name": nm, "url": u, "urls": [u], "mods": [],
        "access": access_note(u), "src": "supp",
    })

# 合并同名条目：页面里同一站点常以两个域名出现（如 pubmed.gov / pubmed.ncbi.nlm.nih.gov），
# 补充平台也可能与页面已有的重复。
merged = collections.OrderedDict()
for p in platforms:
    q = merged.get(p["name"])
    if q is None:
        merged[p["name"]] = p
        continue
    for m in p["mods"]:
        if m not in q["mods"]:
            q["mods"].append(m)
    for u in p["urls"]:
        if u not in q["urls"]:
            q["urls"].append(u)
    if p["src"] == "page":
        q["src"] = "page"
    if p["host"] and (not q["host"] or len(p["host"]) < len(q["host"])):
        q["host"] = p["host"]
platforms = list(merged.values())
for p in platforms:
    p["url"] = max(p["urls"], key=lambda u: (".pdf" not in u.lower(), p["urls"].index(u)))
    p["access"] = access_note(p["url"])

# 排序：页面来源在前（按被引用次数降序），补充平台在后（按名称）。
# 这样“平台速查”打开时最常用的数据库就在最上面。
platforms.sort(key=lambda x: (0 if x["src"] == "page" else 1,
                              -len(x["mods"]) if x["src"] == "page" else 0,
                              x["name"]))

uses_out = []
for uid, uname, udesc, nos in USES:
    mods = [m for m in modules if use_of.get(m["no"]) == uid]
    uses_out.append({
        "id": uid, "name": uname, "desc": udesc,
        "count": len(mods),
        "nos": [m["no"] for m in mods],
        "platforms": sorted({l["host"] for m in mods for l in m["links"]}),
    })

data = {
    "meta": {
        "title": "信息素养与科研工具速查手册",
        "source": "https://csc.xxsuyang.com/Knowledge",
        "modules": len(modules),
        "uses": len(uses_out),
        "platforms": len(platforms),
        "questions": sum(len(m["questions"]) for m in modules),
        "explore": sum(len(m["explore"]) for m in modules),
    },
    "uses": uses_out,
    "modules": modules,
    "platforms": platforms,
}

os.makedirs("out", exist_ok=True)
json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("uses:", len(uses_out), [(u["id"], u["count"]) for u in uses_out])
print("modules:", len(modules), "platforms:", len(platforms),
      "questions:", data["meta"]["questions"], "explore:", data["meta"]["explore"])
print("links total:", sum(len(m["links"]) for m in modules))
miss = [m["no"] for m in modules if not m["links"]]
print("modules without links:", miss)

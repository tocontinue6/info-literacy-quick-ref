# -*- coding: utf-8 -*-
"""Generate the structured Markdown resource report."""
import json, re, os, collections, urllib.parse, datetime
import url_fixes

RAW = "out/knowledge_raw.json"
LC = "out/linkcheck.json"
PDFMETA = "out/pdf_meta.json"
OUT = "out/信息素养与科研工具速查手册-资源清单.md"

d = json.load(open(RAW, encoding="utf-8"))
url_fixes.apply_all(d)          # 应用网址勘误（旧地址已被官方迁移）
lc = json.load(open(LC, encoding="utf-8"))
pdfmeta = json.load(open(PDFMETA, encoding="utf-8"))

items = d["items"]
cats = sorted(d["categories"], key=lambda c: c["sort"])
cat_name = {c["id"]: c["name"] for c in cats}

TRAIL = "）。，、；：！？》】”’…;:,.)\"'"


def clean(u):
    return (u or "").strip().rstrip(TRAIL)


def status_of(u):
    r = lc.get(u)
    if not r:
        return "未检测"
    s = r["status"]
    if s in ("200", "202", "204"):
        return "✅ 可访问"
    if s.startswith("HTTP 3") or s in ("301", "302", "303", "307", "308"):
        return "↪️ 重定向"
    if s.startswith("HTTP 401") or s.startswith("HTTP 403") or s.startswith("HTTP 412") \
            or s.startswith("HTTP 429") or s.startswith("HTTP 418"):
        return "⛔ 反爬拦截（浏览器可访问）"
    if s.startswith("HTTP 404") or s.startswith("HTTP 410"):
        return "❌ 已失效 " + s.split()[1]
    if s.startswith("HTTP 5"):
        return "❌ 服务器错误 " + s.split()[1]
    if s.startswith("HTTP"):
        return "❌ " + s
    if s.startswith("SKIP"):
        return "⚠️ 本地路径／非 HTTP"
    if "Timeout" in s or "timed out" in s:
        return "⏱️ 探测超时（需复验）"
    return "⚠️ 连接失败（需复验）"


# ---------------------------------------------------------------- parsing tools
SEC = re.compile(r"^☆\s*([^：:]{1,20})[：:]?\s*(.*)$")
OPT = re.compile(r"^([A-DＡ-Ｄ])\s*[、.．:：]\s*(.*)$")
QTYPE = re.compile(r"样题\s*\d*\s*[（(]([^）)]*)[）)]?")


def split_sections(text):
    """-> list of (section_title, body_lines)"""
    out, cur, buf = [], None, []
    for ln in text.split("\n"):
        s = ln.strip()
        m = SEC.match(s)
        # 原始页面该节有两种写法（“学习指导及备赛建议”/“学习指导与备赛建议”），按前缀匹配
        if m and (m.group(1) in ("具体要求", "参考资源")
                  or m.group(1).startswith(("学习指导", "样题"))):
            if cur is not None:
                out.append((cur, buf))
            cur, buf = m.group(1) + (("：" + m.group(2)) if m.group(2).strip() else ""), []
        else:
            if cur is None:
                if s:
                    cur, buf = "(前言)", []
                    buf.append(ln)
            elif s and not s.startswith("☆"):
                buf.append(ln)
    if cur is not None:
        out.append((cur, buf))
    return out


OPTSPLIT = re.compile(r"(?=(?:^|\s)[A-DＡ-Ｄ]\s*[、.．]\s*)")


def parse_question(title, body):
    q = {"title": title, "type": "", "stem": [], "options": [],
         "answer": "", "explain": []}
    m = QTYPE.search(title)
    if m:
        q["type"] = m.group(1)
    mode = "stem"

    def take_options(s):
        """Split a line that may hold 1..4 options."""
        marks = [mm.start() for mm in re.finditer(r"(?:^|\s)([A-DＡ-Ｄ])\s*[、.．]\s*", s)]
        if not marks:
            return False
        if len(marks) == 1 and re.match(r"^\s*[A-DＡ-Ｄ]\s*[、.．]", s):
            mm = re.match(r"^\s*([A-DＡ-Ｄ])\s*[、.．]\s*(.*)$", s)
            q["options"].append((mm.group(1), mm.group(2).strip()))
            return True
        if len(marks) >= 2:
            marks.append(len(s))
            for a, b in zip(marks, marks[1:]):
                seg = s[a:b].strip()
                mm = re.match(r"^([A-DＡ-Ｄ])\s*[、.．]\s*(.*)$", seg)
                if mm:
                    q["options"].append((mm.group(1), mm.group(2).strip()))
            return True
        return False

    for ln in body:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("答案解析"):
            mode = "explain"
            rest = re.sub(r"^答案解析\s*[：:]\s*", "", s)
            q["explain"].append(rest.strip())
            continue
        if s.startswith("参考答案") or s.startswith("正确答案"):
            mode = "answer"
            q["answer"] = re.sub(r"^(参考答案|正确答案)\s*[：:]\s*", "", s).strip()
            continue
        if s.startswith("参考答案与解析") or s.startswith("解析"):
            mode = "explain"
            q["explain"].append(re.sub(r"^(参考答案与解析|解析)\s*[：:]\s*", "", s).strip())
            continue
        if mode in ("stem", "options") and take_options(s):
            mode = "options"
            continue
        if mode == "stem":
            q["stem"].append(s)
        elif mode == "explain":
            q["explain"].append(s)
        else:
            q["stem"].append(s)
    return q


modules = []
for it in items:
    text = it["_text"]
    secs = split_sections(text)
    req, guide, res, questions, expl = [], [], [], [], []
    for title, body in secs:
        if title.startswith("具体要求"):
            req = [l.strip() for l in body if l.strip()]
        elif title.startswith("学习指导"):
            guide = [l.strip() for l in body if l.strip()]
        elif title.startswith("样题"):
            questions.append(parse_question(title, body))
        elif title.startswith("参考资源"):
            res = [l.strip() for l in body if l.strip()]
    seen, explorations = set(), []
    for l in guide + req:
        if "探索" in l and l not in seen:
            seen.add(l)
            explorations.append(l)
    modules.append({"it": it, "req": req, "guide": guide, "questions": questions,
                    "explore": explorations, "res": res})

# ---------------------------------------------------------------- links
by_item = collections.defaultdict(list)
for l in d["links"]:
    by_item[l["item_id"]].append({**l, "href": clean(l["href"])})

url_index = collections.OrderedDict()
for l in d["links"]:
    u = clean(l["href"])
    e = url_index.setdefault(u, {"labels": [], "mods": [], "cats": []})
    if l["label"] and l["label"] not in e["labels"]:
        e["labels"].append(l["label"])
    tag = f"{l['category']} / {l['item_title']}"
    if tag not in e["mods"]:
        e["mods"].append(tag)
    if l["category"] not in e["cats"]:
        e["cats"].append(l["category"])
for b in d["bare_urls"]:
    u = clean(b["url"])
    if not u.startswith("http"):
        continue
    e = url_index.setdefault(u, {"labels": [], "mods": [], "cats": []})
    tag = f"{b['category']} / {b['item_title']} (正文)"
    if tag not in e["mods"]:
        e["mods"].append(tag)
    if b["category"] not in e["cats"]:
        e["cats"].append(b["category"])

pdf_urls = {clean(l["href"]) for l in d["pdf_links"]}
ext_urls = {u: e for u, e in url_index.items() if u not in pdf_urls and u.startswith("http")}

# ---------------------------------------------------------------- classification
LOGIN_HOSTS = {
    "www.cnki.net", "cnki.net", "ai.cnki.net", "chkd.cnki.net", "k.cnki.net", "x.cnki.net",
    "navi.cnki.net", "conf.cnki.net", "lawpro.cnki.net", "image.cnki.net",
    "www.wanfangdata.com.cn", "video.wanfangdata.com.cn", "cx.wanfangdata.com.cn",
    "www.cqvip.com", "www.sciencedirect.com", "eci.elsevier.cn",
    "onlinelibrary.wiley.com", "www.tandfonline.com", "dl.acm.org", "ieeexplore.ieee.org",
    "www.jstor.org", "bioone.org",
    "www.spiedigitallibrary.org", "iopscience.iop.org", "asmedigitalcollection.asme.org",
}
MIXED_HOSTS = {
    "www.cambridge.org", "academic.oup.com", "www.nature.com", "www.cell.com",
    "www.science.org", "www.ieee.org",
}
OA_HOSTS = {"doaj.org", "arxiv.org", "www.chinaxiv.org", "www.medrxiv.org", "www.oalib.com",
            "www.ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "pubmed.gov",
            "dspace.mit.edu", "www.doaj.org", "suyang.zxhnzq.com",
            "publishmedia.cbpt.cnki.net", "opendatalab.com", "www.openml.org",
            "archive.ics.uci.edu", "archive-beta.ics.uci.edu", "zh.d2l.ai",
            "www.elementsofai.com"}


def host(u):
    return urllib.parse.urlparse(u).netloc.lower()


def access_note(u):
    h = host(u)
    if h in LOGIN_HOSTS:
        return "需登录/机构订阅"
    if h in MIXED_HOSTS:
        return "部分免费，全文或需机构订阅"
    if h in OA_HOSTS:
        return "开放获取/免费"
    if h.endswith(".gov.cn") or h.endswith(".edu.cn") or h.endswith(".org.cn"):
        return "公共/机构网站"
    if h.endswith("cnki.net") or h.endswith("wanfangdata.com.cn") or h.endswith("cqvip.com"):
        return "需登录/机构订阅"
    return "公开"


# ---------------------------------------------------------------- PDF summaries
PDF_NOTES = {
    "28716c58bcc84f6db5242dd90363c98c.pdf": (
        "《生成式人工智能服务安全基本要求》(TC260-003)",
        "全国网络安全标准化技术委员会(TC260)于 2024-02-29 发布的技术文件。规定了生成式人工智能服务在"
        "安全方面的基本要求，包括**语料安全、模型安全、安全措施**，并给出安全评估要求；适用于服务提供者"
        "开展安全评估，也可供主管部门评判服务安全水平。核心条款：语料来源安全（含违法不良信息超过 5% 的"
        "不应采集、不应使用；使用开源/自采/商业语料须有许可或授权记录）、语料内容过滤与知识产权、语料标注"
        "安全、模型安全、安全措施（关键词库、生成内容测试题库、拒答测试题库、分类模型）、第 9 章安全评估"
        "（评估方法、语料安全评估、生成内容安全评估、问题拒答评估）；附录 A 列出 31 种主要安全风险。"
        "**注意：该 PDF 只有 6 页，而文件目次显示正文至第 10 页、附录至第 10 页之后，"
        "说明它是节选（仅含封面、目次、前言及正文第 1—2 页），并非标准全文。** "
        "需要完整条款时须另找 TC260 官网原文件。"),
    "scu-ai-tool-regulation-2025.pdf": (
        "《四川大学本科教育教学人工智能工具应用规范（试行）》",
        "四川大学校发文件：**川大教〔2025〕28 号**，标题为《关于印发〈四川大学本科教育教学人工智能"
        "工具应用规范（试行）〉的通知》，**2025 年 3 月 26 日**印发（盖四川大学公章）。"
        "该 PDF 为扫描件（TOSHIBA e-STUDIO 扫描仪生成），**无文本层，程序化提取为 0 字符**；"
        "以下要点通过逐页图像人工判读获得：共 18 页；正文为《四川大学本科教育教学人工智能工具应用规范"
        "（试行）》，设“第一章 总则”等章节——第一条明确制定依据为《生成式人工智能服务管理暂行办法》"
        "等规定；第二条界定“人工智能工具（AI 工具）”为以人工智能技术设计的大模型工具（如 DeepSeek、"
        "智谱清言、文心一言等）以及专门为教育教学设计的垂直模型和智能体；第三条界定适用范围为全体教师、"
        "学生、教学辅助人员开展的本科教育教学活动，涵盖专业建设、课程建设、课堂教学、实践教学、创新教育、"
        "教材建设、教师发展、远程教育、教学评估、质量监控等。"),
    "文后参考文献著录规则（GB T 7714— 2025）.pdf": (
        "《信息与文献　参考文献著录规则》(GB/T 7714—2025)",
        "中华人民共和国国家标准 **GB/T 7714—2025**，**代替 GB/T 7714—2015**；"
        "**2025-12-02 发布，2026-07-01 实施**，由国家市场监督管理总局、国家标准化管理委员会发布；"
        "分类号 ICS 01.140.20、CCS A 14。该 PDF 为图片型 PDF，**无文本层，程序化提取为 0 字符**；"
        "以下结构通过逐页图像人工判读获得：全文 45 页；正文第 9 章为“参考文献标引体系编制法”"
        "（9.1 通用要求、9.2 顺序编码制、9.3 著者-出版年制）；附录 A（规范性）“文献类型和文献载体标识代码”"
        "（A.1 文献类型和标识代码、A.2 电子资源载体和标识代码）；附录 B（资料性）“顺序编码制参考文献表"
        "著录格式示例”，覆盖 B.1 图书、B.2 图书中的析出文献、B.3 连续出版物、B.4 连续出版物中的析出文献、"
        "B.5 会议录、B.6 学位论文、B.7 报告、B.8 标准、B.9 专利、B.10 网站/网页、B.11 档案、B.12 地图、"
        "B.13 数据集、B.14 预印本；末尾为参考文献（第 39 页起）。用于知识模块44“参考文献著录格式”。"),
}


def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()


# ---------------------------------------------------------------- build report
L = []
P = L.append
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

P("# 信息素养与科研工具速查手册 · 资源清单\n")
P(f"> 数据来源：<https://csc.xxsuyang.com/Knowledge>　|　报告生成时间：{now}　|　抓取方式：官方数据接口（非人工浏览）\n")

# --- 0 methodology
P("## 一、抓取说明\n")
P("目标页面是一个 Vue 单页应用（SPA），直接请求 HTML 只能拿到“正在加载资源”的骨架，"
  "正文数据全部由 JavaScript 异步请求后台接口后渲染。因此本次抓取采取了“解析前端产物 → 定位官方接口 → 直接取结构化数据”的方式，"
  "数据与页面渲染结果完全一致。\n")
P("| 步骤 | 具体内容 |")
P("| --- | --- |")
P("| 1. 站点入口 | `https://csc.xxsuyang.com/Knowledge` |")
P("| 2. 前端配置 | `/website.config.js` → 环境 `production`，接口网关 `baseUrl/baseUrlXxsy = https://jsgateway.zhixinst.com`，站点标识 `kind = csc2025` |")
P("| 3. 路由分包 | `/static/js/app.2d1f2f86.js` → 路由 `/Knowledge` 对应分包 `chunk-ad6fcdc4`；详情页路由 `/detail` 对应 `chunk-16e5bb42` |")
P("| 4. 接口定位 | `chunk-ad6fcdc4` 中调用 `GetParentList`（分类）与 `GetKnowledgeList`（模块列表）；`chunk-16e5bb42` 中调用 `GetKnowledge`（详情） |")
P("| 5. 数据获取 | `GET /SCC/Website/GetParentList?kind=csc2025`、`GET /SCC/Website/GetKnowledgeList?kind=csc2025` |")
P("| 6. 富文本解析 | 模块正文为 HTML 富文本，含 `具体要求`、`学习指导…`、`样题`、`答案解析`、`参考资源` 等小节（沿用原始页面的小节名） |")
P("| 7. 链接核验 | 对正文中出现的全部 270 个去重链接逐一发起 HTTP 探测，记录状态码 |")
P("| 8. 附件处理 | 下载全部 PDF 附件到本地 `pdf/`，用 pypdf 提取元数据与文本层；对无文本层的扫描件，抽取页面图像后逐页人工判读 |")
P("")
P("**接口清单（本次抓取实际使用）**\n")
P("| 接口 | 方法 | 作用 | 返回 |")
P("| --- | --- | --- | --- |")
P("| `/SCC/Website/GetParentList` | GET | 知识点分类（9 个） | 见附件 `raw/api_parentlist.json` |")
P("| `/SCC/Website/GetKnowledgeList` | GET | 全部知识模块（50 条，含正文） | 见附件 `raw/api_knowledgelist_csc2025.json` |")
P("| `/SCC/Website/GetKnowledge` | GET | 单条详情（`?id=`），列表接口已包含同样内容 | 未单独调用 |")
P("")

# --- 1 overview
n_q = sum(len(m["questions"]) for m in modules)
n_explore = sum(len(m["explore"]) for m in modules)
P("## 二、资源概览\n")
P("| 资源类型 | 数量 | 说明 |")
P("| --- | --- | --- |")
P(f"| 知识点分类 | **{len(cats)}** | 页面顶部的可折叠分组 |")
P(f"| 知识模块（下级页面） | **{len(items)}** | 每个模块对应 `/detail?id=<模块ID>` |")
P(f"| PDF 附件 | **{len(d['pdf_links'])}** | 3 个全部下载成功（其中 1 个源站首次连接被重置，重试后成功） |")
P(f"| 去重链接总数 | **{len(url_index)}** | `<a>` 锚点链接与正文内嵌网址合并去重后 |")
P(f"| 　↳ `<a>` 锚点链接（原始出现 {len(d['links'])} 次） | **{len({l['href'] for l in d['links']})}** | 页面“参考资源／答案解析”中的超链接 |")
P(f"| 　↳ 正文纯文本内嵌网址（原始 {len(d['bare_urls'])} 处） | **{len({b['url'] for b in d['bare_urls']})}** | 写在文字中、非超链接的网址 |")
P(f"| 例题（原页面称“样题”） | **{n_q}** | 含单选题、多选题、判断题，均附正确答案与解析 |")
P(f"| 实践任务 | **{n_explore}** | “学习指导”小节中的动手实践条目 |")
P(f"| 图片资源 | **{len(d['assets'])}** | 正文 `<img>` 引用 |")
P(f"| 需登录/机构订阅链接 | **{sum(1 for u in url_index if access_note(u) == '需登录/机构订阅')}** | 知网、万方、维普、ScienceDirect、Wiley 等 |")
P("")
P("> 说明：上表后两行为分类明细，两者存在重叠（同一网址可能既以超链接出现、也在正文中以纯文本出现），"
  "合并去重后即第一行的 270 个。\n")
P(f"链接可达性探测结果（对全部 {sum(1 for u in url_index if u in lc)} 个去重 URL 逐一发起 HTTP 请求）：\n")
buckets = collections.Counter()
for u in url_index:
    r = lc.get(u)
    if not r:
        continue
    buckets[status_of(u)] += 1
P("| 探测结果 | 数量 |")
P("| --- | --- |")
for k, v in buckets.most_common():
    P(f"| {k} | {v} |")
P("")
P("> 说明：`⛔ 反爬拦截` 与 `⏱️ 探测超时` 并不等于链接失效——这些站点会拒绝脚本请求或对境外/机房 IP 限速，"
  "在浏览器中通常可以正常打开；报告中已单独列出，供人工复核。\n")

# --- 2 module overview: reorganised BY PURPOSE, with exam points
APP = None
try:
    APP = json.load(open("out/app_data.json", encoding="utf-8"))
except Exception:
    APP = None

P("## 三、知识点总览（按使用场景重新分类）\n")
if APP:
    P("> 本节不再按站点原有的 9 个学科分类罗列，而是**按“你打算做什么”重新归为 10 类**，"
      "便于按使用场景快速定位。配套的交互式速查工具见 "
      "[`信息素养与科研工具速查手册.html`](信息素养与科研工具速查手册.html)（含全局搜索与键盘快捷键）。\n")
    P("**用途分类总表**\n")
    P("| 快捷键 | 用途分类 | 适用场景 | 模块数 | 主要平台 |")
    P("| --- | --- | --- | --- | --- |")
    for i, u in enumerate(APP["uses"]):
        key = f"Alt+{i+1}" if i < 9 else "Alt+0"
        names = []
        for h in u["platforms"][:6]:
            nm = next((p["name"] for p in APP["platforms"] if p["host"] == h), h)
            names.append(nm)
        P(f"| `{key}` | **{u['name']}** | {u['desc']} | {u['count']} | {'、'.join(names)} |")
    P("")
    P("#### 索引与网址快捷键\n")
    P("配套网页 [`信息素养与科研工具速查手册.html`](信息素养与科研工具速查手册.html) 是单文件、**完全离线**（不引用任何外部 CDN）的速查工具，"
      "打开即可用，全部操作用键盘完成：\n")
    P("| 快捷键 | 作用 |")
    P("| --- | --- |")
    P("| `/` 或 `Ctrl+K` | 聚焦搜索框（同时搜模块标题、学习要点、关键词、平台、网址） |")
    P("| `Alt+1` … `Alt+9` `Alt+0` | 直达第 1–10 个用途分类 |")
    P("| `[` / `]` | 上一个 / 下一个用途分类 |")
    P("| `↑` `↓`（或 `k` `j`） | 在模块目录中上下移动 |")
    P("| `Enter` | 打开选中的模块 |")
    P("| **`1` … `9` `0`** | **打开当前模块的第 1–10 个资源网址**（新标签页） |")
    P("| `l` | 进入链接导航模式，`↑↓` 选链接、`Enter` 打开（用于第 11 个之后的链接） |")
    P("| `p` | 打开「平台速查」面板（200 个平台，输入即过滤，`1`…`0` 打开前 10 个结果） |")
    P("| `o` / `y` | 在新标签页打开 / 复制当前模块的原始页面地址 |")
    P("| `t` | 切换打开方式：新标签页 ⇄ 当前标签页 |")
    P("| `Esc` / `?` | 关闭浮层 / 显示快捷键帮助 |")
    P("")
    P("---\n")
    P("### 各用途分类下的模块与学习要点\n")
    for i, u in enumerate(APP["uses"]):
        key = f"Alt+{i+1}" if i < 9 else "Alt+0"
        mods = [m for m in APP["modules"] if m["use"] == u["id"]]
        P(f"#### {key}　{u['name']}（{u['count']} 个模块）\n")
        P(f"*{u['desc']}*\n")
        for j, m in enumerate(mods, 1):
            P(f"**{u['id']}-{j}　{m['title']}**　"
              f"（原分类：{m['legacy']}｜{len(m['links'])} 个资源｜{len(m['questions'])} 道例题）\n")
            P(f"- 原始页面：<{m['detail']}>")
            if m["req"]:
                P("- **学习要点（官方“具体要求”）**：")
                for r in m["req"]:
                    P(f"  - {esc(r)}")
            if m["kw"]:
                P(f"- 关键词：{'、'.join(m['kw'][:12])}")
            if m["explore"]:
                P("- 实践任务：")
                for e in m["explore"]:
                    P(f"  - {esc(e)}")
            qs = m["questions"]
            if qs:
                P(f"- 例题：共 {len(qs)} 道（{'、'.join(q['type'] or '未标注' for q in qs)}），"
                  f"答案 {'、'.join(q['answer'] for q in qs)}")
            P("")
        P("")
else:
    P("| # | 分类 | 模块标题 | 链接数 | 例题数 | 实践任务 |")
    P("| --- | --- | --- | --- | --- | --- |")
    for i, m in enumerate(modules, 1):
        it = m["it"]
        P(f"| {i:02d} | {it['_category']} | {esc(it['title'])} | {len(by_item.get(it['id'], []))} | "
          f"{len(m['questions'])} | {len(m['explore'])} |")
    P("")
P("> 每个模块的访问地址：`https://csc.xxsuyang.com/detail?id=<模块ID>`（模块 ID 见附录）。\n")

# --- 3 PDF
P("## 四、PDF 资源列表\n")
P("| # | 文件名 | 来源模块 | 来源链接 | 页数 | 本地文件 | 解析状态 |")
P("| --- | --- | --- | --- | --- | --- | --- |")
pdfrows = []
PDF_LOCAL = {
    "hulianhutongshequ.cn": "pdf/28716c58bcc84f6db5242dd90363c98c.pdf",
    "202.115.54.22": "pdf/scu-ai-tool-regulation-2025.pdf",
    "publishmedia.cbpt.cnki.net": "pdf/文后参考文献著录规则（GB T 7714— 2025）.pdf",
}
for i, l in enumerate(d["pdf_links"], 1):
    u = clean(l["href"])
    local = PDF_LOCAL.get(host(u), "")
    meta = pdfmeta.get(os.path.basename(local)) if local else None
    pages = meta.get("pages", "?") if meta else "?"
    if meta and meta.get("chars_extracted", 0) > 500:
        st = "✅ 已提取文本层"
    elif meta and "error" in meta:
        st = "❌ 解析失败"
    else:
        st = "⚠️ 无文本层（扫描/图片型，需 OCR）"
    P(f"| {i} | {esc(l['label'])} | {l['item_title']} | <{u}> | {pages} | `{local}` | {st} |")
    pdfrows.append((l, u, meta, local))
P("")
P("### PDF 内容摘要\n")
for i, (l, u, meta, local) in enumerate(pdfrows, 1):
    base = os.path.basename(local) if local else ""
    title, note = PDF_NOTES.get(base, (l["label"], "（未收录摘要）"))
    P(f"**PDF-{i}　{title}**\n")
    P(f"- 来源模块：{l['item_title']}（{l['category']}）")
    P(f"- 页面显示名称：{l['label']}")
    P(f"- 原始链接：<{u}>")
    if meta:
        md = meta.get("metadata", {})
        P(f"- 文件大小：{meta.get('bytes', 0):,} 字节　|　页数：{meta.get('pages', '?')}　|　本地路径：`{local}`")
        if md:
            P(f"- 文档元数据：{esc(json.dumps(md, ensure_ascii=False))}")
        P(f"- 文本层字符数：{meta.get('chars_extracted', 0)}")
    P(f"- 内容摘要：{note}")
    P("")

# --- 4 external links
grouped = collections.OrderedDict()
for c in cats:
    grouped[c["name"]] = []
for u, e in url_index.items():
    if not u.startswith("http") or u in pdf_urls:
        continue
    primary = e["cats"][0] if e["cats"] else "其他"
    grouped.setdefault(primary, []).append((u, e))

P("## 五、链接清单（按 URL 去重）\n")
P(f"共 {sum(len(r) for r in grouped.values())} 个去重链接（已剔除 3 个 PDF 附件链接，见第四节），"
  "按所属知识分类归并。状态列为本次实际 HTTP 探测结果。\n")
for cname, rows in grouped.items():
    if not rows:
        continue
    P(f"### {cname}（{len(rows)} 个）\n")
    P("| # | 链接标题 | URL | 出现模块 | 可达性 | 访问属性 |")
    P("| --- | --- | --- | --- | --- | --- |")
    for i, (u, e) in enumerate(sorted(rows, key=lambda x: x[1]["mods"][0]), 1):
        label = e["labels"][0] if e["labels"] else ""
        if label.startswith("http"):
            label = ""
        if not label:
            label = urllib.parse.urlparse(u).netloc
        mods = "；".join(m.split(" / ")[-1].replace(" (正文)", "〔正文〕") for m in e["mods"])
        P(f"| {i} | {esc(label)} | <{u}> | {esc(mods)} | {status_of(u)} | {access_note(u)} |")
    P("")

# --- 5 exercises
P("## 六、例题集锦\n")
P(f"数据源共提供 **{n_q}** 道官方例题（原始页面称“样题”，分布在 {sum(1 for m in modules if m['questions'])} 个知识模块中），"
  "每题均附有正确答案与答案解析。以下按模块原样整理。\n")
qno = 0
for m in modules:
    if not m["questions"]:
        continue
    it = m["it"]
    P(f"### {it['_category']} · {it['title']}\n")
    for q in m["questions"]:
        qno += 1
        head = f"**题 {qno}**"
        if q["type"]:
            head += f"（{q['type']}）"
        P(head + "\n")
        P("> " + " ".join(q["stem"]).strip() + "\n")
        if q["options"]:
            for k, v in q["options"]:
                P(f"- {k}、{v}")
            P("")
        P(f"- **正确答案：** {q['answer'] or '（未提供）'}")
        ex = " ".join(q["explain"]).strip()
        if ex:
            P(f"- **答案解析：** {ex}")
        P("")
P("")

P("### 实践任务（动手实践建议）\n")
P("以下条目出现在各模块的“具体要求 / 学习指导”中，以“探索”字样标记，属于动手实践类任务。\n")
P("| # | 模块 | 任务内容 |")
P("| --- | --- | --- |")
k = 0
for m in modules:
    for e in m["explore"]:
        k += 1
        P(f"| {k} | {esc(m['it']['title'])} | {esc(e)} |")
P("")

# --- 6 pending / anomalies
P("## 七、待确认项与异常清单\n")
P("### 7.1 需登录 / 机构订阅才能访问的资源\n")
P("站点自身配置（`website.config.js` 的 `navLink`）明确把“中国知网”和“爱思唯尔 LeapSpace”标记为 `islogin: true`；"
  "其余以下资源虽可打开链接，但实际取用全文需机构 IP 或账号登录。**本次未尝试绕过任何登录。**\n")
P("| # | 资源/域名 | 链接 | 归属模块 | 登录要求 |")
P("| --- | --- | --- | --- | --- |")
k = 0
for u, e in url_index.items():
    if access_note(u) != "需登录/机构订阅":
        continue
    k += 1
    P(f"| {k} | {esc(host(u))} | <{u}> | {esc(e['mods'][0])} | 需账号/机构IP登录 |")
P("")

P("### 7.2 无法访问 / 异常的链接\n")
P("下列链接在本次自动探测中未返回 200。按性质分三档：**A 类为真实缺陷**（本地路径、404/500 等），"
  "**B 类为反爬拦截**（站点拒绝脚本请求，浏览器通常可正常打开），**C 类为探测超时/重定向**"
  "（可能受网络环境影响，需人工复验）。\n")
P("| # | 类型 | URL | 状态 | 归属模块 |")
P("| --- | --- | --- | --- | --- |")


def sev(u):
    r = lc.get(u)
    if not r:
        return 9
    s = r["status"]
    if s.startswith("SKIP"):
        return 0
    if s.startswith("HTTP 4") and not s.startswith(("HTTP 401", "HTTP 403", "HTTP 412", "HTTP 429")):
        return 1
    if s.startswith("HTTP 5"):
        return 2
    if s.startswith("HTTP 3"):
        return 3
    if s.startswith("HTTP 401") or s.startswith("HTTP 403") or s.startswith("HTTP 412") \
            or s.startswith("HTTP 429"):
        return 4
    if s.startswith("HTTP"):
        return 5
    return 6


SEVNAME = {0: "A 真实缺陷", 1: "A 真实缺陷", 2: "A 真实缺陷", 3: "C 重定向",
           4: "B 反爬拦截", 5: "A 真实缺陷", 6: "C 探测失败", 9: "-"}

k = 0
cand = [u for u in url_index if u in lc and lc[u]["status"] not in ("200", "202", "204")]
cand.sort(key=sev)
for u in cand:
    k += 1
    e = url_index.get(u)
    mods = "；".join(m.replace(" (正文)", "〔正文〕") for m in (e["mods"][:2] if e else [])) or "—"
    P(f"| {k} | {SEVNAME.get(sev(u), '-')} | <{u}> | {status_of(u)} | {esc(mods)} |")
if k == 0:
    P("| - | - | 无 | - | - |")
P("")

P("### 7.3 页面内容缺陷\n")
P("- **正文内存在指向作者本机磁盘的失效链接。** 知识模块09“开放数据资源”中，"
  "“国家统计局数据”一条的锚点地址被写成了本地文件路径：\n")
for u, r in lc.items():
    if r["status"].startswith("SKIP"):
        e = url_index.get(u)
        P(f"  - `{u}`")
        P(f"  - 归属模块：{e['mods'][0] if e else '—'}")
        P("  - 推测：原意应指向该模块的配套文档"
          "《2026年大学生“AI+信息素养”大赛客观题命题范围及备赛建议（2026.7.8修订）.docx》，"
          "上传时误粘贴了本地路径，**线上无法打开**。")
P("")
P("- **两个 PDF 为扫描／图片型，不含文本层**（四川大学 AI 工具规范 18 页、GB/T 7714—2025 共 45 页），"
  "程序化提取字符数为 0。本次已通过抽取页面图像并逐页人工判读补齐了标题、文号、发布/实施日期与章节结构"
  "（见第四节摘要），但**未做全文字符级录入**；若需要引用原文条款，建议人工阅读原件或做 OCR。")
P("- **“参考资源”小节在多数模块中为空**：正文的实际资源链接被内嵌在“具体要求”“例题解析”等段落中，"
  "而非集中列在“☆ 参考资源”之下。本清单已把全部内嵌链接提取并汇总到第五节。")
P("- **模块49 的小节标题写法与其余模块不同**：原始页面中该模块写作“学习指导**与**备赛建议”，"
  "其余 49 个模块写作“学习指导**及**备赛建议”。早期解析规则只匹配“及”，导致该模块的"
  "学习指导内容被并入“具体要求”。现已改为按前缀匹配，两种写法均可正确分段。")
P("- **接口未返回发布时间与作者**：50 个模块的 `createtime` 全部为 `2026-07-08T15:24:36`（导入时间批量写入），"
  "`author` 为空，无法据此判断各模块的实际修订时间。")
P("- **站点接口存在测试环境残留**：前端包内硬编码了 `VUE_APP_BASEURL: \"https://jsgatewaytest.zhixinst.com\"`"
  "（测试网关），正式环境通过 `website.config.js` 覆盖为生产网关，不影响使用，但属配置冗余。")
P("")

P("### 7.4 未纳入本清单的内容\n")
P("- 站点导航栏指向的其他栏目（中国知网专区 `/zhiwang`、`https://xxsuyang.com/`、"
  "`https://ai.xxsuyang.com/`、爱思唯尔 LeapSpace）不属于 `/Knowledge` 页面，未展开抓取。")
P("- 模块详情接口 `/SCC/Website/GetKnowledge` 返回的 `courses`（关联课程）字段在本批数据中均为空，"
  "详情页“相关课程”区块无内容。")
P("")

# --- appendix
P("## 附录 A：模块 ID 对照表\n")
P("| # | 分类 | 模块标题 | 模块 ID | 详情 URL |")
P("| --- | --- | --- | --- | --- |")
for i, m in enumerate(modules, 1):
    it = m["it"]
    P(f"| {i:02d} | {it['_category']} | {esc(it['title'])} | `{it['id']}` | "
      f"<https://csc.xxsuyang.com/detail?id={it['id']}> |")
P("")
P("## 附录 B：分类 ID 对照表\n")
P("| 排序 | 分类名称 | 分类 ID | 模块数 |")
P("| --- | --- | --- | --- |")
for c in cats:
    n = sum(1 for i in items if i.get("categoryid") == c["id"])
    P(f"| {c['sort']} | {c['name']} | `{c['id']}` | {n} |")
P("")
P("## 附录 C：产出文件清单\n")
P("| 文件 | 说明 |")
P("| --- | --- |")
P("| `信息素养与科研工具速查手册.html` | **速查工具**：按使用场景分类 + 学习要点 + 键盘快捷键，单文件离线运行 |")
P("| `out/信息素养与科研工具速查手册-资源清单.md` | 本报告 |")
P("| `out/knowledge_raw.json` | 结构化原始数据（分类 / 模块 / 全部链接 / 正文纯文本） |")
P("| `out/items_text.md` | 50 个模块的正文纯文本 |")
P("| `out/details.txt` | 分类、PDF、域名统计与逐模块链接明细 |")
P("| `out/linkcheck.json` | 270 个链接的 HTTP 可达性探测结果 |")
P("| `out/pdf_meta.json` | PDF 元数据（页数、大小、文本层字符数） |")
P("| `pdf/` | 已下载的 3 个 PDF 附件 |")
P("| `out/pdf_text/` | PDF 文本提取结果 |")
P("| `raw/` | 页面 HTML、前端 JS 产物、接口原始响应 |")
P("")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("wrote", OUT, len("\n".join(L)), "chars,", len(L), "lines")
print("answers:", qno, "| explore tasks:", n_explore, "| distinct urls:", len(url_index))

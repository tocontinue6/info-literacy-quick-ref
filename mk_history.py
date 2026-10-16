# -*- coding: utf-8 -*-
"""把 CHANGELOG.md 拆成三个历史状态，供三次提交分别使用（复刻迭代过程）。

生成到 out/_hist/：
    CHANGELOG-v1.md  仅含初版
    CHANGELOG-v2.md  含初版 + 更新一
    README-v1.md     初版说明（比赛向文案）
"""
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(ROOT, "out", "_hist")
os.makedirs(HIST, exist_ok=True)

full = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()

# 按二级标题切块
parts = re.split(r"\n(?=## )", full)
head = parts[0]
blocks = {}
for p in parts[1:]:
    title = p.split("\n", 1)[0]
    if "更新二" in title:
        blocks["v21"] = p
    elif "更新一" in title:
        blocks["v20"] = p
    elif "初版" in title:
        blocks["v10"] = p
    elif "版本与文件对照" in title:
        blocks["对照"] = p

print("解析到区块:", sorted(blocks))

VERSIONS = [
    ("v1.0", "2026-10-13", "初版", "为比赛整理的《考点速查手册》，按用途重排 50 个知识模块"),
    ("v2.0", "2026-10-16", "更新一", "修复键盘打开网址被环境拦截、反复弹确认框的问题"),
    ("v2.1", "2026-10-16", "更新二", "修正已变更的网址；用途从比赛专用改为通用学习科研工具"),
]

HEADER = """# 版本说明

按时间顺序记录《考点速查手册》的每一次迭代。

| 版本 | 日期 | 对应提交 | 一句话 |
| --- | --- | --- | --- |
{rows}
"""


def header(include_versions, title="《考点速查手册》"):
    rows = "\n".join(
        f"| {v} | {d} | {c} | {s} |" for v, d, c, s in VERSIONS if v in include_versions
    )
    h = HEADER.replace("{rows}", rows)
    return h.replace("《考点速查手册》", title)


def write(name, text):
    p = os.path.join(HIST, name)
    open(p, "w", encoding="utf-8").write(text)
    print("wrote", name, len(text), "chars")


# v1：只要初版
write("CHANGELOG-v1.md",
      header(["v1.0"], "《考点速查手册》") + "\n---\n\n" + blocks["v10"].rstrip() + "\n")

# v2：初版 + 更新一
write("CHANGELOG-v2.md",
      header(["v1.0", "v2.0"], "《考点速查手册》")
      + "\n---\n\n" + blocks["v20"].rstrip()
      + "\n\n---\n\n" + blocks["v10"].rstrip() + "\n")

# ---- 初版 README（比赛向）----
README_V1 = """# 考点速查手册 · 2026 大学生“AI+信息素养”大赛

## 👉 比赛时用这个文件

[`考点速查手册.html`](考点速查手册.html)

单文件、**完全离线**（不引用任何外部资源），双击即可用浏览器打开。

---

## 内容概览

- **50 个知识模块**，按“题目要你做什么”归为 **10 个用途分类**
- 每个模块含：考点（官方“具体要求”原文）、关键词、常考操作、资源链接、样题与答案解析
- **56 道官方样题**（含正确答案与解析）
- **99 条探索任务**
- **200 个平台**速查（页面原有 173 个 + 补充 36 个，补充项均经可达性实测，去重后 200 个）

---

## 快捷键

| 键 | 作用 |
| --- | --- |
| `/` 或 `Ctrl+K` | 搜索（模块标题 / 考点 / 关键词 / 平台 / 网址） |
| `Alt+1` … `Alt+9` `Alt+0` | 直达第 1–10 个用途分类 |
| `↑` `↓` | 在模块目录中移动，`Enter` 打开 |
| **`1` … `9` `0`** | **打开当前模块的第 1–10 个资源网址**（新标签页） |
| `l` | 链接导航模式（用于第 11 个之后的链接） |
| **`p`** | **平台速查面板（200 个平台，输入即过滤，`1`…`0` 秒开前 10 条）** |
| `o` / `y` | 打开 / 复制当前模块的官网原页 |
| `?` | 快捷键帮助 |

**最常用的操作**：题目提到某个平台 → 按 `p` → 输入平台名 → 按 `1` 直接打开。

---

## 数据来源

站点：<https://csc.xxsuyang.com/Knowledge>

该页面是 Vue 单页应用，正文由接口异步加载。本手册通过解析前端产物定位官方接口后直接取结构化数据：

| 接口 | 作用 |
| --- | --- |
| `GET /SCC/Website/GetParentList?kind=csc2025` | 知识点分类（9 个） |
| `GET /SCC/Website/GetKnowledgeList?kind=csc2025` | 全部知识模块（50 条，含正文） |

接口网关：`https://jsgateway.zhixinst.com`
"""
write("README-v1.md", README_V1)

# ---- 修复说明的 v2.0 版（去掉 v2.1 勘误那一部分）----
fx_path = os.path.join(ROOT, "bug修复", "修复说明.md")
if os.path.exists(fx_path):
    fx = open(fx_path, encoding="utf-8").read()
    marker = "# 第二部分：v2.0 修复键盘跳转弹确认框"
    if marker in fx:
        body = fx.split(marker, 1)[1].lstrip()
        # 重新加上 v2.0 的标题
        v2_title = "# 修复说明：键盘打开网址时弹出“即将访问外部链接”确认框\n"
        write("修复说明-v2.md", v2_title + body)
    else:
        print("!! 未找到 v2.0 分节标记，跳过")

print("\n历史状态已生成到 out/_hist/")

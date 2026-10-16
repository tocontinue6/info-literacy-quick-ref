# -*- coding: utf-8 -*-
"""按「初版 → 更新一 → 更新二」三次提交复刻本项目的迭代过程。

用法（在仓库根目录）：python commit_history.py
只做本地提交，不会推送任何远端。
"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(ROOT, "out", "_hist")
FINAL = os.path.join(ROOT, "out", "_final")
os.makedirs(FINAL, exist_ok=True)


def run(*args, check=True):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if r.stdout.strip():
        print("   " + r.stdout.strip().replace("\n", "\n   "))
    if r.stderr.strip():
        print("   ! " + r.stderr.strip().replace("\n", "\n   "))
    if check and r.returncode != 0:
        sys.exit(f"命令失败: {' '.join(args)}")
    return r


def copy(src, dst):
    shutil.copyfile(os.path.join(ROOT, src), os.path.join(ROOT, dst))
    print(f"   {src}  ->  {dst}")


# 先把最终版文档备份出来，供第三次提交恢复
for f in ("README.md", "CHANGELOG.md", os.path.join("bug修复", "修复说明.md")):
    dst = os.path.join(FINAL, f.replace(os.sep, "__"))
    shutil.copyfile(os.path.join(ROOT, f), dst)
print("最终版文档已备份到 out/_final/")

print("\n【提交 1/3】初版：为比赛整理的《考点速查手册》")
copy("out/_hist/README-v1.md", "README.md")
copy("out/_hist/CHANGELOG-v1.md", "CHANGELOG.md")
run("git", "add", "考点速查手册.html", "README.md", "CHANGELOG.md")
run("git", "commit", "-m",
    "初版：为 2026 大学生“AI+信息素养”大赛整理的考点速查手册\n\n"
    "- 目标页面是 Vue 单页应用，通过解析前端产物定位官方接口后直接取结构化数据\n"
    "- 把站点原有的 9 个学科分类，按“你打算做什么”重新归为 10 个用途分类\n"
    "- 每个模块含考点（官方“具体要求”原文）、关键词、常考操作、资源链接、样题与解析\n"
    "- 200 个平台速查；单文件、完全离线、全键盘操作")

print("\n【提交 2/3】更新一：修复键盘打开网址被环境拦截弹确认框")
copy("out/_hist/CHANGELOG-v2.md", "CHANGELOG.md")
copy("out/_hist/修复说明-v2.md", os.path.join("bug修复", "修复说明.md"))
run("git", "add", "bug修复/", "CHANGELOG.md")
run("git", "commit", "-m",
    "修复：键盘打开网址被环境拦截并反复弹确认框\n\n"
    "原因：window.open(url, '_blank', 'noopener') 传入了非空的 features 参数，\n"
    "浏览器因此把它当作弹出窗口（popup）请求；受管控的环境会拦截弹窗并要求确认。\n"
    "鼠标点击 <a target=\"_blank\"> 走的是普通链接导航，不经过该判定，\n"
    "所以表现为“键盘要确认、鼠标不确认”。\n\n"
    "- 移除全部 4 处 window.open，改为激活真实隐藏 <a>，与鼠标点击同路径\n"
    "- 新增「打开方式」开关（t 键）：新标签页 ⇄ 当前标签页\n"
    "- 新增打开后的底部提示条，提供「复制链接」兜底\n"
    "- 状态持久化改为 localStorage + URL hash 双写，应对环境清空页面存储\n"
    "- 补充 39 项回归测试（check_v2.js）")

print("\n【提交 3/3】更新二：网址勘误 + 用途泛化")
for f in ("README.md", "CHANGELOG.md", os.path.join("bug修复", "修复说明.md")):
    shutil.copyfile(os.path.join(FINAL, f.replace(os.sep, "__")), os.path.join(ROOT, f))
    print(f"   恢复最终版 {f}")
run("git", "add", "-A")
run("git", "commit", "-m",
    "修正已变更网址，并把用途从比赛专用改为通用学习科研工具\n\n"
    "网址勘误\n"
    "  国家药品监督管理局数据查询系统地址迁移：\n"
    "  www.nmpa.gov.cn/datasearch  ->  datasearch.nmpa.gov.cn/datasearch\n"
    "  实测旧地址被服务端重定向到 url_change.html（官方“网址已变更”页），\n"
    "  新域名 DNS 正常解析并正常响应。\n"
    "  新增 url_fixes.py 网址勘误表，由 build_data / report / linkcheck / detaillist\n"
    "  统一调用，保证重新生成不会回退；替换同时覆盖正文中的纯文本网址。\n\n"
    "用途泛化（不改功能，只改文案）\n"
    "  考点速查手册 -> 信息素养与科研工具速查手册\n"
    "  考点 -> 学习要点；常考操作（探索任务）-> 实践任务（探索建议）；样题 -> 例题\n"
    "  面向读者由参赛者改为大学生／研究生\n\n"
    "顺带修掉一个解析缺陷\n"
    "  原始页面中模块49 的小节标题写作“学习指导与备赛建议”，\n"
    "  其余 49 个模块写作“学习指导及备赛建议”；早期规则只匹配“及”，\n"
    "  导致该模块的学习指导内容被并入“具体要求”。现改为按前缀匹配。\n\n"
    "其他\n"
    "  新增 README.md / CHANGELOG.md / .gitignore / screenshots；整理脚本目录")

print("\n================ 提交历史 ================")
run("git", "log", "--pretty=format:%h  %ad  %s", "--date=format:%Y-%m-%d")
print("\n\n================ 工作区状态 ================")
run("git", "status", "--short", check=False)
print("\n完成。如需推送到 GitHub，自行执行：")
print('  git remote add origin <你的仓库地址>')
print('  git push -u origin main')

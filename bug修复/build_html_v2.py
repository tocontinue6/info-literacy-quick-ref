# -*- coding: utf-8 -*-
"""生成《信息素养与科研工具速查手册》（v2.x）。

历史沿革：初版为特定比赛整理的“考点速查手册”，v2.1 起改为面向
大学生／研究生的通用学习与科研速查手册，并修复键盘打开网址被环境拦截
弹确认框的问题、应用已变更网址的勘误。

用法（在仓库根目录下）：python "bug修复/build_html_v2.py"
"""
import json, os, html
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import url_fixes

VERSION = "2.1"

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
data = json.load(open(os.path.join(_ROOT, "out", "app_data.json"), encoding="utf-8"))
_old = sum(1 for m in data["modules"] for l in m["links"]
           if l["u"] in url_fixes.URL_FIXES)
if _old:
    raise SystemExit(f"❌ 成品数据里仍有 {_old} 条旧网址，请先重新运行 build_data.py")
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>信息素养与科研工具速查手册</title>
<style>
:root{
  --bg:#f6f7f9; --panel:#fff; --ink:#1a1d21; --dim:#5c6672; --line:#e2e6ea;
  --brand:#1e67ca; --brand-soft:#e8f2ff; --warn:#b45309; --warn-soft:#fef3c7;
  --ok:#15803d; --ok-soft:#dcfce7; --lock:#b91c1c; --lock-soft:#fee2e2;
  --kbd:#eef1f4; --kbd-line:#c9d1d9;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:14px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;}
kbd{display:inline-block;min-width:18px;padding:1px 5px;margin:0 1px;
  font:600 11px/1.5 ui-monospace,Consolas,monospace;color:#334;
  background:var(--kbd);border:1px solid var(--kbd-line);border-bottom-width:2px;
  border-radius:4px;text-align:center}
a{color:var(--brand);text-decoration:none}
a:hover{text-decoration:underline}

header{position:sticky;top:0;z-index:50;display:flex;align-items:center;gap:14px;
  padding:10px 16px;background:var(--panel);border-bottom:1px solid var(--line);
  box-shadow:0 1px 3px rgba(0,0,0,.04);flex-wrap:wrap}
.brand{font-weight:700;font-size:15px;white-space:nowrap}
.brand small{font-weight:400;color:var(--dim);margin-left:6px}
.search-wrap{position:relative;flex:1;min-width:260px}
#q{width:100%;padding:9px 12px 9px 34px;font-size:14px;border:1px solid var(--line);
  border-radius:8px;background:var(--bg);outline:none;font-family:inherit}
#q:focus{border-color:var(--brand);background:#fff;box-shadow:0 0 0 3px var(--brand-soft)}
.search-wrap::before{content:"🔍";position:absolute;left:10px;top:8px;font-size:13px;opacity:.6}
.hbtns{display:flex;gap:6px;align-items:center}
.hbtns button{padding:6px 10px;font:inherit;font-size:12.5px;background:var(--panel);
  border:1px solid var(--line);border-radius:7px;cursor:pointer;color:var(--ink)}
.hbtns button:hover{border-color:var(--brand);color:var(--brand)}
.stats{color:var(--dim);font-size:12.5px;white-space:nowrap}

main{display:grid;grid-template-columns:340px 1fr;gap:0;height:calc(100vh - 57px)}
#side{overflow-y:auto;background:var(--panel);border-right:1px solid var(--line);padding:8px 0 40px}
#detail{overflow-y:auto;padding:20px 26px 60px}

.use{border-bottom:1px solid var(--line)}
.use-head{display:flex;align-items:center;gap:8px;padding:9px 12px;cursor:pointer;
  font-weight:600;font-size:13.5px;user-select:none}
.use-head:hover{background:var(--brand-soft)}
.use-head .cnt{margin-left:auto;font-weight:400;color:var(--dim);font-size:11.5px}
.use.open .use-head{background:var(--brand-soft);color:var(--brand)}
.use .mods{display:none;padding-bottom:4px}
.use.open .mods{display:block}
.mod{display:flex;gap:7px;align-items:baseline;padding:5px 12px 5px 16px;cursor:pointer;
  font-size:13px;border-left:3px solid transparent}
.mod:hover{background:#f0f4f9}
.mod.sel{background:var(--brand-soft);border-left-color:var(--brand);font-weight:600}
.mod .idx{font:600 10.5px/1.6 ui-monospace,Consolas,monospace;color:#889;flex:none}
.mod.sel .idx{color:var(--brand)}

h1{font-size:19px;margin:0 0 6px}
.crumb{color:var(--dim);font-size:12.5px;margin-bottom:14px}
.crumb b{color:var(--brand)}
.actions{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.actions a,.actions button{padding:6px 12px;font:inherit;font-size:12.5px;border-radius:7px;
  border:1px solid var(--line);background:#fff;cursor:pointer;color:var(--ink)}
.actions a:hover,.actions button:hover{border-color:var(--brand);color:var(--brand);text-decoration:none}

section{margin-bottom:22px}
h2{font-size:14px;margin:0 0 9px;padding-bottom:6px;border-bottom:2px solid var(--brand-soft);
  color:var(--brand);letter-spacing:.3px}
ul.req{margin:0;padding-left:20px}
ul.req li{margin:3px 0}
ul.plain{list-style:none;margin:0;padding:0}
ul.plain li{padding:5px 8px;border-radius:6px;margin-bottom:3px}
ul.plain li:nth-child(odd){background:#fafbfc}

.q{border:1px solid var(--line);border-radius:9px;padding:12px 14px;margin-bottom:12px;background:#fff}
.q .qtype{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;
  background:var(--brand-soft);color:var(--brand);font-weight:600;margin-bottom:7px}
.q .stem{font-weight:600;margin-bottom:8px}
.q .opts{margin:0 0 8px;padding-left:0;list-style:none;color:#333}
.q .opts li{padding:1px 0}
.ans{background:var(--ok-soft);color:#14532d;padding:6px 10px;border-radius:6px;font-weight:600;
  display:inline-block;margin-bottom:6px}
.exp{color:#444;font-size:13px;border-left:3px solid var(--line);padding-left:10px}

ol.links{list-style:none;margin:0;padding:0;counter-reset:none}
ol.links li{display:flex;gap:9px;align-items:flex-start;padding:6px 8px;border-radius:7px;
  margin-bottom:2px}
ol.links li:nth-child(odd){background:#fafbfc}
ol.links li.hot{outline:2px solid var(--brand);background:var(--brand-soft)}
.lk{flex:1;min-width:0;word-break:break-all}
.lk .lab{font-weight:600}
.lk .u{color:#6b7280;font-size:11.5px;font-family:ui-monospace,Consolas,monospace}
.tag{flex:none;font-size:10.5px;padding:1px 6px;border-radius:99px;white-space:nowrap}
.tag.login{background:var(--lock-soft);color:var(--lock)}
.tag.mixed{background:var(--warn-soft);color:var(--warn)}
.tag.gov{background:#e0e7ff;color:#3730a3}
.tag.open{background:var(--ok-soft);color:var(--ok)}
.hint{color:var(--dim);font-size:12px;margin-bottom:8px}

.mask{position:fixed;inset:0;background:rgba(15,20,26,.45);z-index:100;display:none;
  align-items:flex-start;justify-content:center;padding:70px 16px 20px}
.mask.on{display:flex}
.modal{background:#fff;border-radius:12px;width:min(880px,100%);max-height:78vh;overflow:auto;
  box-shadow:0 18px 50px rgba(0,0,0,.28)}
.modal h3{margin:0;padding:14px 18px;border-bottom:1px solid var(--line);font-size:15px;
  position:sticky;top:0;background:#fff;z-index:2}
.modal .body{padding:14px 18px 20px}
.kbdgrid{display:grid;grid-template-columns:auto 1fr;gap:7px 14px;align-items:center}
.kbdgrid .k{white-space:nowrap}
.kbdgrid .d{color:#333}
.kgroup{grid-column:1/-1;margin-top:12px;font-weight:700;color:var(--brand);font-size:13px}
.plat{display:flex;gap:9px;align-items:center;padding:6px 8px;border-radius:7px;cursor:pointer}
.plat:hover{background:var(--brand-soft)}
.plat.hot{outline:2px solid var(--brand);background:var(--brand-soft)}
.plat .nm{font-weight:600;min-width:180px}
.plat .hs{color:#6b7280;font-size:11.5px;font-family:ui-monospace,Consolas,monospace}
#platq{width:100%;padding:8px 11px;border:1px solid var(--line);border-radius:7px;
  margin-bottom:10px;font:inherit;outline:none}
#platq:focus{border-color:var(--brand);box-shadow:0 0 0 3px var(--brand-soft)}

#results{position:absolute;top:44px;left:0;right:0;background:#fff;border:1px solid var(--line);
  border-radius:9px;box-shadow:0 12px 30px rgba(0,0,0,.13);max-height:62vh;overflow:auto;
  display:none;z-index:60}
#results.on{display:block}
#results .r{padding:7px 12px;cursor:pointer;display:flex;gap:9px;align-items:baseline;
  border-bottom:1px solid #f2f4f6}
#results .r:last-child{border-bottom:0}
#results .r.hot{background:var(--brand-soft)}
#results .r .t{font-weight:600}
#results .r .s{color:var(--dim);font-size:11.5px;margin-left:auto;white-space:nowrap}
#results .r .u{color:#6b7280;font-size:11.5px;font-family:ui-monospace,Consolas,monospace;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:46%}
.badge{font-size:10.5px;padding:1px 6px;border-radius:99px;background:#eef1f4;color:#556;flex:none}
.badge.mod{background:var(--brand-soft);color:var(--brand)}
.badge.url{background:var(--ok-soft);color:var(--ok)}

@media(max-width:860px){
  main{grid-template-columns:1fr;height:auto}
  #side{max-height:42vh;border-right:0;border-bottom:1px solid var(--line)}
  #detail{padding:16px}
}

/* 打开方式切换按钮 —— 命中时高亮“当前标签页”这一更保守的模式 */
#btn-mode{font-weight:600}
#btn-mode.same{background:var(--warn-soft);border-color:#f0c36d;color:var(--warn)}

/* 轻提示：网址被打开后显示，并提供“复制链接”兜底 */
#toast{position:fixed;left:50%;bottom:22px;transform:translate(-50%,20px);
  display:none;align-items:center;gap:10px;max-width:92vw;
  padding:9px 12px;background:#1f2937;color:#f3f4f6;border-radius:9px;
  box-shadow:0 10px 26px rgba(0,0,0,.3);font-size:12.5px;z-index:200}
#toast.on{display:flex;animation:tin .18s ease-out forwards}
@keyframes tin{to{transform:translate(-50%,0)}}
#toast .tmsg{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:62vw;
  font-family:ui-monospace,Consolas,monospace}
#toast button{padding:4px 9px;font:inherit;font-size:12px;border-radius:6px;cursor:pointer;
  border:1px solid #4b5563;background:#374151;color:#f3f4f6;flex:none}
#toast button:hover{border-color:#9ca3af}
#toast .tclose{background:transparent;border:0;font-size:15px;line-height:1;padding:2px 4px}
</style>
</head>
<body>

<header>
  <div class="brand">信息素养与科研工具速查手册<small>大学生 · 研究生　学习与科研常用资源</small></div>
  <div class="search-wrap">
    <input id="q" placeholder="搜模块 / 要点 / 平台 / 网址…  按 / 聚焦，↑↓ 选择，Enter 激活" autocomplete="off">
    <div id="results"></div>
  </div>
  <div class="hbtns">
    <button id="btn-mode" title="切换网址打开方式 (t)">打开方式：新标签页 <kbd>t</kbd></button>
    <button id="btn-plat" title="平台速查 (p)">平台速查 <kbd>p</kbd></button>
    <button id="btn-help" title="快捷键 (?)">快捷键 <kbd>?</kbd></button>
  </div>
  <div class="stats" id="stats"></div>
</header>

<main>
  <nav id="side"></nav>
  <div id="detail"></div>
</main>

<div class="mask" id="mask-help"><div class="modal">
  <h3>⌨️ 快捷键一览</h3><div class="body" id="helpbody"></div>
</div></div>

<div class="mask" id="mask-plat"><div class="modal">
  <h3>🔗 平台速查 —— 输入名称过滤，按 <kbd>1</kbd>…<kbd>0</kbd> 直接打开前 10 个</h3>
  <div class="body">
    <input id="platq" placeholder="输入平台名或域名，例如：知网 / CNKI / cnki.net / 国家标准">
    <div class="hint" id="platcount" style="margin:6px 0 8px"></div>
    <div id="platlist"></div>
  </div>
</div></div>

<div id="toast"></div>

<script>
const DATA = __DATA__;
const MODS = DATA.modules, USES = DATA.uses, PLATS = DATA.platforms;
const byNo = {}; MODS.forEach(m => byNo[m.no] = m);
const byUse = {}; USES.forEach(u => byUse[u.id] = u);

// lowercased search blobs
MODS.forEach(m => {
  m._blob = [m.title, m.legacy, m.use, (u => u.name)(byUse[m.use] || {name:''}),
    m.kw.join(' '), m.req.join(' '), m.explore.join(' '),
    m.questions.map(q => q.stem + ' ' + q.options.map(o => o.join('')).join(' ') + ' ' + q.answer + ' ' + q.explain).join(' '),
    m.links.map(l => l.label + ' ' + l.u + ' ' + l.host).join(' ')
  ].join(' ').toLowerCase();
});
PLATS.forEach(p => {
  p._blob = (p.name + ' ' + p.host + ' ' + p.urls.join(' ') + ' ' + p.mods.join(' ')).toLowerCase();
});

/* ---------- 状态：优先 localStorage，其次 URL hash ----------
   某些环境（App 内置浏览器 / 沙箱预览）每次打开都会清空 origin 存储，
   因此把状态同时写进 URL hash，任何情况下都能靠链接本身恢复。 */
const HKEY = 'csc-qref-v2';
function loadState() {
  let st = {};
  try { st = JSON.parse(localStorage.getItem(HKEY) || '{}') || {}; } catch (e) { st = {}; }
  const h = new URLSearchParams((location.hash || '').replace(/^#/, ''));
  if (h.get('m')) st.sel = +h.get('m');
  if (h.get('t')) st.openMode = h.get('t');
  return st;
}
function saveState() {
  const st = { sel: S.sel, openMode: S.openMode };
  try { localStorage.setItem(HKEY, JSON.stringify(st)); } catch (e) {}
  try {
    const q = 'm=' + st.sel + '&t=' + st.openMode;
    history.replaceState(null, '', location.pathname + location.search + '#' + q);
  } catch (e) {}
}

const _init = loadState();
const S = { sel: _init.sel && byNo[_init.sel] ? _init.sel : MODS[0].no,
            openMode: _init.openMode === 'same' ? 'same' : 'tab',
            nav: 'toc', li: -1, res: [], ri: 0, platList: [], pi: 0, openUse: {} };
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const TAGS = { login:'需登录', mixed:'部分免费', gov:'公共机构', open:'公开' };

/* ---------- TOC ---------- */
function renderTOC() {
  let h = '';
  USES.forEach((u, i) => {
    const key = i < 9 ? 'Alt+' + (i + 1) : 'Alt+0';
    const open = S.openUse[u.id] !== false;
    var mods = MODS.filter(m => m.use === u.id);
    h += '<div class="use' + (open ? ' open' : '') + '" data-use="' + u.id + '">';
    h += '<div class="use-head" data-toggle="' + u.id + '"><kbd>' + key + '</kbd>'
       + '<span>' + esc(u.name) + '</span><span class="cnt">' + mods.length + ' 模块</span></div>';
    h += '<div class="mods">';
    mods.forEach((m, j) => {
      h += '<div class="mod' + (m.no === S.sel ? ' sel' : '') + '" data-no="' + m.no + '">'
         + '<span class="idx">' + u.id + '-' + (j + 1) + '</span>'
         + '<span>' + String(m.no).padStart(2, '0') + ' ' + esc(m.title.replace(/^知识模块\d+：/, '')) + '</span></div>';
    });
    h += '</div></div>';
  });
  $('side').innerHTML = h;
  $('side').querySelectorAll('.use-head').forEach(e => e.onclick = () => {
    const id = e.dataset.toggle; S.openUse[id] = S.openUse[id] === false; renderTOC();
  });
  $('side').querySelectorAll('.mod').forEach(e => e.onclick = () => selectMod(+e.dataset.no, true));
}

function jumpUse(i) {
  const u = USES[i]; if (!u) return;
  S.openUse[u.id] = true;
  const first = MODS.find(m => m.use === u.id);
  if (first) selectMod(first.no, false);
  renderTOC();
  const el = $('side').querySelector('.use[data-use="' + u.id + '"]');
  if (el) el.scrollIntoView({ block: 'start', behavior: 'smooth' });
  S.nav = 'toc';
}

/* ---------- detail ---------- */
function selectMod(no, scrollTOC) {
  S.sel = no; S.li = -1;
  const m = byNo[no]; if (!m) return;
  saveState();
  const u = byUse[m.use] || { name: '' };
  let h = '<h1>' + esc(m.title) + '</h1>';
  h += '<div class="crumb">用途 <b>' + u.id + ' · ' + esc(u.name) + '</b>　|　'
     + '原分类 ' + esc(m.legacy) + '　|　索引 <b>' + u.id + '-' + (u.nos.indexOf(m.no) + 1) + '</b>　|　'
     + m.links.length + ' 个资源　|　' + m.questions.length + ' 道例题</div>';
  h += '<div class="actions">'
     + '<a href="' + m.detail + '" target="_blank" rel="noopener">打开原始页面 <kbd>o</kbd></a>'
     + '<button data-copy="' + m.detail + '">复制原页链接 <kbd>y</kbd></button>'
     + '<button data-jump="' + u.id + '">回到目录 <kbd>[</kbd></button>'
     + '</div>';

  if (m.req.length) {
    h += '<section><h2>📌 学习要点（官方“具体要求”）</h2><ul class="req">'
       + m.req.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul></section>';
  }
  if (m.kw.length) {
    h += '<section><h2>🔑 关键词</h2><div>'
       + m.kw.map(k => '<span class="badge">' + esc(k) + '</span>').join(' ') + '</div></section>';
  }
  if (m.explore.length) {
    h += '<section><h2>🧭 实践任务（探索建议）</h2><ul class="req">'
       + m.explore.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul></section>';
  }
  if (m.links.length) {
    h += '<section><h2>🔗 资源链接 —— 按数字键直接打开</h2>';
    h += '<div class="hint">数字键 <kbd>1</kbd>…<kbd>9</kbd> <kbd>0</kbd> 打开前 10 个；'
       + '按 <kbd>l</kbd> 进入链接导航模式后用 <kbd>↑</kbd><kbd>↓</kbd> 选择、<kbd>Enter</kbd> 打开。'
       + '若打开时总弹出“即将访问外部链接”确认框，按 <kbd>t</kbd> 切换为“当前标签页”方式。</div>';
    h += '<ol class="links">';
    m.links.forEach((l, i) => {
      const k = i < 9 ? String(i + 1) : (i === 9 ? '0' : '');
      let host = l.host.replace(/^www\./, '');
      h += '<li data-li="' + i + '">' + (k ? '<kbd>' + k + '</kbd>' : '<kbd>·</kbd>')
         + '<span class="lk"><a href="' + esc(l.u) + '" target="_blank" rel="noopener" class="lab">'
         + esc(l.label || host) + '</a><br><span class="u">' + esc(l.u.length > 110 ? l.u.slice(0, 110) + '…' : l.u)
         + '</span></span>'
         + '<span class="tag ' + l.access + '">' + (TAGS[l.access] || '') + '</span></li>';
    });
    h += '</ol></section>';
  } else {
    h += '<section><h2>🔗 资源链接</h2><div class="hint">该模块页面未给出独立链接，学习要点以官方“具体要求”为准；'
       + '可在搜索框输入平台名直接打开（如 <kbd>Kimi</kbd>、<kbd>知网</kbd>）。</div></section>';
  }
  m.questions.forEach((q, qi) => {
    h += '<section><h2>📝 例题 ' + (qi + 1) + '</h2><div class="q">';
    if (q.type) h += '<div class="qtype">' + esc(q.type) + '</div>';
    h += '<div class="stem">' + esc(q.stem) + '</div>';
    if (q.options.length) h += '<ul class="opts">' + q.options.map(o => '<li>' + esc(o[0]) + '、' + esc(o[1]) + '</li>').join('') + '</ul>';
    if (q.answer) h += '<div class="ans">正确答案：' + esc(q.answer) + '</div>';
    if (q.explain) h += '<div class="exp">' + esc(q.explain) + '</div>';
    h += '</div></section>';
  });

  $('detail').innerHTML = h;
  $('detail').scrollTop = 0;
  $('detail').querySelectorAll('[data-copy]').forEach(b => b.onclick = () => copy(b.dataset.copy));
  $('detail').querySelectorAll('[data-jump]').forEach(b => b.onclick = () => {
    const i = USES.findIndex(x => x.id === b.dataset.jump); jumpUse(i);
  });
  if (scrollTOC) {
    $('side').querySelectorAll('.mod').forEach(e => e.classList.toggle('sel', +e.dataset.no === no));
    const el = $('side').querySelector('.mod.sel');
    if (el) el.scrollIntoView({ block: 'nearest' });
  }
}

function copy(t) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(t).catch(() => legacyCopy(t));
  } else { legacyCopy(t); }
  toast('已复制链接：' + t, t);
}
function legacyCopy(t) {
  try {
    const ta = document.createElement('textarea');
    ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select(); document.execCommand('copy');
    document.body.removeChild(ta);
  } catch (e) {}
}

/* ------------------------------------------------------------------
   打开网址：绝不使用 window.open()
   根因：window.open(url,'_blank','noopener') 带 features 参数，会被
   浏览器/WebView 判定为“弹出窗口(popup)”请求并拦截；被拦截时宿主
   环境会弹出“即将访问外部链接…”确认框。鼠标直接点 <a target=_blank>
   走的是普通链接导航，不经过 popup 判定，所以不会弹框。
   修复：改为激活一个真实 <a> 元素，让键盘操作与鼠标点击走同一条路径。
------------------------------------------------------------------ */
let _opener = null;
function openerAnchor() {
  if (!_opener) {
    _opener = document.createElement('a');
    _opener.style.display = 'none';
    _opener.rel = 'noopener noreferrer';
    document.body.appendChild(_opener);
  }
  return _opener;
}

function openURL(u) {
  if (!u) return;
  if (S.openMode === 'same') {                       // 当前标签页：普通导航
    try { location.assign(u); } catch (e) { location.href = u; }
    return;
  }
  const a = openerAnchor();                          // 新标签页：真实链接点击
  a.href = u;
  a.target = '_blank';
  a.click();
  toast('已在新标签页打开：' + u, u);
}

function openLink(i) {
  const m = byNo[S.sel]; const l = m && m.links[i];
  if (!l) return;
  openURL(l.u);
  const el = $('detail').querySelector('li[data-li="' + i + '"]');
  if (el) { el.classList.add('hot'); setTimeout(() => el.classList.remove('hot'), 700); }
}

/* 轻提示：即使被环境拦截，用户也能看到地址并手动复制 */
let _toastT = null;
function toast(msg, url) {
  const t = $('toast');
  t.innerHTML = '<span class="tmsg">' + esc(msg) + '</span>'
    + '<button class="tcopy" type="button">复制链接</button>'
    + '<button class="tclose" type="button">×</button>';
  t.classList.add('on');
  const btn = t.querySelector('.tcopy');
  if (btn) btn.onclick = () => {
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).catch(() => legacyCopy(url));
    else legacyCopy(url);
    btn.textContent = '已复制 ✓';
  };
  const cl = t.querySelector('.tclose');
  if (cl) cl.onclick = () => t.classList.remove('on');
  clearTimeout(_toastT);
  _toastT = setTimeout(() => t.classList.remove('on'), 6000);
}

/* ---------- search ---------- */
function search(q) {
  q = q.trim().toLowerCase();
  if (!q) { S.res = []; renderResults(); return; }
  const parts = q.split(/\s+/);
  const hit = s => parts.every(p => s.includes(p));
  const out = [];
  PLATS.forEach(p => { if (hit(p._blob)) out.push({ t: 'url', name: p.name, sub: p.host, url: p.url, score: p.name.toLowerCase().includes(q) ? 0 : 1 }); });
  MODS.forEach(m => { if (hit(m._blob)) out.push({ t: 'mod', name: m.title, sub: (byUse[m.use] || {}).name, no: m.no, score: m.title.toLowerCase().includes(q) ? 0 : 1 }); });
  out.sort((a, b) => a.score - b.score);
  S.res = out.slice(0, 60); S.ri = 0;
  renderResults();
}

function renderResults() {
  const box = $('results');
  if (!S.res.length) { box.classList.remove('on'); box.innerHTML = ''; return; }
  box.innerHTML = S.res.map((r, i) =>
    '<div class="r' + (i === S.ri ? ' hot' : '') + '" data-i="' + i + '">'
    + '<span class="badge ' + (r.t === 'url' ? 'url' : 'mod') + '">' + (r.t === 'url' ? '网址' : '模块') + '</span>'
    + '<span class="t">' + esc(r.name) + '</span>'
    + (r.t === 'url' ? '<span class="u">' + esc(r.sub) + '</span>' : '')
    + '<span class="s">' + esc(r.sub || '') + (r.t === 'mod' ? ' <kbd>Enter</kbd>' : ' <kbd>Enter</kbd> ↗') + '</span></div>'
  ).join('');
  box.classList.add('on');
  box.querySelectorAll('.r').forEach(e => {
    // 只切换高亮类，不重建 DOM —— 否则鼠标掠过会重置滚动位置
    e.onmouseenter = () => { S.ri = +e.dataset.i; hot(box, '.r', S.ri); };
    e.onclick = () => activateResult(+e.dataset.i);
  });
}

function hot(box, sel, i) {
  box.querySelectorAll(sel).forEach(e => e.classList.toggle('hot', +e.dataset.i === i));
}

function activateResult(i) {
  const r = S.res[i]; if (!r) return;
  if (r.t === 'url') { openURL(r.url); }
  else { selectMod(r.no, true); }
  $('q').value = ''; S.res = []; renderResults(); $('q').blur();
}

/* ---------- platform panel ---------- */
function renderPlats() {
  const q = ($('platq').value || '').trim().toLowerCase();
  const parts = q.split(/\s+/).filter(Boolean);
  const list = PLATS.filter(p => parts.every(x => p._blob.includes(x)));
  S.platList = list; S.pi = 0;
  const box = $('platlist');
  box.innerHTML = list.map((p, i) => {
    const k = i < 9 ? String(i + 1) : (i === 9 ? '0' : '·');
    return '<div class="plat" data-i="' + i + '">'
      + '<kbd>' + k + '</kbd><span class="nm">' + esc(p.name) + '</span>'
      + '<span class="hs">' + esc(p.host) + '</span>'
      + (p.src === 'supp' ? '<span class="tag mixed">补充</span>' : '')
      + '<span class="tag ' + p.access + '">' + (TAGS[p.access] || '') + '</span></div>';
  }).join('') || '<div class="hint">没有匹配的平台</div>';
  $('platcount').textContent = parts.length
    ? '匹配 ' + list.length + ' / ' + PLATS.length + ' 个平台'
    : '共 ' + PLATS.length + ' 个平台（按引用频次排序）';
  box.querySelectorAll('.plat').forEach(e => {
    e.onmouseenter = () => { S.pi = +e.dataset.i; hot(box, '.plat', S.pi); };
    e.onclick = () => openPlat(+e.dataset.i);
  });
}
function openPlat(i) { const p = S.platList[i]; if (p) openURL(p.url); }

/* ---------- help ---------- */
function renderHelp() {
  const K = s => '<kbd>' + esc(s) + '</kbd>';
  const rows = [
    ['g', '导航'],
    ['<kbd>?</kbd>', '显示 / 关闭本帮助'],
    ['<kbd>/</kbd> 或 <kbd>Ctrl</kbd>+<kbd>K</kbd>', '聚焦搜索框'],
    ['<kbd>Esc</kbd>', '清空搜索 / 关闭浮层'],
    ['<kbd>Alt</kbd>+<kbd>1</kbd> … <kbd>Alt</kbd>+<kbd>9</kbd>、<kbd>Alt</kbd>+<kbd>0</kbd>',
     '直达第 1–10 个用途分类'],
    ['<kbd>[</kbd> <kbd>]</kbd>', '上一个 / 下一个用途分类'],
    ['<kbd>↑</kbd> <kbd>↓</kbd> 或 ' + K('k') + ' ' + K('j'), '在模块目录中上下移动'],
    ['<kbd>Enter</kbd>', '打开选中的模块'],
    ['g', '网址'],
    ['<kbd>1</kbd> … <kbd>9</kbd> <kbd>0</kbd>', '打开当前模块的第 1–10 个资源链接（新标签页）'],
    ['<kbd>l</kbd>', '进入链接导航模式，' + K('↑') + K('↓') + ' 选链接、' + K('Enter') + ' 打开（第 11 个之后的链接）'],
    ['<kbd>p</kbd>', '打开 / 关闭「平台速查」面板（' + DATA.meta.platforms + ' 个平台）'],
    ['<kbd>t</kbd>', '切换网址打开方式：<b>新标签页 ↔ 当前标签页</b>（被环境拦截时改用当前标签页）'],
    ['<kbd>o</kbd>', '在新标签页打开当前模块的官网原页'],
    ['<kbd>y</kbd>', '复制当前模块的官网链接'],
    ['g', '搜索'],
    ['直接输入关键词', '同时搜模块标题、学习要点、关键词、平台、网址'],
    ['<kbd>↑</kbd> <kbd>↓</kbd>', '在搜索结果中切换'],
    ['<kbd>Enter</kbd>', '激活：模块 → 跳转；网址 → 打开'],
    ['平台速查面板内', '输入即过滤，<kbd>1</kbd>…<kbd>0</kbd> 直接打开前 10 个结果'],
  ];
  $('helpbody').innerHTML = '<div class="kbdgrid">' + rows.map(r => {
    if (r[0] === 'g') return '<div class="kgroup">' + r[1] + '</div>';
    return '<div class="k">' + r[0] + '</div><div class="d">' + r[1] + '</div>';
  }).join('') + '</div>';
}

/* ---------- keyboard ---------- */
document.addEventListener('keydown', e => {
  const tag = (e.target.tagName || '').toLowerCase();
  const typing = tag === 'input' || tag === 'textarea';
  const platOpen = $('mask-plat').classList.contains('on');
  const helpOpen = $('mask-help').classList.contains('on');

  if (e.key === 'Escape') {
    if (helpOpen) { $('mask-help').classList.remove('on'); return; }
    if (platOpen) { $('mask-plat').classList.remove('on'); return; }
    if ($('results').classList.contains('on')) { S.res = []; renderResults(); $('q').value = ''; $('q').blur(); return; }
    return;
  }
  if (e.key === '?' && !typing) { e.preventDefault(); $('mask-help').classList.toggle('on'); return; }
  if ((e.key === 'k' || e.key === 'K') && (e.ctrlKey || e.metaKey)) { e.preventDefault(); $('q').focus(); return; }
  if (e.key === '/' && !typing) { e.preventDefault(); $('q').focus(); return; }

  if (helpOpen) return;

  // platform panel
  if (platOpen) {
    if (/^[0-9]$/.test(e.key) && e.target !== $('platq') || (e.altKey && /^[0-9]$/.test(e.key))) {
      const n = e.key === '0' ? 10 : +e.key; openPlat(n - 1); e.preventDefault(); return;
    }
    if (e.key === 'ArrowDown') { S.pi = Math.min(S.pi + 1, S.platList.length - 1); renderPlats(); e.preventDefault(); return; }
    if (e.key === 'ArrowUp') { S.pi = Math.max(S.pi - 1, 0); renderPlats(); e.preventDefault(); return; }
    if (e.key === 'Enter') { openPlat(S.pi); e.preventDefault(); return; }
    return;
  }

  // search results
  if ($('results').classList.contains('on') && e.target === $('q')) {
    if (e.key === 'ArrowDown') { S.ri = Math.min(S.ri + 1, S.res.length - 1); renderResults(); e.preventDefault(); return; }
    if (e.key === 'ArrowUp') { S.ri = Math.max(S.ri - 1, 0); renderResults(); e.preventDefault(); return; }
    if (e.key === 'Enter') { activateResult(S.ri); e.preventDefault(); return; }
  }

  if (e.altKey && /^[0-9]$/.test(e.key)) {
    const n = e.key === '0' ? 10 : +e.key; jumpUse(n - 1); e.preventDefault(); return;
  }
  if (typing) return;

  const cur = USES.findIndex(u => u.nos.includes(S.sel));
  if (e.key === 'p' || e.key === 'P') { e.preventDefault(); $('mask-plat').classList.toggle('on'); if ($('mask-plat').classList.contains('on')) { $('platq').value = ''; renderPlats(); $('platq').focus(); } return; }
  if (e.key === '[') { jumpUse((cur - 1 + USES.length) % USES.length); return; }
  if (e.key === ']') { jumpUse((cur + 1) % USES.length); return; }
  if (e.key === 'o' || e.key === 'O') { openURL(byNo[S.sel].detail); return; }
  if (e.key === 't' || e.key === 'T') { setMode(S.openMode === 'tab' ? 'same' : 'tab'); return; }
  if (e.key === 'y' || e.key === 'Y') { copy(byNo[S.sel].detail); return; }
  if (e.key === 'l' || e.key === 'L') { S.nav = (S.nav === 'links' ? 'toc' : 'links'); S.li = 0; hi(); return; }

  if (S.nav === 'links') {
    const n = byNo[S.sel].links.length;
    if (e.key === 'ArrowDown' || e.key === 'j') { S.li = Math.min(S.li + 1, n - 1); hi(); e.preventDefault(); return; }
    if (e.key === 'ArrowUp' || e.key === 'k') { S.li = Math.max(S.li - 1, 0); hi(); e.preventDefault(); return; }
    if (e.key === 'Enter') { openLink(S.li); e.preventDefault(); return; }
  }

  if (/^[0-9]$/.test(e.key)) { openLink(e.key === '0' ? 9 : (+e.key - 1)); e.preventDefault(); return; }

  // module navigation
  const all = MODS.map(m => m.no);
  const i = all.indexOf(S.sel);
  if (e.key === 'ArrowDown' || e.key === 'j') { selectMod(all[Math.min(i + 1, all.length - 1)], true); e.preventDefault(); return; }
  if (e.key === 'ArrowUp' || e.key === 'k') { selectMod(all[Math.max(i - 1, 0)], true); e.preventDefault(); return; }
  if (e.key === 'Enter') { selectMod(S.sel, true); e.preventDefault(); return; }
});

function hi() {
  const m = byNo[S.sel];
  $('detail').querySelectorAll('li[data-li]').forEach(e =>
    e.classList.toggle('hot', +e.dataset.li === S.li));
  const el = $('detail').querySelector('li[data-li="' + S.li + '"]');
  if (el) el.scrollIntoView({ block: 'nearest' });
}

/* ---------- 打开方式 ---------- */
function setMode(m) {
  S.openMode = (m === 'same') ? 'same' : 'tab';
  const b = $('btn-mode');
  b.innerHTML = (S.openMode === 'same' ? '打开方式：当前标签页' : '打开方式：新标签页') + ' <kbd>t</kbd>';
  b.classList.toggle('same', S.openMode === 'same');
  saveState();
}

/* ---------- boot ---------- */
$('q').addEventListener('input', e => search(e.target.value));
$('q').addEventListener('focus', e => { if (e.target.value) search(e.target.value); });
$('platq').addEventListener('input', renderPlats);
$('btn-help').onclick = () => $('mask-help').classList.toggle('on');
$('btn-plat').onclick = () => { $('mask-plat').classList.add('on'); $('platq').value = ''; renderPlats(); $('platq').focus(); };
$('btn-mode').onclick = () => setMode(S.openMode === 'tab' ? 'same' : 'tab');
document.querySelectorAll('.mask').forEach(m => m.onclick = e => { if (e.target === m) m.classList.remove('on'); });

$('stats').innerHTML = DATA.meta.modules + ' 模块 · ' + DATA.meta.uses + ' 用途 · '
  + DATA.meta.platforms + ' 平台 · ' + DATA.meta.questions + ' 例题';

renderTOC();
renderHelp();
setMode(S.openMode);
selectMod(S.sel, true);
</script>
</body>
</html>
"""

html_out = TPL.replace("__DATA__", payload)
html_out = html_out.replace(
    "<meta charset=\"utf-8\">",
    "<meta charset=\"utf-8\">\n<!-- 信息素养与科研工具速查手册 v" + VERSION
    + " | 单文件离线运行 | 键盘打开网址走真实 <a> 激活 | 已应用网址勘误 -->")

# 成品直接输出到仓库根目录，文件名即手册名
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(ROOT_DIR)
path = os.path.join(ROOT_DIR, "信息素养与科研工具速查手册.html")
open(path, "w", encoding="utf-8").write(html_out)
print("wrote", path, round(len(html_out) / 1024, 1), "KB")
print("window.open 残留(含注释):", html_out.count("window.open"))
print("旧网址残留:", sum(html_out.count(o) for o in url_fixes.URL_FIXES))

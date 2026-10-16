// Headless logic test for 考点速查手册.html — runs the real script against a minimal DOM shim.
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('考点速查手册.html', 'utf8');
const m = html.match(/<script>\n?([\s\S]*?)\n?<\/script>/);
if (!m) { console.error('FAIL: no <script> found'); process.exit(1); }
const code = m[1];

const els = {};
function El(id) {
  this.id = id; this._html = ''; this.value = ''; this.dataset = {};
  const INPUTS = ['q', 'platq'];
  this.tagName = INPUTS.includes(id) ? 'INPUT' : 'DIV';
  const set = new Set(id === 'mask-plat' || id === 'mask-help' ? [] : []);
  this.classList = {
    _s: set,
    add: c => set.add(c),
    remove: c => set.delete(c),
    contains: c => set.has(c),
    toggle: c => { set.has(c) ? set.delete(c) : set.add(c); },
  };
}
Object.defineProperty(El.prototype, 'innerHTML', {
  get() { return this._html; }, set(v) { this._html = String(v); },
});
El.prototype.querySelectorAll = () => [];
El.prototype.querySelector = () => null;
El.prototype.addEventListener = () => {};
El.prototype.scrollIntoView = () => {};
Object.defineProperty(El.prototype, 'textContent', {
  get() { return this._html; }, set(v) { this._html = String(v); },
});

const document = {
  getElementById(id) { return els[id] || (els[id] = new El(id)); },
  querySelectorAll: () => [],
  querySelector: () => null,
  addEventListener: () => {},
  activeElement: null,
};

const sandbox = {
  document, console,
  window: { open: () => {} },
  navigator: { clipboard: { writeText: () => {} } },
  setTimeout, JSON, Math, String, Number, Array, Object, RegExp, Error,
};
sandbox.globalThis = sandbox;

let failed = 0;
function ok(cond, label, extra) {
  if (cond) { console.log('  PASS  ' + label); }
  else { failed++; console.log('  FAIL  ' + label + (extra ? '  -> ' + extra : '')); }
}

try {
  vm.runInNewContext(code + '\n;globalThis.__S = S; globalThis.__DATA = DATA;', sandbox, { filename: 'app.js' });
  console.log('boot: no exception\n');
} catch (e) {
  console.log('FAIL: boot threw -> ' + e.stack);
  process.exit(1);
}

const ST = () => sandbox.__S;
const DATA = sandbox.__DATA;

const side = els['side']._html;
const detail = els['detail']._html;

console.log('== boot render ==');
ok(side.length > 1000, 'sidebar rendered (' + side.length + ' chars)');
ok((side.match(/class="mod[" ]/g) || []).length === 50,
   'sidebar lists 50 modules', (side.match(/class="mod[" ]/g) || []).length);
ok(side.includes('Alt+1') && side.includes('Alt+0'), 'Alt+1..Alt+0 key badges present');
['AI 工具实操', 'AI 政策法规与伦理', '检索语法与策略', '通用工具与知识管理']
  .forEach(n => ok(side.includes(n), 'use group present: ' + n));
ok(detail.includes('考点'), 'detail shows 考点 section');
ok(detail.includes('样题'), 'detail shows 样题 section');
ok(detail.includes('正确答案'), 'detail shows answers');
ok(detail.includes('csc.xxsuyang.com/detail?id='), 'detail links to official page');

console.log('\n== every module renders ==');
let errs = [], noReq = [], noLink = [], noQ = [];
for (let n = 1; n <= 50; n++) {
  try {
    sandbox.selectMod(n, true);
    const h = els['detail']._html;
    if (!h.includes('考点（官方“具体要求”）')) noReq.push(n);
    if (!h.includes('section')) errs.push(n + ':no-sections');
    if (!/class="links"/.test(h)) noLink.push(n);
    if (!h.includes('样题')) noQ.push(n);
  } catch (e) { errs.push(n + ':' + e.message); }
}
ok(errs.length === 0, 'all 50 modules render without throwing', errs.join(','));
ok(noReq.length === 0, 'all modules show official 考点', noReq.join(','));
ok(noLink.length === 0, 'all modules have a link list', noLink.join(','));
ok(noQ.length === 0, 'all modules show 样题', noQ.join(','));

console.log('\n== number-key badges on a link-heavy module ==');
sandbox.selectMod(24, true);          // 模块24 OA/预印本，链接最多
const d24 = els['detail']._html;
const kbd = (d24.match(/<kbd>\d<\/kbd>/g) || []).length;
ok(kbd >= 9, 'module 24 shows 1..9 digit badges (' + kbd + ')');
ok(/<kbd>0<\/kbd>/.test(d24), 'module 24 shows the "0" badge for the 10th link');

console.log('\n== search ==');
function trySearch(q, want) {
  sandbox.search(q);
  const res = ST().res;
  const hit = res.some(r => (r.name + ' ' + (r.sub || '') + ' ' + (r.url || '')).toLowerCase().includes(want.toLowerCase()));
  ok(res.length > 0 && hit, 'search "' + q + '" -> ' + res.length + ' hits, contains "' + want + '"',
     JSON.stringify(res.slice(0, 3).map(r => r.name)));
}
trySearch('知网', '知网');
trySearch('cnki', 'cnki');
trySearch('国家标准', '标准');
trySearch('布尔逻辑', '布尔逻辑');
trySearch('学习强国', '学习强国');
sandbox.search('GB/T 7714');
ok(ST().res.some(r => r.no === 44), 'search "GB/T 7714" resolves to module 44',
   JSON.stringify(ST().res.map(r => r.name)));
sandbox.search('科word');
ok(ST().res.length === 0, 'nonsense multi-term query returns nothing',
   JSON.stringify(ST().res.map(r => r.name)));
sandbox.search('知网'); sandbox.renderResults();
ok(els['results']._html.includes('网址'), 'results panel renders with 网址 badge');
ok(els['results']._html.includes('中国知网'), 'results panel lists 中国知网 CNKI');

console.log('\n== platform panel ==');
els['platq'].value = '';
sandbox.renderPlats();
const all = ST().platList.length;
ok(all === DATA.platforms.length && all >= 200,
   'platform panel loads ALL entries (' + all + '/' + DATA.platforms.length + ')');
ok(DATA.platforms.every(p => p.name && p.name.trim()), 'no blank platform names');
ok(new Set(DATA.platforms.map(p => p.name)).size === DATA.platforms.length, 'no duplicate platform names');
const pl = els['platlist']._html;
ok(pl.includes('中国知网') && pl.includes('国家标准全文公开系统'), 'platform names present in default list');
ok(pl.indexOf('中国知网') < pl.length / 2, 'most-referenced platform sits in the top half');
els['platq'].value = '专利';
sandbox.renderPlats();
ok(ST().platList.length > 0 && ST().platList.length < 40,
   'platform filter "专利" -> ' + ST().platList.length);
ok(ST().platList.every(p => p._blob.includes('专利')), 'filter is exact (all results match)');
els['platq'].value = 'kimi';
sandbox.renderPlats();
ok(ST().platList.length >= 1 && /kimi/i.test(ST().platList[0].url + ST().platList[0].host),
   'platform filter "kimi" -> ' + ST().platList.length);
els['platq'].value = '';
sandbox.renderPlats();

console.log('\n== shortcuts: jumpUse / openLink ==');
let opened = [];
sandbox.window.open = u => { opened.push(u); };
for (let i = 0; i < 10; i++) sandbox.jumpUse(i);
ok(true, 'jumpUse(0..9) did not throw');
sandbox.selectMod(24, true);
sandbox.openLink(0); sandbox.openLink(9); sandbox.openLink(3);
ok(opened.length === 3, 'openLink(0/9/3) opened 3 URLs', JSON.stringify(opened));
ok(opened.every(u => /^https?:\/\//.test(u)), 'opened URLs are absolute http(s)');
sandbox.openLink(999);
ok(opened.length === 3, 'out-of-range openLink is a safe no-op');

console.log('\n== help overlay ==');
const hb = els['helpbody']._html;
ok(hb.includes('<kbd>Alt</kbd>') && hb.includes('<kbd>1</kbd>'), 'help lists the Alt+N category shortcuts');
ok(hb.includes('平台速查') && hb.includes(String(DATA.platforms.length)),
   'help shows the real platform count (' + DATA.platforms.length + ')');
ok((hb.match(/kgroup/g) || []).length === 3, 'help is grouped into 3 sections');
ok(!/173|\bnull\b|undefined/.test(hb), 'help has no stale numbers or undefined values');

console.log('\n' + (failed === 0 ? 'ALL CHECKS PASSED' : failed + ' CHECK(S) FAILED'));
process.exit(failed === 0 ? 0 : 1);

// v2.x 回归测试：验证“键盘打开网址”不再走 window.open()，而是激活真实 <a>。
// 直接触发真实的 keydown 处理函数，走完整链路。每次 boot 都建全新环境。
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const TARGET = '信息素养与科研工具速查手册.html';
console.log('测试对象: ' + TARGET + '\n');

const html = fs.readFileSync(path.join(ROOT, TARGET), 'utf8');
const m = html.match(/<script>\n?([\s\S]*?)\n?\n?<\/script>/);
if (!m) { console.error('FAIL: no <script>'); process.exit(1); }
const code = m[1];

let failed = 0;
const ok = (c, label, extra) => {
  if (c) console.log('  PASS  ' + label);
  else { failed++; console.log('  FAIL  ' + label + (extra !== undefined ? '  -> ' + extra : '')); }
};

/* ---------------- 环境工厂 ---------------- */
function makeEnv(init) {
  init = init || {};
  const env = {
    els: {}, handlers: {},
    anchorClicks: [], windowOpenCalls: [], locationAssigns: [],
    replaceStateCalls: [], storage: Object.assign({}, init.storage || {}),
  };

  function El(id, tag) {
    this.id = id; this._html = ''; this.value = ''; this.dataset = {};
    this.tagName = tag || (['q', 'platq'].includes(id) ? 'INPUT' : 'DIV');
    const set = new Set();
    this.classList = {
      _s: set,
      add: c => set.add(c),
      remove: c => set.delete(c),
      contains: c => set.has(c),
      toggle: (c, force) => {
        const on = force === undefined ? !set.has(c) : !!force;
        on ? set.add(c) : set.delete(c);
        return on;
      },
    };
    this.style = {};
  }
  Object.defineProperty(El.prototype, 'innerHTML', {
    get() { return this._html; }, set(v) { this._html = String(v); },
  });
  Object.defineProperty(El.prototype, 'textContent', {
    get() { return this._html; }, set(v) { this._html = String(v); },
  });
  ['querySelectorAll'].forEach(k => { El.prototype[k] = () => []; });
  El.prototype.querySelector = () => null;
  El.prototype.addEventListener = () => {};
  El.prototype.scrollIntoView = () => {};
  El.prototype.focus = () => {};
  El.prototype.blur = () => {};
  El.prototype.select = () => {};
  El.prototype.appendChild = function (c) { (this._c = this._c || []).push(c); };
  El.prototype.removeChild = function () {};

  const document = {
    getElementById(id) { return env.els[id] || (env.els[id] = new El(id)); },
    querySelectorAll: () => [],
    querySelector: () => null,
    addEventListener(type, fn) { (env.handlers[type] = env.handlers[type] || []).push(fn); },
    activeElement: null,
    body: new El('body', 'BODY'),
    createElement(tag) {
      const e = new El('created-' + tag, tag.toUpperCase());
      e.click = () => env.anchorClicks.push({
        tag: e.tagName, href: e.href, target: e.target, rel: e.rel,
      });
      return e;
    },
    execCommand: () => true,
  };

  const location = {
    hash: init.hash || '', pathname: '/x.html', search: '', href: '',
    assign(u) { env.locationAssigns.push(u); },
  };
  const history = { replaceState: (a, b, url) => env.replaceStateCalls.push(url) };

  const sandbox = {
    document, console,
    window: { open: (...a) => { env.windowOpenCalls.push(a); return null; } },
    navigator: { clipboard: { writeText: () => Promise.resolve() } },
    location, history,
    localStorage: {
      getItem: k => (k in env.storage ? env.storage[k] : null),
      setItem: (k, v) => { env.storage[k] = String(v); },
      removeItem: k => { delete env.storage[k]; },
    },
    setTimeout, clearTimeout, JSON, Math, String, Number, Array, Object, RegExp,
    Error, URLSearchParams, Promise, Date,
  };
  sandbox.globalThis = sandbox;
  env.sandbox = sandbox;

  env.boot = function () {
    vm.runInNewContext(code + '\n;globalThis.__S = S; globalThis.__DATA = DATA;',
      sandbox, { filename: 'v2.js' });
    return env;
  };
  env.S = () => sandbox.__S;
  env.DATA = () => sandbox.__DATA;
  env.$ = id => env.els[id] || (env.els[id] = new El(id));
  env.key = function (k, opts) {
    const ev = Object.assign({
      key: k, altKey: false, ctrlKey: false, metaKey: false,
      target: { tagName: 'BODY' }, preventDefault() {},
    }, opts || {});
    (env.handlers.keydown || []).forEach(fn => fn(ev));
  };
  env.search = q => sandbox.search(q);
  env.selectMod = (n, s) => sandbox.selectMod(n, s);
  env.renderPlats = () => sandbox.renderPlats();
  env.openLink = i => sandbox.openLink(i);
  return env;
}

/* ---------------- tests ---------------- */
let env = makeEnv();
try { env.boot(); console.log('boot: no exception\n'); }
catch (e) { console.log('FAIL boot threw -> ' + e.stack); process.exit(1); }

const DATA = env.DATA();
const m24 = DATA.modules.find(x => x.no === 24);

console.log('== 核心修复：键盘打开网址不使用 window.open ==');
env.selectMod(24, true);
env.anchorClicks = []; env.windowOpenCalls = [];
env.key('1');
ok(env.anchorClicks.length === 1, '按数字键 1 → 恰好激活 1 个真实 <a>', JSON.stringify(env.anchorClicks));
ok(env.anchorClicks[0] && env.anchorClicks[0].tag === 'A', '被激活的元素是 <a>');
ok(env.anchorClicks[0] && env.anchorClicks[0].href === m24.links[0].u,
   'href 指向模块24的第 1 个链接', env.anchorClicks[0] && env.anchorClicks[0].href);
ok(env.anchorClicks[0] && env.anchorClicks[0].target === '_blank', 'target=_blank');
ok(env.anchorClicks[0] && /noopener/.test(env.anchorClicks[0].rel || ''), 'rel 含 noopener');
ok(env.windowOpenCalls.length === 0, 'window.open() 完全未被调用');

env.anchorClicks = [];
env.key('0');
ok(env.anchorClicks.length === 1 && env.anchorClicks[0].href === m24.links[9].u,
   '按 0 → 第 10 个链接');
env.key('9');
ok(env.anchorClicks[1] && env.anchorClicks[1].href === m24.links[8].u, '按 9 → 第 9 个链接');
ok(env.windowOpenCalls.length === 0, '多次按键后 window.open() 仍为 0 次');

console.log('\n== 所有键盘出口都不走 window.open ==');
env.anchorClicks = []; env.windowOpenCalls = [];
env.search('知网'); env.sandbox.activateResult(0);
ok(env.windowOpenCalls.length === 0, '搜索结果激活不走 window.open()');
env.anchorClicks = [];
env.renderPlats(); env.sandbox.openPlat(0);
ok(env.windowOpenCalls.length === 0, '平台速查面板不走 window.open()');
env.anchorClicks = [];
env.key('o');
ok(env.windowOpenCalls.length === 0, '按 o 打开官网原页不走 window.open()');
ok(env.anchorClicks.length === 1 && /csc\.xxsuyang\.com\/detail\?id=/.test(env.anchorClicks[0].href),
   '按 o 打开的是官网 detail 页');
env.anchorClicks = [];
env.key('l'); env.key('Enter');
ok(env.anchorClicks.length === 1, '链接导航模式下 Enter 也走真实 <a>');
ok(env.windowOpenCalls.length === 0, 'window.open() 总计 0 次');
env.key('l');

console.log('\n== 打开方式切换（t）==');
ok(env.S().openMode === 'tab', '默认：新标签页');
env.key('t');
ok(env.S().openMode === 'same', '按 t → 当前标签页');
env.anchorClicks = []; env.locationAssigns = [];
env.openLink(0);
ok(env.anchorClicks.length === 0 && env.locationAssigns.length === 1,
   '当前标签页模式用 location.assign 导航（普通跳转，不触发 popup 判定）',
   JSON.stringify(env.locationAssigns));
ok(env.$('btn-mode')._html.includes('当前标签页'), '按钮文字已更新为“当前标签页”');
ok(env.$('btn-mode').classList.contains('same'), '按钮进入高亮状态');
env.key('t');
ok(env.S().openMode === 'tab', '再按 t → 切回新标签页');
ok(env.$('btn-mode')._html.includes('新标签页') && !env.$('btn-mode').classList.contains('same'),
   '按钮文字与高亮同步复位');
ok(!/undefined/.test(env.$('btn-mode')._html), '按钮文字无 undefined');
ok((env.$('btn-mode')._html.match(/<kbd>t<\/kbd>/g) || []).length <= 1,
   'kbd 徽标不会被重复追加', env.$('btn-mode')._html);

console.log('\n== 状态持久化（应对“缓存被清空”）==');
ok(env.replaceStateCalls.length > 0, '状态写入了 URL hash');
const lastHash = env.replaceStateCalls[env.replaceStateCalls.length - 1] || '';
ok(/m=\d+/.test(lastHash) && /t=tab/.test(lastHash), 'hash 含模块号与打开方式：' + lastHash);
ok(Object.keys(env.storage).length > 0, '同时也写入了 localStorage');
env.selectMod(7, true);
ok(/m=7/.test(env.replaceStateCalls[env.replaceStateCalls.length - 1]), '切换模块后 hash 同步更新');

// 存储被清空、只剩 URL hash
let e2 = makeEnv({ hash: '#m=33&t=same' });
let err = null;
try { e2.boot(); } catch (e) { err = e; }
ok(!err, '仅凭 URL hash 也能重新启动', err && err.message);
ok(e2.S() && e2.S().sel === 33, '从 hash 恢复了模块 33', e2.S() && e2.S().sel);
ok(e2.S() && e2.S().openMode === 'same', '从 hash 恢复了打开方式 same');

// localStorage 完好
let e3 = makeEnv({ storage: { 'csc-qref-v2': JSON.stringify({ sel: 12, openMode: 'same' }) } });
err = null;
try { e3.boot(); } catch (e) { err = e; }
ok(!err, 'localStorage 场景正常启动', err && err.message);
ok(e3.S() && e3.S().sel === 12, '从 localStorage 恢复了模块 12', e3.S() && e3.S().sel);

// 两者都没有
let e4 = makeEnv();
e4.boot();
ok(e4.S().sel === 1, '无任何存储时回到模块 1');

console.log('\n== 回归：原有功能未破坏 ==');
let bad = [];
for (let n = 1; n <= 50; n++) { try { e4.selectMod(n, true); } catch (e) { bad.push(n + ':' + e.message); } }
ok(bad.length === 0, '50 个模块全部可渲染', bad.join(','));
e4.renderPlats();
ok(e4.S().platList.length === DATA.platforms.length,
   '平台面板加载 ' + DATA.platforms.length + ' 个平台');
e4.search('cnki');
ok(e4.S().res.length > 0, '搜索仍有结果');
ok(e4.$('helpbody')._html.includes('<kbd>t</kbd>'), '帮助里已列出 t 键');
ok(e4.$('helpbody')._html.includes(String(DATA.platforms.length)), '帮助里平台数正确');
ok(e4.$('side')._html.length > 1000 && (e4.$('side')._html.match(/class="mod[" ]/g) || []).length === 50,
   '侧边栏仍列出 50 个模块');
ok(!/window\.open\s*\(/.test(code.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '')),
   '可执行代码中已无 window.open(');

console.log('\n' + (failed === 0 ? 'ALL CHECKS PASSED' : failed + ' CHECK(S) FAILED'));
process.exit(failed === 0 ? 0 : 1);

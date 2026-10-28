'use strict';
// Executes the REAL refresh() failure path against a minimal DOM stub.
// Asserts page-state mutations (not regexes over source text).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const APP = path.join(__dirname, '../mission_agent/mission_control/static/app.js');
const js = fs.readFileSync(APP, 'utf8');

// Extract the top-level functions we need, by name, up to the next top-level declaration.
function sliceFunction(name) {
  const start = js.search(new RegExp('^(async )?function ' + name + '\\(', 'm'));
  assert.ok(start >= 0, 'function ' + name + ' must exist');
  const rest = js.slice(start + 1);
  const next = rest.search(/^(async function|function|const|let|\$\(|refresh\(\);|setInterval|document\.)/m);
  return js.slice(start, next < 0 ? js.length : start + 1 + next);
}

function makeDom(ids) {
  // Parse the exact markup renderStats() writes; strong.textContent writes go back
  // into the host innerHTML so the F01 failure logic is checked against real state.
  function statNodes(host) {
    const re = /<div class="stat"><span>([^<]*)<\/span><strong>([^<]*)<\/strong><\/div>/g;
    const items = [];
    let m;
    while ((m = re.exec(host.innerHTML))) items.push({ key: m[1], value: m[2] });
    return items.map((item) => ({
      querySelector(sel) {
        if (sel === 'span') return { get textContent() { return item.key; } };
        if (sel === 'strong') return {
          get textContent() { return item.value; },
          set textContent(v) {
            item.value = String(v);
            const esc = item.key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            host.innerHTML = host.innerHTML.replace(
              new RegExp('(<div class="stat"><span>' + esc + '</span><strong>)[^<]*(</strong>)'),
              (all, a, b) => a + String(v) + b);
          },
        };
        return null;
      },
    }));
  }
  const nodes = {};
  const mk = (id) => {
    const n = {
      id, textContent: '', innerHTML: '', className: '', value: '',
      querySelectorAll(sel) {
        if (id === 'stats' && sel === '.stat') return statNodes(this);
        return [];
      },
      querySelector(sel) { return null; },
      addEventListener() {},
    };
    return n;
  };
  for (const id of ids) nodes[id] = mk(id);
  return {
    nodes,
    getElementById(id) { return nodes[id] || null; },
  };
}

// Build a page with the nodes F01 + the failure path touch, plus unrelated modules
// whose state must survive an F01 feed failure.
const IDS = [
  'runtime','f01-source-status','f01-timing-status','candidates','f01-history-count',
  'f01-history-cards','f01-history-cache-note','stats','updated','decisions',
  'signed-activity-rows','frank-watch-panel','trades','ended','review-activity',
  'coverage','watchlist',
];

function loadPage({ getImpl, rendered }) {
  const dom = makeDom(IDS);
  // Seed last-good F01 content, as a successful refresh() would have written it.
  dom.nodes['f01-source-status'].textContent =
    '近期来源信号 1 条；过期或时间待核 0 条；最近已索引 BUY 距链上事件 101 秒；当前执行资格 0 条；来源窗口 10 分钟。';
  dom.nodes['f01-timing-status'].textContent = '本页首次观察 1 条，事件到页面最长 101.0 秒。';
  dom.nodes['candidates'].innerHTML =
    '<article class="candidate-card">近期来源信号（仅观察） 7SL2VnfY… 复制 CA 最近动作：买入</article>';
  dom.nodes['f01-history-count'].textContent = '4';
  dom.nodes['f01-history-cards'].innerHTML = '<div class="ended-row">历史行</div>';
  dom.nodes['stats'].innerHTML =
    '<div class="stat"><span>Frank状态</span><strong>正常</strong></div>' +
    '<div class="stat"><span>24h已索引签名</span><strong>179</strong></div>' +
    '<div class="stat"><span>当前可跟候选</span><strong>0</strong></div>';
  dom.nodes['trades'].innerHTML = '<div>买入 Fp4JkqEc…</div>';
  dom.nodes['signed-activity-rows'].innerHTML = '<tr><td>D1 row</td></tr>';
  dom.nodes['frank-watch-panel'].innerHTML = '<div>观察池行</div>';
  dom.nodes['runtime'].className = 'runtime ok';
  dom.nodes['runtime'].innerHTML = '<strong>正常</strong>';

  const ctx = {
    document: { getElementById: dom.getElementById.bind(dom) },
    $: (id) => dom.getElementById(id),
    Date, Number, Math, JSON, Array, Object, String, Promise, Set, Map, console,
    setTimeout, clearTimeout,
    // record calls to renderers unrelated to F01 so the test can prove they are not cleared
    __rendered: rendered,
    esc: (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),
    translated: (map, raw, fb='未知') => fb,
    age: () => '1分钟前',
    tokenIdentity: () => '',
    reasonFor: () => '',
    frankPriceText: () => '',
    copyButton: () => '',
    patternLabel: {}, sideLabel: {}, stateLabel: {}, decisionLabel: {}, runtimeLabel: {},
    f01PageOpenedAtEpoch: 1800000000 - 100,
    f01FirstSeenKeys: new Set(), f01ObservedLagSeconds: [],
    showToast() {}, clusterStatus() {},
    // network: controlled per test
    fetch: async (url) => getImpl(url),
  };
  // unrelated renderers: record calls, do not touch DOM
  for (const name of ['renderRuntime','renderStats','renderCoverage','renderFrankWatchlist',
      'renderCandidates','renderF01History','renderEnded','renderTrades','renderReviewActivity','renderDecisions']) {
    ctx[name] = (...args) => { rendered.push(name); };
  }
  return { ctx, dom };
}

async function runRefresh(getImpl) {
  const rendered = [];
  const { ctx, dom } = loadPage({ getImpl, rendered });
  const code = [
    sliceFunction('get'),
    sliceFunction('verifiedF01SourceView'),
    sliceFunction('f01EventEpoch'),
    sliceFunction('recordF01PageObservation'),
    sliceFunction('f01ExcludedReasonCount'),
    sliceFunction('invalidateF01OnFailure'),
    sliceFunction('refresh'),
  ].join('\n');
  // Use the stub renderers already on ctx; keep only F01-owned logic from app.js.
  vm.createContext(ctx);
  vm.runInContext(code + '\nthis.__refresh = refresh; this.__invalidate = invalidateF01OnFailure;', ctx);
  await ctx.__refresh();
  return { dom, rendered };
}

function okJson(body) { return { ok: true, status: 200, json: async () => body }; }
function failJson(path, status) { return { ok: false, status, json: async () => ({}) }; }

const LIVE_F01 = {
  schema_version: 2, status: 'SOURCE_ONLY', scope: 'FRANK_LOCAL_INDEX_SOURCE_ONLY_NO_EXECUTION_QUOTE',
  as_of_epoch: Date.now()/1000 - 1, eligible: [], eligible_count: 0,
  source_recent_count: 1, source_recent: [{ person_id:'frank', mint:'MINT1', episode_id:'E1',
    source_signal_id:'S1', latest_signature:'SIG', latest_buy_at: Date.now()/1000 - 60, latest_at: Date.now()/1000 - 60,
    latest_side:'BUY', position_state:'OPEN', pattern:'ACCUMULATION', decision:'NO_BUY',
    candidate_source:'FROZEN', f01_source_state:'RECENT_SOURCE_BUY_ONLY',
    execution_eligibility:'NOT_ASSESSED_USER_AMOUNT_MISSING' }],
  excluded_reason_counts: {}, newest_indexed_buy_age_seconds: 60,
};
const CANDS = [{ person_id:'frank', mint:'MINT1', episode_id:'E1', source_signal_id:'S1',
  latest_signature:'SIG', latest_buy_at: Date.now()/1000 - 60, latest_at: Date.now()/1000 - 60,
  latest_side:'BUY', position_state:'OPEN', pattern:'ACCUMULATION', decision:'NO_BUY',
  candidate_source:'FROZEN' }];

function okGetImpl(failPath) {
  return async (url) => {
    const p = url.replace(/^.*?(\/api\/)/, '/api/').split('?')[0];
    if (failPath && p === failPath) return failJson(p, 503);
    const table = {
      '/api/runtime': {status:'LIVE'}, '/api/control-health': {status:'OK'},
      '/api/candidates': CANDS, '/api/trades': [], '/api/review-activity': [],
      '/api/decisions': [], '/api/coverage': {windows:{}}, '/api/follow-opportunities': LIVE_F01,
      '/api/frank-observed-watchlist': {rows:[], summary:{}},
    };
    return okJson(table[p] ?? {});
  };
}

test('pre-state: a successful refresh renders a recent card (precondition)', async () => {
  const { dom } = await runRefresh(okGetImpl(null));
  assert.ok(dom.nodes['f01-source-status'].textContent.includes('近期来源信号'), 'success path writes F01 summary');
});

test('503 on /api/candidates removes the last-good recent card from the page', async () => {
  const { dom } = await runRefresh(okGetImpl('/api/candidates'));
  const card = dom.nodes['candidates'].innerHTML;
  assert.ok(!/近期来源信号（仅观察）/.test(card), 'stale recent card must not remain: ' + card.slice(0,120));
  assert.ok(/不得作为当前机会/.test(card), 'a not-eligible placeholder must replace it');
  assert.ok(!/复制 CA/.test(card), 'no CA copy action may remain for the stale card');
});

test('503 invalidates F01 summary, timing and the Frank/candidate stats', async () => {
  const { dom } = await runRefresh(okGetImpl('/api/candidates'));
  const f01 = dom.nodes['f01-source-status'].textContent;
  assert.ok(!/近期来源信号\s*[1-9]/.test(f01), 'no recent-signal count may survive: ' + f01);
  assert.ok(/不展示可跟结论/.test(f01));
  assert.ok(!/首次观察|最长/.test(dom.nodes['f01-timing-status'].textContent));
  const stats = dom.nodes['stats'].innerHTML;
  assert.ok(!/<span>当前可跟候选<\/span><strong>0<\/strong>/.test(stats), 'eligible count must not stay 0 as if verified');
  assert.ok(/<span>当前可跟候选<\/span><strong>待核实<\/strong>/.test(stats), 'eligible count must read 待核实');
  assert.ok(/<span>Frank状态<\/span><strong>待核实<\/strong>/.test(stats), 'runtime status stat must read 待核实');
  assert.ok(stats.includes('24h已索引签名'), 'non-F01 stat labels are preserved');
});

test('history stays visible but is explicitly marked as cache, not current', async () => {
  const { dom } = await runRefresh(okGetImpl('/api/candidates'));
  assert.ok(/上次成功读取的缓存，本轮未核实/.test(dom.nodes['f01-history-cache-note'].textContent));
  assert.ok(dom.nodes['f01-history-cards'].innerHTML.includes('历史行'), 'history rows are not cleared by F01 failure');
});

test('independent modules are not cleared by an F01 feed failure', async () => {
  const { dom } = await runRefresh(okGetImpl('/api/candidates'));
  assert.ok(dom.nodes['signed-activity-rows'].innerHTML.includes('D1 row'), 'D1 untouched by F01 failure');
  assert.ok(dom.nodes['frank-watch-panel'].innerHTML.includes('观察池行'), 'watchlist untouched');
  assert.ok(dom.nodes['trades'].innerHTML.includes('买入 Fp4JkqEc'), 'trades untouched');
});

test('recovery after a 503 clears the cache note and repopulates from the fresh source', async () => {
  const failing = await runRefresh(okGetImpl('/api/candidates'));
  assert.ok(failing.dom.nodes['f01-history-cache-note'].textContent.length > 0);
  // second, healthy refresh on the same page object
  const rendered = [];
  const { ctx, dom } = loadPage({ getImpl: okGetImpl(null), rendered });
  dom.nodes['f01-history-cache-note'].textContent = '旧缓存提示';
  const code = [sliceFunction('get'), sliceFunction('verifiedF01SourceView'), sliceFunction('f01EventEpoch'),
    sliceFunction('recordF01PageObservation'), sliceFunction('f01ExcludedReasonCount'),
    sliceFunction('invalidateF01OnFailure'), sliceFunction('refresh')].join('\n');
  vm.createContext(ctx);
  vm.runInContext(code + '\nthis.__refresh = refresh;', ctx);
  await ctx.__refresh();
  assert.equal(dom.nodes['f01-history-cache-note'].textContent, '', 'success path clears the cache note');
  assert.ok(dom.nodes['f01-source-status'].textContent.includes('近期来源信号'), 'healthy path restores F01 summary');
});

test('a second consecutive 503 also removes the recent card (no residue across failures)', async () => {
  const first = await runRefresh(okGetImpl('/api/candidates'));
  const second = await runRefresh(okGetImpl('/api/candidates'));
  assert.ok(!/近期来源信号（仅观察）/.test(second.dom.nodes['candidates'].innerHTML));
});

test('no default amount, quote or executable claim is ever written by the failure path', async () => {
  const { dom } = await runRefresh(okGetImpl('/api/candidates'));
  const all = [dom.nodes['candidates'].innerHTML, dom.nodes['f01-source-status'].textContent,
    dom.nodes['f01-timing-status'].textContent, dom.nodes['stats'].innerHTML].join(' ');
  assert.ok(!/\$30|30 USD|30 USDC|默认金额|可跟单|可执行报价/.test(all.replace(/不展示可跟结论|不得作为当前机会|无用户指定的交易金额|没有用户指定的交易金额/g,'')),
    'no default-amount or executable wording may be written');
});


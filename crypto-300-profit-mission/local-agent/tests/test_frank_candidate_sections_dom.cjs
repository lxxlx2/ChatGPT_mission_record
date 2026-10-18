'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const dir = path.resolve(__dirname, '../mission_agent/mission_control/static');
const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
const app = fs.readFileSync(path.join(dir, 'app.js'), 'utf8');
const helper = fs.readFileSync(path.join(dir, 'frank_candidate_sections.js'), 'utf8');

const helperAt = html.indexOf('<script src="/static/frank_candidate_sections.js"></script>');
const appAt = html.indexOf('<script src="/static/app.js"></script>');
const f01At = html.indexOf('<script src="/static/frank_f01_primary_freshness.js"></script>');
assert(helperAt >= 0 && appAt > helperAt && f01At > appAt);
assert(html.includes('id="archived-candidates-panel" hidden'));
assert(html.includes('WAIT / NO_BUY 不是买入信号'));
assert(html.includes('当前跟单机会'));
assert(html.includes('id="archived-candidates-count"'));

function slice(start, end) {
  const a = app.indexOf(start);
  const b = app.indexOf(end, a + start.length);
  assert(a >= 0 && b > a, 'source integration function missing');
  return app.slice(a, b);
}

const elements = {
  candidates: {innerHTML:''},
  'archived-candidates-panel': {hidden: true},
  'archived-candidates-count': {textContent: ''},
  'archived-candidates': {innerHTML:''},
};
const context = {
  Date,
  $: id => elements[id],
  esc: x => String(x ?? ''),
  translated: (dict, key, fallback) => dict[key] || key || fallback,
  decisionLabel: {BUY:'可跟', SMALL_BUY:'小仓跟', WAIT:'等待', NO_BUY:'不跟', UNASSESSED:'未评估'},
  patternLabel: {REENTRY_WATCH:'重新建仓观察', MULTIPLE:'强建仓', ACCUMULATION:'持续建仓'},
  stateLabel: {OPEN:'模型持有', CLOSED:'模型退出', INVENTORY_UNDETERMINED:'仓位不明'},
  sideLabel: {BUY:'买入', SELL:'卖出', REENTRY:'重新建仓'},
  badge: (key) => String(key),
  age: () => '历史时间',
  reasonFor: () => '不能跟单',
  tokenIdentity: x => 'CA:' + x,
  copyButton: () => '',
  researchLinks: () => '',
  metric: (title, value) => title + ':' + value,
  n: value => String(value),
  money: value => String(value),
  frankQuote: () => '历史支付',
  frankPriceText: () => '历史参考价',
  quoteUnavailableText: () => '无实时报价',
};
vm.createContext(context);
vm.runInContext(helper, context);
vm.runInContext(slice('function renderCandidates(rows) {', 'function withinHours(ts,hours) {'), context);
const split = context.FrankCandidateSections.split;
const now = Date.now() / 1000;
const date = seconds => new Date(seconds * 1000).toISOString();
const basis = {
  mint: 'A'.repeat(32), person_id: 'frank', pattern:'ACCUMULATION',
  position_state:'OPEN', latest_side:'BUY', latest_at: now - 4,
  latest_buy_at: now - 4, decision_created_at: date(now - 3), decision: 'BUY',
  quote_observed_at: date(now - 2), buy_count: 2, sell_count: 0,
  metrics: {}, decision_quote: {
    status:'OK', route_exists:true,
    execution_price_usdc:'12.34', price_impact_pct:'0.21'
  }
};
const four = [
  {...basis, decision:'NO_BUY', position_state:'CLOSED', latest_side:'SELL'},
  {...basis, decision:'NO_BUY', position_state:'CLOSED', latest_side:'SELL'},
  {...basis, decision:'NO_BUY', position_state:'INVENTORY_UNDETERMINED', latest_side:'SELL'},
  {...basis, decision:'WAIT', pattern:'REENTRY_WATCH', latest_buy_at:now-164310,
    decision_created_at:date(now-113541)}
];
const p = split(four, now);
assert.equal(p.current.length, 0);
assert.equal(p.archived.length, 4);
context.renderCandidates(p.current);
context.renderArchivedCandidates(p.archived);
assert(elements.candidates.innerHTML.includes('当前没有需要跟踪的 Frank 候选'));
assert.equal(elements['archived-candidates-panel'].hidden, false);
assert.equal(elements['archived-candidates-count'].textContent, '4');
assert(elements['archived-candidates'].innerHTML.includes('历史判断'));
assert(!elements['archived-candidates'].innerHTML.includes('12.34'));

context.renderCandidates([basis]);
assert(elements.candidates.innerHTML.includes('12.34'));
context.renderCandidates([{...basis, quote_observed_at:date(now-120)}]);
assert(elements.candidates.innerHTML.includes('报价已过期，不代表当前成交条件'));
assert(!elements.candidates.innerHTML.includes('12.34'));
vm.runInContext('delete globalThis.FrankCandidateSections', context);
context.renderCandidates([basis]);
assert(elements.candidates.innerHTML.includes('报价已过期，不代表当前成交条件'));

console.log('FRANK_CANDIDATE_SECTIONS_DOM_INTEGRATION_PASS');

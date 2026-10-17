'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync(
  'mission_agent/mission_control/static/index.html', 'utf8'
);
assert.match(html, /<script src="\/static\/app\.js"><\/script>\s*<script src="\/static\/frank_f01_primary_freshness\.js"><\/script>\s*<script src="\/static\/frank_source_context\.js"><\/script>/);
assert.match(html, /href="\/static\/frank_source_context\.css"/);
assert.equal((html.match(/data-view="signals"/g) || []).length, 1);
assert.equal((html.match(/data-view="cluster"/g) || []).length, 1);
assert.equal((html.match(/class="view-tab"/g) || []).length, 1);

const src = fs.readFileSync(
  'mission_agent/mission_control/static/frank_source_context.js', 'utf8'
);
const MINT = 'So11111111111111111111111111111111111111112';
const REVIEW = 'F01_SIGNAL_VS_ARCHIVED_WALLET_REQUIRES_REVIEW';
const current = {
  schema_version: 1, kind: 'FRANK_CURRENT_F01_WITH_A05_RESEARCH_CONTEXT',
  upstream: {f01: 'SOURCE_READ'},
  candidate_count: 1, combined_trade_permission: false,
  archive_is_live_wallet_portfolio: false,
  f01_valid_until_epoch: Date.now() / 1000 + 6,
  candidates: [{
    mint: MINT, person_id: 'frank', source_signal_id: 'signal-1',
    f01_decision: 'BUY', wallet_observation_state: 'OPEN_ACCOUNT_ZERO',
    observed_quantity: '0.000000', review_required_reason: REVIEW,
    archived_source_only: true, current_wallet_position_verified: false,
    historical_sale_confirmed: false, may_trade_based_on_combination: false,
    observation_at_utc: '2026-10-17T00:00:00Z'
  }]
};
let pane = null;
let mutationNotify = null;
const calls = [];
const timers = [];
let visible = [MINT];
const cardContainer = {
  insertAdjacentElement(where, el) {
    assert.equal(where, 'afterend');
    pane = el;
  },
  querySelectorAll(selector) {
    assert.equal(selector, '.candidate-card');
    return visible.map(mint => ({
      querySelector: (selector) => selector === '.ca-full'
        ? {textContent:mint} : null,
      dataset: {
        f01SourceSignalId: 'signal-1',
        f01Decision: 'BUY',
        f01GuardState: 'VERIFIED'
      }
    }));
  }
};
class Observer {
  constructor(callback) { mutationNotify = callback; }
  observe(element, options) {
    assert.equal(element, cardContainer);
    assert.equal(options.childList, true);
  }
}
const fakeDocument = {
  getElementById(id) {
    if (id === 'follow-opportunities') return {};
    if (id === 'candidates') return cardContainer;
    return null;
  },
  createElement(tag) {
    assert.equal(tag, 'section');
    return {id: '', className: '', innerHTML: '',
            setAttribute: () => {}};
  }
};
const scope = {
  console, document: fakeDocument, MutationObserver: Observer,
  clearTimeout: () => {},
  setTimeout: (fn) => { timers.push(fn); return timers.length; },
  fetch: (url, options) => {
    calls.push({url, options});
    return Promise.resolve({ok:true,json:()=>Promise.resolve(current)});
  }
};
vm.runInNewContext(src, scope, {filename: 'frank_source_context.js'});

(async () => {
  await new Promise(setImmediate);
  assert.ok(pane, 'formal F01 pane must mount after candidates');
  assert.match(pane.innerHTML, /需要复核/);
  assert.match(pane.innerHTML, /0\.000000/);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, '/api/research/current-follow-context');
  assert.equal(calls[0].options.method, 'GET');
  assert.equal(calls[0].options.cache, 'no-store');
  assert.equal(timers.length, 1);
  current.f01_valid_until_epoch = Date.now() / 1000 - 1;
  timers[0]();
  assert.match(pane.innerHTML, /资格已过期/);
  assert.doesNotMatch(pane.innerHTML, /0\.000000/);
  current.f01_valid_until_epoch = Date.now() / 1000 + 6;

  visible = [];
  mutationNotify();
  await new Promise(setImmediate);
  assert.match(pane.innerHTML, /尚未匹配/);
  assert.equal(calls.length, 2);

  visible = [MINT];
  current.f01_valid_until_epoch = Date.now() / 1000 - 1;
  mutationNotify();
  await new Promise(setImmediate);
  assert.match(pane.innerHTML, /资格已过期/);
  assert.doesNotMatch(pane.innerHTML, /0\.000000/);
  assert.equal(calls.length, 3);
  assert.equal(calls.some(x=>x.options.method !== 'GET'), false);
  console.log('FRANK_SOURCE_CONTEXT_MOUNT_PASS: existing formal F01 tab, expiry, no extra poll');
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

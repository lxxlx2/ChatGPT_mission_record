import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const script = fs.readFileSync(new URL(
  '../mission_agent/mission_control/static/frank_risk_and_quote.js', import.meta.url), 'utf8');
const mint = '3'.repeat(43);
const input = '4'.repeat(43);
const time = 1795000000;
const manifest = 'b'.repeat(32);
const run = 'a'.repeat(32);
const hash = 'a'.repeat(64);
const settle = () => new Promise(r => setImmediate(r));

function browser(backend) {
  const elements = new Map();
  const calls = [];
  const timers = new Map();
  let next = 0;
  let now = time;
  function element() {
    const handlers = new Map();
    return {
      value: '', textContent: '', children: [], disabled: false, hidden: false,
      addEventListener(name, call) { handlers.set(name, call); },
      appendChild(child) { this.children.push(child); },
      replaceChildren(...children) { this.children = children; },
      dispatch(name) { handlers.get(name)?.(); },
      click() { if (!this.disabled) this.dispatch('click'); },
    };
  }
  function get(key) {
    if (!elements.has(key)) elements.set(key, element());
    return elements.get(key);
  }
  vm.runInNewContext(script, {
    document: {getElementById: get, createElement: element, addEventListener() {}},
    URLSearchParams, AbortController, Intl,
    Date: class extends Date { static now() { return now * 1000; } },
    crypto: {randomUUID: () => 'request-'+ ++next},
    setTimeout(callback, ms) { timers.set(++next, {callback, at: now+ms/1000}); return next; },
    clearTimeout(id) { timers.delete(id); },
    fetch: async (path, options) => {
      calls.push({path, options});
      const response = await backend(path, options);
      return {ok: !response.error, status: response.error ? 503 : 200, json: async () => response};
    },
  });
  return {
    calls, r: name => get('frank-risk-'+name), q: name => get('frank-quote-'+name), get,
    advance(seconds) {
      now += seconds;
      for (const [id, timer] of [...timers]) if (timer.at <= now) {
        timers.delete(id);
        timer.callback();
      }
    },
  };
}

test('quote requires a manually entered raw amount and expires without a new request', async () => {
  const b = browser((path, options) => {
    assert.equal(path, '/api/frank-quote');
    const body = JSON.parse(options.body);
    assert.deepEqual(body, {mint, input_mint: input, input_amount_raw: '271', slippage_bps: 48});
    return {status: 'OK', quote_id: hash, input: body, input_mint: input,
      output_mint: mint, in_amount_raw: '271', out_amount_raw: '912', other_amount_threshold_raw: '900',
      slippage_bps: 48, price_impact_pct: '0.2', observed_at: time, expires_at: time+30,
      route_plan: [{amm_key: input, input_mint: input, output_mint: mint,
        in_amount_raw: '271', out_amount_raw: '912'}], route_exists: true,
      source_ref: {source: 'JUPITER_OFFICIAL', request_sha256: hash, response_sha256: hash}};
  });
  b.q('mint').value = mint;
  b.q('input-mint').value = input;
  b.q('slippage').value = '48';
  b.q('read').click();
  assert.equal(b.calls.length, 0);
  b.q('amount').value = '271';
  b.q('read').click();
  await settle();
  assert.match(b.q('status').textContent, /当前路由参考/);
  assert.equal(b.q('details').children.length, 3);
  b.advance(30);
  assert.match(b.q('status').textContent, /已过期/);
  assert.equal(b.q('details').children.length, 0);
  assert.equal(b.calls.length, 1);
});

test('risk reading remains read-only and failed refresh reuses the same key', async () => {
  let posted = 0;
  const b = browser((path, opts) => {
    if (opts.method === 'GET') return {status: 'OK', rows: [], total_matching: 0, returned: 0, next_cursor: null};
    if (!posted++) return {error: 'PRIVATE_UPSTREAM_DIAGNOSTICS'};
    return {state: 'COMPLETE', run_id: run, as_of: time, created_at: time, rows_count: 4,
      created_updates: 1, deduped_updates: 1, source_refs: {fact_manifest_id: manifest, fact_as_of: time-5}};
  });
  assert.equal(b.calls.length, 0);
  b.r('read-updates').click();
  await settle();
  assert.equal(b.calls[0].options.headers['X-Frank-Research-Read'], '1');
  assert.equal(b.calls[0].options.method, 'GET');
  b.r('manifest').value = manifest;
  b.r('refresh').click();
  await settle();
  assert.doesNotMatch(b.r('run-status').textContent, /PRIVATE_UPSTREAM/);
  b.r('refresh').click();
  await settle();
  assert.equal(b.calls[1].options.body, b.calls[2].options.body);
  assert.equal(b.r('run').value, run);
  assert.match(b.r('run-status').textContent, /新增 1 条/);
  assert.ok(b.calls.every(call => !call.path.includes('frank-quote')));
});

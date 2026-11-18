import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const code = fs.readFileSync(new URL(
  '../mission_agent/mission_control/static/frank_wallet_cost.js', import.meta.url), 'utf8');
const run = 'a'.repeat(32);
const otherRun = 'b'.repeat(32);
const manifest = 'c'.repeat(32);
const mint = '4'.repeat(43);
const otherMint = '5'.repeat(43);
const at = 1795000000;
const money = (denomination, raw_numerator, raw_denominator = '1', decimals = 6) =>
  ({denomination, raw_numerator, raw_denominator, decimals});

class Element {
  constructor(tag) {
    this.tag = tag;
    this.value = '';
    this.disabled = false;
    this.hidden = false;
    this.open = false;
    this.contents = '';
    this.children = [];
    this.handlers = new Map();
  }
  set textContent(value) { this.contents = value; this.children = []; }
  get textContent() { return [this.contents, ...this.children.map(x => x.textContent)].join('\n'); }
  appendChild(child) { this.children.push(child); }
  replaceChildren(...children) { this.contents = ''; this.children = children; }
  addEventListener(event, listener) { this.handlers.set(event, listener); }
  removeEventListener(event, listener) {
    if (this.handlers.get(event) === listener) this.handlers.delete(event);
  }
  dispatch(event) { this.handlers.get(event)?.(); }
  click() { if (!this.disabled) this.dispatch('click'); }
}

const settle = () => new Promise(resolve => setImmediate(resolve));
function browser(backend) {
  const elements = new Map();
  const calls = [];
  let keys = 0;
  const get = id => {
    if (!elements.has(id)) elements.set(id, new Element('existing'));
    return elements.get(id);
  };
  const e = name => get('frank-cost-' + name);
  vm.runInNewContext(code, {
    document: {getElementById: get, createElement: tag => new Element(tag)},
    fetch: async (url, options) => {
      const request = new URL(url, 'http://127.0.0.1:8766');
      calls.push({request, options});
      const result = await backend(request, options);
      if (result?.httpStatus) return {ok: false, status: result.httpStatus};
      return {ok: true, json: async () => result};
    },
    AbortController, URLSearchParams, crypto: {randomUUID: () => 'key-' + (++keys)},
    setTimeout: () => 1, clearTimeout: () => {},
  });
  return {e, get, calls};
}

function asset(id = mint) {
  return {
    mint: id, decimals: 6, quantity_raw: '18446744073709551615000001',
    known_cost_quantity_raw: '6000000', unknown_cost_quantity_raw: '18446744073709551609000001',
    remaining_costs: [money('USDC', '4500001', '3')],
    realized_summary: {covered_quantity_raw: '2000000', sold_quantity_raw: '4000000',
      partial_pnl: [money('USDC', '3265000'), money('WSOL', '-10000000', '1', 9)], pnl: null},
    valuation: {status: 'PRICED', source: 'DEXSCREENER_API', observed_at: at - 10,
      expires_at: at + 50, price_usd: '0.25', value_usd: '6.01'},
    covered_unrealized_pnl: null, unrealized_pnl: null,
    lots: [{lot_id: 'a', quantity_raw: '10000000', remaining_quantity_raw: '6000000',
      costs: [money('USDC', '1234567')], remaining_costs: [money('USDC', '4500001', '3')]}],
    movements: [],
  };
}
function basis(rows = [asset()], overrides = {}) {
  return {
    run_id: run, manifest_id: manifest, as_of: at - 100, created_at: at,
    rows, total_matching: rows.length, returned: rows.length, next_cursor: null,
    fees: {network_fee_lamports: '5000', network_fee_unknown_transactions: 3,
      initial_funding_paid_lamports: '2039280', rent_paid_lamports: null, rent_refunded_lamports: null},
    valuation: {as_of: at, max_age_seconds: 60, covered_positions: 1, unpriced_mints: [otherMint],
      partial_value_usd: '6.01', full_wallet_value_usd: null},
    ...overrides,
  };
}

test('explicit rebuild reuses selected facts and reads the resulting fixed run', async () => {
  const b = browser((_, options) => options.method === 'POST'
    ? {state: 'COMPLETE', run_id: run, manifest_id: manifest} : basis());
  assert.equal(b.calls.length, 0);
  b.e('rebuild').click();
  assert.equal(b.calls.length, 0);
  assert.match(b.e('status').textContent, /完整的事实快照 ID/);

  b.get('frank-manifest-id').value = manifest;
  b.e('use-manifest').click();
  assert.equal(b.e('manifest').value, manifest);
  assert.equal(b.calls.length, 0);
  b.e('rebuild').click();
  await settle();
  assert.equal(b.calls.length, 2);
  assert.equal(b.calls[0].request.pathname, '/api/frank-cost-rebuild');
  assert.deepEqual(JSON.parse(b.calls[0].options.body), {input_manifest_id: manifest, idempotency_key: 'key-1'});
  assert.equal(b.calls[1].request.pathname, '/api/frank-cost-basis');
  assert.equal(b.calls[1].request.searchParams.get('run_id'), run);
  assert.equal(b.calls[1].options.headers['X-Frank-Research-Read'], '1');
  assert.equal(b.e('table').hidden, false);
});

test('fixed pagination pins the actual run and transports the opaque cursor once', async () => {
  const opaque = 'a+/= &?b';
  const b = browser(req => req.searchParams.has('cursor')
    ? basis([asset(otherMint)], {total_matching: 2})
    : basis([asset()], {total_matching: 2, next_cursor: opaque}));
  b.e('read').click();
  await settle();
  assert.equal(b.calls[0].request.searchParams.has('run_id'), false);
  assert.equal(b.e('run').value, run);
  assert.equal(b.e('next').disabled, false);
  b.e('next').click();
  await settle();
  assert.equal(b.calls[1].request.searchParams.get('run_id'), run);
  assert.equal(b.calls[1].request.searchParams.get('cursor'), opaque);
  assert.equal(b.e('next').disabled, true);
  assert.match(b.e('rows').textContent, new RegExp(otherMint));
});

test('large exact quantities, original currencies and unknown total are visible separately', async () => {
  const b = browser(() => basis());
  b.e('read').click();
  await settle();

  const text = b.e('rows').textContent;
  assert.match(text, /索引余额 18446744073709551615\.000001/);
  assert.match(text, /4500001\/3 × 10\^-6 USDC/);
  assert.match(text, /覆盖部分 3\.265 USDC · -0\.01 WSOL/);
  assert.match(text, /全部卖出盈亏 未知/);
  assert.match(text, /整仓未实现盈亏 未知/);
  assert.match(text, /DexScreener · 观测于/);
  assert.match(text, /有效期至/);
  const summary = b.e('summary').textContent;
  assert.match(summary, /已核实初始注资 0\.00203928 SOL · 已核实租金支出 未知/);
  assert.match(summary, /已估值部分 6\.01 USD · 整钱包价值 未知/);

  const row = b.e('rows').children[0];
  const lots = row.children[5].children[0];
  assert.doesNotMatch(lots.textContent, /1\.234567 USDC/);
  lots.open = true;
  lots.dispatch('toggle');
  assert.match(lots.textContent, /1\.234567 USDC/);
});

test('unpriced balance keeps stale reason and unknown value even if backend subtotal is zero', async () => {
  const unpriced = {...asset(), valuation: {status: 'UNPRICED', reason: 'STALE_OBSERVATION', value_usd: '0'}};
  const b = browser(() => basis([unpriced], {valuation: {covered_positions: 0, unpriced_mints: [mint],
    partial_value_usd: '0', full_wallet_value_usd: null}}));
  b.e('read').click();
  await settle();
  assert.match(b.e('rows').textContent, /参考估值未知 · 已捕获的报价过期/);
  assert.match(b.e('summary').textContent, /已估值部分 未知 · 整钱包价值 未知/);
  assert.doesNotMatch(b.e('summary').textContent, /0 USD/);
});

test('editing a filter aborts an old read and fences a delayed result', async () => {
  let release;
  const b = browser(req => req.searchParams.has('mint') ? basis([asset(otherMint)]) :
    new Promise(resolve => { release = resolve; }));
  b.e('read').click();
  b.e('mint').value = otherMint;
  b.e('mint').dispatch('input');
  assert.equal(b.calls[0].options.signal.aborted, true);
  b.e('read').click();
  await settle();
  release(basis([asset()]));
  await settle();
  assert.equal(b.calls[1].request.searchParams.get('mint'), otherMint);
  assert.match(b.e('rows').textContent, new RegExp(otherMint));
  assert.doesNotMatch(b.e('rows').textContent, new RegExp(mint));
});

test('uncertain rebuild retries the same key and hides transport error details', async () => {
  let builds = 0;
  const b = browser((_, options) => {
    if (options.method === 'POST' && !builds++) throw new Error('PRIVATE_RPC_URL');
    return options.method === 'POST' ? {state: 'COMPLETE', run_id: run, manifest_id: manifest} : basis();
  });
  b.e('manifest').value = manifest;
  b.e('rebuild').click();
  await settle();
  assert.match(b.e('status').textContent, /尚未确认/);
  assert.doesNotMatch(b.e('status').textContent, /PRIVATE_RPC_URL/);
  b.e('rebuild').click();
  await settle();
  assert.equal(b.calls[0].options.body, b.calls[1].options.body);
  assert.equal(b.calls[2].request.searchParams.get('run_id'), run);
});

test('view rejects a different response run or mint after explicit selection', async () => {
  const b = browser(() => basis([asset()], {run_id: otherRun}));
  b.e('run').value = run;
  b.e('mint').value = otherMint;
  b.e('read').click();
  await settle();
  assert.match(b.e('status').textContent, /无法核实/);
  assert.equal(b.e('run').value, run);
  assert.equal(b.e('table').hidden, true);
  assert.equal(b.e('next').disabled, true);
});


import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const script = fs.readFileSync(new URL(
  '../mission_agent/mission_control/static/frank_history_coverage.js', import.meta.url,
), 'utf8');
const endAt = 1_795_033_108;

function payload(days = 'all') {
  return {
    schema_version: 1,
    status: 'PARTIAL_SOURCE',
    as_of: endAt,
    data: {
      person_id: 'frank',
      days,
      start_at: days === 'all' ? null : endAt - days * 86400,
      end_at: endAt,
      indexed_oldest_at: endAt - 1000,
      indexed_newest_at: endAt - 100,
      scanner_observed_at: null,
      indexed_signatures: days === 'all' ? 1204 : 1200,
      timed_signatures: 1200,
      untimed_signatures: days === 'all' ? 4 : 0,
      untimed_source_signatures: 4,
      parser_unresolved_signatures: days === 'all' ? 16 : 12,
      pending_detected_signatures: null,
      categories: {
        ACTIVE_TRADE: 1120,
        PASSIVE_TRANSFER: 30,
        FAILED_TX: 18,
        ATA_CREATE: 20,
        UNKNOWN_NEEDS_REVIEW: 9,
        OTHER_OR_UNKNOWN: days === 'all' ? 7 : 3,
      },
    },
    coverage: {full_chain_verified: false, known_gaps: null, backfill_status: 'UNKNOWN', stop_reason: 'UNKNOWN'},
  };
}

function browser(fetcher) {
  function node() {
    return {
      value: '', textContent: '', disabled: false, children: [], events: new Map(),
      addEventListener(name, listener) { this.events.set(name, listener); },
      dispatch(name) { return this.events.get(name)?.(); },
      click() { if (!this.disabled) return this.dispatch('click'); },
      replaceChildren(...children) { this.children = children; },
      set innerHTML(_) { assert.fail('History coverage must render plain text'); },
    };
  }
  const elements = new Map(['window', 'read', 'status', 'detail'].map(name => ['frank-coverage-' + name, node()]));
  const get = name => elements.get('frank-coverage-' + name);
  const calls = [];
  get('window').value = 'all';
  get('status').textContent = '尚未读取';
  vm.runInNewContext(script, {
    document: {getElementById: id => elements.get(id), createElement: () => node()},
    fetch: async (path, options) => {
      calls.push({path, options});
      return fetcher(path, options);
    },
    AbortController, setTimeout, clearTimeout,
  });
  return {
    calls,
    get,
    lines: () => get('detail').children.map(paragraph => paragraph.textContent).join('\n'),
    select(days) { get('window').value = days; get('window').dispatch('change'); },
  };
}

const response = body => ({ok: true, json: async () => body});

test('only a click reads each supported local window and preserves the read gate', async () => {
  const page = browser(path => {
    const days = path.split('=')[1];
    return response(payload(days === 'all' ? days : Number(days)));
  });
  assert.equal(page.get('status').textContent, '尚未读取');
  for (const [i, days] of ['all', '1', '7', '30'].entries()) {
    page.select(days);
    assert.equal(page.calls.length, i);
    assert.equal(page.lines(), '');
    await page.get('read').click();
    assert.match(page.lines(), days === 'all' ? /全部本机记录/ : new RegExp(`最近 ${days} 天`));
    assert.match(page.lines(), days === 'all' ? /已计入 4 条无区块时间/ : /4 条本机签名缺少区块时间，无法归入本窗口/);
    assert.match(page.lines(), /主动交易 1,120 条.*失败交易 18 条.*创建关联代币账户（ATA） 20 条/);
    assert.match(page.lines(), days === 'all' ? /解析仍待核实 16 条/ : /解析仍待核实 12 条/);
    assert.match(page.lines(), /本窗口已检测但尚未入索引 未知/);
    assert.match(page.lines(), /历史缺口 未知 · 历史回补状态未知/);
    assert.match(page.get('status').textContent, /全链覆盖未核实/);
    const {path, options} = page.calls[i];
    assert.equal(path, '/api/frank-coverage?days=' + days);
    assert.equal(options.method, 'GET');
    assert.equal(options.cache, 'no-store');
    assert.equal(options.credentials, 'same-origin');
    assert.equal(options.headers['X-Frank-Research-Read'], '1');
    assert.equal(options.body, undefined);
  }
});

test('recorded gaps and window pending counts are shown using fixed labels', async () => {
  const result = payload(7);
  result.coverage.known_gaps = ['CURSOR_GAP_UNRESOLVED', 'DETECTED_SIGNATURES_NOT_INDEXED', '<script>secret()</script>'];
  result.coverage.stop_reason = 'CURSOR_GAP_UNRESOLVED';
  result.data.scanner_observed_at = endAt - 100;
  result.data.pending_detected_signatures = 8;
  const page = browser(() => response(result));
  page.select('7');
  await page.get('read').click();
  assert.match(page.lines(), /本窗口已检测但尚未入索引 8 条/);
  assert.match(page.lines(), /已记录历史游标缺口，尚未解决；有已检测但尚未入索引的签名/);
  assert.match(page.lines(), /最近一次成功扫描记录 (?!未知).*最近记录的停止原因 扫描时未能找到已保存的历史游标/);
  result.coverage.stop_reason = '<img onerror="secret()">';
  await page.get('read').click();
  assert.match(page.lines(), /最近记录的停止原因 未知/);
  assert.doesNotMatch(page.lines(), /secret|<img|<script/);
});

test('late response cannot repaint the selected window after a newer reply', async () => {
  let finishOld;
  const page = browser(path => path.endsWith('all') ?
    new Promise(resolve => { finishOld = resolve; }) : response(payload(7)));
  const old = page.get('read').click();
  assert.equal(page.get('read').disabled, true);
  page.get('read').click();
  assert.equal(page.calls.length, 1);
  page.select('7');
  assert.equal(page.calls[0].options.signal.aborted, true);
  assert.equal(page.get('read').disabled, false);
  assert.equal(page.lines(), '');
  assert.match(page.get('status').textContent, /时间范围已改变/);
  await page.get('read').click();
  finishOld(response(payload()));
  await old;
  assert.equal(page.get('read').disabled, false);
  assert.match(page.lines(), /最近 7 天/);
  assert.doesNotMatch(page.lines(), /全部本机记录/);
});

test('valid zero is shown as a local count while unavailable and malformed replies clear it', async () => {
  const empty = payload('all');
  Object.assign(empty.data, {
    indexed_signatures: 0, timed_signatures: 0, untimed_signatures: 0, untimed_source_signatures: 0,
    parser_unresolved_signatures: 0, indexed_oldest_at: null, indexed_newest_at: null, pending_detected_signatures: 0,
  });
  for (const key of Object.keys(empty.data.categories)) empty.data.categories[key] = 0;
  let reply = response(empty);
  const page = browser(() => reply);
  await page.get('read').click();
  assert.match(page.lines(), /已索引 0 条签名/);
  assert.match(page.lines(), /已索引记录时间 未知/);
  assert.match(page.lines(), /本窗口已检测但尚未入索引 0 条/);
  for (const badReply of [
    {ok: false, json: async () => ({error: '<img onerror="secret()">'})},
    response(payload(30)),
    response({...empty, data: {...empty.data, indexed_signatures: '0'}}),
    response({...empty, data: {...empty.data, timed_signatures: 1}}),
    response({...empty, data: {...empty.data, categories: {...empty.data.categories, ACTIVE_TRADE: 1}}}),
  ]) {
    reply = badReply;
    await page.get('read').click();
    assert.equal(page.lines(), '');
    assert.match(page.get('status').textContent, /签名数量、全链覆盖和历史缺口均未核实/);
    assert.equal(page.get('read').disabled, false);
  }
});

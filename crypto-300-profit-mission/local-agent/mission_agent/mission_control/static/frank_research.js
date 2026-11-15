/* Explicit user-triggered research; no startup fetch, timer or source polling. */
(() => {
  'use strict';
  const el = id => document.getElementById('frank-source-' + id);
  if (!el('balance')) return;
  let next = null, lastBalance = null, busy = false, viewEpoch = 0;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  async function request(path, body) {
    const options = body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}
      : {headers:{'X-Frank-Research-Read':'1'}};
    const response = await fetch(path, {...options, cache:'no-store'});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'HTTP_' + response.status);
    return result;
  }
  function controls(value) {
    busy = value;
    el('balance').disabled = value;
    el('market').disabled = value;
    el('signals').disabled = value;
    el('resume').disabled = value || !lastBalance;
  }
  async function read(cursor = null) {
    const epoch = ++viewEpoch;
    el('rows').innerHTML = '<tr><td colspan="5">正在读取固定来源结果…</td></tr>';
    el('summary').textContent = '正在读取，先前结果不代表本次查询。';
    el('next').disabled = true;
    let url = '/api/frank-positions?limit=100';
    const mint = el('mint').value.trim();
    if (mint) url += '&mint=' + encodeURIComponent(mint);
    if (cursor) url += '&cursor=' + encodeURIComponent(cursor);
    const p = await request(url);
    if (epoch !== viewEpoch) return;
    next = p.next_cursor || null;
    el('next').disabled = !next;
    if (!p.rows) {
      el('summary').textContent = '余额未知：' + (p.reason || p.status);
      el('rows').innerHTML = '<tr><td colspan="5">尚无完整全钱包快照，请手动刷新</td></tr>';
      return;
    }
    const markets = new Map();
    let murl = '/api/frank-market-observations?limit=1000';
    while (murl) {
      const part = await request(murl);
      if (epoch !== viewEpoch) return;
      for (const r of part.rows || []) markets.set(r.mint, r);
      murl = part.next_cursor ? '/api/frank-market-observations?limit=1000&cursor=' + encodeURIComponent(part.next_cursor) : null;
    }
    const time = new Date(Number(p.observed_at)*1000).toLocaleString('zh-CN');
    const programs = (p.programs || []).map(r => r.program_id.slice(0,8) + ' slot ' + r.slot + ' / ' + r.account_count + '账户').join('；');
    const failure = p.latest_refresh_attempt && p.latest_refresh_attempt.state === 'ERROR'
      ? '；最近刷新失败：' + JSON.stringify(p.latest_refresh_attempt.errors) : '';
    el('summary').textContent = (p.current_balance_verified ? '时效内采集余额' : '历史快照，当前余额未核实') +
      '；采集 ' + time + '；来源年龄 ' + p.age_seconds + '秒；总计 ' + p.account_count + '账户 / ' + p.mint_count +
      ' Mint；本页 ' + p.returned + ' / 匹配 ' + p.total_matching + '；原生SOL ' + (p.native_sol || {}).ui_amount + '；' + programs + failure;
    el('rows').innerHTML = p.rows.map(r => {
      const mark = markets.get(r.mint);
      const age = mark ? Date.now()/1000 - Number(mark.observed_at) : null;
      const price = mark && mark.status === 'OK' && age >= 0 && age <= 60
        ? String(mark.price_usd) + ' USD/token（' + Math.floor(age) + '秒前）'
        : (mark ? (age < 0 ? '来源时间异常' : age > 60 ? '参考价已过期' : mark.reason || '无价') : '未采集行情');
      return '<tr><td><code>' + esc(r.mint) + '</code></td><td>' + esc(r.ui_amount) + '</td><td>' +
        esc(r.account_count) + '</td><td>' + esc(price) + '</td><td>' + esc(r.model_state) + ' / ' + esc(r.chain_state) + '</td></tr>';
    }).join('') || '<tr><td colspan="5">该完整快照中没有匹配Mint；未发现开放账户不等于从未持有</td></tr>';
    // Capture valuation remains explicit about unpriced coverage; never display a
    // partial subtotal as the full wallet value.
    if (p.valuation) el('summary').textContent += '；有价 ' + p.valuation.covered_positions +
      ' / 无价 ' + p.valuation.unpriced_positions + '；已估值部分 ' + p.valuation.priced_subtotal_usd +
      ' USD；非零Token合计 ' + (p.valuation.total_value_usd == null ? '未知（资料不完整）' : p.valuation.total_value_usd + ' USD') +
      '；原生SOL参考估值 ' + ((p.valuation.native_sol_valuation || {}).total_value_usd ?? '未知') + ' USD（单列，不作全钱包净值）';
    const cards = document.getElementById('frank-intelligence-reload');
    if (cards) cards.click(); // Existing read-only analysis; no market/quote fetch.
  }
  async function run(kind, resume = false, scope = 'positions') {
    if (busy) return;
    controls(true);
    try {
      let job;
      if (resume) job = await request('/api/frank-balance-refresh/resume', {refresh_id:lastBalance, idempotency_key:crypto.randomUUID()});
      else job = await request('/api/frank-' + kind + '-refresh', {
        idempotency_key:crypto.randomUUID(), ...(kind === 'market' ? {scope} : {})
      });
      if (kind === 'balance') lastBalance = job.job_id;
      while (true) {
        el('status').textContent = '任务 ' + job.job_id + '：' + job.state + '；' + JSON.stringify(job.progress || {});
        if (!['QUEUED','RUNNING'].includes(job.state)) break;
        await new Promise(resolve => setTimeout(resolve, 1000));
        job = await request('/api/frank-' + kind + '-refresh?refresh_id=' + encodeURIComponent(job.job_id));
      }
      el('status').textContent = '任务 ' + job.job_id + '：' + job.state +
        ((job.errors || []).length ? '；' + JSON.stringify(job.errors) : '；来源结果已保留');
      await read();
    } catch (e) {
      el('status').textContent = '请求未完成：' + e.message + '；已保留任务，可重新读取或恢复。';
    } finally { controls(false); }
  }
  el('balance').addEventListener('click', () => run('balance'));
  el('market').addEventListener('click', () => run('market'));
  el('signals').addEventListener('click', () => run('market', false, 'signals'));
  el('resume').addEventListener('click', () => run('balance', true));
  el('read').addEventListener('click', () => read().catch(e => { el('status').textContent = e.message; }));
  el('find').addEventListener('click', () => read().catch(e => { el('status').textContent = e.message; }));
  el('next').addEventListener('click', () => { if (next) read(next).catch(e => { el('status').textContent = e.message; }); });
})();

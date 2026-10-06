const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const n = (v, digits=4) => {
  const x = Number(v);
  return Number.isFinite(x) ? x.toLocaleString(undefined,{maximumFractionDigits:digits}) : 'N/A';
};
const short = (mint) => mint ? `${mint.slice(0,6)}…${mint.slice(-4)}` : 'N/A';
const age = (ts) => {
  if (!ts) return 'N/A';
  const sec = Math.max(0, Math.floor(Date.now()/1000 - Number(ts)));
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec/60)}m`;
  return `${Math.floor(sec/3600)}h`;
};
const badge = (value) => `<span class="badge ${String(value).toLowerCase().replaceAll('_','-')}">${esc(value)}</span>`;
const frankQuote = (x) => {
  const asset = x.latest_buy_original_quote_asset;
  const qty = x.latest_buy_original_quote_quantity;
  if (!asset || qty == null) return 'N/A';
  const original = `${n(qty,6)} ${esc(asset === 'So11111111111111111111111111111111111111112' ? 'WSOL' : asset)}`;
  if (!x.latest_buy_quote_was_normalized) return original;
  return `${original}<small> ≈ ${n(x.latest_buy_usdc_equivalent,2)} USDC（历史换算）</small>`;
};

async function get(path) {
  const r = await fetch(path,{cache:'no-store'});
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}

function renderRuntime(runtime) {
  $('runtime').className = `runtime ${String(runtime.status||'UNKNOWN').toLowerCase()}`;
  $('runtime').innerHTML = `${badge(runtime.status||'UNKNOWN')}<span>poll ${n(runtime.heartbeat_age_seconds,0)}s</span><span>PID ${esc(runtime.pid ?? 'N/A')}</span>`;
}

function renderStats(candidates, runtime) {
  const counts = {BUY:0,SMALL_BUY:0,WAIT:0,NO_BUY:0,UNASSESSED:0};
  candidates.forEach(x => counts[x.decision] = (counts[x.decision]||0)+1);
  const items = [
    ['Frank', runtime.status||'UNKNOWN'],
    ['BUY', counts.BUY],
    ['SMALL BUY', counts.SMALL_BUY],
    ['WAIT', counts.WAIT],
    ['NO BUY', counts.NO_BUY],
    ['Candidates', candidates.length],
  ];
  $('stats').innerHTML = items.map(([k,v]) => `<div class="stat"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join('');
}

function renderCandidates(rows) {
  $('candidates').innerHTML = rows.map(x => {
    const m = x.metrics || {};
    return `<tr>
      <td><code title="${esc(x.mint)}">${esc(short(x.mint))}</code></td>
      <td>${badge(x.decision||'UNASSESSED')}</td>
      <td>${esc(x.pattern)}</td>
      <td>${esc(x.buy_count)}/${esc(x.sell_count)}</td>
      <td>${esc(x.latest_side||'N/A')} ${age(x.latest_at)}</td>
      <td>${frankQuote(x)}</td>
      <td>${n(m.frank_latest_buy_price_usdc,8)}</td>
      <td>${n(m.execution_price_usdc,8)}</td>
      <td>${m.price_deviation_pct != null ? n(m.price_deviation_pct,2)+'%' : 'N/A'}</td>
      <td>${m.price_impact_pct != null ? n(m.price_impact_pct,2)+'%' : 'N/A'}</td>
      <td>${esc(x.position_state||'N/A')}</td>
    </tr>`;
  }).join('') || '<tr><td colspan="11" class="empty">暂无候选</td></tr>';
}

function renderTrades(rows) {
  $('trades').innerHTML = rows.slice(0,30).map(x => `<div class="feed-row">
    <div>${badge(x.side)}</div>
    <div><code>${esc(short(x.mint))}</code><small>${esc(x.signature)}</small></div>
    <time>${new Date(Number(x.block_time)*1000).toLocaleString()}</time>
  </div>`).join('') || '<div class="empty">暂无交易</div>';
}

function renderDecisions(rows) {
  $('decisions').innerHTML = rows.slice(0,30).map(x => {
    const b = x.body || {};
    return `<div class="feed-row">
      <div>${badge(x.decision)}</div>
      <div><code>${esc(short(x.mint))}</code><small>${esc(b.previous_decision||'NONE')} → ${esc(x.decision)}</small></div>
      <time>${esc(x.created_at)}</time>
    </div>`;
  }).join('') || '<div class="empty">暂无 Decision</div>';
}

async function refresh() {
  try {
    const [runtime,candidates,trades,decisions] = await Promise.all([
      get('/api/runtime'), get('/api/candidates'), get('/api/trades'), get('/api/decisions')
    ]);
    renderRuntime(runtime);
    renderStats(candidates,runtime);
    renderCandidates(candidates);
    renderTrades(trades);
    renderDecisions(decisions);
    $('updated').textContent = `更新 ${new Date().toLocaleTimeString()}`;
  } catch (e) {
    $('runtime').className = 'runtime offline';
    $('runtime').textContent = `DASHBOARD ERROR: ${e.message}`;
  }
}

refresh();
setInterval(refresh, 5000);

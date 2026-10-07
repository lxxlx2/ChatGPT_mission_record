const $ = (id) => document.getElementById(id);

const USDC_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';
const WSOL_MINT = 'So11111111111111111111111111111111111111112';

const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c]));

const n = (v, digits=4) => {
  const x = Number(v);
  return Number.isFinite(x)
    ? x.toLocaleString('zh-CN',{maximumFractionDigits:digits})
    : '暂无';
};

const money = (v, digits=8) => {
  const x = Number(v);
  if (!Number.isFinite(x)) return '暂无';
  return x.toLocaleString('zh-CN',{
    minimumFractionDigits: x > 0 && x < 0.01 ? Math.min(6,digits) : 0,
    maximumFractionDigits: digits,
  });
};

const short = (value, left=6, right=4) =>
  value ? `${value.slice(0,left)}…${value.slice(-right)}` : '暂无';

const age = (ts) => {
  if (!ts) return '时间未知';
  const sec = Math.max(0, Math.floor(Date.now()/1000 - Number(ts)));
  if (sec < 60) return `${sec}秒前`;
  if (sec < 3600) return `${Math.floor(sec/60)}分钟前`;
  if (sec < 86400) return `${Math.floor(sec/3600)}小时前`;
  return `${Math.floor(sec/86400)}天前`;
};

const decisionLabel = {
  BUY:'可跟',
  SMALL_BUY:'小仓跟',
  WAIT:'等待',
  NO_BUY:'不跟',
  UNASSESSED:'未评估',
};

const patternLabel = {
  ACCUMULATION:'持续建仓',
  MULTIPLE:'多次强加仓',
  NONE:'无跟单模式',
};

const stateLabel = {
  OPEN:'持仓中',
  CLOSED:'已退出',
  INVENTORY_UNDETERMINED:'仓位不明',
};

const sideLabel = {
  BUY:'买入',
  ADD:'加仓',
  REENTRY:'重新建仓',
  SELL:'卖出',
  EXIT:'退出仓位',
  SELL_POSITION_UNRESOLVED:'卖出待确认',
  ACTIVE_TRADE:'主动交易',
};

const runtimeLabel = {
  LIVE:'正常',
  RUNNING:'正常',
  OK:'正常',
  STARTING:'启动中',
  DEGRADED:'异常降级',
  OFFLINE:'离线',
  STOPPED:'已停止',
  UNKNOWN:'未知',
};

const reasonText = {
  FRANK_RUNTIME_NOT_LIVE:'Frank 实时监控当前不在线，先不跟。',
  POSITION_STATE_CLOSED:'Frank 已经退出该仓位，不跟。',
  POSITION_STATE_INVENTORY_UNDETERMINED:'无法确认 Frank 当前仓位，不跟。',
  INVENTORY_UNDETERMINED:'无法确认 Frank 当前持仓数量，不跟。',
  ZERO_OR_NEGATIVE_INVENTORY:'Frank 当前已没有可确认持仓，不跟。',
  LATEST_ACTION_SELL:'Frank 最新动作是卖出，等待新的买入序列。',
  NO_FOLLOW_PATTERN:'目前还没有形成可跟随的建仓模式。',
  FRANK_BUY_SIGNAL_STALE_OR_UNKNOWN:'Frank 最近有效买入已经过期或时间未知，当前不追。',
  CRITICAL_DATA_INCOMPLETE:'关键价格或执行数据不完整，等待数据恢复。',
  QUOTE_METRICS_INVALID:'Jupiter 报价缺少有效成交价或价格冲击数据。',
  NO_EXECUTABLE_JUPITER_ROUTE:'Jupiter 当前没有可执行的跟单路径，不跟。',
  PRICE_TOO_FAR_FROM_FRANK:'当前价格已经离 Frank 买入价太远，暂时不追。',
  EXECUTION_IMPACT_TOO_HIGH:'当前 $30 跟单的预计价格冲击太高，暂时不追。',
  FRANK_MULTIPLE_ACTIVE:'Frank 当前处于多次强加仓模式。',
  PRICE_STILL_CLOSE_TO_FRANK:'当前成交价仍接近 Frank 的参考买入价。',
  EXECUTION_IMPACT_ACCEPTABLE:'当前预计价格冲击在可接受范围。',
  FRANK_PATTERN_ACTIVE:'Frank 当前仍处于可跟随建仓模式。',
  FOLLOWABLE_WITH_SMALL_SIZE:'当前条件只适合小仓跟随。',
  ACCUMULATION_NOT_MULTIPLE:'目前只是持续建仓，还没有升级到强 MULTIPLE。',
  PRICE_DEVIATION_ABOVE_BUY_LIMIT:'价格偏离超过“正常跟随”阈值，只适合小仓。',
  PRICE_IMPACT_ABOVE_BUY_LIMIT:'价格冲击超过“正常跟随”阈值，只适合小仓。',
};

const missingText = {
  FRESH_FRANK_BUY:'缺少 10 分钟内的新鲜 Frank 买入。',
  LIVE_FRANK_RUNTIME:'Frank 实时监控不在线。',
  QUOTE_TIMESTAMP:'Jupiter 报价没有有效时间戳。',
  QUOTE_STALE:'Jupiter 报价已过期。',
  EXECUTION_PRICE_OR_IMPACT:'缺少当前成交价或价格冲击。',
  TOKEN_DECIMALS_UNKNOWN:'Token decimals 未确认。',
  JUPITER_QUOTE_UNAVAILABLE:'Jupiter 当前报价不可用。',
};

function translated(map, raw, fallback='未知') {
  if (raw == null || raw === '') return fallback;
  return map[raw] || String(raw);
}

function badge(value, labelMap=decisionLabel) {
  const cls = String(value || 'unknown').toLowerCase().replaceAll('_','-');
  const label = translated(labelMap,value,String(value || '未知'));
  return `<span class="badge ${esc(cls)}" title="原始状态：${esc(value || 'UNKNOWN')}">${esc(label)}</span>`;
}

function quoteAsset(asset) {
  if (asset === USDC_MINT) return 'USDC';
  if (asset === WSOL_MINT) return 'SOL';
  return asset || '未知资产';
}

function frankQuote(x) {
  const asset = x.latest_buy_original_quote_asset || x.latest_buy_quote_asset;
  const qty = x.latest_buy_original_quote_quantity ?? x.latest_buy_quote_quantity;
  if (!asset || qty == null) return '暂无';
  const original = `${n(qty,6)} ${esc(quoteAsset(asset))}`;
  if (!x.latest_buy_quote_was_normalized) return original;
  return `${original}<span class="subvalue">≈ ${n(x.latest_buy_usdc_equivalent,2)} USDC（历史换算）</span>`;
}

function reasonFor(x) {
  const reasons = Array.isArray(x.reasons) ? x.reasons : [];
  const missing = Array.isArray(x.missing) ? x.missing : [];
  const pieces = [];
  for (const r of reasons) pieces.push(reasonText[r] || r);
  for (const m of missing) pieces.push(missingText[m] || m);
  const unique = [...new Set(pieces.filter(Boolean))];
  if (unique.length) return unique.join(' ');
  if (x.decision === 'UNASSESSED') return '等待 Mission Control 完成首次评估。';
  return '当前没有额外说明。';
}

function copyButton(value, label='复制') {
  if (!value) return '';
  return `<button class="copy-btn" type="button" data-copy="${esc(value)}">${esc(label)}</button>`;
}

function researchLinks(mint) {
  if (!mint) return '';
  const encoded = encodeURIComponent(mint);
  return `<a class="link-btn" href="https://solscan.io/token/${encoded}" target="_blank" rel="noreferrer">Solscan ↗</a>`;
}

function tokenIdentity(mint) {
  if (!mint) return '<span class="muted">CA 未知</span>';
  return `
    <div class="ca-row">
      <span class="ca-label">CA</span>
      <code class="ca-full">${esc(mint)}</code>
      ${copyButton(mint,'复制 CA')}
      ${researchLinks(mint)}
    </div>`;
}

async function copyText(value, button) {
  try {
    await navigator.clipboard.writeText(value);
  } catch (_) {
    const area = document.createElement('textarea');
    area.value = value;
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    document.execCommand('copy');
    area.remove();
  }
  const old = button.textContent;
  button.textContent = '已复制';
  button.classList.add('copied');
  showToast('已复制到剪贴板');
  setTimeout(() => {
    button.textContent = old;
    button.classList.remove('copied');
  }, 1200);
}

function showToast(text) {
  const toast = $('toast');
  toast.textContent = text;
  toast.classList.add('show');
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove('show'), 1400);
}

document.addEventListener('click', (event) => {
  const button = event.target.closest('[data-copy]');
  if (!button) return;
  copyText(button.dataset.copy,button);
});

async function get(path) {
  const r = await fetch(path,{cache:'no-store'});
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}

function renderRuntime(runtime, control) {
  const rawStatus = runtime.status || 'UNKNOWN';
  const heartbeat = Number(runtime.heartbeat_age_seconds);
  const heartbeatText = Number.isFinite(heartbeat)
    ? `上次心跳 ${Math.round(heartbeat)} 秒前`
    : '心跳时间未知';
  const controlText = translated(runtimeLabel,control?.status,'未知');

  $('runtime').className = `runtime ${String(rawStatus).toLowerCase()}`;
  $('runtime').innerHTML = `
    <div class="runtime-main">
      ${badge(rawStatus,runtimeLabel)}
      <strong>Frank 监控${translated(runtimeLabel,rawStatus,'未知')}</strong>
      <span>· ${esc(heartbeatText)}</span>
      <span>· 跟单引擎${esc(controlText)}</span>
    </div>
    <details class="tech-details">
      <summary>技术信息</summary>
      <div>Frank PID：${esc(runtime.pid ?? '未知')}</div>
      <div>原始状态：${esc(rawStatus)}</div>
      <div>生产交易：${esc(runtime.production_trading ?? '未知')}</div>
      <div>最后处理 Slot：${esc(runtime.last_processed_slot ?? '未知')}</div>
    </details>`;
}

function renderStats(candidates, runtime) {
  const counts = {BUY:0,SMALL_BUY:0,WAIT:0,NO_BUY:0,UNASSESSED:0};
  candidates.forEach(x => counts[x.decision] = (counts[x.decision]||0)+1);
  const items = [
    ['Frank监控', translated(runtimeLabel,runtime.status,'未知')],
    ['可跟', counts.BUY],
    ['小仓跟', counts.SMALL_BUY],
    ['等待', counts.WAIT],
    ['不跟', counts.NO_BUY],
    ['候选', candidates.length],
  ];
  $('stats').innerHTML = items.map(([k,v]) =>
    `<div class="stat"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`
  ).join('');
}

function metric(label,value,help='') {
  return `<div class="metric" ${help ? `title="${esc(help)}"` : ''}>
    <span>${esc(label)}</span>
    <strong>${value}</strong>
  </div>`;
}

function quoteUnavailableText(x, q) {
  const reason = q?.reason;
  if (reason === 'POSITION_NOT_FOLLOWABLE') return '未请求（Frank 已退出）';
  if (reason === 'LATEST_ACTION_SELL') return '未请求（Frank 最新动作是卖出）';
  if (reason === 'FRANK_RUNTIME_NOT_LIVE') return '未请求（Frank 监控不在线）';
  if (reason === 'TOKEN_DECIMALS_UNKNOWN') return '无法报价（Token decimals 未知）';
  if (q?.status === 'UNAVAILABLE') return `报价不可用（${reason || 'Jupiter 异常'}）`;
  if (q?.status === 'OK' && q?.route_exists === false) return '无可执行路径';
  return '暂无可用报价';
}

function frankPriceText(x, m) {
  const value = m.frank_latest_buy_price_usdc ?? x.latest_buy_price_usdc;
  if (value != null) return `${money(value,8)}`;
  if (x.latest_buy_price_status === 'SOL_EVENT_TIME_USDC_UNAVAILABLE') return '无法计算（缺历史 SOL/USD）';
  if (x.latest_buy_price_status === 'QUOTE_PRICE_UNAVAILABLE') return '无法从原始交易计算';
  return '暂无参考价';
}

function renderCandidates(rows) {
  $('candidates').innerHTML = rows.map(x => {
    const m = x.metrics || {};
    const q = x.decision_quote || {};
    const decision = x.decision || 'UNASSESSED';
    const reason = reasonFor(x);

    const frankPriceRaw = m.frank_latest_buy_price_usdc ?? x.latest_buy_price_usdc;
    const execRaw = m.execution_price_usdc ?? q.execution_price_usdc;
    const impactRaw = m.price_impact_pct ?? q.price_impact_pct;

    let deltaRaw = m.price_deviation_pct;
    if (deltaRaw == null && frankPriceRaw != null && execRaw != null) {
      const f = Number(frankPriceRaw);
      const e = Number(execRaw);
      if (Number.isFinite(f) && f > 0 && Number.isFinite(e)) {
        deltaRaw = (e / f - 1) * 100;
      }
    }

    const delta = deltaRaw != null ? `${n(deltaRaw,2)}%` : quoteUnavailableText(x,q);
    const impact = impactRaw != null ? `${n(impactRaw,2)}%` : quoteUnavailableText(x,q);
    const frankPrice = frankPriceText(x,m);
    const execPrice = execRaw != null ? `${money(execRaw,8)}` : quoteUnavailableText(x,q);
    const buys = x.buy_count ?? 0;
    const sells = x.sell_count ?? 0;

    return `<article class="candidate-card decision-${esc(decision.toLowerCase().replaceAll('_','-'))}">
      <div class="candidate-head">
        <div class="candidate-title">
          ${badge(decision)}
          <strong>${esc(translated(patternLabel,x.pattern,'未形成模式'))}</strong>
          <span class="state-text">Frank仓位：${esc(translated(stateLabel,x.position_state,'未知'))}</span>
        </div>
        <div class="candidate-time">最近动作：${esc(translated(sideLabel,x.latest_side,'未知'))} · ${esc(age(x.latest_at))}</div>
      </div>

      ${tokenIdentity(x.mint)}

      <div class="decision-reason">
        <span>为什么是“${esc(translated(decisionLabel,decision,decision))}”</span>
        <strong>${esc(reason)}</strong>
      </div>

      <div class="metrics-grid">
        ${metric('Frank 买/卖次数',`买 ${esc(buys)} · 卖 ${esc(sells)}`,'当前观察到的建仓序列内买入/卖出次数，不代表钱包终身累计。')}
        ${metric('Frank 最近动作',`${esc(translated(sideLabel,x.latest_side,'未知'))} · ${esc(age(x.latest_at))}`)}
        ${metric('Frank 原始支付',frankQuote(x),'Frank 真实交易使用的报价资产和数量。')}
        ${metric('Frank 参考买入价',frankPrice,'直接来自 Frank 最近买入事件；即使当前 Decision 因超时提前结束，也尽量展示。')}
        ${metric('当前 $30 成交价',execPrice,'Jupiter 已经请求过就展示真实报价；只有明确跳过/失败才显示原因。')}
        ${metric('相对 Frank 偏离',esc(delta),'如果决策提前返回但 Frank 参考价和 Jupiter 报价都存在，Dashboard 会独立计算偏离供研究。')}
        ${metric('预计价格冲击',esc(impact),'用 $30 USDC 下单时 Jupiter 估算的价格冲击；已退出仓位不会浪费请求。')}
      </div>
    </article>`;
  }).join('') || '<div class="empty">当前没有需要跟踪的 Frank 候选</div>';
}

function withinHours(ts,hours) {
  const value = Number(ts);
  if (!Number.isFinite(value)) return false;
  const ageSeconds = Date.now()/1000 - value;
  return ageSeconds >= 0 && ageSeconds <= hours * 3600;
}

function renderEnded(rows) {
  const recent = rows
    .filter(x => x.position_state === 'CLOSED' && withinHours(x.latest_at,24))
    .sort((a,b) => Number(b.latest_at || 0) - Number(a.latest_at || 0));

  const panel = $('ended-panel');
  $('ended-count').textContent = recent.length;
  panel.hidden = recent.length === 0;

  $('ended').innerHTML = recent.map(x => `
    <div class="ended-row">
      <div class="ended-main">
        ${badge(x.decision || 'NO_BUY')}
        <strong>${esc(translated(patternLabel,x.pattern,'未形成模式'))}</strong>
        <span>${esc(age(x.latest_at))}退出</span>
      </div>
      <div class="ended-ca">
        <code>${esc(x.mint)}</code>
        ${copyButton(x.mint,'复制 CA')}
        ${researchLinks(x.mint)}
      </div>
      <div class="ended-note">${esc(reasonFor(x))}</div>
    </div>
  `).join('');
}

function tradeHint(side) {
  const hints = {
    BUY:'Frank 新买入。',
    ADD:'Frank 在已有仓位上继续加仓。',
    REENTRY:'Frank 退出后重新建立仓位。',
    SELL:'Frank 有卖出动作。',
    EXIT:'Frank 已退出该观察仓位。',
    SELL_POSITION_UNRESOLVED:'检测到卖出，但无法精确重建卖出后的剩余仓位；这条只作为风险提示。',
  };
  return hints[side] || `原始事件：${side || 'UNKNOWN'}`;
}

function renderTrades(rows) {
  $('trades').innerHTML = rows.slice(0,30).map(x => {
    const side = x.side || 'UNKNOWN';
    const solscan = x.signature
      ? `<a class="link-btn compact" href="https://solscan.io/tx/${encodeURIComponent(x.signature)}" target="_blank" rel="noreferrer">交易 ↗</a>`
      : '';
    return `<div class="feed-row trade-row">
      <div class="feed-badge">${badge(side,sideLabel)}</div>
      <div class="feed-main">
        <div class="feed-token"><code>${esc(short(x.mint,8,6))}</code> ${copyButton(x.mint,'复制 CA')}</div>
        <small>${esc(tradeHint(side))}</small>
        <div class="hash-row"><span>Tx ${esc(short(x.signature,10,8))}</span> ${copyButton(x.signature,'复制 Tx')} ${solscan}</div>
      </div>
      <time>${new Date(Number(x.block_time)*1000).toLocaleString('zh-CN')}</time>
    </div>`;
  }).join('') || '<div class="empty">暂无交易</div>';
}

function renderDecisions(rows) {
  $('decisions').innerHTML = rows.slice(0,30).map(x => {
    const b = x.body || {};
    const previous = b.previous_decision || 'NONE';
    const previousLabel = previous === 'NONE' ? '首次评估' : translated(decisionLabel,previous,previous);
    const nowLabel = translated(decisionLabel,x.decision,x.decision);
    return `<div class="feed-row decision-row">
      <div class="feed-badge">${badge(x.decision)}</div>
      <div class="feed-main">
        <div class="feed-token"><code>${esc(short(x.mint,8,6))}</code> ${copyButton(x.mint,'复制 CA')}</div>
        <small>${esc(previousLabel)} → ${esc(nowLabel)}</small>
      </div>
      <time>${new Date(x.created_at).toLocaleString('zh-CN')}</time>
    </div>`;
  }).join('') || '<div class="empty">暂无判断变化</div>';
}

async function refresh() {
  try {
    const [runtime,control,candidates,trades,decisions] = await Promise.all([
      get('/api/runtime'),
      get('/api/control-health'),
      get('/api/candidates'),
      get('/api/trades'),
      get('/api/decisions')
    ]);
    const activeCandidates = candidates.filter(x => x.position_state !== 'CLOSED');
    const endedCandidates = candidates.filter(x => x.position_state === 'CLOSED');

    renderRuntime(runtime,control);
    renderStats(activeCandidates,runtime);
    renderCandidates(activeCandidates);
    renderEnded(endedCandidates);
    renderTrades(trades);
    renderDecisions(decisions);
    $('updated').textContent = `更新于 ${new Date().toLocaleTimeString('zh-CN')}`;
  } catch (e) {
    $('runtime').className = 'runtime offline';
    $('runtime').innerHTML = `<strong>控制台读取失败</strong><span>${esc(e.message)}</span>`;
  }
}

refresh();
setInterval(refresh,5000);

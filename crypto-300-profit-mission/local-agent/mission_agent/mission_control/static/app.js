const $ = (id) => document.getElementById(id);

const USDC_MINT = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';
const WSOL_MINT = 'So11111111111111111111111111111111111111112';

const esc = (v) => String(v ?? '').replace(/[&<>"']/g, c => ({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c]));

const n = (v, digits=4) => {
  if (v == null || v === '') return '暂无';
  const x = Number(v);
  return Number.isFinite(x)
    ? x.toLocaleString('zh-CN',{maximumFractionDigits:digits})
    : '暂无';
};

const money = (v, digits=8) => {
  if (v == null || v === '') return '暂无';
  const x = Number(v);
  if (!Number.isFinite(x)) return '暂无';
  return x.toLocaleString('zh-CN',{
    minimumFractionDigits: x > 0 && x < 0.01 ? Math.min(6,digits) : 0,
    maximumFractionDigits: digits,
  });
};

const smallPrice = (value) => {
  if (value == null || value === '') return '暂无';
  const x=Number(value);
  if (!Number.isFinite(x) || x<=0) return '暂无';
  if (x<0.00001) return x.toExponential(2);
  return Number(x.toPrecision(4)).toLocaleString('en-US',{maximumFractionDigits:8});
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
  REENTRY_WATCH:'重新建仓观察',
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
  REVIEW:'待复核',
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
  FRANK_REENTRY_WATCH_ACTIVE:'Frank 清仓后重新建仓，已进入观察；目前还没有形成持续建仓或多次强加仓信号。',
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
  return `<a class="link-btn" href="https://solscan.io/token/${encoded}" target="_blank" rel="noreferrer">Solscan ↗</a> <a class="link-btn" href="https://gmgn.ai/sol/token/${encoded}" target="_blank" rel="noreferrer">GMGN 图表 ↗</a>`;
}

function tokenIdentity(mint) {
  if (!mint) return '<span class="muted">CA 未知</span>';
  return `
    <div class="ca-row">
      <span class="ca-label">CA</span>
      <code class="ca-full">${esc(mint)}</code>
      ${copyButton(mint,'复制 CA')}
      <button class="link-btn" type="button" data-cluster-ca="${esc(mint)}">链上查询</button>
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
  const clusterButton = event.target.closest('[data-cluster-ca]');
  if (clusterButton) {
    const mint=clusterButton.dataset.clusterCa;
    $('cluster-mint').value=mint;
    setView('cluster');
    $('cluster-mint').focus();
    showToast('已带入 CA，可直接开始查询');
    return;
  }
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
    </div>`;
}

function renderStats(candidates, runtime, coverage) {
  const w = coverage?.windows?.['24h'] || {};
  const action = candidates.filter(x => x.decision === 'BUY' || x.decision === 'SMALL_BUY').length;
  const items = [
    ['Frank状态', translated(runtimeLabel,runtime.status,'未知')],
    ['24h已索引签名', w.indexed_signatures ?? '—'],
    ['本地已识别买入', w.recognized_buys ?? '—'],
    ['本地已识别卖出', w.recognized_sells ?? '—'],
    ['24h待复核', w.unknown_needs_review ?? '—'],
    ['当前可跟候选', action],
  ];
  $('stats').innerHTML = items.map(([key,value]) =>
    `<div class="stat"><span>${esc(key)}</span><strong>${esc(value)}</strong></div>`
  ).join('');
}

function renderCoverage(coverage) {
  const node = $('coverage');
  if (!node) return;
  if (coverage?.status !== 'OK') {
    node.textContent = '本地索引覆盖率不可读取；当前不能判断链上交易是否漏报。';
    return;
  }
  const w=coverage.windows || {};
  const t=w['24h'] || {};
  const since=coverage.earliest_indexed_block_time
    ? new Date(Number(coverage.earliest_indexed_block_time)*1000).toLocaleString('zh-CN')
    : '未知';
  node.innerHTML =
    `<span>24h签名 ${esc(t.indexed_signatures ?? '—')} · 已分类 ${esc(t.recognized_trades ?? '—')} · 待核 ${esc(t.unknown_needs_review ?? '—')}</span>` +
    `<span>7d ${esc(w['7d']?.recognized_trades ?? '—')} · 30d ${esc(w['30d']?.recognized_trades ?? '—')} · 最早 ${esc(since)}</span>` +
    '<span>已索引分类数量，完整性仍须与独立链上数据对账。</span>';
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

function tradeAmount(x) {
  const asset = x.observed_quote_asset;
  const qty = x.observed_quote_quantity;
  if (qty == null || !asset) return '交易资金腿金额待核实';
  if (x.body?.amount_predicate === 'UNDETERMINED' && !x.body?.original_quote) return '多资产路线的目标成本未确认';
  const amount = n(qty,asset === USDC_MINT ? 2 : 4);
  if (asset === USDC_MINT) return amount + ' USDC';
  if (asset === WSOL_MINT || asset === 'SOL') return amount + ' SOL';
  return amount + ' ' + short(asset,6,4);
}

function fillPrice(x) {
  const price = Number(x.verified_fill_price_usdc);
  if (!Number.isFinite(price) || price <= 0) return '成交价不可核实';
  const digits=Math.max(0,Math.min(18,5-Math.floor(Math.log10(price))));
  return '$' + smallPrice(price);
}

function renderTrades(rows) {
  $('trades').innerHTML = rows.slice(0,50).map(x => {
    const side = x.side || 'UNKNOWN';
    const isBuy=['BUY','ADD','REENTRY'].includes(side);
    const tx=x.signature
      ? `<a class="link-btn compact" href="https://solscan.io/tx/${encodeURIComponent(x.signature)}" target="_blank" rel="noreferrer">链上原始交易 ↗</a>`
      : '';
    return `<div class="feed-row trade-row">
      <div class="feed-badge">${badge(side,sideLabel)}</div>
      <div class="feed-main">
        <div class="feed-token"><code>${esc(short(x.mint,8,6))}</code> ${copyButton(x.mint,'复制 CA')}</div>
        <div class="trade-core"><strong>${esc(isBuy?'买入':'卖出')}：${esc(tradeAmount(x))}</strong><span>成交 ${esc(fillPrice(x))}</span></div>
        <small>${esc(tradeHint(side))}</small>
        <div class="hash-row">${copyButton(x.signature,'复制 Tx')}</div>
      </div>
      <time>${new Date(Number(x.block_time)*1000).toLocaleString('zh-CN')}</time>
    </div>`;
  }).join('') || '<div class="empty">本地尚无可识别交易；这不代表钱包没有链上活动</div>';
}

function renderReviewActivity(rows) {
  const panel=$('review-activity-panel');
  const count=$('review-activity-count');
  if (!panel || !count) return;
  count.textContent=rows.length;
  panel.hidden=rows.length===0;
  $('review-activity').innerHTML=rows.slice(0,30).map(x => {
    const mints=(x.candidate_mints || []);
    const mintHtml=mints.length
      ? mints.map(m => `<code>${esc(short(m,8,6))}</code> ${copyButton(m,'复制 CA')}`).join(' ')
      : '<span>目标资产未能唯一确定</span>';
    const solscan=x.signature
      ? `<a class="link-btn compact" href="https://solscan.io/tx/${encodeURIComponent(x.signature)}" target="_blank" rel="noreferrer">交易 ↗</a>`
      : '';
    const residual=(x.residual_flow_candidates || []);
    const reason=x.review_scope==='SIGNED_OPPOSING_FLOW_MARKET_UNPROVEN'
      ? 'Frank 已签名且存在相反资产流，但市场程序/指令证据不足；未进入跟随模型。'
      : x.classification_reason==='AMBIGUOUS_USER_EXCHANGE_ASSETS' && residual.length
        ? '检测到新建资产账户存在 receive→spend 守恒残余，但无法证明该支出与另一目标资产属于同一路由；保持待复核，不进入跟随模型。'
        : x.classification_reason==='AMBIGUOUS_USER_EXCHANGE_ASSETS'
          ? '多资产/多结算腿，无法安全归约成单一买卖；未进入跟随模型。'
          : `未归约原因：${x.classification_reason || 'UNKNOWN'}`;
    return `<div class="feed-row trade-row">
      <div class="feed-badge">${badge('REVIEW',sideLabel)}</div>
      <div class="feed-main">
        <div class="feed-token">${mintHtml}</div>
        <small>${esc(reason)}</small>
        <div class="hash-row"><span>Tx ${esc(short(x.signature,10,8))}</span> ${copyButton(x.signature,'复制 Tx')} ${solscan}</div>
      </div>
      <time>${new Date(Number(x.block_time)*1000).toLocaleString('zh-CN')}</time>
    </div>`;
  }).join('') || '<div class="empty">暂无待复核行为</div>';
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
    const [runtime,control,candidates,trades,reviewActivity,decisions,coverage] = await Promise.all([
      get('/api/runtime'),
      get('/api/control-health'),
      get('/api/candidates'),
      get('/api/trades'),
      get('/api/review-activity'),
      get('/api/decisions'),
      get('/api/coverage')
    ]);
    const activeCandidates = candidates.filter(x => x.position_state !== 'CLOSED');
    const endedCandidates = candidates.filter(x => x.position_state === 'CLOSED');

    renderRuntime(runtime,control);
    renderStats(activeCandidates,runtime,coverage);
    renderCoverage(coverage);
    renderCandidates(activeCandidates);
    renderEnded(endedCandidates);
    renderTrades(trades);
    renderReviewActivity(reviewActivity);
    renderDecisions(decisions);
    $('updated').textContent = `更新于 ${new Date().toLocaleTimeString('zh-CN')}`;
  } catch (e) {
    $('runtime').className = 'runtime offline';
    $('runtime').innerHTML = `<strong>控制台读取失败</strong><span>${esc(e.message)}</span>`;
  }
}

refresh();
setInterval(refresh,5000);


const clusterPresetHelp = {
  quick:'快速：Top20 全部解析；浅扫前 6 个 owner，每个最多 8 笔目标币历史 + 4 笔 funding。用于快速排雷。',
  standard:'标准：Top20 全部解析；先浅扫前 6 个 owner（12 + 8），只对出现关系证据、重大未确认角色或高风险标签的钱包自动加深到 30 + 12。',
  deep:'深度：Top20 owner 全部深扫；每个最多 100 笔目标币历史 + 50 笔 funding。仅用于高价值项目或强烈怀疑分仓/集群时。',
};

const clusterMetricLabel = {
  RAW_TOP10_PCT:'原始 Top10',
  EX_LP_TOP10_PCT:'排除 LP 后 Top10',
  EX_SPECIAL_TOP10_PCT:'排除特殊地址后 Top10',
  LARGEST_CONFIRMED_RELATION_GROUP_PCT:'最大确认关系组',
  LARGEST_PROBABLE_CONTROL_CLUSTER_PCT:'最大 probable 控制集群',
  LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT:'最大 probable 执行集群',
  DEV_LINKED_CLUSTER_PCT:'Dev 关联集群',
  CLUSTER_ADJUSTED_TOP10_PCT:'集群调整后 Top10',
  UNRESOLVED_MATERIAL_HOLDER_PCT:'重大未确认持仓',
  KNOWN_EX_LP_TOP10_PCT:'已识别池/Vault 排除后 Top10',
  KNOWN_EX_SPECIAL_TOP10_PCT:'已知标签下排除特殊地址 Top10',
  KNOWN_CLUSTER_ADJUSTED_TOP10_PCT:'已知证据下集群调整 Top10',
};

const clusterRoleLabel = {
  ORDINARY:'普通地址',
  UNRESOLVED:'未确认',
  TOKEN_ACCOUNT_OWNER_UNRESOLVED:'Token Program 地址，角色未确认',
  PROGRAM_OWNED_UNRESOLVED:'程序控制地址，角色未确认',
  PROTOCOL_VAULT:'协议/DEX Vault',
  PUBLIC_PROGRAM:'公共程序',
  PUBLIC_INFRA:'公共基础设施',
  AMM_POOL:'AMM 池',
  LP:'LP',
  CEX:'CEX',
  BRIDGE:'跨链桥',
  ROUTER:'路由',
  MARKET_MAKER:'做市',
  DEV:'Dev',
  CREATOR:'创建者',
  TREASURY:'金库',
  ESCROW:'托管',
  VESTING:'锁仓',
  LOCK:'锁定',
  BURN:'销毁',
};

const clusterEdgeLabel = {
  DIRECT_TOKEN_TRANSFER:'直接目标币转账',
  DIRECT_QUOTE_TRANSFER:'直接 SOL/USDC/WSOL 转账',
  COMMON_FUNDER_EOA:'已确认 EOA 共同资金源',
  COMMON_FUNDER_CEX:'共同 CEX 资金源（不作为共同控制）',
  COMMON_FUNDER_UNRESOLVED:'共同资金源，身份未确认',
  BATCH_FUNDING:'同一笔批量 funding',
  COMMON_SIGNER:'共同已确认 signer',
  COMMON_SIGNER_UNRESOLVED:'共同 signer，身份未确认',
  COMMON_CONSOLIDATION:'向同一已确认 EOA/Dev 地址归集',
  COMMON_CONSOLIDATION_UNRESOLVED:'向同一未确认地址归集',
  SYNC_BUY:'同步买入',
  SYNC_SELL:'同步卖出',
  IDENTICAL_SIZE:'相同下单金额',
  SAME_EXECUTION_PROGRAM:'相同非公共执行程序',
  REPEATED_SYNC_BEHAVIOR:'重复同步行为',
  SHARED_INFRA:'共享公共基础设施（不代表共同控制）',
  COMMON_FUNDER_CEX:'共同 CEX 资金源（不代表共同控制）',
};

let clusterLastAutoLoaded=false;

async function loadLatestCluster(mint, silent=false) {
  if (!mint) return false;
  try {
    const report=await get('/api/cluster-latest?mint=' + encodeURIComponent(mint));
    $('cluster-mint').value=mint;
    renderClusterReport(report);
    if (!silent) showToast('已加载上次查询结果');
    return true;
  } catch (_) {
    return false;
  }
}

function setView(name) {
  const view = name === 'cluster' ? 'cluster' : 'signals';
  const heading=$('product-title');
  if (heading) heading.textContent=view==='cluster' ? 'CA 快速分析' : 'Frank 信号';
  document.querySelectorAll('.view-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === view);
  });
  $('signals-view').classList.toggle('active', view === 'signals');
  $('cluster-view').classList.toggle('active', view === 'cluster');
  if (window.location.hash !== '#' + view) history.replaceState(null,'','#' + view);
  if (view==='cluster' && !clusterLastAutoLoaded) {
    clusterLastAutoLoaded=true;
    const mint=localStorage.getItem('mission-meme-last-cluster-ca') || '';
    if (mint) loadLatestCluster(mint,true);
  }
}

document.querySelectorAll('.view-tab').forEach(btn => {
  btn.addEventListener('click', () => setView(btn.dataset.view));
});

window.addEventListener('hashchange', () => setView(window.location.hash.slice(1)));
setView(window.location.hash.slice(1));

$('cluster-preset').addEventListener('change', (e) => {
  $('cluster-preset-help').textContent = clusterPresetHelp[e.target.value] || '';
  const values=['quick','standard','deep'];
  document.querySelectorAll('.preset-guide>div').forEach((node,index) => {
    node.classList.toggle('active',values[index]===e.target.value);
  });
});

function clusterStatus(kind, title, detail='') {
  const el = $('cluster-status');
  el.hidden = false;
  el.className = 'cluster-status ' + kind.toLowerCase();
  el.innerHTML = '<strong>' + esc(title) + '</strong>' + (detail ? '<span>' + esc(detail) + '</span>' : '');
}

function clusterMetricValue(v) {
  if (v === 'UNRESOLVED' || v == null) return '<span class="unresolved">未确认</span>';
  const x = Number(v);
  return Number.isFinite(x) ? n(x,4) + '%' : esc(v);
}


function usd(v,digits=2) {
  if (v == null || v === '') return '暂无';
  const x=Number(v);
  if (!Number.isFinite(x)) return '暂无';
  if (Math.abs(x)>=1000000) return '$' + n(x/1000000,2) + 'M';
  if (Math.abs(x)>=1000) return '$' + n(x/1000,2) + 'K';
  return '$' + n(x,digits);
}

function pctText(v) {
  if (v == null || v === '') return '暂无';
  const x=Number(v);
  return Number.isFinite(x) ? n(x,2) + '%' : '暂无';
}

function authorityText(value,status='OK') {
  if (status!=='OK') return '<span class="unresolved">未确认</span>';
  if (value == null || value==='') return '<span class="ok-text">已撤销 / null</span>';
  if (value==='UNAVAILABLE') return '<span class="unresolved">未自动确认</span>';
  return '<code>' + esc(short(String(value),8,6)) + '</code>' + copyButton(String(value),'复制');
}

function fact(label,value,sub='') {
  return '<div class="fact-card"><span>' + esc(label) + '</span><strong>' + value + '</strong>' +
    (sub ? '<small>' + sub + '</small>' : '') + '</div>';
}

function safeHttpUrl(value) {
  try {
    const u=new URL(String(value || ''));
    return (u.protocol==='http:' || u.protocol==='https:') ? u.href : '';
  } catch (_) {
    return '';
  }
}

function quoteAssetLabel(asset) {
  if (asset===WSOL_MINT || asset==='SOL') return 'SOL';
  if (asset===USDC_MINT || asset==='USDC') return 'USDC';
  return asset ? short(String(asset),6,4) : '未知';
}

function acquisitionCell(h) {
  const a=h.first_acquisition || {};
  if (a.status==='NOT_SCANNED') return '<span class="muted">未深扫</span>';
  if (a.status!=='CONFIRMED_BOUNDED') return '<span class="unresolved">未确认</span>';
  const pay=a.quote_quantity != null
    ? n(a.quote_quantity,6) + ' ' + quoteAssetLabel(a.quote_asset)
    : '支付额未解析';
  const when=a.block_time ? new Date(Number(a.block_time)*1000).toLocaleString('zh-CN') : '时间未知';
  const tx=a.signature ? '<a class="link-btn compact" href="https://solscan.io/tx/' + encodeURIComponent(a.signature) + '" target="_blank" rel="noreferrer">Tx ↗</a>' : '';
  return '<div class="holder-evidence"><b>市场买入</b><span>' + esc(pay) + '</span><small>' + esc(when) + ' ' + tx + '</small></div>';
}

function fundingCell(h) {
  const f=h.funding;
  if (!h.deep_scanned) return '<span class="muted">未深扫</span>';
  if (!f) return '<span class="unresolved">未确认</span>';
  const role=clusterRoleLabel[f.source_role] || f.source_role || '未确认';
  const link=f.source ? '<a class="link-btn compact" href="https://solscan.io/account/' + encodeURIComponent(f.source) + '" target="_blank" rel="noreferrer">查看 ↗</a>' : '';
  return '<div class="holder-evidence"><code>' + esc(short(f.source,7,5)) + '</code><span>' +
    esc(f.sol != null ? n(f.sol,6) + ' SOL' : '金额未解析') + '</span><small>' + esc(role) + ' ' + link + '</small></div>';
}

const assessmentLabel = {
  'RISK / AUTHORITY_PRESENT':'风险 / 权限仍存在',
  'RISK / ACTIVE_CHAIN_PERMISSION':'风险 / 存在有效链上权限或扩展',
  'WATCH / CHAIN_PERMISSION_UNRESOLVED':'观察 / Token-2022 权限状态待核实',
  'WATCH / CONTROL_CLUSTER_RISK':'观察 / 存在可能共同控制集群',
  'WATCH / WALLET_CLUSTER_UNRESOLVED':'观察 / 钱包集群尚未完全确认',
  'WATCH / CHAIN_STRUCTURE_PASS':'观察 / 链上结构通过当前扫描',
};

function renderAssessmentHistory(rows) {
  rows=(rows || []).slice(-6).reverse();
  if (!rows.length) return '<div class="next-checks"><b>结论变化</b><span>暂无历史结论记录</span></div>';
  return '<div class="next-checks"><b>结论变化</b>' + rows.map(row => {
    const when=row.observed_at ? new Date(Number(row.observed_at)*1000).toLocaleString('zh-CN') : '时间未知';
    const risk=(row.new_risk || []).length ? ' · 新风险 ' + (row.new_risk || []).join(', ') : '';
    const cleared=(row.removed_uncertainty || []).length ? ' · 已消除不确定项 ' + (row.removed_uncertainty || []).join(', ') : '';
    return '<span><strong>' + esc(when) + '</strong> · ' +
      esc(row.structure_rating || 'UNRESOLVED') + ' / ' + esc(row.investment_rating || 'UNRESOLVED') +
      ' · ' + esc(row.reason || '') + esc(risk) + esc(cleared) + '</span>';
  }).join('') + '</div>';
}

function clusterProgressDetail(job) {
  const p=job.progress || {};
  const stage=p.stage || job.status || 'RUNNING';
  if (stage==='BASE_READY') {
    const name=[p.name,p.symbol].filter(Boolean).join(' · ') || 'Token 信息已读取';
    return name + (p.market_cap_usd != null ? ' · MC ' + usd(p.market_cap_usd) : '') +
      (p.liquidity_usd != null ? ' · LP ' + usd(p.liquidity_usd) : '') +
      ' · 正在解析 Top20 owner';
  }
  if (stage==='HOLDERS_READY') return 'Top20 owner 已解析 ' + esc(p.top_accounts_resolved ?? 0) + ' 个，开始历史浅扫';
  if (stage==='OWNER_SCAN') return '历史浅扫 ' + esc(p.scanned ?? 0) + ' / ' + esc(p.target ?? '?') + ' 个 owner';
  if (stage==='FUNDING_SCAN') return '建仓前 funding 回看 ' + esc(p.scanned ?? 0) + ' / ' + esc(p.target ?? '?');
  if (stage==='ADAPTIVE_DEEPEN') return '发现需要继续核实的钱包，正在自适应加深 ' + esc(p.scanned ?? 0) + ' / ' + esc(p.target ?? '?');
  if (stage==='FINALIZING') return '链上扫描完成，正在生成集群、风险和结论';
  if (stage==='REPORT_PERSISTING') return '正在保存完整报告和结论变化历史';
  return job.preset === 'deep'
    ? '深度扫描会读取更多历史交易，免费 RPC 下需要更长时间。'
    : '正在执行只读链上分析…';
}


function renderClusterPreview(job) {
  const node=$('cluster-preview');
  const p=job?.preview;
  if (!node || !p) { if (node) node.hidden=true; return; }
  const known=p.token_status==='OK';
  const authRisk=known && (p.mint_authority != null || p.freeze_authority != null);
  const extRisks=(p.active_extension_risks || []).length;
  const extUnknown=(p.unresolved_extension_risks || []).length;
  const authority= !known ? '权限尚未验证'
    : (authRisk || extRisks) ? '存在活动权限或扩展风险'
    : extUnknown ? '部分扩展风险待核实'
    : '已解析权限未发现活动风险';
  const ready=p.market_status==='OK';
  const q=p.execution_quote_30_usdc;
  const quoteAt=q?.observed_at == null ? NaN : Number(q.observed_at);
  const quoteAge=Date.now()/1000-quoteAt;
  const quoteFresh=Number.isFinite(quoteAge) && quoteAge>=0 && quoteAge<=30;
  const quoteText=!q ? '正在请求 Jupiter 报价'
    : !quoteFresh ? '报价已过期，完整报告将刷新'
    : q.status==='OK' && q.route_exists===true &&
      q.execution_price_usdc != null && q.price_impact_pct != null
      ? '$'+smallPrice(q.execution_price_usdc)+' · 冲击 '+pctText(q.price_impact_pct)
      : '暂不可成交 / 报价不可用';
  node.hidden=false;
  node.innerHTML=
    '<div class="cluster-preview-head"><strong>已取得基础行情，持仓与资金关系仍在扫描</strong><span>临时结果，待链上报告核实</span></div>' +
    '<div class="cluster-preview-items">' +
    fact('代币',esc([p.name,p.symbol].filter(Boolean).join(' / ') || '名称未确认')) +
    fact('参考价',ready ? esc(usd(p.price_usd,8)) : '暂不可用') +
    fact('市值',ready ? esc(usd(p.market_cap_usd)) : '暂不可用') +
    fact('主池流动性',ready ? esc(usd(p.liquidity_usd)) : '暂不可用') +
    fact('$30 可成交报价',esc(quoteText),'Jupiter 只读报价，30 秒后过期，不能直接视为下单建议') +
    fact('权限',esc(authority)) +
    fact('原始 Top10 持币占比', p.raw_top10_resolved_pct != null
      ? esc(pctText(p.raw_top10_resolved_pct)) : '待解析', '含池子，未做 LP 排除或钱包关联归因') +
    '</div><p>已解析 Owner：' + esc(p.top_accounts_resolved ?? '待查询') +
    '。原始 Top10 可能含 LP 或交易所；钱包聚类仍在独立核对，不能据此认定筹码安全或可跟单。</p>';
}

function clusterErrorMessage(error) {
  const raw=((error?.type || '') + ' ' + (error?.message || '')).toUpperCase();
  if (raw.includes('429') || raw.includes('RATE_LIMIT')) {
    return '免费 Solana RPC 触发限流（HTTP 429）。系统已经自动降速并切换备用免费节点；如果仍失败，稍后重试，或先用“快速”档。';
  }
  if (raw.includes('403')) {
    return '当前免费 RPC 拒绝了请求（HTTP 403）。系统会尝试备用节点；持续出现时可在本机配置其他免费 RPC。';
  }
  return (error?.type || 'ERROR') + ' · ' + (error?.message || '未知错误');
}

function holderRole(h) {
  const label = clusterRoleLabel[h.role] || h.role || '未确认';
  const unresolved = String(h.role || '').includes('UNRESOLVED');
  return '<span class="role-pill ' + (unresolved ? 'unresolved-role' : '') + '">' + esc(label) + '</span>';
}

function ownerCell(owner) {
  return '<div class="owner-cell"><code>' + esc(short(owner,8,6)) + '</code>' +
    copyButton(owner,'复制') +
    '<a class="link-btn compact" href="https://solscan.io/account/' + encodeURIComponent(owner) + '" target="_blank" rel="noreferrer">查看 ↗</a></div>';
}

function renderClusterGroup(group, kind) {
  const confidence = group.confidence || kind;
  const evidence = Array.isArray(group.evidence) ? group.evidence : [];
  const edgeTypes = [...new Set(evidence.map(e => clusterEdgeLabel[e.type] || e.type))];
  const wallets = (group.wallets || []).map(w =>
    '<div class="cluster-wallet">' + ownerCell(w) + '<span>' +
    esc(n((group.wallet_balances_raw || {})[w],0)) + ' raw</span></div>'
  ).join('');
  return '<article class="cluster-card">' +
    '<div class="cluster-card-head"><div><span class="confidence ' + esc(String(confidence).toLowerCase()) + '">' +
      esc(confidence === 'CONFIRMED_RELATION' ? '确认关系' : confidence === 'PROBABLE_CONTROL_CLUSTER' ? '可能共同控制' : '可能共同执行') +
    '</span><strong>' + esc(group.cluster_id || '') + '</strong></div><b>' + esc(group.supply_pct || '0') + '%</b></div>' +
    '<div class="cluster-wallets">' + wallets + '</div>' +
    '<div class="cluster-evidence-tags">' + (edgeTypes.map(x => '<span>' + esc(x) + '</span>').join('') || '<span>无自动证据摘要</span>') + '</div>' +
  '</article>';
}

function renderClusterReport(report) {
  $('cluster-result').hidden = false;
  $('cluster-preview').hidden = true;
  const coverage = report.coverage || {};
  const metrics = report.metrics || {};
  const mint = report.mint || '';
  const strictComplete = coverage.special_normalization_complete === true;
  const ctrl = report.probable_control_clusters || [];
  const exec = report.probable_execution_clusters || [];
  const rel = report.confirmed_relation_groups || [];
  const unresolvedEdges = report.unresolved_relation_edges || [];
  const errors = report.transaction_errors || [];
  const profile = report.token_profile || {};
  const market = report.market || {};
  const mainPair = market.main_pair || {};
  const quote = report.execution_quote_30_usdc || {};
  const assessment = report.assessment || {};

  const observedAt = report.observed_at == null ? NaN : Number(report.observed_at);
  const observedText = Number.isFinite(observedAt)
    ? new Date(observedAt * 1000).toLocaleString('zh-CN')
    : '时间未知';
  const observedAge = Number.isFinite(observedAt) ? age(observedAt) : '时间未知';
  const tokenName = market.name || '名称未取到';
  const tokenSymbol = market.symbol || '—';

  $('cluster-summary').innerHTML = [
    ['代币', '<span>' + esc(tokenName) + '</span><span class="subvalue">' + esc(tokenSymbol) + '</span>'],
    ['CA', '<code class="summary-ca">' + esc(mint) + '</code>' + copyButton(mint,'复制 CA')],
    ['参考价', market.status==='OK' && market.price_usd != null ? esc('$'+smallPrice(market.price_usd)) : '<span class="unresolved">不可用</span>'],
    ['市值', esc(usd(market.market_cap_usd))],
    ['流动性', esc(usd(mainPair.liquidity_usd))],
  ].map(([k,v]) => '<div class="cluster-summary-card"><span>' + k + '</span><strong>' + v + '</strong></div>').join('');

  const activeAuthorities = assessment.active_authorities || [];
  const activeExtensionRisks=assessment.active_extension_risks || [];
  const unresolvedExtensionRisks=assessment.unresolved_extension_risks || [];
  let chainConclusion = '合约权限未确认';
  if (assessment.chain_permission_status === 'PASS') {
    chainConclusion = 'Mint authority 与 Freeze authority 均未活动；已解析的敏感 Token-2022 扩展未发现活动风险。';
  } else if (assessment.chain_permission_status === 'RISK') {
    const risks=activeAuthorities.concat(activeExtensionRisks.map(x => 'Token-2022 ' + (x.name || '扩展') + ' / ' + (x.reason || 'ACTIVE_RISK')));
    chainConclusion = '存在活动链上权限/扩展风险：' + risks.join('、') + '。';
  } else if (assessment.chain_permission_status === 'UNRESOLVED' && unresolvedExtensionRisks.length) {
    chainConclusion = '存在 Token-2022 敏感扩展，但当前 RPC 解析信息不足以判断其是否活动：' +
      unresolvedExtensionRisks.map(x => (x.name || '扩展') + ' / ' + (x.reason || 'UNRESOLVED')).join('、') + '。';
  }

  let clusterConclusion = '钱包集群状态未确认';
  if (assessment.cluster_status === 'PROBABLE_CONTROL_CLUSTER_PRESENT') {
    clusterConclusion = '发现可能共同控制集群，最大占比 ' + (metrics.LARGEST_PROBABLE_CONTROL_CLUSTER_PCT || '未知') + '%。';
  } else if (assessment.cluster_status === 'WALLET_CLUSTER_UNRESOLVED') {
    const unknownShare = metrics.UNRESOLVED_MATERIAL_HOLDER_PCT;
    clusterConclusion = '当前未完成全部钱包归因；重大未确认持仓约 ' +
      (unknownShare == null || unknownShare === 'UNRESOLVED' ? '未确认' : unknownShare + '%') +
      '。不能写成“筹码已确认干净”。';
  } else if (assessment.cluster_status === 'NO_MATERIAL_CONTROL_CLUSTER_FOUND') {
    clusterConclusion = '当前 bounded scan 未发现重大 probable control cluster。';
  }

  if (rel.length) {
    const confirmedMax = Math.max(...rel.map(x=>Number(x.supply_pct)).filter(Number.isFinite));
    if (Number.isFinite(confirmedMax)) {
      clusterConclusion = '发现直接资金或代币关系，最大关联组约 ' + n(confirmedMax,2) +
        '%；这不能证明同一控制人。' + clusterConclusion;
    }
  }

  let marketConclusion = '当前市场数据未取到。';
  if (market.status === 'OK') {
    const h24 = (mainPair.volume || {}).h24;
    marketConclusion = '参考价 $' + smallPrice(market.price_usd) +
      ' · MC ' + usd(market.market_cap_usd) +
      ' · 主池流动性 ' + usd(mainPair.liquidity_usd) +
      ' · 24h 成交 ' + usd(h24) + '。';
  }

  const structureConclusion=assessmentLabel[assessment.trading_status] || assessment.trading_status || '等待数据';
  $('cluster-conclusion').innerHTML =
    '<div class="conclusion-leads">' +
      '<div class="conclusion-lead"><span>链上 / 市场结构结论</span><strong>' + esc(structureConclusion) + '</strong></div>' +
    '</div>' +
    '<div class="conclusion-grid">' +
      '<div><b>链上权限</b><p>' + esc(chainConclusion) + '</p></div>' +
      '<div><b>Holder / Cluster</b><p>' + esc(clusterConclusion) + '</p></div>' +
      '<div><b>市场状态</b><p>' + esc(marketConclusion) + '</p></div>' +
    '</div>' +
    '<details class="cluster-assessment-history"><summary>历史判断变化（仅供复核）</summary>' +
    renderAssessmentHistory(report.assessment_history) + '</details>';

  const supplyApprox = report.supply_raw == null || report.decimals == null
    ? NaN : Number(report.supply_raw) / (10 ** Number(report.decimals));
  $('cluster-token-profile').innerHTML =
    fact('名称 / Symbol','<span>' + esc(tokenName) + ' · ' + esc(tokenSymbol) + '</span>','名称来自市场元数据；权限来自链上') +
    fact('Token Program','<span>' + esc(profile.token_program || '未确认') + '</span>') +
    fact('Supply','<span>' + esc(Number.isFinite(supplyApprox) ? n(supplyApprox,2) : '暂无') + '</span>') +
    fact('Mint authority',authorityText(profile.mint_authority,profile.status)) +
    fact('Freeze authority',authorityText(profile.freeze_authority,profile.status)) +
    fact('Metadata update authority',authorityText(profile.metadata_update_authority,profile.metadata_update_authority_status==='CHAIN_PARSED' ? 'OK' : 'UNAVAILABLE')) +
    fact('Token-2022 扩展','<span>' + esc((profile.extensions || []).join(', ') || '无已解析扩展') + '</span>') +
    fact('活动扩展风险','<span>' + ((profile.active_extension_risks || []).length ? '<span class="warn-text">' + esc((profile.active_extension_risks || []).map(x => (x.name || '扩展') + ': ' + (x.reason || 'ACTIVE_RISK')).join(', ')) + '</span>' : '<span class="ok-text">未发现</span>') + '</span>') +
    fact('非活动敏感扩展','<span>' + esc((profile.inactive_sensitive_extensions || []).map(x => x.name || '扩展').join(', ') || '无') + '</span>') +
    fact('待核实敏感扩展','<span>' + ((profile.unresolved_sensitive_extensions || []).length ? '<span class="warn-text">' + esc((profile.unresolved_sensitive_extensions || []).map(x => x.name || '扩展').join(', ')) + '</span>' : '<span class="ok-text">无</span>') + '</span>');

  const h24tx=(mainPair.txns || {}).h24 || {};
  const h1tx=(mainPair.txns || {}).h1 || {};
  const safeMarketUrl=safeHttpUrl(mainPair.url);
  const marketUrl=safeMarketUrl
    ? '<a class="link-btn compact" href="' + esc(safeMarketUrl) + '" target="_blank" rel="noreferrer">市场页 ↗</a>'
    : '';
  const pairLink=mainPair.pair_address
    ? '<a class="link-btn compact" href="https://solscan.io/account/' + encodeURIComponent(mainPair.pair_address) + '" target="_blank" rel="noreferrer">Pool ↗</a>'
    : '';
  const finalQuoteAt = quote.observed_at == null ? NaN : Number(quote.observed_at);
  const finalQuoteAge = Date.now()/1000 - finalQuoteAt;
  const finalQuoteFresh = Number.isFinite(finalQuoteAge) && finalQuoteAge>=0 && finalQuoteAge<=30;
  const quoteText = !finalQuoteFresh
    ? '<span class="unresolved">报价已过期，请重新查询</span>'
    : quote.status==='OK' && quote.route_exists===true &&
      quote.execution_price_usdc != null && quote.price_impact_pct != null
      ? '$'+smallPrice(quote.execution_price_usdc) + '<span class="subvalue">冲击 ' + pctText(quote.price_impact_pct) + '</span>'
      : '<span class="unresolved">' + esc(quote.reason || '报价不可用') + '</span>';

  $('cluster-market').innerHTML =
    fact('查询时参考价','<span>' + (market.status==='OK' && market.price_usd != null ? '$'+smallPrice(market.price_usd) : '<span class="unresolved">不可用</span>') + '</span>','DexScreener 参考价') +
    fact('$30 实际可成交价','<span>' + quoteText + '</span>','Jupiter read-only quote') +
    fact('Market Cap','<span>' + (market.status==='OK' ? usd(market.market_cap_usd) : '暂无') + '</span>') +
    fact('主池流动性','<span>' + (market.status==='OK' ? usd(mainPair.liquidity_usd) : '暂无') + '</span>') +
    fact('24h 成交额','<span>' + (market.status==='OK' ? usd((mainPair.volume || {}).h24) : '暂无') + '</span>') +
    fact('24h 买 / 卖','<span>' + esc((h24tx.buys ?? '—') + ' / ' + (h24tx.sells ?? '—')) + '</span>') +
    fact('1h 买 / 卖','<span>' + esc((h1tx.buys ?? '—') + ' / ' + (h1tx.sells ?? '—')) + '</span>') +
    fact('价格变化','<span>1h ' + esc(pctText((mainPair.price_change || {}).h1)) + ' · 24h ' + esc(pctText((mainPair.price_change || {}).h24)) + '</span>') +
    fact('主池 / DEX','<span>' + esc((mainPair.dex_id || '未确认') + ' · ' + short(mainPair.pair_address || '',7,5)) + '</span>',pairLink + ' ' + marketUrl);

  const primary = [
    'RAW_TOP10_PCT','KNOWN_EX_LP_TOP10_PCT','DEV_LINKED_CLUSTER_PCT',
    'LARGEST_PROBABLE_CONTROL_CLUSTER_PCT','UNRESOLVED_MATERIAL_HOLDER_PCT'
  ];
  const extra = [
    'EX_LP_TOP10_PCT','EX_SPECIAL_TOP10_PCT','LARGEST_CONFIRMED_RELATION_GROUP_PCT',
    'LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT','CLUSTER_ADJUSTED_TOP10_PCT'
  ];
  const renderConcentration = key =>
    '<div class="cluster-metric"><span>' + esc(clusterMetricLabel[key] || key) + '</span><strong>' +
    clusterMetricValue(metrics[key]) + '</strong></div>';
  $('cluster-metrics').innerHTML = primary.map(renderConcentration).join('') +
    '<details class="cluster-extra-metrics"><summary>查看其余集中度指标</summary><div class="cluster-metrics-extra">' +
    extra.map(renderConcentration).join('') + '</div></details>';

  $('cluster-holders').innerHTML = (report.holders || []).map(h =>
    '<tr><td>' + esc(h.rank) + '</td><td>' + ownerCell(h.owner) + '</td><td>' +
    esc(h.supply_pct) + '%</td><td>' + holderRole(h) + '</td><td>' +
    fundingCell(h) + '</td><td>' + acquisitionCell(h) + '</td></tr>'
  ).join('') || '<tr><td colspan="6" class="empty">没有可解析 holder</td></tr>';

  const rpcFailures=Object.values(coverage.rpc_endpoint_failures || {}).reduce((a,b)=>a+Number(b||0),0);
  const warnings = [];
  if (!strictComplete) warnings.push('特殊地址身份归一化尚未完成，严格 EX_* / cluster-adjusted 指标会保持“未确认”；“已识别 LP 后 Top10”仍可作为部分事实查看。');
  if (unresolvedEdges.length) warnings.push('存在 ' + unresolvedEdges.length + ' 条未确认共同 funder/signer/归集关系，未升级为共同控制。');
  if (errors.length) warnings.push('有 ' + errors.length + ' 笔历史交易读取/解析失败，覆盖率不是 100%。');
  if (rpcFailures) warnings.push('免费 RPC 共出现 ' + rpcFailures + ' 次失败/限流，系统已尝试自动降速或切换备用节点。');
  if (market.status!=='OK') warnings.push('市场参考数据不可用：' + (market.reason || 'UNKNOWN') + '。链上 holder 结果仍可独立成立。');

  $('cluster-coverage').innerHTML =
    '<div class="coverage-grid">' +
      '<div><span>RPC 调用</span><strong>' + esc(coverage.rpc_calls ?? 0) + '</strong></div>' +
      '<div><span>本地缓存命中</span><strong>' + esc(coverage.rpc_cache_hits ?? 0) + '</strong></div>' +
      '<div><span>使用 RPC 节点</span><strong>' + esc(Object.keys(coverage.rpc_endpoint_calls || {}).length || 1) + '</strong></div>' +
      '<div><span>RPC 失败/限流</span><strong>' + esc(rpcFailures) + '</strong></div>' +
      '<div><span>每 owner 历史上限</span><strong>' + esc(coverage.history_per_holder ?? 0) + '</strong></div>' +
      '<div><span>Funding 回看</span><strong>' + esc(coverage.funding_lookback ?? 0) + '</strong></div>' +
    '</div>' +
    '<div class="trust-box">' + (warnings.map(x => '<p>⚠ ' + esc(x) + '</p>').join('') || '<p class="ok-text">当前自动分析未发现覆盖率警告。</p>') + '</div>';

  $('cluster-control').innerHTML =
    rel.map(g => renderClusterGroup(g,'relation')).join('') +
    ctrl.map(g => renderClusterGroup(g,'control')).join('') ||
    '<div class="empty">当前 bounded evidence 未形成确认关系组或 probable 控制集群</div>';

  $('cluster-execution').innerHTML =
    exec.map(g => renderClusterGroup(g,'execution')).join('') ||
    '<div class="empty">当前 bounded evidence 未形成 probable 执行集群</div>';

  const edges = report.edges || [];
  const grouped = {};
  edges.forEach(e => grouped[e.type] = (grouped[e.type] || 0) + 1);
  $('cluster-evidence').innerHTML =
    '<div class="evidence-counts">' +
      Object.entries(grouped).sort((a,b)=>b[1]-a[1]).map(([type,count]) =>
        '<div><span>' + esc(clusterEdgeLabel[type] || type) + '</span><strong>' + esc(count) + '</strong></div>'
      ).join('') +
    '</div>' +
    '<details class="cluster-raw-details"><summary>查看覆盖与限制说明</summary>' +
      '<div class="limitations">' + (report.limitations || []).map(x => '<p>' + esc(x) + '</p>').join('') + '</div>' +
    '</details>';

  const websites=(market.websites || []).map(url => safeHttpUrl(url)).filter(Boolean).map(url =>
    '<a class="link-btn" href="' + esc(url) + '" target="_blank" rel="noreferrer">网站 ↗</a>'
  ).join('');
  const socials=(market.socials || []).map(x =>
    '<span class="narrative-link">' + esc((x.platform || 'social') + ': ' + (x.handle || '')) + '</span>'
  ).join('');
  $('cluster-narrative').innerHTML =
    '<div class="narrative-state"><strong>未接入 X/FOMO 外部叙事检索</strong>' +
    '<p>目前仅展示市场资料附带的链接；不抓取实时官方帖子，也不提供官方认领或叙事打分。</p></div>' +
    '<div class="narrative-links">' + (websites || socials ? websites + socials : '<span class="muted">当前市场资料没有可展示的官网/社交链接</span>') + '</div>';

  clusterStatus('done','分析已更新', '数据时间 ' + observedAge + (rpcFailures ? ' · 有部分链上请求失败，详情见证据' : ''));
}


let clusterPollTimer = null;

async function pollClusterJob(jobId) {
  clearTimeout(clusterPollTimer);
  try {
    const job = await get('/api/cluster-analysis?job_id=' + encodeURIComponent(jobId));
    if (job.status === 'DONE') {
      $('cluster-submit').disabled = false;
      $('cluster-submit').textContent = '重新查询';
      localStorage.setItem('mission-meme-last-cluster-ca',job.mint);
      const loaded=await loadLatestCluster(job.mint,true);
      if (!loaded) clusterStatus('error','查询已完成，但结果文件读取失败');
      return;
    }
    if (job.status === 'ERROR') {
      $('cluster-preview').hidden = true;
      $('cluster-submit').disabled = false;
      $('cluster-submit').textContent = '重新查询';
      clusterStatus('error','查询失败',clusterErrorMessage(job.error));
      return;
    }
    renderClusterPreview(job);
    clusterStatus('running',
      job.status === 'QUEUED' ? '等待开始分析' : '正在扫描链上数据',
      clusterProgressDetail(job));
    clusterPollTimer = setTimeout(() => pollClusterJob(jobId), 1200);
  } catch (e) {
    $('cluster-submit').disabled = false;
    clusterStatus('error','查询状态读取失败',e.message);
  }
}

$('cluster-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const mint = $('cluster-mint').value.trim();
  const preset = $('cluster-preset').value;
  if (!mint) {
    clusterStatus('error','请输入 Solana CA');
    return;
  }
  $('cluster-submit').disabled = true;
  $('cluster-submit').textContent = '分析中…';
  $('cluster-result').hidden = true;
  $('cluster-preview').hidden = true;
  clusterStatus('running','准备链上分析','只读查询，不连接钱包，不发交易。');
  try {
    const r = await fetch('/api/cluster-analysis',{
      method:'POST',
      cache:'no-store',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({mint,preset}),
    });
    const payload = await r.json();
    if (!r.ok) throw new Error(payload.error || ('HTTP ' + r.status));
    localStorage.setItem('mission-meme-last-cluster-ca',mint);
    pollClusterJob(payload.job_id);
  } catch (e) {
    $('cluster-submit').disabled = false;
    $('cluster-submit').textContent = '开始查询';
    clusterStatus('error','无法开始查询',e.message);
  }
});

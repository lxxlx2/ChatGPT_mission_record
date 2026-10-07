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
  return `<a class="link-btn" href="https://solscan.io/token/${encoded}" target="_blank" rel="noreferrer">Solscan ↗</a>`;
}

function tokenIdentity(mint) {
  if (!mint) return '<span class="muted">CA 未知</span>';
  return `
    <div class="ca-row">
      <span class="ca-label">CA</span>
      <code class="ca-full">${esc(mint)}</code>
      ${copyButton(mint,'复制 CA')}
      <button class="link-btn" type="button" data-cluster-ca="${esc(mint)}">链上查询</button>
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


const clusterPresetHelp = {
  quick:'快速：Top20 全部解析；深扫前 6 个 owner，每个最多 12 笔目标币历史 + 8 笔建仓前 funding。用于第一轮排雷。',
  standard:'标准：Top20 全部解析；深扫前 10 个 owner，每个最多 30 笔目标币历史 + 12 笔建仓前 funding。默认正式分析。',
  deep:'深度：Top20 owner 全部深扫；每个最多 100 笔目标币历史 + 50 笔建仓前 funding。用于重要项目或疑似分仓/集群，免费 RPC 压力最大。',
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
  KNOWN_EX_LP_TOP10_PCT:'已知标签下排除 LP Top10',
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
  const x=Number(v);
  if (!Number.isFinite(x)) return '暂无';
  if (Math.abs(x)>=1000000) return '
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

  const observedAt = Number(report.observed_at);
  const observedText = Number.isFinite(observedAt)
    ? new Date(observedAt * 1000).toLocaleString('zh-CN')
    : '时间未知';
  const observedAge = Number.isFinite(observedAt) ? age(observedAt) : '时间未知';
  const tokenName = market.name || '名称未取到';
  const tokenSymbol = market.symbol || '—';

  $('cluster-summary').innerHTML = [
    ['Token', '<span>' + esc(tokenName) + '</span><span class="subvalue">' + esc(tokenSymbol) + '</span>'],
    ['CA', '<code class="summary-ca">' + esc(mint) + '</code>' + copyButton(mint,'复制 CA')],
    ['观测时间', esc(observedText) + '<span class="subvalue">' + esc(observedAge) + '</span>'],
    ['Top owner 已解析', esc(coverage.top_accounts_resolved ?? 0) + ' / 20'],
    ['深扫 owner', esc(coverage.deep_holders_scanned ?? 0)],
    ['控制集群', esc(ctrl.length)],
    ['身份归一化', strictComplete ? '<span class="ok-text">已完成</span>' : '<span class="warn-text">未完成</span>'],
  ].map(([k,v]) => '<div class="cluster-summary-card"><span>' + k + '</span><strong>' + v + '</strong></div>').join('');

  const activeAuthorities = assessment.active_authorities || [];
  let chainConclusion = '合约权限未确认';
  if (assessment.chain_permission_status === 'PASS') {
    chainConclusion = 'Mint authority 与 Freeze authority 均已撤销，当前未见这两项一级权限红旗。';
  } else if (assessment.chain_permission_status === 'RISK') {
    chainConclusion = '仍存在活动权限：' + activeAuthorities.join('、') + '。需要先处理权限风险。';
  }

  let clusterConclusion = '钱包集群状态未确认';
  if (assessment.cluster_status === 'PROBABLE_CONTROL_CLUSTER_PRESENT') {
    clusterConclusion = '发现可能共同控制集群，最大占比 ' + (metrics.LARGEST_PROBABLE_CONTROL_CLUSTER_PCT || '未知') + '%。';
  } else if (assessment.cluster_status === 'WALLET_CLUSTER_UNRESOLVED') {
    clusterConclusion = '当前未完成全部钱包归因；重大未确认持仓约 ' + (metrics.UNRESOLVED_MATERIAL_HOLDER_PCT || '0') + '%。不能写成“筹码已确认干净”。';
  } else if (assessment.cluster_status === 'NO_MATERIAL_CONTROL_CLUSTER_FOUND') {
    clusterConclusion = '当前 bounded scan 未发现重大 probable control cluster。';
  }

  let marketConclusion = '当前市场数据未取到。';
  if (market.status === 'OK') {
    const h24 = (mainPair.volume || {}).h24;
    marketConclusion = '参考价 ' + usd(market.price_usd,6) +
      ' · MC ' + usd(market.market_cap_usd) +
      ' · 主池流动性 ' + usd(mainPair.liquidity_usd) +
      ' · 24h 成交 ' + usd(h24) + '。';
  }

  $('cluster-conclusion').innerHTML =
    '<div class="conclusion-lead"><span>当前结论</span><strong>' +
      esc(assessmentLabel[assessment.trading_status] || assessment.trading_status || '等待数据') +
    '</strong></div>' +
    '<div class="conclusion-grid">' +
      '<div><b>链上权限</b><p>' + esc(chainConclusion) + '</p></div>' +
      '<div><b>Holder / Cluster</b><p>' + esc(clusterConclusion) + '</p></div>' +
      '<div><b>市场状态</b><p>' + esc(marketConclusion) + '</p></div>' +
      '<div><b>叙事关系</b><p>项目方是否正式确认 exact CA、creator fee claim、买入或锁仓，当前本地工具不会仅凭币名/X 链接自动确认。</p></div>' +
    '</div>' +
    '<div class="next-checks"><b>下一步最值得核实</b>' +
      '<span>① 项目方/叙事主体是否明确确认这个 CA</span>' +
      '<span>② creator claim → 买入 → lock/treasury 是否能链上闭环</span>' +
      '<span>③ ATH/关键价位用历史行情或实时盘口验证，不从当前快照猜</span>' +
    '</div>';

  const supplyApprox = Number(report.supply_raw) / (10 ** Number(report.decimals || 0));
  $('cluster-token-profile').innerHTML =
    fact('名称 / Symbol','<span>' + esc(tokenName) + ' · ' + esc(tokenSymbol) + '</span>','名称来自市场元数据；权限来自链上') +
    fact('Token Program','<span>' + esc(profile.token_program || '未确认') + '</span>') +
    fact('Supply','<span>' + esc(Number.isFinite(supplyApprox) ? n(supplyApprox,2) : '暂无') + '</span>') +
    fact('Mint authority',authorityText(profile.mint_authority,profile.status)) +
    fact('Freeze authority',authorityText(profile.freeze_authority,profile.status)) +
    fact('Metadata update authority',authorityText(profile.metadata_update_authority,profile.metadata_update_authority_status==='CHAIN_PARSED' ? 'OK' : 'UNAVAILABLE'));

  const h24tx=(mainPair.txns || {}).h24 || {};
  const h1tx=(mainPair.txns || {}).h1 || {};
  const marketUrl=mainPair.url
    ? '<a class="link-btn compact" href="' + esc(mainPair.url) + '" target="_blank" rel="noreferrer">市场页 ↗</a>'
    : '';
  const pairLink=mainPair.pair_address
    ? '<a class="link-btn compact" href="https://solscan.io/account/' + encodeURIComponent(mainPair.pair_address) + '" target="_blank" rel="noreferrer">Pool ↗</a>'
    : '';
  const quoteText = quote.status==='OK' && quote.route_exists
    ? usd(quote.execution_price_usdc,8) + '<span class="subvalue">冲击 ' + pctText(quote.price_impact_pct) + '</span>'
    : '<span class="unresolved">' + esc(quote.reason || '报价不可用') + '</span>';

  $('cluster-market').innerHTML =
    fact('当前参考价','<span>' + (market.status==='OK' ? usd(market.price_usd,8) : '<span class="unresolved">不可用</span>') + '</span>','DexScreener 参考价') +
    fact('$30 实际可成交价','<span>' + quoteText + '</span>','Jupiter read-only quote') +
    fact('Market Cap','<span>' + (market.status==='OK' ? usd(market.market_cap_usd) : '暂无') + '</span>') +
    fact('主池流动性','<span>' + (market.status==='OK' ? usd(mainPair.liquidity_usd) : '暂无') + '</span>') +
    fact('24h 成交额','<span>' + (market.status==='OK' ? usd((mainPair.volume || {}).h24) : '暂无') + '</span>') +
    fact('24h 买 / 卖','<span>' + esc((h24tx.buys ?? '—') + ' / ' + (h24tx.sells ?? '—')) + '</span>') +
    fact('1h 买 / 卖','<span>' + esc((h1tx.buys ?? '—') + ' / ' + (h1tx.sells ?? '—')) + '</span>') +
    fact('价格变化','<span>1h ' + esc(pctText((mainPair.price_change || {}).h1)) + ' · 24h ' + esc(pctText((mainPair.price_change || {}).h24)) + '</span>') +
    fact('主池 / DEX','<span>' + esc((mainPair.dex_id || '未确认') + ' · ' + short(mainPair.pair_address || '',7,5)) + '</span>',pairLink + ' ' + marketUrl);

  const primary = [
    'RAW_TOP10_PCT','KNOWN_EX_LP_TOP10_PCT','EX_LP_TOP10_PCT','EX_SPECIAL_TOP10_PCT',
    'LARGEST_CONFIRMED_RELATION_GROUP_PCT','LARGEST_PROBABLE_CONTROL_CLUSTER_PCT',
    'LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT','DEV_LINKED_CLUSTER_PCT',
    'CLUSTER_ADJUSTED_TOP10_PCT','UNRESOLVED_MATERIAL_HOLDER_PCT'
  ];
  $('cluster-metrics').innerHTML = primary.map(key =>
    '<div class="cluster-metric"><span>' + esc(clusterMetricLabel[key] || key) + '</span><strong>' +
    clusterMetricValue(metrics[key]) + '</strong></div>'
  ).join('');

  $('cluster-holders').innerHTML = (report.holders || []).map(h =>
    '<tr><td>' + esc(h.rank) + '</td><td>' + ownerCell(h.owner) + '</td><td>' +
    esc(h.supply_pct) + '%</td><td>' + holderRole(h) + '</td><td>' +
    acquisitionCell(h) + '</td><td>' + fundingCell(h) + '</td></tr>'
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

  const websites=(market.websites || []).map(url =>
    '<a class="link-btn" href="' + esc(url) + '" target="_blank" rel="noreferrer">网站 ↗</a>'
  ).join('');
  const socials=(market.socials || []).map(x =>
    '<span class="narrative-link">' + esc((x.platform || 'social') + ': ' + (x.handle || '')) + '</span>'
  ).join('');
  $('cluster-narrative').innerHTML =
    '<div class="narrative-state"><strong>未自动确认项目方/叙事主体与 exact CA 的关系</strong>' +
    '<p>这里可以展示 token profile 中的公开链接，但链接存在 ≠ 项目方认领。creator fee claim、creator 买入、lock/treasury 关系必须另外做第一方或链上闭环。</p></div>' +
    '<div class="narrative-links">' + (websites || socials ? websites + socials : '<span class="muted">当前市场资料没有可展示的官网/社交链接</span>') + '</div>';

  clusterStatus('done','查询完成',
    '观测于 ' + observedText + '（' + observedAge + '） · finalized RPC 调用 ' +
    (coverage.rpc_calls ?? 0) + ' · 本地缓存命中 ' + (coverage.rpc_cache_hits ?? 0) +
    (rpcFailures ? ' · 自动处理 RPC 失败/限流 ' + rpcFailures + ' 次' : ''));
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
      $('cluster-submit').disabled = false;
      $('cluster-submit').textContent = '重新查询';
      clusterStatus('error','查询失败',clusterErrorMessage(job.error));
      return;
    }
    clusterStatus('running',
      job.status === 'QUEUED' ? '等待开始分析' : '正在扫描链上数据',
      job.preset === 'deep' ? '深度扫描会读取更多历史交易，免费 RPC 下需要更长时间。' : '正在解析 owner、资金源、转账和同步行为…');
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
 + n(x/1000000,2) + 'M';
  if (Math.abs(x)>=1000) return '
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
  const coverage = report.coverage || {};
  const metrics = report.metrics || {};
  const mint = report.mint || '';
  const strictComplete = coverage.special_normalization_complete === true;
  const ctrl = report.probable_control_clusters || [];
  const exec = report.probable_execution_clusters || [];
  const rel = report.confirmed_relation_groups || [];
  const unresolvedEdges = report.unresolved_relation_edges || [];
  const errors = report.transaction_errors || [];

  const observedAt = Number(report.observed_at);
  const observedText = Number.isFinite(observedAt)
    ? new Date(observedAt * 1000).toLocaleString('zh-CN')
    : '时间未知';
  const observedAge = Number.isFinite(observedAt) ? age(observedAt) : '时间未知';

  $('cluster-summary').innerHTML = [
    ['CA', '<code class="summary-ca">' + esc(mint) + '</code>' + copyButton(mint,'复制 CA')],
    ['观测时间', esc(observedText) + '<span class="subvalue">' + esc(observedAge) + '</span>'],
    ['Top owner 已解析', esc(coverage.top_accounts_resolved ?? 0) + ' / 20'],
    ['深扫 owner', esc(coverage.deep_holders_scanned ?? 0)],
    ['控制集群', esc(ctrl.length)],
    ['执行集群', esc(exec.length)],
    ['身份归一化', strictComplete ? '<span class="ok-text">已完成</span>' : '<span class="warn-text">未完成</span>'],
  ].map(([k,v]) => '<div class="cluster-summary-card"><span>' + k + '</span><strong>' + v + '</strong></div>').join('');

  const primary = [
    'RAW_TOP10_PCT','EX_LP_TOP10_PCT','EX_SPECIAL_TOP10_PCT',
    'LARGEST_CONFIRMED_RELATION_GROUP_PCT','LARGEST_PROBABLE_CONTROL_CLUSTER_PCT',
    'LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT','DEV_LINKED_CLUSTER_PCT',
    'CLUSTER_ADJUSTED_TOP10_PCT','UNRESOLVED_MATERIAL_HOLDER_PCT'
  ];
  $('cluster-metrics').innerHTML = primary.map(key =>
    '<div class="cluster-metric"><span>' + esc(clusterMetricLabel[key] || key) + '</span><strong>' +
    clusterMetricValue(metrics[key]) + '</strong></div>'
  ).join('');

  $('cluster-holders').innerHTML = (report.holders || []).map(h =>
    '<tr><td>' + esc(h.rank) + '</td><td>' + ownerCell(h.owner) + '</td><td>' +
    esc(h.supply_pct) + '%</td><td>' + holderRole(h) + '</td></tr>'
  ).join('') || '<tr><td colspan="4" class="empty">没有可解析 holder</td></tr>';

  const warnings = [];
  if (!strictComplete) warnings.push('特殊地址身份归一化尚未完成，严格 EX_* / cluster-adjusted 指标会保持“未确认”。');
  if (unresolvedEdges.length) warnings.push('存在 ' + unresolvedEdges.length + ' 条未确认共同 funder/signer/归集关系，未升级为共同控制。');
  if (errors.length) warnings.push('有 ' + errors.length + ' 笔历史交易读取/解析失败，覆盖率不是 100%。');
  $('cluster-coverage').innerHTML =
    '<div class="coverage-grid">' +
      '<div><span>RPC 调用</span><strong>' + esc(coverage.rpc_calls ?? 0) + '</strong></div>' +
      '<div><span>本地缓存命中</span><strong>' + esc(coverage.rpc_cache_hits ?? 0) + '</strong></div>' +
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

  clusterStatus('done','查询完成',
    '观测于 ' + observedText + '（' + observedAge + '） · 数据源：Solana finalized JSON-RPC · RPC 调用 ' +
    (coverage.rpc_calls ?? 0) + ' · 缓存命中 ' + (coverage.rpc_cache_hits ?? 0));
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
      $('cluster-submit').disabled = false;
      $('cluster-submit').textContent = '重新查询';
      clusterStatus('error','查询失败', (job.error?.type || 'ERROR') + ' · ' + (job.error?.message || '未知错误'));
      return;
    }
    clusterStatus('running',
      job.status === 'QUEUED' ? '等待开始分析' : '正在扫描链上数据',
      job.preset === 'deep' ? '深度扫描会读取更多历史交易，免费 RPC 下需要更长时间。' : '正在解析 owner、资金源、转账和同步行为…');
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
 + n(x/1000,2) + 'K';
  return '
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
  const coverage = report.coverage || {};
  const metrics = report.metrics || {};
  const mint = report.mint || '';
  const strictComplete = coverage.special_normalization_complete === true;
  const ctrl = report.probable_control_clusters || [];
  const exec = report.probable_execution_clusters || [];
  const rel = report.confirmed_relation_groups || [];
  const unresolvedEdges = report.unresolved_relation_edges || [];
  const errors = report.transaction_errors || [];

  const observedAt = Number(report.observed_at);
  const observedText = Number.isFinite(observedAt)
    ? new Date(observedAt * 1000).toLocaleString('zh-CN')
    : '时间未知';
  const observedAge = Number.isFinite(observedAt) ? age(observedAt) : '时间未知';

  $('cluster-summary').innerHTML = [
    ['CA', '<code class="summary-ca">' + esc(mint) + '</code>' + copyButton(mint,'复制 CA')],
    ['观测时间', esc(observedText) + '<span class="subvalue">' + esc(observedAge) + '</span>'],
    ['Top owner 已解析', esc(coverage.top_accounts_resolved ?? 0) + ' / 20'],
    ['深扫 owner', esc(coverage.deep_holders_scanned ?? 0)],
    ['控制集群', esc(ctrl.length)],
    ['执行集群', esc(exec.length)],
    ['身份归一化', strictComplete ? '<span class="ok-text">已完成</span>' : '<span class="warn-text">未完成</span>'],
  ].map(([k,v]) => '<div class="cluster-summary-card"><span>' + k + '</span><strong>' + v + '</strong></div>').join('');

  const primary = [
    'RAW_TOP10_PCT','EX_LP_TOP10_PCT','EX_SPECIAL_TOP10_PCT',
    'LARGEST_CONFIRMED_RELATION_GROUP_PCT','LARGEST_PROBABLE_CONTROL_CLUSTER_PCT',
    'LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT','DEV_LINKED_CLUSTER_PCT',
    'CLUSTER_ADJUSTED_TOP10_PCT','UNRESOLVED_MATERIAL_HOLDER_PCT'
  ];
  $('cluster-metrics').innerHTML = primary.map(key =>
    '<div class="cluster-metric"><span>' + esc(clusterMetricLabel[key] || key) + '</span><strong>' +
    clusterMetricValue(metrics[key]) + '</strong></div>'
  ).join('');

  $('cluster-holders').innerHTML = (report.holders || []).map(h =>
    '<tr><td>' + esc(h.rank) + '</td><td>' + ownerCell(h.owner) + '</td><td>' +
    esc(h.supply_pct) + '%</td><td>' + holderRole(h) + '</td></tr>'
  ).join('') || '<tr><td colspan="4" class="empty">没有可解析 holder</td></tr>';

  const warnings = [];
  if (!strictComplete) warnings.push('特殊地址身份归一化尚未完成，严格 EX_* / cluster-adjusted 指标会保持“未确认”。');
  if (unresolvedEdges.length) warnings.push('存在 ' + unresolvedEdges.length + ' 条未确认共同 funder/signer/归集关系，未升级为共同控制。');
  if (errors.length) warnings.push('有 ' + errors.length + ' 笔历史交易读取/解析失败，覆盖率不是 100%。');
  $('cluster-coverage').innerHTML =
    '<div class="coverage-grid">' +
      '<div><span>RPC 调用</span><strong>' + esc(coverage.rpc_calls ?? 0) + '</strong></div>' +
      '<div><span>本地缓存命中</span><strong>' + esc(coverage.rpc_cache_hits ?? 0) + '</strong></div>' +
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

  clusterStatus('done','查询完成',
    '观测于 ' + observedText + '（' + observedAge + '） · 数据源：Solana finalized JSON-RPC · RPC 调用 ' +
    (coverage.rpc_calls ?? 0) + ' · 缓存命中 ' + (coverage.rpc_cache_hits ?? 0));
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
      $('cluster-submit').disabled = false;
      $('cluster-submit').textContent = '重新查询';
      clusterStatus('error','查询失败', (job.error?.type || 'ERROR') + ' · ' + (job.error?.message || '未知错误'));
      return;
    }
    clusterStatus('running',
      job.status === 'QUEUED' ? '等待开始分析' : '正在扫描链上数据',
      job.preset === 'deep' ? '深度扫描会读取更多历史交易，免费 RPC 下需要更长时间。' : '正在解析 owner、资金源、转账和同步行为…');
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
 + n(x,digits);
}

function pctText(v) {
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
  'WATCH / CONTROL_CLUSTER_RISK':'观察 / 存在可能共同控制集群',
  'WATCH / WALLET_CLUSTER_UNRESOLVED':'观察 / 钱包集群尚未完全确认',
  'WATCH / CHAIN_STRUCTURE_PASS':'观察 / 链上结构通过当前扫描',
};

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
  const coverage = report.coverage || {};
  const metrics = report.metrics || {};
  const mint = report.mint || '';
  const strictComplete = coverage.special_normalization_complete === true;
  const ctrl = report.probable_control_clusters || [];
  const exec = report.probable_execution_clusters || [];
  const rel = report.confirmed_relation_groups || [];
  const unresolvedEdges = report.unresolved_relation_edges || [];
  const errors = report.transaction_errors || [];

  const observedAt = Number(report.observed_at);
  const observedText = Number.isFinite(observedAt)
    ? new Date(observedAt * 1000).toLocaleString('zh-CN')
    : '时间未知';
  const observedAge = Number.isFinite(observedAt) ? age(observedAt) : '时间未知';

  $('cluster-summary').innerHTML = [
    ['CA', '<code class="summary-ca">' + esc(mint) + '</code>' + copyButton(mint,'复制 CA')],
    ['观测时间', esc(observedText) + '<span class="subvalue">' + esc(observedAge) + '</span>'],
    ['Top owner 已解析', esc(coverage.top_accounts_resolved ?? 0) + ' / 20'],
    ['深扫 owner', esc(coverage.deep_holders_scanned ?? 0)],
    ['控制集群', esc(ctrl.length)],
    ['执行集群', esc(exec.length)],
    ['身份归一化', strictComplete ? '<span class="ok-text">已完成</span>' : '<span class="warn-text">未完成</span>'],
  ].map(([k,v]) => '<div class="cluster-summary-card"><span>' + k + '</span><strong>' + v + '</strong></div>').join('');

  const primary = [
    'RAW_TOP10_PCT','EX_LP_TOP10_PCT','EX_SPECIAL_TOP10_PCT',
    'LARGEST_CONFIRMED_RELATION_GROUP_PCT','LARGEST_PROBABLE_CONTROL_CLUSTER_PCT',
    'LARGEST_PROBABLE_EXECUTION_CLUSTER_PCT','DEV_LINKED_CLUSTER_PCT',
    'CLUSTER_ADJUSTED_TOP10_PCT','UNRESOLVED_MATERIAL_HOLDER_PCT'
  ];
  $('cluster-metrics').innerHTML = primary.map(key =>
    '<div class="cluster-metric"><span>' + esc(clusterMetricLabel[key] || key) + '</span><strong>' +
    clusterMetricValue(metrics[key]) + '</strong></div>'
  ).join('');

  $('cluster-holders').innerHTML = (report.holders || []).map(h =>
    '<tr><td>' + esc(h.rank) + '</td><td>' + ownerCell(h.owner) + '</td><td>' +
    esc(h.supply_pct) + '%</td><td>' + holderRole(h) + '</td></tr>'
  ).join('') || '<tr><td colspan="4" class="empty">没有可解析 holder</td></tr>';

  const warnings = [];
  if (!strictComplete) warnings.push('特殊地址身份归一化尚未完成，严格 EX_* / cluster-adjusted 指标会保持“未确认”。');
  if (unresolvedEdges.length) warnings.push('存在 ' + unresolvedEdges.length + ' 条未确认共同 funder/signer/归集关系，未升级为共同控制。');
  if (errors.length) warnings.push('有 ' + errors.length + ' 笔历史交易读取/解析失败，覆盖率不是 100%。');
  $('cluster-coverage').innerHTML =
    '<div class="coverage-grid">' +
      '<div><span>RPC 调用</span><strong>' + esc(coverage.rpc_calls ?? 0) + '</strong></div>' +
      '<div><span>本地缓存命中</span><strong>' + esc(coverage.rpc_cache_hits ?? 0) + '</strong></div>' +
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

  clusterStatus('done','查询完成',
    '观测于 ' + observedText + '（' + observedAge + '） · 数据源：Solana finalized JSON-RPC · RPC 调用 ' +
    (coverage.rpc_calls ?? 0) + ' · 缓存命中 ' + (coverage.rpc_cache_hits ?? 0));
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
      $('cluster-submit').disabled = false;
      $('cluster-submit').textContent = '重新查询';
      clusterStatus('error','查询失败', (job.error?.type || 'ERROR') + ' · ' + (job.error?.message || '未知错误'));
      return;
    }
    clusterStatus('running',
      job.status === 'QUEUED' ? '等待开始分析' : '正在扫描链上数据',
      job.preset === 'deep' ? '深度扫描会读取更多历史交易，免费 RPC 下需要更长时间。' : '正在解析 owner、资金源、转账和同步行为…');
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

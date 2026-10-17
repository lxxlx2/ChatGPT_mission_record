/* F01 business-tab A05 research context; read-only, no trade execution.
   The page's existing F01 cards remain the sole frozen eligibility renderer. */
(() => {
  'use strict';
  const KIND = 'FRANK_CURRENT_F01_WITH_A05_RESEARCH_CONTEXT';
  const REVIEW = 'F01_SIGNAL_VS_ARCHIVED_WALLET_REQUIRES_REVIEW';
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const validMint = (value) => typeof value === 'string' &&
    /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(value);
  const asDate = (value) => {
    if (typeof value !== 'string') return '未确认';
    const dt = new Date(value);
    return Number.isFinite(dt.getTime()) ? dt.toLocaleString('zh-CN') : '未确认';
  };
  const stateLabels = Object.freeze({
    OPEN_ACCOUNT_NONZERO: '归档观察：账户余额非零',
    OPEN_ACCOUNT_ZERO: '归档观察：账户余额为零，不代表已卖出',
    NO_OPEN_ACCOUNT_OBSERVED: '最近完整双程序扫描未观察到开放账户，不代表已卖出',
    SOURCE_UNAVAILABLE: '来源失效或不完整，余额未知',
    OUTSIDE_FROZEN_TARGET_ROSTER: '不在已冻结的 32 Mint 研究范围，余额未知'
  });
  const noEvidence = (message) => '<p class="frank-source-unavailable">' +
    escapeHtml(message) + '</p>';

  function renderModel(doc, displayedMints, nowEpoch) {
    if (!doc || typeof doc !== 'object' || doc.schema_version !== 1 ||
        doc.kind !== KIND || doc.combined_trade_permission !== false ||
        doc.archive_is_live_wallet_portfolio !== false ||
        !doc.upstream || doc.upstream.f01 !== 'SOURCE_READ' ||
        !Array.isArray(doc.candidates) ||
        !Number.isInteger(doc.candidate_count) ||
        doc.candidate_count !== doc.candidates.length) {
      return noEvidence('独立仓位来源未接入或 F01 资格不可用；不展示旧仓位。');
    }
    const expiry = doc.f01_valid_until_epoch;
    if (typeof expiry !== 'number' || !Number.isFinite(expiry) ||
        !Number.isFinite(nowEpoch) || nowEpoch >= expiry) {
      return noEvidence('F01 当前资格已过期，等待下一次刷新；旧 BUY 不应继续跟随。');
    }
    if (doc.candidates.length === 0) {
      return noEvidence('当前 F01 没有可跟候选。仓位来源对照无需显示。');
    }
    const visible = displayedMints && typeof displayedMints.get === 'function'
      ? displayedMints : new Map();
    const seen = new Set();
    const rows = [];
    for (const row of doc.candidates) {
      if (!row || !validMint(row.mint) ||
          !['BUY', 'SMALL_BUY'].includes(row.f01_decision) ||
          typeof row.source_signal_id !== 'string' || !row.source_signal_id ||
          seen.has(row.mint)) {
        return noEvidence('候选身份或来源格式异常，已隐藏本次仓位对照。');
      }
      seen.add(row.mint);
      const current = visible.get(row.mint);
      if (!current) continue;
      if (current.source_signal_id !== row.source_signal_id ||
          current.decision !== row.f01_decision ||
          current.guard_state !== 'VERIFIED') {
        return noEvidence('F01 当前信号已更新或未校验，旧仓位来源不得混用。');
      }
      const state = stateLabels[row.wallet_observation_state];
      if (!state || row.archived_source_only !== true ||
          row.current_wallet_position_verified !== false ||
          row.historical_sale_confirmed !== false ||
          row.may_trade_based_on_combination !== false) {
        return noEvidence('仓位来源证明不完整，已隐藏本次对照。');
      }
      const needsReview = row.review_required_reason === REVIEW;
      if (row.review_required_reason != null && !needsReview) {
        return noEvidence('复核状态无法识别，已隐藏本次对照。');
      }
      const quantity = row.wallet_observation_state === 'OPEN_ACCOUNT_NONZERO' ||
        row.wallet_observation_state === 'OPEN_ACCOUNT_ZERO'
        ? (typeof row.observed_quantity === 'string' &&
           /^\d+(\.\d+)?$/.test(row.observed_quantity) &&
           row.observed_quantity.length <= 96
          ? row.observed_quantity : null) : null;
      if ((row.wallet_observation_state === 'OPEN_ACCOUNT_NONZERO' ||
           row.wallet_observation_state === 'OPEN_ACCOUNT_ZERO') &&
          quantity === null) {
        return noEvidence('余额精度证据异常，已隐藏本次对照。');
      }
      const status = needsReview
        ? '<strong class="frank-source-review">需要复核：F01 信号与归档观察不一致</strong>'
        : '<span>未发现本轮预设的跨源冲突，不等于可以交易</span>';
      const stateLabel = state + (quantity !== null ? ' · ' + quantity : '');
      rows.push('<li class="frank-source-row"><div><code>' +
        escapeHtml(row.mint) + '</code> ' +
        '<button type="button" class="link-btn compact" data-cluster-ca="' +
        escapeHtml(row.mint) + '">查此 CA</button></div>' +
        '<div class="frank-source-facts"><span>原 F01 判断 ' +
        escapeHtml(row.f01_decision) + '</span><span>' +
        escapeHtml(stateLabel) + '</span></div><div>' + status +
        '</div><small>来源观察时间：' + escapeHtml(asDate(row.observation_at_utc)) +
        '；不等于当前实时仓位、完整成本或卖出证明</small></li>');
    }
    if (!rows.length) return noEvidence(
      'F01 页面候选与本次只读仓位来源尚未匹配，已隐藏旧信号及旧余额。');
    const seconds = Math.max(0, Math.floor(expiry - nowEpoch));
    return '<p class="frank-source-notice">A05/F02 只读来源对照 · F01 资格剩余约 ' +
      escapeHtml(seconds) + ' 秒；本区域不发交易指令，数据与上方 F01 卡片独立核对。</p>' +
      '<ul class="frank-source-list">' + rows.join('') + '</ul>';
  }

  // Export pure rendering contract for the Node negative-case suite.
  const api = {renderModel};
  if (typeof globalThis !== 'undefined') globalThis.FrankSourceContextUI = api;
  if (typeof document === 'undefined') return;
  const host = document.getElementById('follow-opportunities');
  const cardContainer = document.getElementById('candidates');
  if (!host || !cardContainer || typeof MutationObserver === 'undefined') return;

  const pane = document.createElement('section');
  pane.id = 'frank-source-context';
  pane.className = 'frank-source-context';
  pane.setAttribute('aria-label', 'A05 钱包研究来源对照');
  pane.innerHTML = noEvidence('独立仓位来源尚未核对。');
  cardContainer.insertAdjacentElement('afterend', pane);
  let sequence = 0;
  let stored = null;
  let expiryTimer = null;
  const observedMints = () => new Map(Array.from(
    cardContainer.querySelectorAll('.candidate-card'),
    (card) => {
      const mint=(card.querySelector('.ca-full')?.textContent || '').trim();
      return [mint, {
        source_signal_id:card.dataset.f01SourceSignalId,
        decision:card.dataset.f01Decision,
        guard_state:card.dataset.f01GuardState,
      }];
    }
  ).filter(pair => validMint(pair[0])));
  const draw = () => {
    pane.innerHTML = renderModel(stored, observedMints(), Date.now() / 1000);
  };
  const load = async () => {
    const requestNo = ++sequence;
    stored = null;
    if (expiryTimer !== null) clearTimeout(expiryTimer);
    expiryTimer = null;
    draw();
    try {
      const response = await fetch('/api/research/current-follow-context', {
        method: 'GET', cache: 'no-store', credentials: 'same-origin'
      });
      if (!response.ok) throw new Error('SOURCE_UNAVAILABLE');
      const doc = await response.json();
      if (requestNo !== sequence) return;
      stored = doc;
      draw();
      const exp = doc && doc.f01_valid_until_epoch;
      if (typeof exp === 'number' && Number.isFinite(exp)) {
        const delay = Math.max(0, Math.ceil(exp * 1000 - Date.now()));
        expiryTimer = setTimeout(() => {
          if (requestNo === sequence) draw();
        }, Math.min(delay + 1, 2147483647));
      }
    } catch (_) {
      if (requestNo !== sequence) return;
      stored = null;
      draw();
    }
  };

  // Reuse the existing F01 page's 5s render cadence. No new polling loop,
  // scheduler, background process, RPC, or active CA research.
  const observer = new MutationObserver(() => { void load(); });
  observer.observe(cardContainer, {childList: true});
  if (typeof window !== 'undefined' && typeof window.addEventListener === 'function')
    window.addEventListener('frank:f01-guard-updated', draw);
  void load();
})();

(() => {
  'use strict';

  const byId = id => document.getElementById(id);
  const risk = name => byId('frank-risk-' + name);
  const quote = name => byId('frank-quote-' + name);
  if (!risk('updates') || !byId('frank-execution-quote')) return;

  const refreshPath = '/api/frank-intelligence-refresh';
  const updatesPath = '/api/frank-intelligence-updates';
  const quotePath = '/api/frank-quote';
  const id = /^[a-f0-9]{32}$/;
  const hash = /^[a-f0-9]{64}$/;
  const mint = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
  const signature = /^[1-9A-HJ-NP-Za-km-z]{32,88}$/;
  const codePattern = /^[A-Z][A-Z0-9_]{1,95}$/;
  const decimal = /^-?[0-9]+(?:\.[0-9]+)?$/;
  const integer = /^(0|[1-9][0-9]*)$/;
  const rawAmount = value => typeof value === 'string' && value.length <= 20 &&
    integer.test(value) && BigInt(value) <= 18446744073709551615n;
  const count = value => Number.isSafeInteger(value) && value >= 0;
  const timestamp = value => typeof value === 'number' && Number.isFinite(value) &&
    value >= 0 && Number.isFinite(new Date(value * 1000).getTime());
  const dateFormat = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Bangkok', dateStyle: 'medium', timeStyle: 'medium', hourCycle: 'h23',
  });
  const time = value => timestamp(value) ? dateFormat.format(value * 1000) + '（曼谷时间）' : '未知';
  const kindLabels = new Map([
    ['SELL_OBSERVED', '观察到卖出'],
    ['POSITION_REDUCTION_OBSERVED', '观察到减仓'],
    ['REENTRY_OBSERVED', '观察到重新买入'],
    ['PRICE_REFERENCE_STALE', '参考行情过期'],
    ['ABOVE_VERIFIED_BUY_REFERENCE', '参考价高于已核实买价'],
    ['EVIDENCE_GAP', '证据缺口'],
  ]);
  const referenceLabels = [
    ['fact_manifest_id', '事实快照', id],
    ['facts_sha256', '事实摘要', hash],
    ['event_fact_id', '事件事实 ID', hash],
    ['position_sha256', '仓位观察摘要', hash],
    ['market_sha256', '行情输入摘要', hash],
    ['market_observation_sha256', '行情观察摘要', hash],
  ];
  let runRequest = null;
  let updateRequest = null;
  let currentPage = null;
  let pendingRefresh = null;
  let quoteRequest = null;
  let displayedQuote = null;
  let expiryTimer = null;

  function node(tag, text) {
    const element = document.createElement(tag);
    element.textContent = text;
    return element;
  }

  function detail(tag, label, lines) {
    const group = document.createElement(tag);
    if (tag === 'details') group.appendChild(node('summary', label));
    if (tag === 'article') {
      group.className = 'candidate-card';
      group.appendChild(node('h3', label));
    }
    for (const line of lines) group.appendChild(node('p', line));
    return group;
  }

  function refLines(refs) {
    return referenceLabels.flatMap(([key, label, pattern]) => {
      const value = refs?.[key];
      return typeof value === 'string' && pattern.test(value) ? [label + ' ' + value] : [];
    });
  }

  async function request(path, controller, payload, timeout = 30000) {
    const writing = payload !== undefined;
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(path, {
        method: writing ? 'POST' : 'GET', cache: 'no-store', credentials: 'same-origin',
        signal: controller.signal,
        ...(writing ? {headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)} :
          {headers: {'X-Frank-Research-Read': '1'}}),
      });
      let body;
      try { body = await response.json(); } catch { body = {}; }
      if (!response.ok) throw {status: response.status, code: body?.error};
      return body;
    } finally {
      clearTimeout(timer);
    }
  }

  function setRunControls() {
    risk('refresh').disabled = Boolean(runRequest);
    risk('read-run').disabled = Boolean(runRequest);
    risk('use-manifest').disabled = Boolean(runRequest);
  }

  function renderRun(body, expectedRun) {
    if (body?.state !== 'COMPLETE' || !id.test(body.run_id ?? '') ||
        (expectedRun && body.run_id !== expectedRun) || !timestamp(body.as_of) ||
        ![body.rows_count, body.created_updates, body.deduped_updates].every(count)) {
      throw new Error('Invalid run');
    }
    risk('run').value = body.run_id;
    risk('run-status').textContent = '已处理 ' + body.rows_count + ' 个分析条目。新增 ' +
      body.created_updates + ' 条风险记录，' + body.deduped_updates + ' 条已有记录。';
    risk('run-details').replaceChildren(detail('details', '分析运行和输入证据', [
      '运行 ID ' + body.run_id,
      '事实截止 ' + time(body.source_refs?.fact_as_of),
      '分析于 ' + time(body.as_of),
      '记录于 ' + time(body.created_at),
      ...refLines(body.source_refs),
    ]));
  }

  async function runFromInput(refresh) {
    if (runRequest) return;
    const field = risk(refresh ? 'manifest' : 'run');
    const value = field.value.trim();
    if ((value || !refresh) && !id.test(value)) {
      risk('run-status').textContent = refresh ? '请输入完整的事实快照 ID，或留空。' : '请输入完整的分析运行 ID。';
      return;
    }
    let payload;
    if (refresh) {
      if (pendingRefresh?.manifest !== value) {
        pendingRefresh = {manifest: value, key: crypto.randomUUID()};
      }
      payload = {idempotency_key: pendingRefresh.key, ...(value ? {input_manifest_id: value} : {})};
    }
    const controller = new AbortController();
    const path = refresh ? refreshPath : refreshPath + '?' + new URLSearchParams({run_id: value});
    runRequest = controller;
    setRunControls();
    risk('run-details').replaceChildren();
    risk('run-status').textContent = refresh ? '正在根据本机证据计算并记录…' : '正在读取分析运行…';
    try {
      const body = await request(path, controller, payload, 60000);
      if (runRequest !== controller || field.value.trim() !== value) return;
      const manifest = body?.source_refs?.fact_manifest_id;
      if (refresh && value && manifest !== value) throw new Error('Manifest mismatch');
      renderRun(body, refresh ? null : value);
      if (refresh) pendingRefresh = null;
    } catch (error) {
      if (runRequest !== controller || field.value.trim() !== value) return;
      risk('run-status').textContent = error?.status === 404
        ? refresh ? '未找到指定的事实快照。' : '未找到这次分析。'
        : error?.status === 409 ? '请求与已有记录冲突。请核对输入后重试。'
          : refresh ? '计算结果尚未确认。重试会沿用同一请求键。' : '分析运行暂不可读。';
      if (refresh && [400, 404, 409].includes(error?.status)) pendingRefresh = null;
    } finally {
      if (runRequest === controller) {
        runRequest = null;
        setRunControls();
      }
    }
  }

  const filter = () => ({mint: risk('mint').value.trim(), kind: risk('kind').value});
  const sameFilter = (a, b) => a.mint === b.mint && a.kind === b.kind;

  function setUpdateControls() {
    risk('read-updates').disabled = Boolean(updateRequest);
    risk('next').disabled = Boolean(updateRequest) || !currentPage?.cursor;
  }

  function riskCard(row) {
    const lines = [
      'Mint ' + row.mint,
      '事件时间 ' + time(row.observed_at) + ' · 记录截止 ' + time(row.as_of),
    ];
    if (typeof row.reason === 'string' && codePattern.test(row.reason)) lines.push('原因 ' + row.reason);
    if (typeof row.signature === 'string' && signature.test(row.signature)) lines.push('交易签名 ' + row.signature);
    if (typeof row.source_signal_id === 'string' && /^[a-f0-9]{32,64}$/.test(row.source_signal_id)) {
      lines.push('原始信号 ID ' + row.source_signal_id);
    }
    const missing = Array.isArray(row.missing) ? row.missing.filter(value =>
      typeof value === 'string' && codePattern.test(value)) : [];
    if (missing.length) lines.push('待核证据 ' + missing.join('、'));
    const card = detail('article', kindLabels.get(row.kind), lines);
    const refs = ['更新 ID ' + row.update_id, ...refLines(row.source_refs)];
    if (hash.test(row.previous_update_id ?? '')) refs.push('前一次更新 ID ' + row.previous_update_id);
    card.appendChild(detail('details', '来源与更新关系', refs));
    return card;
  }

  function renderUpdates(body, query) {
    const {rows, returned, total_matching: total, next_cursor: cursor} = body ?? {};
    if (body?.notification_enabled !== false || !Array.isArray(rows) || returned !== rows.length ||
        !count(total) || returned > total || (cursor !== null && (typeof cursor !== 'string' || !cursor || !returned)) ||
        !rows.every(row => hash.test(row?.update_id ?? '') && mint.test(row.mint ?? '') &&
          kindLabels.has(row.kind) && (!query.mint || query.mint === row.mint) &&
          (!query.kind || query.kind === row.kind)) ||
        new Set(rows.map(row => row.update_id)).size !== rows.length) {
      throw new Error('Invalid risk list');
    }
    risk('rows').replaceChildren(...rows.map(riskCard));
    currentPage = {query, cursor};
    risk('updates-status').textContent = returned
      ? '共 ' + total + ' 条持久风险记录，本页 ' + returned + ' 条。'
      : '当前筛选没有已保存的风险更新。';
  }

  async function readUpdates(cursor = null) {
    if (updateRequest) return;
    const query = filter();
    if ((query.mint && !mint.test(query.mint)) || (query.kind && !kindLabels.has(query.kind))) {
      risk('updates-status').textContent = '请核对筛选用的 Mint 和变化类型。';
      return;
    }
    if (cursor && !sameFilter(currentPage.query, query)) return;
    const params = new URLSearchParams({limit: '25'});
    if (query.mint) params.set('mint', query.mint);
    if (query.kind) params.set('kind', query.kind);
    if (cursor) params.set('cursor', cursor);
    const controller = new AbortController();
    updateRequest = controller;
    setUpdateControls();
    risk('updates-status').textContent = '正在读取本机风险记录…';
    try {
      const body = await request(updatesPath + '?' + params, controller);
      if (updateRequest === controller && sameFilter(query, filter())) renderUpdates(body, query);
    } catch (error) {
      if (updateRequest !== controller) return;
      risk('updates-status').textContent = error?.status === 409
        ? '记录分页已变化，请从第一页读取。' : '风险记录暂不可读。';
      currentPage = null;
      risk('rows').replaceChildren();
    } finally {
      if (updateRequest === controller) {
        updateRequest = null;
        setUpdateControls();
      }
    }
  }

  function resetFilter() {
    updateRequest?.abort();
    updateRequest = null;
    currentPage = null;
    risk('rows').replaceChildren();
    risk('updates-status').textContent = '';
    setUpdateControls();
  }

  function quoteInput() {
    const bps = quote('slippage').value.trim();
    return {
      mint: quote('mint').value.trim(),
      input_mint: quote('input-mint').value.trim(),
      input_amount_raw: quote('amount').value.trim(),
      slippage_bps: /^\d{1,5}$/.test(bps) ? Number(bps) : null,
    };
  }

  function matchesQuote(a, b) {
    return a?.mint === b.mint && a.input_mint === b.input_mint &&
      a.input_amount_raw === b.input_amount_raw && a.slippage_bps === b.slippage_bps;
  }

  function recheckExpiry() {
    if (!displayedQuote) return;
    if (Date.now() / 1000 >= displayedQuote.expires_at) {
      displayedQuote = null;
      quote('status').textContent = '报价已过期。需要新的路由参考时请重新请求。';
      quote('details').replaceChildren();
      clearTimeout(expiryTimer);
      expiryTimer = null;
    } else {
      clearTimeout(expiryTimer);
      expiryTimer = setTimeout(recheckExpiry, Math.max(1,
        Math.min(2147483647, Math.ceil(displayedQuote.expires_at * 1000 - Date.now()))));
    }
  }

  function renderQuote(body, input) {
    const refs = body?.source_ref;
    const ok = body?.status === 'OK';
    if ((!ok && body?.status !== 'NO_ROUTE') || !hash.test(body.quote_id ?? '') ||
        !matchesQuote(body.input, input) || body.input_mint !== input.input_mint ||
        body.output_mint !== input.mint || body.in_amount_raw !== input.input_amount_raw ||
        body.slippage_bps !== input.slippage_bps || !timestamp(body.observed_at) ||
        !timestamp(body.expires_at) || body.observed_at >= body.expires_at ||
        !hash.test(refs?.request_sha256 ?? '') || !hash.test(refs?.response_sha256 ?? '') ||
        !codePattern.test(refs?.source ?? '') || !Array.isArray(body.route_plan) ||
        (ok && (!rawAmount(body.out_amount_raw) || !rawAmount(body.other_amount_threshold_raw) ||
          !decimal.test(body.price_impact_pct ?? '') || body.route_exists !== true || body.route_plan.length === 0)) ||
        (!ok && (body.route_exists !== false || body.route_plan.length !== 0))) {
      throw new Error('Invalid quote');
    }

    const common = [
      '报价 ID ' + body.quote_id,
      '来源 ' + refs.source,
      '来源时间 ' + time(body.observed_at),
      '有效期至 ' + time(body.expires_at),
      '请求摘要 ' + refs.request_sha256,
      '响应摘要 ' + refs.response_sha256,
    ];
    const amounts = [
      '输入 ' + body.in_amount_raw + ' 原始单位 · ' + body.input_mint,
      '输出 ' + body.out_amount_raw + ' 原始单位 · ' + body.output_mint,
      '最小输出 ' + body.other_amount_threshold_raw + ' 原始单位',
      '滑点 ' + body.slippage_bps + ' 基点 · 价格影响 ' + body.price_impact_pct + '%',
    ];
    const routes = body.route_plan.map(hop => {
      if (!mint.test(hop?.amm_key ?? '') || !mint.test(hop.input_mint ?? '') ||
          !mint.test(hop.output_mint ?? '') || !rawAmount(hop.in_amount_raw) || !rawAmount(hop.out_amount_raw)) {
        throw new Error('Invalid quote route');
      }
      return hop.amm_key + ' · ' + hop.in_amount_raw + ' ' + hop.input_mint +
        ' → ' + hop.out_amount_raw + ' ' + hop.output_mint;
    });

    quote('status').textContent = ok ? '报价可作为当前路由参考。' : '该输入下暂未找到路由。';
    quote('details').replaceChildren(
      detail('div', '', ok ? amounts : []),
      ...(ok ? [detail('details', '路由步骤', routes)] : []),
      detail('details', '报价时间和来源证据', common),
    );
    displayedQuote = body;
    recheckExpiry();
  }

  function resetQuote() {
    quoteRequest?.abort();
    quoteRequest = null;
    displayedQuote = null;
    clearTimeout(expiryTimer);
    expiryTimer = null;
    quote('read').disabled = false;
    quote('status').textContent = '';
    quote('details').replaceChildren();
  }

  async function readQuote() {
    if (quoteRequest) return;
    resetQuote();
    const input = quoteInput();
    if (!mint.test(input.mint) || !mint.test(input.input_mint) || input.mint === input.input_mint ||
        !rawAmount(input.input_amount_raw) || input.input_amount_raw === '0' ||
        input.slippage_bps === null || input.slippage_bps > 10000) {
      quote('status').textContent = '请输入两个不同的 Mint、正整数原始金额和 0 至 10000 基点的滑点。';
      return;
    }
    const controller = new AbortController();
    quoteRequest = controller;
    quote('read').disabled = true;
    quote('status').textContent = '正在请求指定输入的报价…';
    try {
      const body = await request(quotePath, controller, input);
      if (quoteRequest === controller && matchesQuote(quoteInput(), input)) renderQuote(body, input);
    } catch (error) {
      if (quoteRequest !== controller) return;
      quote('status').textContent = error?.code === 'JUPITER_QUOTE_NOT_CONFIGURED'
        ? '报价来源尚未配置。' : error?.status === 400 ? '报价输入未通过来源校验。'
          : '暂未取得可核实的报价。';
    } finally {
      if (quoteRequest === controller) {
        quoteRequest = null;
        quote('read').disabled = false;
      }
    }
  }

  risk('use-manifest').addEventListener('click', () => {
    const value = byId('frank-manifest-id')?.value.trim();
    if (!id.test(value ?? '')) {
      risk('run-status').textContent = '请先选择已有事实快照。';
      return;
    }
    risk('manifest').value = value;
  });
  risk('refresh').addEventListener('click', () => runFromInput(true));
  risk('read-run').addEventListener('click', () => runFromInput(false));
  for (const name of ['manifest', 'run']) {
    risk(name).addEventListener('input', () => {
      runRequest?.abort();
      runRequest = null;
      risk('run-status').textContent = '';
      risk('run-details').replaceChildren();
      setRunControls();
    });
  }
  risk('mint').addEventListener('input', resetFilter);
  risk('kind').addEventListener('change', resetFilter);
  risk('read-updates').addEventListener('click', () => readUpdates());
  risk('next').addEventListener('click', () => {
    if (currentPage?.cursor) readUpdates(currentPage.cursor);
  });
  for (const name of ['mint', 'input-mint', 'amount', 'slippage']) {
    quote(name).addEventListener('input', resetQuote);
  }
  quote('read').addEventListener('click', readQuote);
  document.addEventListener('visibilitychange', recheckExpiry);
})();

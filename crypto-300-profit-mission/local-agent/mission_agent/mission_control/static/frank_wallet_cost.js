(() => {
  'use strict';

  const element = name => document.getElementById('frank-cost-' + name);
  const fields = {
    manifest: element('manifest'), run: element('run'), mint: element('mint'),
    useManifest: element('use-manifest'), rebuild: element('rebuild'), read: element('read'),
    next: element('next'), status: element('status'), summary: element('summary'),
    table: element('table'), rows: element('rows'),
  };
  if (!Object.values(fields).every(Boolean)) return;

  const rebuildPath = '/api/frank-cost-rebuild';
  const readPath = '/api/frank-cost-basis';
  const idPattern = /^[a-f0-9]{32}$/;
  const mintPattern = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
  const integerPattern = /^-?(?:0|[1-9][0-9]*)$/;
  const decimalPattern = /^-?[0-9]+(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?$/i;
  const unknown = '未知';
  const timeFormat = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Bangkok', dateStyle: 'medium', timeStyle: 'medium', hourCycle: 'h23',
  });
  const countFormat = new Intl.NumberFormat('zh-CN');
  const readHeaders = {'X-Frank-Research-Read': '1'};
  const reasons = new Map([
    ['OBSERVATION_MISSING_OR_INVALID', '缺少可核实报价'],
    ['USD_PRICE_UNAVAILABLE', '无美元参考价'],
    ['STALE_OBSERVATION', '已捕获的报价过期'],
    ['FUTURE_OBSERVATION', '报价时间晚于估值时点'],
    ['POSITION_INVALID', '余额或精度未核实'],
    ['NO_POSITION', '无待估值余额'],
    ['NO_BALANCE', '无待估值余额'],
    ['NO_REMAINING_QUANTITY', '无待估值余额'],
    ['INSUFFICIENT_OPENING_COVERAGE', '期初数量和成本尚未核实'],
    ['UNKNOWN_COST', '来源成本未知'],
  ]);
  const movementLabels = {
    BUY: '买入', SELL: '卖出', TRANSFER_IN: '转入', TRANSFER_OUT: '转出',
    INTERNAL_TRANSFER: '钱包内部划转', ATA_MIGRATION: '关联账户迁移',
    UNRESOLVED: '待核实变动',
  };
  let active = null;
  let pendingBuild = null;
  let page = null;

  const list = value => Array.isArray(value) ? value : [];
  const timestamp = value => typeof value === 'number' && Number.isFinite(value) &&
    value >= 0 && Number.isFinite(new Date(value * 1000).getTime());
  const time = value => timestamp(value) ? timeFormat.format(value * 1000) + '（曼谷时间）' : unknown;
  const count = value => Number.isSafeInteger(value) && value >= 0;
  const number = value => typeof value === 'string' && integerPattern.test(value);
  const decimals = value => Number.isInteger(value) && value >= 0 && value <= 255;
  const labelCount = value => count(value) ? countFormat.format(value) : unknown;
  const dollar = value => typeof value === 'string' && decimalPattern.test(value) ? value + ' USD' : unknown;
  const reasonText = (reason, fallback = '尚无可核实证据') => reasons.get(reason) ?? fallback;

  function raw(value, places) {
    if (!number(value) || !decimals(places)) return unknown;
    if (places === 0) return value;
    const negative = value.startsWith('-');
    const digits = (negative ? value.slice(1) : value).padStart(places + 1, '0');
    const whole = digits.slice(0, -places);
    const part = digits.slice(-places).replace(/0+$/, '');
    return (negative ? '-' : '') + whole + (part ? '.' + part : '');
  }

  function money(values) {
    const rendered = list(values).flatMap(value => {
      if (!value || !number(value.raw_numerator) || typeof value.raw_denominator !== 'string' ||
          !/^[1-9][0-9]*$/.test(value.raw_denominator) || !decimals(value.decimals)) return [];
      const denomination = ['USD', 'USDC', 'USDT', 'SOL', 'WSOL'].includes(value.denomination)
        ? value.denomination : mintPattern.test(value.mint ?? '') ? value.mint : '';
      if (!denomination) return [];
      if (value.raw_denominator === '1') return [raw(value.raw_numerator, value.decimals) + ' ' + denomination];
      const scaled = value.decimals ? ' × 10^-' + value.decimals : '';
      return [value.raw_numerator + '/' + value.raw_denominator + scaled + ' ' + denomination];
    });
    return rendered.length ? rendered.join(' · ') : unknown;
  }

  function node(tag, value) {
    const item = document.createElement(tag);
    if (value !== undefined) item.textContent = value;
    return item;
  }

  function addLines(parent, lines) {
    for (const line of lines) parent.appendChild(node('p', line));
  }

  function details(label, entries, addEntry) {
    const group = node('details');
    group.appendChild(node('summary', label + ' ' + labelCount(entries.length) + ' 条'));
    const populate = () => {
      if (!group.open) return;
      group.removeEventListener('toggle', populate);
      for (const entry of entries) {
        if (entry && typeof entry === 'object') group.appendChild(addEntry(entry));
      }
    };
    if (entries.length) group.addEventListener('toggle', populate);
    return group;
  }

  function saleDetails(asset) {
    const quantity = value => raw(value, asset.decimals);
    return details('逐笔卖出', list(asset.realized), event => {
      const item = node('div');
      addLines(item, [
        '卖出 ' + quantity(event.quantity_raw) + ' · 成本与收入已覆盖 ' + quantity(event.covered_quantity_raw),
        '原币成本 ' + money(event.costs) + ' · 收入 ' + money(event.proceeds),
        '覆盖部分盈亏 ' + money(event.partial_pnl) + ' · 本笔全部盈亏 ' + money(event.pnl),
      ]);
      if (event.reason) item.appendChild(node('p', reasonText(event.reason)));
      return item;
    });
  }

  function assetRow(asset) {
    const row = node('tr');
    const quantity = value => raw(value, asset.decimals);
    const mint = node('td');
    mint.appendChild(node('code', asset.mint));
    const inventory = node('td');
    addLines(inventory, [
      '索引余额 ' + quantity(asset.quantity_raw),
      '成本已知 ' + quantity(asset.known_cost_quantity_raw),
      '成本未知 ' + quantity(asset.unknown_cost_quantity_raw),
    ]);

    const costs = node('td');
    costs.appendChild(node('p', money(asset.remaining_costs)));
    if (list(asset.remaining_costs).length > 0) {
      costs.appendChild(node('p', '仅含成本已知批次'));
    }

    const realized = node('td');
    const sales = asset.realized_summary ?? {};
    addLines(realized, [
      '卖出数量 ' + quantity(sales.sold_quantity_raw) + ' · 已覆盖 ' + quantity(sales.covered_quantity_raw),
      '覆盖部分 ' + money(sales.partial_pnl),
      '全部卖出盈亏 ' + money(sales.pnl),
    ]);
    if (list(asset.realized).length > 0) realized.appendChild(saleDetails(asset));

    const valuation = node('td');
    const quote = asset.valuation;
    if (quote?.status === 'PRICED' && dollar(quote.value_usd) !== unknown) {
      const source = quote.source === 'DEXSCREENER_API' ? 'DexScreener' : '本机已捕获行情';
      addLines(valuation, [
        '索引余额参考价值 ' + dollar(quote.value_usd),
        '参考价 ' + dollar(quote.price_usd) + '/代币',
        source + ' · 观测于 ' + time(quote.observed_at),
        '有效期至 ' + time(quote.expires_at),
      ]);
    } else {
      valuation.appendChild(node('p', '参考估值未知 · ' + reasonText(quote?.reason)));
    }
    const uncovered = list(asset.covered_unrealized_pnl);
    addLines(valuation, [
      '覆盖部分未实现盈亏 ' + money(uncovered),
      '整仓未实现盈亏 ' + money(asset.unrealized_pnl),
    ]);
    for (const entry of uncovered) {
      if (entry?.covered_quantity_raw != null) {
        valuation.appendChild(node('p', money([entry]) + ' · 覆盖 ' + quantity(entry.covered_quantity_raw)));
      }
    }

    const movements = node('td');
    movements.appendChild(details('成本批次', list(asset.lots), lot => {
      const item = node('div');
      addLines(item, [
        '开仓 ' + quantity(lot.quantity_raw) + ' · 剩余 ' + quantity(lot.remaining_quantity_raw),
        '原币成本 ' + money(lot.costs) + ' · 剩余成本 ' + money(lot.remaining_costs),
      ]);
      if (count(lot.slot)) item.appendChild(node('p', 'Slot ' + lot.slot));
      if (lot.reason) item.appendChild(node('p', reasonText(lot.reason)));
      return item;
    }));
    movements.appendChild(details('资金变动', list(asset.movements), movement => {
      const kind = Object.hasOwn(movementLabels, movement.kind) ? movementLabels[movement.kind] : '索引活动';
      const slot = count(movement.slot) ? ' · Slot ' + movement.slot : '';
      return node('p', kind + ' ' + quantity(movement.delta_raw) + slot);
    }));

    for (const cell of [mint, inventory, costs, realized, valuation, movements]) row.appendChild(cell);
    return row;
  }

  function lamports(value) {
    const amount = raw(value, 9);
    return amount === unknown ? amount : amount + ' SOL';
  }

  function renderSummary(result) {
    const summary = node('div');
    const fees = result.fees ?? {};
    const value = result.valuation ?? {};
    const hasUnpricedCount = Array.isArray(value.unpriced_mints) &&
      value.unpriced_mints.every(mint => typeof mint === 'string' && mintPattern.test(mint));
    const unpriced = hasUnpricedCount ? value.unpriced_mints : [];
    const partialValue = value.covered_positions > 0 ? dollar(value.partial_value_usd) : unknown;
    addLines(summary, [
      '事实截止 ' + time(result.as_of) + ' · 账本生成于 ' + time(result.created_at),
      '已核实网络费 ' + lamports(fees.network_fee_lamports) +
        ' · 网络费待核交易 ' + labelCount(fees.network_fee_unknown_transactions) + ' 笔',
      '已核实初始注资 ' + lamports(fees.initial_funding_paid_lamports) +
        ' · 已核实关户转回 ' + lamports(fees.close_refund_received_lamports),
      '已核实租金支出 ' + lamports(fees.rent_paid_lamports) +
        ' · 已核实租金退款 ' + lamports(fees.rent_refunded_lamports),
      '已估值 Mint ' + labelCount(value.covered_positions) + ' 个 · 未估值 Mint ' +
        (hasUnpricedCount ? labelCount(unpriced.length) + ' 个' : unknown),
      '已估值部分 ' + partialValue + ' · 整钱包价值 ' + dollar(value.full_wallet_value_usd),
      '估值时点 ' + time(value.as_of) + ' · 行情最大允许年龄 ' + labelCount(value.max_age_seconds) + ' 秒',
    ]);
    if (unpriced.length) summary.appendChild(details('未估值 Mint', unpriced.map(mint => ({mint})),
      entry => node('p', entry.mint)));
    return summary;
  }

  function currentQuery() {
    return {run: fields.run.value.trim(), mint: fields.mint.value.trim()};
  }

  function updateControls() {
    const busy = active !== null;
    for (const field of ['rebuild', 'read', 'useManifest', 'manifest']) fields[field].disabled = busy;
    const query = currentQuery();
    fields.next.disabled = busy || !page?.cursor || page.run !== query.run || page.mint !== query.mint;
  }

  function clearResults() {
    page = null;
    fields.rows.replaceChildren();
    fields.summary.replaceChildren();
    fields.table.hidden = true;
  }

  async function request(url, controller, payload) {
    const read = payload === undefined;
    const timer = read ? setTimeout(() => controller.abort(), 30000) : null;
    try {
      const response = await fetch(url, {
        method: read ? 'GET' : 'POST', cache: 'no-store', credentials: 'same-origin', signal: controller.signal,
        ...(read ? {headers: readHeaders} : {
          headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
        }),
      });
      if (!response.ok) {
        const message = response.status === 404
          ? read ? '未找到这个账本。可以先用事实快照重建。' : '未找到可用的事实快照。'
          : response.status === 409 ? '账本、快照或分页状态已变化。请从第一页重新读取。'
              : read ? '账本暂不可读。' : '重建结果尚未确认。再次点击会继续使用同一请求键。';
        throw new Error(message);
      }
      return await response.json();
    } finally {
      if (timer !== null) clearTimeout(timer);
    }
  }

  function renderPage(result, query) {
    const {run_id: run, manifest_id: manifest, rows, returned, total_matching: total, next_cursor: cursor} = result ?? {};
    if (typeof run !== 'string' || !idPattern.test(run) ||
        (query.run && query.run !== run) || typeof manifest !== 'string' || !idPattern.test(manifest) ||
        !Array.isArray(rows) || !count(total) || returned !== rows.length || returned > total ||
        (cursor !== null && (typeof cursor !== 'string' || cursor === '' || returned === 0)) ||
        !rows.every(asset => typeof asset?.mint === 'string' && mintPattern.test(asset.mint) &&
          (!query.mint || asset.mint === query.mint)) || new Set(rows.map(asset => asset.mint)).size !== rows.length) {
      throw new Error('账本返回的数据无法核实。');
    }
    const displayRows = rows.map(assetRow);
    const summary = renderSummary(result);
    fields.run.value = run;
    fields.summary.replaceChildren(summary);
    fields.rows.replaceChildren(...displayRows);
    fields.table.hidden = rows.length === 0;
    page = {run, mint: query.mint, cursor};
    fields.status.textContent = rows.length === 0 ? '该账本没有符合条件的 Mint。' :
      '账本来自快照 ' + manifest + '。共 ' + labelCount(total) + ' 个 Mint，本页 ' + labelCount(returned) + ' 个。';
  }

  async function readPage(query, cursor = null, action = null) {
    if (active && active !== action) return;
    if ((query.run && !idPattern.test(query.run)) || (query.mint && !mintPattern.test(query.mint))) {
      fields.status.textContent = '请输入完整的账本 ID 或 Mint，或留空读取全部。';
      return;
    }
    const controller = action ?? new AbortController();
    active = controller;
    updateControls();
    fields.status.textContent = '正在读取本机账本…';
    const parameters = new URLSearchParams({limit: '25'});
    if (query.run) parameters.set('run_id', query.run);
    if (query.mint) parameters.set('mint', query.mint);
    if (cursor) parameters.set('cursor', cursor);
    try {
      const result = await request(readPath + '?' + parameters, controller);
      const now = currentQuery();
      if (active === controller && query.run === now.run && query.mint === now.mint) renderPage(result, query);
    } catch (error) {
      if (active === controller) {
        fields.status.textContent = safeError(error, '账本暂不可读。请重试。');
      }
    } finally {
      if (!action && active === controller) {
        active = null;
        updateControls();
      }
    }
  }

  const safeErrors = new Set([
    '未找到这个账本。可以先用事实快照重建。',
    '未找到可用的事实快照。',
    '账本、快照或分页状态已变化。请从第一页重新读取。',
    '账本暂不可读。',
    '账本返回的数据无法核实。',
    '重建结果尚未确认。再次点击会继续使用同一请求键。',
  ]);
  const safeError = (error, fallback) => safeErrors.has(error?.message) ? error.message : fallback;

  async function rebuild() {
    if (active) return;
    const manifest = fields.manifest.value.trim();
    if (!idPattern.test(manifest)) {
      fields.status.textContent = '请输入完整的事实快照 ID。';
      return;
    }
    if (pendingBuild?.manifest !== manifest) pendingBuild = {manifest, key: crypto.randomUUID()};
    const controller = new AbortController();
    active = controller;
    updateControls();
    fields.status.textContent = '正在从固定事实重建本机成本账本…';
    try {
      const result = await request(rebuildPath, controller, {
        input_manifest_id: manifest, idempotency_key: pendingBuild.key,
      });
      if (active !== controller) return;
      if (result?.state !== 'COMPLETE' || result.manifest_id !== manifest ||
          typeof result.run_id !== 'string' || !idPattern.test(result.run_id)) {
        throw new Error('重建结果尚未确认。再次点击会继续使用同一请求键。');
      }
      pendingBuild = null;
      fields.run.value = result.run_id;
      clearResults();
      await readPage(currentQuery(), null, controller);
    } catch (error) {
      if (active === controller) fields.status.textContent = safeError(error,
        '重建结果尚未确认。再次点击会继续使用同一请求键。');
    } finally {
      if (active === controller) {
        active = null;
        updateControls();
      }
    }
  }

  function editQuery() {
    active?.abort();
    active = null;
    clearResults();
    fields.status.textContent = '筛选条件已变更。点击读取账本查看结果。';
    updateControls();
  }

  fields.useManifest.addEventListener('click', () => {
    const value = document.getElementById('frank-manifest-id')?.value.trim();
    if (value && idPattern.test(value)) {
      fields.manifest.value = value;
      fields.status.textContent = '已选用上方快照。点击重建 FIFO 账本。';
    } else {
      fields.status.textContent = '请先创建或选中上方的事实快照。';
    }
  });
  fields.rebuild.addEventListener('click', () => void rebuild());
  fields.read.addEventListener('click', () => void readPage(currentQuery()));
  fields.next.addEventListener('click', () => {
    if (page?.cursor && !fields.next.disabled) void readPage(currentQuery(), page.cursor);
  });
  fields.run.addEventListener('input', editQuery);
  fields.mint.addEventListener('input', editQuery);
  clearResults();
  updateControls();
})();


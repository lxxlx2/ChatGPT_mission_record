(() => {
  'use strict';
  const element = name => document.getElementById('frank-coverage-' + name);
  const windowSelect = element('window');
  const readButton = element('read');
  const status = element('status');
  const detail = element('detail');
  if (!windowSelect || !readButton || !status || !detail) return;

  const windows = new Set(['all', '1', '7', '30']);
  const categories = {
    ACTIVE_TRADE: '主动交易',
    PASSIVE_TRANSFER: '被动转入或转出',
    FAILED_TX: '失败交易',
    ATA_CREATE: '创建关联代币账户（ATA）',
    UNKNOWN_NEEDS_REVIEW: '待核实',
    OTHER_OR_UNKNOWN: '其他或未知',
  };
  const categoryKeys = Object.keys(categories);
  const stopReasons = new Map([
    ['CURSOR_GAP_UNRESOLVED', '扫描时未能找到已保存的历史游标'],
    ['RAW_UNAVAILABLE_CURSOR_NOT_ADVANCED', '交易原始数据缺失，游标未推进'],
    ['CHAIN_SLOT_CONFLICT', '交易 slot 与签名索引不一致'],
    ['CHAIN_SIGNATURE_CONFLICT', '原始交易与签名索引不一致'],
  ]);
  const gapReasons = new Map([
    ['CURSOR_GAP_UNRESOLVED', '已记录历史游标缺口，尚未解决'],
    ['DETECTED_SIGNATURES_NOT_INDEXED', '有已检测但尚未入索引的签名'],
  ]);
  const dateFormat = new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Bangkok', dateStyle: 'medium', timeStyle: 'medium', hourCycle: 'h23',
  });
  const countFormat = new Intl.NumberFormat('zh-CN');
  const count = value => Number.isSafeInteger(value) && value >= 0;
  const asTime = value => Number.isFinite(value) && value >= 0 &&
    Number.isFinite(new Date(value * 1000).getTime());
  const time = value => asTime(value) ? dateFormat.format(value * 1000) : '未知';
  let activeRead = null;

  function render(body, days) {
    const {data, coverage} = body ?? {};
    const expectedDays = days === 'all' ? days : Number(days);
    if (body?.schema_version !== 1 || body.status !== 'PARTIAL_SOURCE' ||
        data?.person_id !== 'frank' || data.days !== expectedDays ||
        coverage?.full_chain_verified !== false || !asTime(data.end_at) ||
        (days !== 'all' && !asTime(data.start_at)) ||
        ![data.indexed_signatures, data.timed_signatures, data.untimed_signatures,
          data.untimed_source_signatures, data.parser_unresolved_signatures].every(count) ||
        !categoryKeys.every(key => count(data.categories?.[key]))) {
      throw new Error('Unexpected history coverage response');
    }
    const categoryTotal = categoryKeys.reduce((total, key) => total + data.categories[key], 0);
    const unresolved = data.categories.UNKNOWN_NEEDS_REVIEW + data.categories.OTHER_OR_UNKNOWN;
    if (data.indexed_signatures !== data.timed_signatures + data.untimed_signatures ||
        data.indexed_signatures !== categoryTotal || data.parser_unresolved_signatures !== unresolved ||
        data.untimed_signatures !== (days === 'all' ? data.untimed_source_signatures : 0)) {
      throw new Error('Inconsistent history coverage counts');
    }

    const format = value => countFormat.format(value);
    const range = days === 'all' ? `全部本机记录，统计截至 ${time(data.end_at)}` :
      `最近 ${days} 天，${time(data.start_at)} 至 ${time(data.end_at)}`;
    const timestamps = asTime(data.indexed_oldest_at) && asTime(data.indexed_newest_at) ?
      `${time(data.indexed_oldest_at)} 至 ${time(data.indexed_newest_at)}` : '未知';
    const missingTimestamps = days === 'all' ?
      `已计入 ${format(data.untimed_signatures)} 条无区块时间的签名。` :
      `另有 ${format(data.untimed_source_signatures)} 条本机签名缺少区块时间，无法归入本窗口。`;
    const gaps = Array.isArray(coverage.known_gaps) ?
      [...gapReasons].filter(([code]) => coverage.known_gaps.includes(code)).map(([, label]) => label) : [];
    const pending = count(data.pending_detected_signatures) ? `${format(data.pending_detected_signatures)} 条` : '未知';
    const stop = stopReasons.get(coverage.stop_reason) ?? '未知';
    const lines = [
      `${range}（曼谷时间）。`,
      `已索引 ${format(data.indexed_signatures)} 条签名，其中 ${format(data.timed_signatures)} 条有区块时间。${missingTimestamps}`,
      `已索引记录时间 ${timestamps}。`,
      categoryKeys.map(key => `${categories[key]} ${format(data.categories[key])} 条`).join(' · '),
      `解析仍待核实 ${format(data.parser_unresolved_signatures)} 条 · 本窗口已检测但尚未入索引 ${pending}。`,
      `历史缺口 ${gaps.join('；') || '未知'} · 历史回补状态未知。`,
      `最近一次成功扫描记录 ${time(data.scanner_observed_at)} · 最近记录的停止原因 ${stop}。`,
    ];
    detail.replaceChildren(...lines.map(line => {
      const paragraph = document.createElement('p');
      paragraph.textContent = line;
      return paragraph;
    }));
    status.textContent = '已读取本机签名索引。全链覆盖未核实。';
  }

  windowSelect.addEventListener('change', () => {
    activeRead?.abort();
    activeRead = null;
    readButton.disabled = false;
    detail.replaceChildren();
    status.textContent = '时间范围已改变，请读取本机覆盖。';
  });

  readButton.addEventListener('click', async () => {
    if (activeRead) return;
    const days = windowSelect.value;
    if (!windows.has(days)) return;

    const controller = new AbortController();
    activeRead = controller;
    readButton.disabled = true;
    detail.replaceChildren();
    status.textContent = '正在读取本机签名索引…';
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
      const response = await fetch('/api/frank-coverage?days=' + days, {
        method: 'GET', cache: 'no-store', credentials: 'same-origin',
        headers: {'X-Frank-Research-Read': '1'}, signal: controller.signal,
      });
      if (!response.ok) throw new Error('History coverage source unavailable');
      const body = await response.json();
      if (activeRead === controller && windowSelect.value === days) render(body, days);
    } catch (_) {
      if (activeRead === controller && windowSelect.value === days) {
        status.textContent = '本机覆盖读取失败。签名数量、全链覆盖和历史缺口均未核实。';
      }
    } finally {
      clearTimeout(timer);
      if (activeRead === controller) {
        activeRead = null;
        readButton.disabled = false;
      }
    }
  });
})();

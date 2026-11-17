/* User-owned watch metadata. No startup request, source fetch or automatic write. */
(() => {
  'use strict';
  const el = name => document.getElementById('frank-watch-meta-' + name);
  if (!el('mint') || !el('load') || !el('save')) return;
  const validMint = value => /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(value);
  const overrides = new Set(['FOLLOW', 'HIDE', 'DEFAULT']);
  let epoch = 0, loaded = null, saving = false, dirty = false;
  let retry = null, preservedDraft = null, listNext = null, historyNext = null;
  const currentMint = () => el('mint').value.trim();
  const draft = () => ({pinned:el('pinned').checked === true, note:el('note').value,
                        watch_override:el('override').value});
  function setDraft(value) {
    el('pinned').checked = value.pinned;
    el('note').value = value.note;
    el('override').value = value.watch_override;
  }
  function controls() {
    const ready = loaded && loaded.mint === currentMint();
    el('save').disabled = saving || !ready;
    for (const key of ['pinned','note','override']) el(key).disabled = saving || !ready;
    el('load').disabled = saving;
    if (el('next')) el('next').disabled = saving || !listNext || !!currentMint();
  }
  function clearIdentity() {
    ++epoch;
    loaded = null; dirty = false; retry = null; preservedDraft = null;
    listNext = null; historyNext = null;
    setDraft({pinned:false,note:'',watch_override:'DEFAULT'});
    if (el('history')) el('history').replaceChildren();
    el('status').textContent = '代币已改变，请读取该Mint后编辑。';
    controls();
  }
  async function request(path, body) {
    const options = body === undefined ? {headers:{'X-Frank-Research-Read':'1'}} :
      {method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30000);
    let response, value;
    try {
      response = await fetch(path, {...options,cache:'no-store',signal:controller.signal});
      value = await response.json();
    } finally { clearTimeout(timer); }
    if (!response.ok) {
      const error = new Error('HTTP_' + response.status);
      error.status = response.status;
      error.code = typeof value.error === 'string' && /^[A-Z][A-Z0-9_]*$/.test(value.error)
        ? value.error : error.message;
      throw error;
    }
    return value;
  }
  function rowOf(value, mint) {
    const row = value && typeof value.data === 'object' ? value.data : value;
    if (!row || row.mint !== mint || !Number.isSafeInteger(row.revision) || row.revision < 0 ||
        typeof row.pinned !== 'boolean' || typeof row.note !== 'string' || !overrides.has(row.watch_override) ||
        (row.person_id != null && row.person_id !== 'frank') || (row.chain != null && row.chain !== 'solana')) {
      throw new Error('元数据响应身份或版本无效，未允许保存。');
    }
    return row;
  }
  function cell(text) {
    const td = document.createElement('td'); td.textContent = String(text ?? ''); return td;
  }
  function renderList(rows, append = false) {
    if (!el('rows')) return;
    if (!append) el('rows').replaceChildren();
    for (const row of rows) {
      const tr = document.createElement('tr');
      tr.appendChild(cell(row.mint));
      tr.appendChild(cell(row.pinned ? '已收藏' : '未收藏'));
      tr.appendChild(cell(row.note));
      tr.appendChild(cell(({FOLLOW:'用户关注',HIDE:'用户隐藏',DEFAULT:'默认观察'})[row.watch_override] || '未核实'));
      tr.appendChild(cell(row.revision));
      const action = document.createElement('td');
      const button = document.createElement('button'); button.type = 'button';
      button.className = 'link-btn'; button.textContent = '读取编辑';
      button.addEventListener('click', () => {
        el('mint').value = row.mint; clearIdentity(); void load();
      });
      action.appendChild(button); tr.appendChild(action); el('rows').appendChild(tr);
    }
  }
  function when(value) {
    const date = new Date(typeof value === 'number' ? value * 1000 : value);
    return Number.isFinite(date.getTime()) ? date.toLocaleString('zh-CN') : '时间未记录';
  }
  async function history(mint, token, cursor = null) {
    if (!el('history')) return;
    let path = '/api/frank-watch-metadata-events?mint=' + encodeURIComponent(mint) + '&limit=100';
    if (cursor) path += '&cursor=' + encodeURIComponent(cursor);
    const result = await request(path);
    if (token !== epoch || currentMint() !== mint) return;
    if (!Array.isArray(result.rows)) throw new Error('变更审计响应无效。');
    if (!cursor) el('history').replaceChildren();
    else if (historyNext) historyNext.remove();
    historyNext = null;
    for (const event of result.rows) {
      if (event.mint !== mint) throw new Error('变更审计Mint不匹配。');
      const paragraph = document.createElement('p');
      paragraph.textContent = when(event.created_at) + ' · 版本 ' + event.revision +
        ' · 变更 ' + (event.event_id || '未记录') + ' · ' + JSON.stringify(event.before) + ' → ' + JSON.stringify(event.after);
      el('history').appendChild(paragraph);
    }
    if (!result.rows.length && !cursor) {
      const paragraph = document.createElement('p'); paragraph.textContent = '该Mint尚无保存的用户变更。';
      el('history').appendChild(paragraph);
    }
    if (result.next_cursor) {
      const button = document.createElement('button'); button.type = 'button';
      button.className = 'link-btn'; button.textContent = '更多变更历史';
      button.addEventListener('click', () => {
        button.disabled = true;
        void history(mint, token, result.next_cursor).catch(() => {
          if (token === epoch) { button.disabled = false; el('status').textContent = '审计读取失败，请重新读取最新记录。'; }
        });
      });
      historyNext = button; el('history').appendChild(button);
    }
  }
  async function load(cursor = null) {
    if (saving) return;
    const mint = currentMint();
    if (mint && !validMint(mint)) { clearIdentity(); el('status').textContent = '请输入完整Solana Mint。'; return; }
    const keep = preservedDraft && preservedDraft.mint === mint ? preservedDraft.value :
      (loaded && loaded.mint === mint && dirty ? draft() : null);
    const token = ++epoch;
    loaded = null; listNext = null; controls();
    el('status').textContent = mint ? '正在读取该Mint的本机用户记录…' : '正在读取已保存的观察记录…';
    try {
      let path = '/api/frank-watch-metadata?limit=100';
      if (mint) path += '&mint=' + encodeURIComponent(mint);
      if (cursor) path += '&cursor=' + encodeURIComponent(cursor);
      const result = await request(path);
      if (token !== epoch || currentMint() !== mint) return;
      if (!Array.isArray(result.rows)) throw new Error('元数据列表响应无效。');
      if (!mint) {
        renderList(result.rows, !!cursor); listNext = result.next_cursor || null;
        if (el('history')) el('history').replaceChildren();
        el('status').textContent = '已读取保存记录' + (result.total_matching != null ? '，共 ' + result.total_matching + ' 个Mint' : '') +
          (listNext ? '；可继续下一页。' : '；当前列表已到末页。') + '请选择Mint并读取后编辑。';
      } else {
        if (result.rows.length !== 1) throw new Error('精确Mint查询未返回唯一身份。');
        loaded = rowOf(result.rows[0], mint);
        setDraft(keep || loaded); dirty = !!keep; preservedDraft = null;
        el('status').textContent = '已读取版本 ' + loaded.revision + (keep ? '；已保留草稿，请确认后保存。' : '；修改仅影响用户观察记录。');
        void history(mint, token).catch(() => {
          if (token === epoch) el('status').textContent += ' 变更审计暂不可读，可重新读取。';
        });
      }
    } catch (error) {
      if (token !== epoch) return;
      loaded = null;
      if (keep) { preservedDraft = {mint,value:keep}; setDraft(keep); }
      el('status').textContent = error.status === 409 ? '列表版本已变化，请从第一页重新读取；草稿保留。' : '本机记录读取失败，未允许保存。';
    } finally { if (token === epoch) controls(); }
  }
  async function save() {
    const mint = currentMint();
    if (saving || !loaded || loaded.mint !== mint) return;
    const value = draft();
    if (!overrides.has(value.watch_override) || typeof value.note !== 'string') return;
    const expected = loaded.revision;
    const intent = JSON.stringify({mint,expected_revision:expected,...value});
    if (!retry || retry.intent !== intent) retry = {intent,key:crypto.randomUUID()};
    const token = epoch; saving = true; controls();
    el('status').textContent = '正在保存用户观察记录…';
    try {
      const result = await request('/api/frank-watch-metadata/' + encodeURIComponent(mint),
        {expected_revision:expected,idempotency_key:retry.key,...value});
      if (token !== epoch || currentMint() !== mint) return;
      loaded = rowOf(result,mint); setDraft(loaded); dirty = false; retry = null; preservedDraft = null;
      el('status').textContent = '已保存版本 ' + loaded.revision + '；收藏、备注与用户观察选择已持久保存。';
      void history(mint,token).catch(() => {
        if (token === epoch) el('status').textContent += ' 审计暂不可读，保存结果仍保留。';
      });
    } catch (error) {
      if (token !== epoch) return;
      if (error.status === 409) {
        preservedDraft = {mint,value}; loaded = null; retry = null;
        el('status').textContent = '版本冲突，草稿已保留；请读取最新版本，确认草稿后再保存。';
      } else {
        el('status').textContent = '保存结果尚未确认；草稿保留。可点击保存重试同一请求，或读取最新记录核对。';
      }
    } finally { saving = false; controls(); }
  }
  el('mint').addEventListener('input', clearIdentity);
  for (const key of ['pinned','note','override']) {
    const changed = () => { dirty = true; retry = null; };
    el(key).addEventListener('input',changed); el(key).addEventListener('change',changed);
  }
  el('load').addEventListener('click', () => { void load(); });
  el('save').addEventListener('click', () => { void save(); });
  if (el('next')) el('next').addEventListener('click', () => { if (listNext && !currentMint()) void load(listNext); });
  controls();
})();

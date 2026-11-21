(() => {
  'use strict';
  const get = name => document.getElementById('frank-notification-' + name);
  if (!get('panel')) return;
  const stateLabels = {
    PENDING:'待处理', SENDING:'发送中', IN_FLIGHT:'结果待核对', SENT_UNVERIFIED:'发送结果未核实',
    SENT_VERIFIED:'台账标记已核实', COMMAND_ACCEPTED:'本地命令已受理', RETRY_PENDING:'等待恢复',
    RETRYABLE_ERROR:'可恢复错误', PERMANENT_ERROR:'终止错误', CREDENTIAL_BLOCKED:'凭据不可用',
    MANUAL_REVIEW:'待核对', DRY_RUN_AUDIT:'仅记录',
  };
  const proofLabels = {
    GMAIL_SENT_READBACK:'Gmail Sent 回读已绑定', LOCAL_COMMAND_ACKNOWLEDGMENT:'本地命令已受理',
    OUTCOME_UNVERIFIED:'结果未核实', NO_VERIFIED_RECEIPT:'无可核验回执',
  };
  const segments = {
    event_to_detect:'事件至检测', detect_to_index:'检测至入库', index_to_classify:'入库至分类',
    classify_to_signal:'分类至信号', signal_to_decision:'信号至决策', decision_to_enqueue:'决策至入队',
    enqueue_to_attempt:'入队至尝试', attempt_to_provider_acceptance_log:'尝试至记录受理',
    recorded_acceptance_to_gmail_readback:'记录受理至 Gmail 回读', attempt_to_recipient_delivery:'尝试至收件',
  };
  const hash = /^[a-f0-9]{64}$/;
  const time = new Intl.DateTimeFormat('zh-CN',{dateStyle:'short',timeStyle:'medium',timeZone:'Asia/Bangkok'});
  let currentCursor = null;
  let nextCursor = null;
  let busy = false;
  const pending = new Map();

  function element(tag, value) {
    const el = document.createElement(tag);
    if (value != null) el.textContent = value;
    return el;
  }

  function setBusy(value) {
    busy = value;
    get('channel').disabled = value;
    get('read').disabled = value;
    get('next').disabled = value || !nextCursor;
  }

  async function request(path, body) {
    const params = body
      ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}
      : {headers:{'X-Frank-Research-Read':'1'}};
    const response = await fetch(path,{...params,mode:'same-origin',cache:'no-store',signal:AbortSignal.timeout(10000)});
    if (response.status === 409) throw new Error('STALE');
    if (!response.ok) throw new Error('UNAVAILABLE');
    return response.json();
  }

  function paint(row) {
    const item = element('article');
    item.className = 'cluster-card';
    const delivery = row.delivery || {};
    const channel = row.channel === 'gmail' ? 'Gmail' : '本地';
    const source = row.source_namespace === 'SCANNER_V1' ? 'Frank V1' : 'Mission Control';
    item.append(element('strong',source+' · '+channel+' · '+(stateLabels[row.outbox_status] || '状态未核实')));
    item.append(element('p',proofLabels[delivery.receipt_proof] || '回执未核实'));
    const evidence = element('details');
    evidence.append(element('summary','身份、来源与分段延迟'));
    evidence.append(element('p','通知 ID '+row.notification_id));
    if (hash.test(row.policy_hash || '')) evidence.append(element('p','策略摘要 '+row.policy_hash));
    if (Number.isSafeInteger(delivery.attempt_count)) evidence.append(element('p','已记录尝试 '+delivery.attempt_count+' 次'));
    if (typeof delivery.last_activity_at==='string' && Number.isFinite(Date.parse(delivery.last_activity_at))) {
      evidence.append(element('p','最后活动 '+time.format(new Date(delivery.last_activity_at))+'（曼谷时间）'));
    }
    const timing = element('ul');
    for (const [key,label] of Object.entries(segments)) {
      const value = row.latency?.[key];
      const seconds = typeof value?.seconds==='number' && Number.isFinite(value.seconds) && value.seconds>=0 ? value.seconds+' 秒' : '证据不足';
      timing.append(element('li',label+' · '+seconds));
    }
    evidence.append(timing);
    item.append(evidence);
    const archive = row.archive;
    if (archive && typeof archive.archived==='boolean' && Number.isSafeInteger(archive.revision) && archive.revision>=0) {
      const button = element('button',archive.archived?'取消归档':'归档此记录');
      button.className = 'link-btn';
      button.type = 'button';
      button.addEventListener('click',()=>changeArchive(row,button));
      item.append(button);
    }
    return item;
  }

  async function load(cursor) {
    const query = new URLSearchParams({limit:'20'});
    if (get('channel').value) query.set('channel',get('channel').value);
    if (cursor) query.set('cursor',cursor);
    const data = await request('/api/frank-notification-audit?'+query);
    if (!['OK','PARTIAL'].includes(data.status) || !Array.isArray(data.rows)) throw new Error('INVALID');
    const rows = data.rows.filter(row=>row && hash.test(row.notification_id) && ['gmail','local'].includes(row.channel));
    if (rows.length!==data.rows.length) throw new Error('INVALID');
    get('rows').replaceChildren(...rows.map(paint));
    currentCursor = cursor;
    nextCursor = typeof data.next_cursor==='string' && data.next_cursor?data.next_cursor:null;
    get('status').textContent = (data.status==='PARTIAL'?'部分本机审计台账不可读。':'')+
      (rows.length?'本页 '+rows.length+' 条通知记录。':'本页没有可读取的通知记录。');
  }

  async function read(cursor) {
    if (busy) return;
    setBusy(true);
    get('status').textContent = '读取本机通知审计…';
    try { await load(cursor); }
    catch (err) {
      get('status').textContent = err.message==='STALE'?'来源已更换，请从第一页读取。':'通知审计暂不可用。';
    } finally { setBusy(false); }
  }

  async function changeArchive(row,button) {
    if (busy) return;
    const key = [row.notification_id,row.channel,row.archive.revision,String(!row.archive.archived)].join(':');
    const id = pending.get(key) || crypto.randomUUID();
    pending.set(key,id);
    button.disabled = true;
    setBusy(true);
    try {
      await request('/api/frank-notification-archive',{notification_id:row.notification_id,channel:row.channel,
        archived:!row.archive.archived,expected_revision:row.archive.revision,idempotency_key:id});
      pending.delete(key);
      await load(currentCursor);
    } catch (err) {
      if (err.message==='STALE') pending.delete(key);
      get('status').textContent = err.message==='STALE'?'归档版本已变化，请重新读取。':'归档结果暂未确认，可重试同一操作。';
    } finally {
      button.disabled = false;
      setBusy(false);
    }
  }

  get('channel').addEventListener('change',()=> {
    nextCursor = null;
    get('next').disabled = true;
    get('rows').replaceChildren();
    get('status').textContent = '选择后点读取通知审计。';
  });
  get('read').addEventListener('click',()=>read(null));
  get('next').addEventListener('click',()=>{if (nextCursor) read(nextCursor);});
})();

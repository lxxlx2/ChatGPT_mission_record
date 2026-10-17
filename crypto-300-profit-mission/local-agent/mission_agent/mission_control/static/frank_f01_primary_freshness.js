/* Display-only guard around the approved F01 candidate renderer.
   Frozen BUY decisions stay unchanged; an unverified/expired main card may
   never retain the visual '可跟' label from an earlier response. */
(() => {
  'use strict';
  const MAX_F01_AGE_SECONDS = 8;
  const validMint = mint => typeof mint === 'string' &&
    /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(mint);
  const isAction = d => d === 'BUY' || d === 'SMALL_BUY';

  function verifyRows(rows, doc, now) {
    if (!Array.isArray(rows) || !doc || doc.status !== 'OK' ||
        !Array.isArray(doc.eligible) ||
        !Number.isInteger(doc.eligible_count) ||
        doc.eligible_count !== doc.eligible.length ||
        typeof doc.as_of_epoch !== 'number' ||
        !Number.isFinite(doc.as_of_epoch) ||
        !Number.isFinite(now) || now < doc.as_of_epoch ||
        now >= doc.as_of_epoch + MAX_F01_AGE_SECONDS) return null;
    const identities = (input) => {
      const m = new Map();
      for (const row of input) {
        if (!row || row.person_id !== 'frank' || !validMint(row.mint) ||
            !isAction(row.decision) ||
            typeof row.source_signal_id !== 'string' || !row.source_signal_id ||
            m.has(row.mint)) return null;
        m.set(row.mint, row.source_signal_id + '\0' + row.decision);
      }
      return m;
    };
    const expected = identities(rows);
    const received = identities(doc.eligible);
    if (!expected || !received || expected.size !== received.size) return null;
    for (const [mint, identity] of expected) {
      if (received.get(mint) !== identity) return null;
    }
    return doc.as_of_epoch + MAX_F01_AGE_SECONDS;
  }
  if (typeof globalThis !== 'undefined')
    globalThis.FrankPrimaryF01Freshness = {verifyRows};
  if (typeof window === 'undefined' || typeof document === 'undefined' ||
      typeof window.renderCandidates !== 'function') return;

  const original = window.renderCandidates;
  const container = document.getElementById('candidates');
  if (!container) return;
  let generation = 0;
  let expiresAt = 0;
  let timeout = null;
  let cards = [];
  let originRows = [];
  const countLabel = () => {
    const stats = document.getElementById('stats');
    if (!stats) return null;
    for (const node of stats.querySelectorAll('.stat')) {
      const label = node.querySelector('span');
      if (label && label.textContent.trim() === '当前可跟候选')
        return node.querySelector('strong');
    }
    return null;
  };
  const reflectCount = (verified) => {
    const el = countLabel();
    if (el) el.textContent = verified ? String(cards.length) : '待核实';
  };
  const emit = () => {
    if (typeof window.dispatchEvent === 'function' && typeof Event === 'function')
      window.dispatchEvent(new Event('frank:f01-guard-updated'));
  };
  const mask = () => {
    for (const info of cards) {
      const {card, badge, conclusion} = info;
      card.dataset.f01GuardState = 'UNVERIFIED';
      card.classList.remove('decision-buy', 'decision-small-buy');
      card.classList.add('decision-unverified');
      if (badge) {
        badge.textContent = '资格已失效 / 待核实';
        badge.className = 'badge no-buy';
      }
      if (conclusion)
        conclusion.textContent = '当前跟单结论：“资格已失效或来源待核实，不跟”';
    }
    reflectCount(false);
    emit();
  };
  const reveal = (until) => {
    const now = Date.now() / 1000;
    if (now >= until) { mask(); return; }
    for (const {card,badge,conclusion, originalBadge, originalConclusion, originalClass} of cards) {
      card.dataset.f01GuardState = 'VERIFIED';
      card.dataset.f01ValidUntilEpoch = String(until);
      card.className = originalClass;
      if (badge && originalBadge) {
        badge.className = originalBadge.cls;
        badge.textContent = originalBadge.text;
      }
      if (conclusion) conclusion.textContent = originalConclusion;
    }
    reflectCount(true);
    emit();
  };
  const cancel = () => {
    if (timeout !== null) clearTimeout(timeout);
    timeout = null;
  };
  const checkCurrent = () => {
    const gen = ++generation;
    cancel();
    expiresAt = 0;
    mask();
    if (!cards.length) return;
    void (async () => {
      try {
        const response = await fetch('/api/follow-opportunities', {
          method:'GET', cache:'no-store', credentials:'same-origin'
        });
        if (!response.ok) return;
        const doc = await response.json();
        if (gen !== generation) return;
        const until = verifyRows(originRows, doc, Date.now()/1000);
        if (until === null) return;
        expiresAt = until;
        reveal(until);
        timeout = setTimeout(() => {
          if (gen === generation) {
            expiresAt = 0;
            mask();
          }
        }, Math.max(0, Math.ceil((until - Date.now()/1000)*1000) + 1));
      } catch (_) {
        if (gen === generation) mask();
      }
    })();
  };
  window.renderCandidates = function(rows, status) {
    original.call(this, rows, status);
    originRows = Array.isArray(rows) ? rows : [];
    const rendered = Array.from(container.querySelectorAll('.candidate-card'));
    const eligible = originRows.filter(r => r && isAction(r.decision));
    cards = rendered.map((card, index) => {
      const row = originRows[index] || {};
      const badge = card.querySelector('.candidate-head .badge');
      const conclusion = card.querySelector('.decision-reason > span');
      card.dataset.f01SourceSignalId = String(row.source_signal_id || '');
      card.dataset.f01Decision = String(row.decision || '');
      return {
        card, badge, conclusion,
        originalBadge: badge ? {cls:badge.className,text:badge.textContent} : null,
        originalConclusion: conclusion ? conclusion.textContent : '',
        originalClass: card.className
      };
    });
    if (eligible.length !== rendered.length) {
      // Never trust an unexpected DOM/card mapping or a mixed old renderer.
      originRows = [];
    }
    checkCurrent();
  };
  if (typeof document.addEventListener === 'function') {
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && cards.length) {
        if (Date.now()/1000 >= expiresAt) mask();
        checkCurrent();
      }
    });
  }
  // When original app.js rendered before this script loaded, there is no
  // trusted source identity. Fail closed until its next controlled render.
  if (container.querySelectorAll('.candidate-card').length) {
    for (const card of container.querySelectorAll('.candidate-card')) {
      card.classList.remove('decision-buy','decision-small-buy');
      card.classList.add('decision-unverified');
      const badge=card.querySelector('.candidate-head .badge');
      if (badge) {badge.className='badge no-buy';badge.textContent='资格待核实';}
      const c=card.querySelector('.decision-reason > span');
      if (c) c.textContent='当前资格未核实，不跟';
    }
  }
})();

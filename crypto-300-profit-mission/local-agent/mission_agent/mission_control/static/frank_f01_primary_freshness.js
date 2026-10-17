/* Read-only, fail-closed presentation guard for the frozen F01 renderer.
   Historical BUY is never '可跟' without fresh same-signal F01 evidence. */
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
    const identities = (input, allowNonAction) => {
      const m = new Map();
      for (const row of input) {
        if (allowNonAction && row && !isAction(row.decision)) continue;
        if (!row || row.person_id !== 'frank' || !validMint(row.mint) ||
            !isAction(row.decision) ||
            typeof row.source_signal_id !== 'string' || !row.source_signal_id ||
            m.has(row.mint)) return null;
        m.set(row.mint, row.source_signal_id + '\0' + row.decision);
      }
      return m;
    };
    const expected = identities(rows, true);
    const received = identities(doc.eligible, false);
    // An empty or mixed historic row set must NEVER verify a missing BUY.
    if (!expected || !received || expected.size === 0 ||
        expected.size !== received.size) return null;
    for (const [mint, identity] of expected)
      if (received.get(mint) !== identity) return null;
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
  let timer = null;
  let request = null;
  let actionCards = [];
  let allRows = [];
  let verifiedSnapshot = null;

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
  const reflectCount = verified => {
    const label = countLabel();
    if (label) label.textContent = verified ? String(actionCards.length) :
      actionCards.length ? '待核实' : '0';
  };
  const emit = () => {
    if (typeof window.dispatchEvent === 'function' && typeof Event === 'function')
      window.dispatchEvent(new Event('frank:f01-guard-updated'));
  };
  const mask = () => {
    for (const {card, badge, conclusion} of actionCards) {
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
  const reveal = until => {
    if (Date.now() / 1000 >= until) { mask(); return; }
    for (const {card, badge, conclusion, originalBadge, originalConclusion, originalClass} of actionCards) {
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
    if (timer !== null) clearTimeout(timer);
    timer = null;
    if (request !== null && typeof request.abort === 'function') request.abort();
    request = null;
  };
  const armExpiry = (gen, until) => {
    if (timer !== null) clearTimeout(timer);
    timer = setTimeout(() => {
      if (gen === generation) {
        expiresAt = 0;
        verifiedSnapshot = null;
        mask();
      }
    }, Math.max(0, Math.ceil((until - Date.now() / 1000) * 1000) + 1));
  };

  const checkCurrent = preserve => {
    const gen = ++generation;
    cancel();
    const prior = expiresAt;
    if (preserve && actionCards.length && Date.now() / 1000 < prior) {
      reveal(prior);
      armExpiry(gen, prior);
    } else {
      expiresAt = 0;
      verifiedSnapshot = null;
      mask();
    }
    if (!actionCards.length) return;

    void (async () => {
      const controller = typeof AbortController === 'function' ?
        new AbortController() : null;
      request = controller;
      // Bound the independent verification path; stalled F01 never revives BUY.
      const budget = controller ? setTimeout(() => controller.abort(), 2500) : null;
      try {
        const response = await fetch('/api/follow-opportunities', {
          method: 'GET', cache: 'no-store', credentials: 'same-origin',
          ...(controller ? {signal: controller.signal} : {})
        });
        if (!response.ok) throw new Error('F01_SOURCE_UNAVAILABLE');
        const doc = await response.json();
        if (gen !== generation) return;
        const until = verifyRows(allRows, doc, Date.now() / 1000);
        if (until === null) throw new Error('F01_IDENTITY_OR_TTL_INVALID');
        expiresAt = until;
        verifiedSnapshot = JSON.stringify(allRows);
        reveal(until);
        armExpiry(gen, until);
      } catch (_) {
        if (gen === generation) {
          expiresAt = 0;
          verifiedSnapshot = null;
          mask();
        }
      } finally {
        if (budget !== null) clearTimeout(budget);
        if (gen === generation) request = null;
      }
    })();
  };

  window.renderCandidates = function(rows, status) {
    const incoming = Array.isArray(rows) ? rows : [];
    const snapshot = JSON.stringify(incoming);
    const preserve = !!verifiedSnapshot && snapshot === verifiedSnapshot &&
      expiresAt > Date.now() / 1000;
    original.call(this, rows, status);
    allRows = incoming;
    const rendered = Array.from(container.querySelectorAll('.candidate-card'));
    const allCards = [];
    const seen = new Set();
    let mapped = rendered.length === incoming.length;
    for (let index = 0; index < rendered.length; index++) {
      const card = rendered[index];
      const row = incoming[index];
      const mint = (card.querySelector('.ca-full')?.textContent || '').trim();
      if (!row || !validMint(mint) || mint !== row.mint || seen.has(mint))
        mapped = false;
      seen.add(mint);
      if (!row || !isAction(row.decision)) continue;
      const badge = card.querySelector('.candidate-head .badge');
      const conclusion = card.querySelector('.decision-reason > span');
      card.dataset.f01SourceSignalId = String(row.source_signal_id || '');
      card.dataset.f01Decision = String(row.decision || '');
      allCards.push({
        card, badge, conclusion,
        originalBadge: badge ? {cls:badge.className,text:badge.textContent} : null,
        originalConclusion: conclusion ? conclusion.textContent : '',
        originalClass: card.className
      });
    }
    actionCards = allCards;
    if (!mapped) {
      allRows = [];
      checkCurrent(false);
      return;
    }
    checkCurrent(preserve);
  };

  if (typeof document.addEventListener === 'function')
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && actionCards.length) checkCurrent(
        !!verifiedSnapshot && Date.now() / 1000 < expiresAt);
    });

  // Any early-rendered cards before this script loaded have no trustworthy
  // identity; the following normal F01 render must verify anew.
  const initial = Array.from(container.querySelectorAll('.candidate-card'));
  if (initial.length) {
    for (const card of initial) {
      const badge = card.querySelector('.candidate-head .badge');
      if (!badge || !['可跟','小仓跟'].includes(badge.textContent)) continue;
      card.classList.remove('decision-buy','decision-small-buy');
      card.classList.add('decision-unverified');
      card.dataset.f01GuardState = 'UNVERIFIED';
      badge.className = 'badge no-buy';
      badge.textContent = '资格待核实';
      const text = card.querySelector('.decision-reason > span');
      if (text) text.textContent = '当前资格未核实，不跟';
    }
  }
})();

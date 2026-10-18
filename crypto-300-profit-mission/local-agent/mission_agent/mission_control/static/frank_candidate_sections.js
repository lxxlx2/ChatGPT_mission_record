/* Display-only current-vs-history grouping. The reviewed F01 gate remains the
   sole authority for executable BUY/SMALL_BUY presentation. */
(() => {
  'use strict';
  const BUY_WINDOW_SECONDS = 600;
  const BUY_SIDES = new Set(['BUY', 'ADD', 'REENTRY']);
  const epoch = value => {
    if (typeof value === 'number') return Number.isFinite(value) ? value : null;
    if (typeof value !== 'string' || !value.trim()) return null;
    if (/^\d+(?:\.\d+)?$/.test(value)) {
      const n = Number(value);
      return Number.isFinite(n) ? n : null;
    }
    if (!/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return null;
    const ms = Date.parse(value);
    return Number.isFinite(ms) ? ms / 1000 : null;
  };
  const fresh = (value, now, windowSeconds) => {
    const at = epoch(value);
    return at !== null && now >= at && now - at <= windowSeconds;
  };
  function split(rows, now = Date.now() / 1000) {
    const current = [], archived = [];
    const validClock = Number.isFinite(now);
    for (const row of Array.isArray(rows) ? rows : []) {
      if (!row || typeof row !== 'object') continue;
      const recentBuy = validClock && fresh(row.latest_buy_at, now, BUY_WINDOW_SECONDS);
      const recentDecision = validClock && fresh(row.decision_created_at, now, BUY_WINDOW_SECONDS);
      const pending = row.decision === 'UNASSESSED' && !row.decision_created_at;
      const active = row.candidate_source !== 'MISSION_CONTROL_OVERLAY' &&
        row.position_state === 'OPEN' && BUY_SIDES.has(row.latest_side) &&
        recentBuy && (recentDecision || pending);
      (active ? current : archived).push(row);
    }
    return { current, archived };
  }
  if (typeof globalThis !== 'undefined')
    globalThis.FrankCandidateSections = { split, epoch, fresh };
})();

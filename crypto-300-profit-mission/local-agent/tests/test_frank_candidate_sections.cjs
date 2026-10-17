'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const code = fs.readFileSync(path.join(__dirname, '../mission_agent/mission_control/static/frank_candidate_sections.js'), 'utf8');
const sandbox = { Date };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const { split, fresh, epoch } = sandbox.FrankCandidateSections;
const now = 1_800_000_000;
const iso = t => new Date(t * 1000).toISOString();
const base = { person_id: 'frank', pattern: 'ACCUMULATION', position_state: 'OPEN',
  latest_side: 'BUY', decision: 'WAIT', latest_buy_at: now - 10,
  decision_created_at: iso(now - 4) };
const c = row => ({ ...base, ...row });
const inputs = [
  c({ decision: 'NO_BUY', position_state: 'CLOSED', latest_side: 'SELL' }),
  c({ decision: 'NO_BUY', position_state: 'INVENTORY_UNDETERMINED', latest_side: 'SELL' }),
  c({ decision: 'WAIT', latest_buy_at: now - 164310, decision_created_at: iso(now - 113541) }),
  c({ candidate_source: 'MISSION_CONTROL_OVERLAY', decision: 'BUY' }),
  c({ decision: 'BUY', decision_created_at: iso(now - 601) }),
  c({ decision: 'BUY', latest_buy_at: now + 1 }),
  c({ decision: 'BUY', latest_buy_at: now - 600, decision_created_at: iso(now - 600) }),
  c({ decision: 'WAIT', latest_side: 'ADD' }),
  c({ decision: 'UNASSESSED', decision_created_at: undefined, latest_side: 'REENTRY' }),
];
const result = split(inputs, now);
assert.equal(result.current.length, 3);
assert.equal(result.archived.length, 6);
assert.equal(result.current[0].decision, 'BUY');
assert.equal(result.current[2].decision, 'UNASSESSED');
assert.equal(split(inputs.slice(0, 3), now).current.length, 0);
assert.equal(split(inputs, NaN).current.length, 0);
assert.equal(fresh(now - 600, now, 600), true);
assert.equal(fresh(now - 601, now, 600), false);
assert.equal(fresh(now + 1, now, 600), false);
assert.equal(fresh('2026-10-18T06:10:33+07:00', epoch('2026-10-17T23:10:33Z'), 0), true);
assert.equal(epoch('2026-10-18T06:10:33'), null);
assert.equal(epoch('bogus'), null);
assert.equal(split([null, undefined], now).current.length, 0);
console.log('FRANK_CURRENT_CANDIDATE_SECTIONS_TEST_PASS');

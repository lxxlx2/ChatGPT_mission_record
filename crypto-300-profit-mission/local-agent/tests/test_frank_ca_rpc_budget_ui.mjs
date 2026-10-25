import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(
  new URL('../mission_agent/mission_control/static/app.js', import.meta.url), 'utf8'
);
const match = source.match(/function clusterErrorMessage\(error\) \{[\s\S]*?\n\}/);
assert.ok(match, 'must find production CA error message function');
const context = vm.createContext({});
vm.runInContext(match[0]+';globalThis.clusterErrorMessage = clusterErrorMessage;', context);
const format = context.clusterErrorMessage;

test('budget exhausted is explicitly incomplete, not generic rate-limit/retry', () => {
  const message = format({
    type: 'RPC_JOB_BUDGET_EXHAUSTED',
    message: 'CLUSTER_ANALYSIS_INCOMPLETE_BUDGET_EXHAUSTED',
  });
  assert.match(message, /分析未完成/);
  assert.match(message, /停止追加请求/);
  assert.doesNotMatch(message, /稍后重试/);
});

test('legacy normal error path remains intact', () => {
  assert.match(format({type: 'SomeFailure', message: 'CLUSTER_ANALYSIS_UNAVAILABLE'}), /SomeFailure/);
});

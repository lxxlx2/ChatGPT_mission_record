# F0 BSC RPC response adapter — offline only

Status: `OFFLINE_RPC_FIXTURE_ONLY / 18_TESTS_PASS / NOT_LIVE / NO_GO`.

Upstream authority: PR #113 fixed `9134fcd41df49ef836b81c8a040974ad89c1fde1`; F0 preparation PR #116 fixed `cf88cd9f6568502f5c052ae3befc9cc16cbab98b`; offline state-machine PR #118 independent APPROVE at fixed `78e4d26ff7cd1074b7c8de44109b4356e5d0409d`. The new branch is based on PR #118's approved SHA, with this adapter added without modifying the previously approved state machine.

## Specific new capability

- `block_candidates` consumes a **saved** `eth_getBlockByNumber` `full_transaction_flag=true` JSON-RPC envelope; requires block/tx identity and unique tx hashes. Enumerates watched senders and *unwatched Router senders* as control candidates. These are **not** pre-registered, randomly sampled or executable controls yet: no online discovery was performed.
- `receipt_observation` consumes a **saved** `eth_getTransactionReceipt` response. Verifies tx hash and block identity; parses well-formed ERC20 `Transfer` log topics, wallet in/out and quote-token transfer direction. A BUY/SELL hint is possible only for a restricted simple one-token, opposite quote-asset-flow case at a preconfigured Router. The result **always** says `E2_attested=false` and `finality=UNRESOLVED_F1_POLICY`: receipt logs alone do not prove swap-route causality; genuine confirmations, reorg monitoring, taxes and saleability are not verified.
- `decode_get_amounts_out` consumes a **saved** `eth_call` JSON-RPC response with ABI `uint256[]` result, strict dynamic-array offset/count/positive-amount checks. It returns `SIMULATED_ARCHIVE_QUOTE`, **not `QUOTED`**. Failed/invalid responses yield `NO_QUOTE`.
- JSON parser is standard-library only. No networking/client, sockets, token signing, fees, production notifications, launcher, scheduler, persistent pipeline or RPC credentials.
- `--fixture` CLI accepts only explicitly `trial=true`, `mode=OFFLINE_RPC_FIXTURE_ONLY`. All actual E3, real QUOTED, PnL and RPC counts remain zero. No RPC was invoked during local tests.

## Evidence and limitations

Offline synthetic-on-the-wire-shaped fixtures exercise full-block transaction enumeration, receipt log parsing and ABI quote shape without claiming the fixtures were captured on BSC. The output names and source hashes are preserved for reproducible offline review.

**Outstanding F0 hard gates, not solved by this PR:** a free, timely source for watchlist and full ordinary Router control stream; observed first-actionable timestamp capture; deterministic random control selection at runtime; shared actual `+60/+300/+900s` requested/received timestamps; independent per-wallet coverage denominator; transaction replay/monotonic clock integration with PR #118; actual on-chain E2 causal Router logs; provider quotas and separate control-stream costs. No live service is authorized. Do not call this implementation an integrated real-time collector.

BNB official sources for future F0 network feasibility (not tested in this PR):

- https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/ (some official public mainnet endpoints disable `eth_getLogs`, transport limits apply)
- https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/bsc-api-list/ (`eth_getBlockByNumber` full transaction flag and finality APIs)

## Actual offline commands

```zsh
python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -p 'test_f0_rpc_adapter.py' -v
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_rpc_adapter.py --fixture crypto-300-profit-mission/bsc-forward-follow-model/f0/fixtures/rpc_envelopes.json
```

The first command runs 18 adapter tests. To run the previously approved state-machine tests too, use `python3 -m unittest discover -s crypto-300-profit-mission/bsc-forward-follow-model/f0/tests -v` from the full branch checkout. Any actual F0 RPC, Mac daemon or 24–48h trial still requires separate user authorization and a budgeted run contract.

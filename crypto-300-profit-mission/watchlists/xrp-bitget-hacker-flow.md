# XRP / Bitget Hacker Flow Monitor

Updated: 2026-09-27 01:18 Asia/Bangkok
Status: ACTIVE while the Variational XRP event position remains active

## Purpose

Track attacker-controlled XRP supply that can invalidate or materially weaken the existing XRP event-long thesis.

This is a factual event-flow monitor. It does not create a new trade.

## Canonical incident anchor

Bitget's official incident update identifies the primary XRP attacker hub:
- `rwNhefsz1UQEusxhCvHip3RANinWi4CTck`

BitOK independently reconstructed the initial hub inflow and five first-tier holding wallets:
- `rDRV9nLg8xbLsafKZnhNgWuE1TiSLE95hs`
- `r3UGfDM4ZyFSCzKH7TQEjgago9QoUJagtJ`
- `rH7oMFKBgdK99TPQctFVzddD7srRzyCqZn`
- `rwSjBrtxBC75TqZ5YvJ1TGfaRpQvVNsAKw`
- `r6NcwN3dR5ciyBv9XsLyMNc9Kg2FBCs7Y`

Initial stolen XRP routed to the hub: about **102.98M XRP**.

## Verified baselines

2026-09-25 03:35 UTC BitOK reconstruction:
- hub + first-tier wallets: about **102.59M XRP** still held;
- only a small branch had moved onward.

2026-09-26 CoinDesk follow-up:
- about **54M XRP** had left the five original attacker holding accounts;
- about **49M XRP** remained across those original holding accounts;
- two 20M-XRP wallets were almost emptied and a third was being drained.

Important: movement from original holding accounts does not prove all XRP was sold. Classify destination separately.

## Stored triggers

While the XRP position is active, every Mission run must check fresh evidence for:

1. **ATTACKER_MAJOR_MOVE**
   - newly verified attacker-controlled XRP movement >= **5M XRP** since the prior stored baseline, even if destination is not yet classified.

2. **ATTACKER_LIQUIDITY_RISK**
   - >= **5M XRP** routed toward a CEX, bridge, swap venue or other executable-liquidity path;
   - or several smaller traced movements whose verified aggregate reaches >=5M XRP.

3. **BITGET_REPLENISHMENT**
   - credible Bitget-controlled XRP replenishment / market acquisition >= **5M XRP**.

4. **FLOW_REGIME_CHANGE**
   - original attacker holding-cluster balance falls by >=10% from the previous verified baseline;
   - or destination classification changes materially from parked/internal to executable liquidity.

## Alert policy

A new trigger is substantive and should use Gmail + ChatGPT because it affects an active XRP position.

Alert must distinguish:
- attacker internal redistribution;
- bridge/swap flow;
- CEX deposit / executable liquidity;
- unclassified destination.

Do not claim "sold" unless sale/exchange evidence supports it.

Deduplicate by the verified cumulative-flow milestone and destination class.

## Source order

Prefer:
1. Bitget official incident updates;
2. direct XRPL/explorer evidence when available;
3. SlowMist/MistTrack, BitOK, Lookonchain or similarly attributable on-chain tracing;
4. CoinDesk / The Block for independently reported current balances and movements.

Chinese-language websites are not evidence sources.

## Monitoring defect found 2026-09-27

The prior `positions/xrp-variational.md` said to monitor attacker flows, but the automatic runtime lacked a dedicated address/baseline lane. As a result, the Sep-26 ~54M-XRP movement was not surfaced by the Mission monitor.

This file is the operational repair.

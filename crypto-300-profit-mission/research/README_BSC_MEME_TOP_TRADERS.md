BSC Meme Top Traders — manual, read-only, 2026-10-10

This Git folder contains the full researcher-facing source and offline tests. Do not download or unpack previous ZIP attachments. The original 18 project candidates plus the Alpha-only token BUBB are included (19 total).

Source:
- `bsc_meme_top_traders_readonly.py`: collect the 19 token rankings (GMGN, BSC, profit and sell volume), export raw provider responses, summarize cross-token wallet candidates.
- `bsc_top_trader_crosscheck.py`: conservative additional recency and 2026-first candidate audit on the preceding exports. It DOES NOT transform provider-reported PnL into verified on-chain PnL.
- `test_bsc_meme_top_traders_readonly.py`, `test_bsc_top_trader_crosscheck.py`: offline tests with invented wallets/data, no API calls.

Official upstream `gmgn-cli` installation: `npm install -g gmgn-cli`. Official auth check: `gmgn-cli config --check`; if this check fails, use `gmgn-cli config` and follow its official API Key setup instructions. Never include a personal API key in Git, output screenshots, or messages.

Safe macOS terminal workflow, does not modify an existing local Mission clone:

```bash
set -e
WORKDIR="$(mktemp -d)"
git clone --depth 1 --branch main https://github.com/lxxlx2/ChatGPT_mission_record.git "$WORKDIR/mission"
npm install -g gmgn-cli
gmgn-cli config --check
python3 -m unittest discover -s "$WORKDIR/mission/crypto-300-profit-mission/research" -p "test_bsc_meme_top_traders_readonly.py" -v
python3 -m unittest discover -s "$WORKDIR/mission/crypto-300-profit-mission/research" -p "test_bsc_top_trader_crosscheck.py" -v
python3 "$WORKDIR/mission/crypto-300-profit-mission/research/bsc_top_trader_crosscheck.py" --mode both --root "$HOME/Documents/ChatGPT/BSC_Meme_Top100" --window-days 30
printf 'Results at: %s\n' "$HOME/Documents/ChatGPT/BSC_Meme_Top100/analysis"
```

If `gmgn-cli config --check` fails, the script is not run because `set -e` stops commands immediately. This is correct and prevents unauthenticated report fabrication. CLI or API rate limits may similarly stop or limit collection. Outputs are user-local; they are **not automatically pushed into Git** because provider data and local configurations must be checked before publication.

Expected data exports:
- `raw/<token>_profit.json`, `raw/<token>_sell_volume_cur.json` (source snapshots)
- `analysis/coverage.csv`, `analysis/token_trader_samples.csv`, `analysis/cross_token_wallets.csv`
- `analysis/summary.json`, `analysis/active_candidate_review.csv`, `analysis/review_summary.json`

Interpretation: a provider ranking is not verified *historical all-DEX top-profit*; missing direct buys and incoming token transfers are exclusion flags. The same token receiver can represent a multiuser router. Recent token activity is not a confirmed recent swap. A complete followability test requires original buyer/recipient funding graph, all failed/losing trades, contemporaneous quote-asset trade receipts, 5/15/30-minute replay with gas/slippage, and live trade activity confirmation.

No schedules, automations, live validation, private keys, wallet connection, swap calls, production trading or Git production config changes are made. Status: `OBSERVE_ONLY`; `PRODUCTION_TRADING=NO_GO`.

Audited chain findings and limitations: `BSC_MEME_TOP_TRADERS_AUDIT_2026-10-10.md`.

# Mission 旧模块命名、导航及过期状态整改审计（2026-10-18）

Status: `DOCUMENTATION_ONLY / REVIEW_PENDING / NO_PATH_RENAMES`
Scope: existing **main-branch** documentation as of 2026-10-18. New/unreviewed [address-analysis Draft PR #97](https://github.com/lxxlx2/ChatGPT_mission_record/pull/97) explicitly excluded from legacy rename checks. The independent new module is indexed as `UNMERGED`; no claim its files exist on main.

## Verified baseline and governing policy

Primary repository rule: [docs/REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md); Mission-specific authority: [MISSION_SPEC.md](../crypto-300-profit-mission/MISSION_SPEC.md), [state/latest.md](../crypto-300-profit-mission/state/latest.md). Human-authored canonical research titles identify both **entity** and **purpose**; preferred filenames lower-case kebab-case `<entity>-<purpose>.md`. Operational current pointers, frozen schemas/policies, machine-generated artifacts, cross-referenced upper-case reports and immutable audit evidence retain their stable names unless a separate compatible migration is reviewed.

Inspected legacy areas: repository main/root and Mission README, Crypto Daily and TGE runtime authority/README, docs, `research/{projects,tokens,memes,nfts}`, Mission `positions/`, `watchlists/`, `meme/`, `local-agent/`, `state/`. The mapped project research directories have consistent lower-kebab-case substantive research filenames, with `README.md` used as the standard index exception.

## Corrected existing files without moving referenced paths

| Existing stable path | Actual remediation | Why |
| --- | --- | --- |
| `README.md` | Link new 449-wallet PR #97 as **Draft/unmerged**, add durable wallet/PnL/source/Git/scheduler rules and exception wording | Avoid treating incomplete research as approved monitoring or complete wallet profits |
| `crypto-300-profit-mission/README.md` | Add independent address-analysis module status + evidence/valuation/compatibility rule with no claim of main merge | Make Mission entry discoverable now without changing other module ownership |
| `crypto-300-profit-mission/positions/README.md` | **Remove stale GANG escrow pending status**; classify as closed, 0 GANG and **−96.210562 USDC before SOL fees**, sourced to dated `gang.md` | Prevent an already exited asset being counted as active capital |
| `crypto-300-profit-mission/positions/pons.md` | H1 specifies PONS historical spot/perp close and evidence | Old `PONS Position` hid the purpose |
| `crypto-300-profit-mission/positions/unicred.md` | H1 specifies historical UNICRED NFT ownership/exit | Old `UNICRED Position` hid purpose |
| `crypto-300-profit-mission/positions/gstock-plan.md` | H1 specifies GSTOCK BNB-chain closed position | Old `GStock BNB Chain Position` too generic |
| `crypto-300-profit-mission/positions/kardashev.md` | H1 states Meme historical position and retired monitor | Preserve past observations without implying active monitoring |
| `crypto-300-profit-mission/positions/shartcoin.md` | H1 states Solana Meme historical transaction and exit | Old generic H1 |
| `crypto-300-profit-mission/positions/eth-conditional.md` | H1 and explicit historical/NO_GO warning: old hourly monitoring statements superseded by current paused authority | Prevent a stored discretionary plan being mistaken for actionable live orders |
| `crypto-300-profit-mission/local-agent/README.md` | H1 identifies **Phase 1–2 synthetic history**, warning links latest Mission/Meme status | Historical statements like “no real runtime exists” do not describe later development |
| `crypto-300-profit-mission/watchlists/nft-mint-radar.md` | H1 and paused-runtime note; change old “runs hourly” into **original design, currently paused** | Prevent false active monitor coverage claim |
| `docs/REPOSITORY_STRUCTURE.md` | Clarify canonical exceptions and replace obsolete “Crypto Daily :00 / TGE :14 / $300 Mission :29” testing example | Old schedule examples conflict with current task state and can accidentally restart a paused task |
| `crypto-daily/README.md` | Correct obsolete :10 times to HH:20 at 00/03/06/08/09/10/11/12/16/20 per 2026-10-10 runtime override; note 10/11 recovery-only | README conflicted with `crypto-daily/AUTOMATION_RUNTIME.md`; configuration unchanged |
| `airdrop-tge-monitor/README.md` | Document current HH:00 hourly schedule and legacy :50/:14 supersession | Aligned with `airdrop-tge-monitor/AUTOMATION_RUNTIME.md`; no task mutation |

## Not renamed deliberately: compatibility and evidentiary retention

1. Mission/Meme uppercase `FRANK_*`, `MISSION_MEME_*`, `WALLET_CLUSTER_*`, Local Agent `PHASE_*` and `CURRENT_MAINLINE_CHECKPOINT.md`. These are frozen configurations, review reports, historical phase snapshots and widely linked documents. The existing uppercase naming is **legacy exception**, not an invitation to create new uppercase human research files. No blanket file moves without direct consumer/dependency analysis.
2. `crypto-300-profit-mission/research/BSC_MEME_*.json` and other large source artifacts. Source JSON names/versions/hashes are research evidence; renaming them invalidates historical reproducibility and can break scripts.
3. `portfolio/current.md`, `performance/current.md`, `state/latest.md`, `health/current.md`, `positions/*.md` legacy compatibility aliases, existing `runs` audit and all task automation files are **unchanged paths**. There is no creation of new automation, Gmail sending or Mac deployment.
4. Newly created but unreviewed Draft PR modules (including address-analysis PR #97 and independently progressing Frank/Monster/BSC draft work) are **not** swept by this legacy remediation. They retain their own versioned review gates.

## Still open / not misrepresented as done

- **Comprehensive legacy path renaming not executed.** Uppercase stable files should be changed only after dependency scan, explicit migration plan, preserved compatibility link and actual runtime acceptance when applicable.
- **No live scheduling/health validation performed.** Git documentation now points to real runtime authority; this change itself is not proof a monitor or email runs correctly.
- **Not a historical PnL backfill.** Current portfolio and realized gains/losses retain their existing independent canonical records.
- The 449-wallet research PR is still **DRAFT / UNMERGED**. Batch 001 records BSC 20/20 signed-transaction screening and one token roundtrip; wallet-level month/lifetime profits are unresolved.

## Review / merge gates

This work changes documentation only, preserves every original path and runtime schema, and requires:
- remote readback on all edited files and the root/Mission crosslinks;
- actual PR diff comparison against latest main;
- no runtime/config/positions/holdings mutations beyond document corrections;
- human review before merge to main, separate from PR #97 review.

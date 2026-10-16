# Frank PR85 — Mac Safari localhost synthetic QA authorized

Date: 2026-10-16 Asia/Bangkok. The user explicitly approved temporary **Mac 127.0.0.1 synthetic HTTP + actual Safari acceptance** for the PR85 pinned combined source. This authorization does **not** extend to real Solana RPC, private Sidecar, production SQLite, Gmail, trading, automated agents, merging, deploying, or cleaning old files.

## Fixed source

- Already user-Mac verified root: `/Users/jerson/.local/share/frank-pr85-mac-qa-R1c6kmCU/repo`.
- Content tree: `eea30efa09cb1509d7eee3fde3043ee7155257cf` (independent approved + GitHub CI + user Mac preflight).
- Mac ephemeral HEAD: `c019f365d834dbd4f1d1ca39a8b2d95c63d753d6`; compare **content tree** rather than ephemeral commit metadata.
- Original F02 #73 `5755b8b96080f21635eaa5354588cbb8f6561ab0`, C02 #84 `8d425e4d0e9db9f27abd8ad662e4d59e64b57e53`, F01 #83 `d2eeebc1b49d2bae38e05d7d01f6839e3ba237f4`, QA harness #85 `40febd8275c7710a8697af5a0503569a2bb5cb8d` remain unchanged and Draft.
- Separate QA **script only**, not a modification of the approved product tree: branch `qa/frank-pr85-approved-mac-safari-localhost-20261016`, immutable code SHA `68f1267e8b35db4d8fecc84eafd27ca55aa2ee3a`, path `crypto-300-profit-mission/local-agent/scripts/frank_pr85_synthetic_safari_qa.py`. Fetch it using the branch, verify SHA, then `git show` its source into an out-of-repository QA runtime file. **Never checkout the QA branch over the approved Mac source tree.**
- New script's own [GitHub Actions smoke run #38873977753](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38873977753) **SUCCESS**. In disposable CI runner, rebuilt approved exact Git tree, opened three actual loopback native F01/C02/F02/bridge handlers on random ports, requested F01 (1 eligible / 2 excluded), C02 mint A/B distinct states, F02 32 rows with one nonzero and one zero, and bridge trade permission False, then closed the listeners and confirmed tree/working directory unchanged. No actual Mac Safari has yet been executed.
- Two preceding smoke runs failed: first used incomplete GitHub Actions checkout lacking frozen main tree, second omitted required verified Mint identity status in the synthetic CA fixture. Both were repaired **only in QA launcher/CI**; no approved product source was changed. Do not relabel those failed runs as PASS.

## Authorized browser session

On user Mac, from the existing verified root, check tree and Git clean; fetch SHA-pinned QA script; create an isolated venv and one QA runtime launcher file within the verified QA root; run only that script under `PYTHONPATH` of the approved combined local-agent. The launcher rejects incorrect QA root/tree, guards outbound Python sockets to loopback, writes fresh **synthetic-only** F02 original-wire + isolated SQLite under a new subdirectory of the QA root, and uses genuine HTTP/HTML/JS files from the pinned combined source. It does **not** run `frank_f02_manual_refresh.py --execute`, which would otherwise perform actual RPC.

The script opens real Mac Safari after synthetic native HTTP smoke success and holds all listeners in the foreground. Do not use a pipe into Python stdin because terminal input is needed for orderly shutdown. Run the QA script as a file placed under `qa-runtime/` (outside product Git tree). Session log/receipts are written to `safari-session-*/session.json` inside QA root.

Check on the actual Safari UI:

1. F01: one actionable synthetic BUY with consistent price/impact, an already SELL excluded row and a bad `1e-999` quote excluded. The latter two cannot appear as green actionable. Formal signals/watchlist must not display raw Slot/hash or duplicate official F02 tab.
2. C02: query the two printed **different exact CA values with the same synthetic label**. A is a verified synthetic identity; B remains unconfirmed. Only A may show complete verified authority condition; B must show unknown. Expanded source audit on B must not expose `mint_sha256_64hex` or `slot_502`; retain exact CA and failure source.
3. F02 internal research tab: 32 synthetic mints, exactly one observed nonzero 123, one confirmed zero and other 30 no account. With explicit shortened QA `max_age_seconds=120`, after 120 seconds the page/source must mask all observed quantities to SOURCE_UNAVAILABLE (never zero/SELL). Wait and test background/foreground and search. Raw source Slot/SHA is permitted only on the internal research UI, never on official two business tabs.
4. Take screenshots, preserve timestamps and Console/errors. Press **Enter** in the original terminal to stop only the three started synthetic services, leaving old data and product source untouched. The terminal must print `MAC_PR85_SYNTHETIC_SESSION_ENDED` and confirm all listeners stopped and source tree unchanged. Send output and screenshots back for genuine Safari business acceptance assessment.

Current status: **USER_AUTHORIZED / QA_LAUNCHER_CI_SMOKE_PASS / MAC_SAFARI_PENDING**. GitHub/CI synthetic smoke does not prove Mac UI nor any real current wallet balances. NO_MERGE/NO_DEPLOY/NO_NEW_REAL_RPC/NO_TRADES/NO_GMAIL/NO_PRODUCTION_SQLITE_WRITE/NO_AUTOMATION/NO_FILE_CLEANUP continue.


## Mac zsh 问题修复：变量后面紧跟 refspec 冒号

Mac 首次执行独立 QA 启动前的 Git fetch 时遇到：

```
fatal: couldn't find remote ref refs/heads/qa/frank-pr85-approved-mac-safari-localhost-20261016efs/remotes/origin/qa/frank-pr85-approved-mac-safari-localhost-20261016
```

原因是 zsh 对 `$RUNNER_BRANCH:refs` 的 `:r` **变量修饰符**解释，冒号后的 `r` 被消费，错误地拼出 `...20261016efs/...`。这是此前助手提供的 Mac CLI 字符串 bug，**不是分支不存在、不是 PR85 源码变化，也不是 Safari 失败**。GitHub 已独立读回远端 QA 分支 SHA `68f1267e8b35db4d8fecc84eafd27ca55aa2ee3a`。

**固定写法**：

```zsh
git -C "$REPO" fetch --no-tags origin "refs/heads/${RUNNER_BRANCH}:refs/remotes/origin/${RUNNER_BRANCH}"
```

```zsh
[[ "$(git -C "$REPO" rev-parse "refs/remotes/origin/${RUNNER_BRANCH}")" == "$RUNNER_SHA" ]] || { print -u2 "QA_SCRIPT_SHA_MISMATCH"; exit 1; }
```

`git show` 的 `SHA:path` 必须同样避免裸变量相邻冒号：`"$RUNNER_SHA:$SCRIPT_PATH"` 在 zsh 中应使用 `"${RUNNER_SHA}:${SCRIPT_PATH}"`。推荐在终端统一使用 **`"${RUNNER_SHA}:${SCRIPT_PATH}"`**，避免随后在 script show 命令中再次出现同类错误。

请运行完整更正后的命令，不要改变/删除已经核验的产品 Git checkout；该失败在启动服务之前，Mac Safari 仍 NOT_RUN。生产禁令及批准边界不变。

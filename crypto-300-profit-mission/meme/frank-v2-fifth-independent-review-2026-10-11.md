# Frank V2 PR #31 第五轮独立代码与安全审查（2026-10-11 曼谷）

## 0. 最终判断

| 判断 | 结论 | 条件 |
|---|---|---|
| 代码审核 | **CONDITIONAL_PASS** | 精确 HEAD `2309beab75e890a22cc8483a274dfae1b9cdddcf` 无 Critical/High/影响正确性的 Medium 阻塞。LOW 项需按第 6 节处理。N2/N3 修复已有最小补丁，建议合并前纳入。 |
| Mac 只读验收 | **READY**（隔离执行，需用户授权） | 第 7 节方案全程只读、隔离副本、不改生产。前提：第三方复审不为 BLOCK。 |
| 合并 main | **NOT_READY** | 需要：Mac 只读验收完成；当前 main 上 PR31+32+33 组合 merge-tree 复测；第三方复审；PR 标题与首行状态更新。 |

- 审查 SHA：`2309beab75e890a22cc8483a274dfae1b9cdddcf`（审查开始时远端 `research/frank-wallet-v2-d0-readonly-20261011` 已确认为该值，全程未变化）。
- 基准 SHA：`c65d04a8f14d7efe6e0956fa2914781ec2d96b5f`（第三轮）。
- 当前 main：`14babfeaedcefc63ee4f14d5fcbfa0367fc48631`。合并基底 `30271cb9`；PR 独有 172 个提交，main 独有 324 个提交。
- 交付状态：**NOT_PUSHED**。`git push --dry-run` 报错 `could not read Username`，沙箱无推送凭证。补丁已生成并验证可应用。
- 审查方式：干净 worktree，不依赖前几轮的未提交补丁或缓存。未采信作者或前几轮结论，逐项重跑。

## 1. 测试命令与实际结果

所有命令在 `crypto-300-profit-mission/local-agent` 下执行，Python 3.12.3，依赖按 CI 安装。

| 项目 | 命令 | 退出码 | 通过 | 失败 | 跳过 |
|---|---|---|---|---|---|
| 完整套件（CI 环境） | `FRANK_EXPECT_REAL_GIT_REPLAY=1 python -m pytest -q -rs tests` | 0 | 1175 | 0 | 0 |
| ATA 专项 | `python -m pytest -q tests/test_frank_ata_backfill_v1.py` | 0 | 45 | 0 | 0 |
| 钱包/Dashboard/证据导出子集 | `pytest tests/test_frank_wallet_*_v2.py tests/test_frank_transfer_archive_v2.py tests/test_meme_evidence_sync.py tests/test_mission_control_service.py tests/test_mission_control_dashboard.py tests/test_mission_control_delivery.py` | 0 | 155 | 0 | 0 |
| 真实 Git 归档回放 | `FRANK_EXPECT_REAL_GIT_REPLAY=1 pytest -q -rs tests/research/test_frank_git_real_transfer_replay.py` | 0 | 3 | 0 | 0 |
| JavaScript 语法 | `node --check mission_agent/mission_control/static/app.js` | 0 | — | — | — |
| 合并树（本地临时合并提交 `8b4bba3d`，未推送）完整套件 | 同上 | 0 | 1175 | 0 | 0 |
| 合并树 ATA 专项 | 同上 | 0 | 45 | 0 | 0 |
| 合并树真实回放 | 同上 | 0 | 3 | 0 | 0 |
| main 自身基线（`14babfea`） | 同上 | 0 | 1047 | 0 | — |
| N2/N3 修复后完整套件 | 同上（在补丁 worktree） | 0 | 1177 | 0 | 0 |

说明：
- 合并树测试在合并提交的干净 worktree 中执行，并已核对 `ata_backfill.py` 的文件哈希与 PR 版本一致。
- 首次尝试合并树测试时因提交者身份缺失，`commit-tree` 失败，导致 worktree 检出了错误的提交。该次结果已丢弃，重做后结果如上。
- 本轮没有发现任何跳过项。CI 页面的日志文本无法从沙箱静态抓取（前端渲染），因此“CI 日志中的 1175”只能由本地复跑确认，不能独立确认。

## 2. F1 至 F7 逐项验证

**F1 失败交易签名绑定（PASS）**
- 源码：`validate_transaction` 中签名绑定检查位于 `meta.err` 判断之前。
- 反向验证（基线 `70745a5c` 对比当前 HEAD，通过真实 CLI `run()`）：基线结果为 `BOUNDED_COMPLETED`、退出码 0；当前为 `PARTIAL_TX_UNVERIFIED`、退出码 3。

**F2 HTTP 异常家族（PASS）**
- 源码：两处 RPC 异常捕获为 `HTTPException` 家族，`IncompleteRead` 引用已全部移除。
- 反向验证结果（同 F1 方法）：

| 异常 | 基线 | 当前 |
|---|---|---|
| BadStatusLine | 穿透，无产物 | PARTIAL_RPC_INTERRUPTED，产物写入 |
| LineTooLong | 穿透，无产物 | PARTIAL_RPC_INTERRUPTED，产物写入 |
| IncompleteRead | 穿透，无产物 | PARTIAL_RPC_INTERRUPTED，产物写入 |
| RemoteDisconnected / socket.timeout / SSLEOFError / URLError | 已覆盖 | 已覆盖 |
| EOFError | 穿透 | 穿透（见第 5 节，当前路径不可达） |

- 新增 6 个参数化用例（3 种异常 × 2 个失败点）。在基线源码上 4 个失败、2 个通过（IncompleteRead 基线已修复），当前全部通过。

**F3 J7 摘要签名更正（PASS）**
- 原始文件 `frank-v2-j7-onchain-three-transfer-origin-2026-10-11.json` 与基线哈希一致（未改写，符合不可变证据策略）。
- 更正文件 `frank-v2-ata-index-scope-correction-2026-10-11.json` 中的 88 字符签名存在于原始 RPC 归档 `frank-v2-j7-raw-rpc-responses-sha256-2026-10-11.json`。
- 原始归档：UTF-8 SHA256 复算一致，slot 454705939 一致，`meta.err=null`，主签名一致。
- 余额 `7846838050235 → 12508217470763` 与原始摘要一致。
- 摘要文件中 82 字符签名仍存在，由更正文件控制解释。

**F4 J7 第三方签名转入（PASS）**
- 原始归档中两笔缺失收款的 `accountKeys` 均不含主钱包 `498g…`，该地址只出现在 `tokenBalances.owner` 中。
- 依据 Solana `getSignaturesForAddress` 的账户键匹配语义，主钱包签名索引不会返回此类纯 ATA 转账。这一结论属于协议语义推断，本沙箱无法直连主网复验。
- 回放生成的 payload 中 J7 的 `local_recognized_buys=0`、`local_recognized_sells=1`、`pnl_usd=None`，被动转入未计入 BUY。
- Dashboard 前端已去掉“历史索引缺口”文案，并注明“以上均不直接代表买卖或索引故障”。

**F5 BPxx 窗口分类（PASS）**
- Python 输出（回放生成）：窗口前 63，窗口内 3（失败 1，成功未验证 1，成功已验证 1）。
- 代码强制校验 `outside + inside == gaps`，以及 `failed + success_unverified + verified ≤ inside`。
- 独立重算：66 = 63 + 3，与摘要一致。
- Python → API 字段 → JavaScript 渲染：前端读取的 24 个字段中，除快照相关的 4 个外，其余都存在于 payload 中。快照字段仅在存在手工导入快照时由 `reconcile_watchlist` 生成，缺失时前端显示“链上余额未核实”。`reconcile_watchlist` 使用 `deepcopy`，ATA 窗口字段在合并后保留。
- 回放 payload 的不变量：BUY/SELL 计数相对种子数据变化为 0；纯被动转入行上没有本地 BUY 计数。
- 注意：线上 API 读取的是生产 SQLite，沙箱中无法直接调用；上述为同一管线在归档数据上的等价验证。

**F6 证据导出脱敏（PASS，附 N2/N3 残留）**
- 反向验证：基线中 `file:///Users/…`、`(/Users/…)`、引号路径、`~/Library/…`、`path:/home/…`、Alchemy 路径密钥、邮箱均未被脱敏；当前全部脱敏。
- 已归档证据字符串（44,418 条）的 old/new 对比：修复前后唯一差异是 N2 所述的 GitHub 链接（见第 5 节）。

**F7 BPxx 3knj 原始归档（PASS）**
- 文件 `frank-v2-bpxx-3knj-raw-getTransaction-2026-10-11.json`：UTF-8 字节 5344，SHA256 一致。
- `signatures[0]` 与请求签名一致；`meta.err=null`；slot 452919433。
- 余额 `1001346785078260 → 1001347556621590`，增量 `771543330`，小数位 9，与摘要一致。
- `accountIndex=3` 指向 `5WnoYg…`，即 BPxx 规范 ATA（与本地推导一致）。
- `WALLET` 不在 `accountKeys` 中；blockTime `2026-10-03T11:25:51Z`。
- 来源：已连接的 Alchemy 提供商（`getTransaction` jsonParsed，finalized），不是冻结 V1 使用的公共 Solana RPC。归档中已如实注明。
- 成本与 PnL 均为未知，本报告不推断收益。

## 3. 反向回归与 PDA

- **PDA 独立验证**：使用 `solders.find_program_address`（非被测代码），对证据中 29 个有效 base58 公钥形式的 ATA 字段重算，**29/29 一致**。同一扫描器在当前 HEAD 上得到相同结果。
- **密钥与路径扫描**：PR 新增的 342 行内容中，唯一命中为测试夹具中的合成路径 `alice`，判定 PASS。
- **成本与盈亏**：2026-10-11 证据中所有成本、盈亏字段为 `None` 或未确认。无虚构收益推导。
- **证据不可变性**：`frank-v2-known-ata-gap-summary-2026-10-11.json` 与基线哈希一致，未被覆盖。

## 4. main 兼容性

- `git merge-tree --write-tree origin/main 2309beab` 退出码 0，**无文本冲突**，合并树 `5363a2a6`。
- 在本地临时合并提交 `8b4bba3d9f86edd2d240b2acaae48d943d8b50a8` 上（未推送）完整测试：**1175 passed，0 跳过**，与 PR 单独测试一致。
- main 上新增的 Frank V2 相关文档包括 `frank-v2-ata-backfill-design-evidence-review-2026-10-11.md`，该文件存在于 main 而不在 PR 分支中，合并无路径冲突。
- 局限：本次兼容性只覆盖 PR #31 与当前 main。main 状态文档 §69 记录的四种组合（PR31/32/33）CI 是在父提交 `383dddf5` 上完成的，当前 main 已前进至 `14babfea`。需要在当前 main 上重做 PR31+32+33 组合的 merge-tree 与完整测试，才能覆盖组合风险。

## 5. N2 至 N5 与其他残留项

**N2（LOW，已修复，补丁待合并）**：GitHub 长分支名链接被误判为密钥。
- 证据：`frank-v2-remaining-six-ata-first-page-signatures-2026-10-11.json` 中的 `original_evidence_source` 被替换为 `[URL_REDACTED]`。这是当前唯一的真实证据差异。
- 修复：对 `github.com`、`solscan.io`、`gmgn.ai`、`dexscreener.com`、`api.exchange.coinbase.com` 跳过“长路径段即密钥”规则，但保留关键词和 userinfo 检查。未知域名仍保持原保守规则。
- 修复后：已归档证据的脱敏输出与基线 `70745a5c` 完全一致；新增 2 个回归测试，在修复前失败、修复后通过。

**N3（LOW，已修复，补丁待合并）**：`profile: ok` 误判为本地路径。
- 原因：`file:` 缺少词边界，且未要求斜杠。
- 修复：要求 `file:` 前无字母，且后接 `/`。`profile: ok`、`reconfile: 3`、`file transfer note`、`deposit ~ approx 3` 均保留。

**N4（LOW，设计项，未实施）**：短路径密钥（如 12 字符）与主机名中的密钥仍原样保留。
- 当前证据中未发现此类内容，实际风险低。
- 建议方案（不在本轮实施）：
  1. 导出层采用主机白名单：只导出白名单主机的完整 URL，其他 URL 只保留 scheme 与 host，路径替换为 `[PATH_REDACTED]`。
  2. 对未知主机的子域名标签做长随机串检测（≥24 字符、混合字母数字）。
  3. 白名单须覆盖 Solscan、GitHub、GMGN、Dexscreener、官方 Coinbase API，并有回归测试确认正常链接不被破坏。
- 不应仅凭长度猜测所有密钥，否则会破坏大量正常链接。

**N5（LOW，文档措辞，未修改）**：F3 更正文件中“direct_mainnet_rpc”描述的是已连接的 Alchemy 提供商端点，并非公共主网 RPC。
- 历史证据不得静默改写，应新增一条带日期的更正说明，明确来源名称。
- `RPC_ERROR_-32602_WRONGSIZE` 的直连结果无原始归档，属于作者声称。

**M5（ALT 与 loaded addresses）**：代码层面已验证，真实供应商行为仍未验证。
- 合成场景：A（原始消息，静态键 + ATA 为 loaded writable）、B（jsonParsed 完整列表）、C（jsonParsed 部分列表）均正确验证。
- D（余额行索引超出 provider 键列表）返回 `ATA_NOT_IN_TX_KEYS`，失败关闭。
- E（索引错位）返回 `PARTIAL_PRE_POST_BALANCE_UNVERIFIED`，失败关闭，未伪造验证。
- 结论：不阻塞 Mac 只读验收（只读取既有归档，不做 ALT 相关的新决策）。

**L3（OPEN，阻塞“开启 CA 证据导出”，不阻塞 Mac 只读验收）**：
- 位置：`server.py` 第 581 行，`self.evidence_executor.submit(GitEvidencePublisher(self.evidence_spool).sync)` 返回的 Future 被丢弃。
- 影响：`sync()` 内部对大部分错误做了捕获，但顶层 `mkdir` 等操作不在内部 `try` 中，其异常会留在无人读取的 Future 里，既不记录也不上报。
- 处理：导出默认关闭，本轮不改。开启导出前必须增加 done-callback，记录异常类型名（不记录消息），并写入健康状态。

**L4（OPEN，文档）**：`--since-time` 帮助文本为“0 = bounded recent history only”，与行为不符。
- 实际：`since_time=0` 从不触发时间边界（`when < since_time` 永远为假），扫描仅受 `--pages-per-ata` 与 `--max-transactions` 限制。
- 建议文本：`0 = no time lower bound; scan still limited by --pages-per-ata and --max-transactions and reports PARTIAL when those stop it`。

**EOFError（LOW，当前不可达）**：
- 在 Python 3.12 标准库中检查：`urllib.request`、`http.client`、`socket` 不抛出 `EOFError`；`ssl` 只引用名称 `SSLEOFError`；`EOFError` 只由 `gzip` 抛出。
- `SolanaRPC` 不发送 `Accept-Encoding`，也不手动解压，因此 gzip 路径不会被触发。
- 空响应、HTML 响应、截断 JSON 均被归为 `JSONDecodeError`（`ValueError` 子类），已被捕获。
- 结论：不为 `EOFError` 扩大捕获范围，避免吞掉编程错误。

## 6. 需要的修改清单

| 优先级 | 项目 | 状态 | 处理 |
|---|---|---|---|
| 建议合并前 | N2、N3 | 补丁已验证 | `frank-pr31-r5-n2-n3-sanitizer-fix.patch` |
| 开启导出前必须 | L3 | 未修复 | 增加 done-callback 与健康状态记录 |
| 合并前 | L4 | 未修复 | 更新帮助文本 |
| 合并前 | PR 标题与首行状态 | 未更新 | 标题仍含“1139-test gate”，首行仍为第二轮状态头 |
| 后续 | N4 | 设计 | 白名单导出方案 |
| 后续 | N5 | 文档 | 新增带日期的更正说明 |
| 后续 | M5 | 真实供应商验证 | 不阻塞 Mac 只读验收 |

## 7. Mac 只读验收执行方案

目标：验证 PR31 代码的 Dashboard 与 ATA 证据在真实 Mac 数据副本上的表现，不触碰生产。

**前提与边界**
- 生产 Dashboard 在 `127.0.0.1:8765`，当前运行的是 legacy 版本（参见 main 状态文档 §70）。本方案不替换、不重启生产服务。
- 隔离实例使用 `127.0.0.1:8766`，代码来自 `git archive 2309beab…` 的导出目录。
- 严禁使用 `scripts/mission_meme_v1.py loop` 或 `cycle`：二者会写库并可能发送邮件。只允许 `serve`。
- 控制库不得直接指向生产。`ControlDB.__init__` 会执行 `CREATE TABLE IF NOT EXISTS` 并切换 `journal_mode=WAL`，必须使用复制出来的控制库。

**变量（执行前由你确认实际路径，报告中不记录个人路径）**
```
WORK="$HOME/FrankPR31ReadonlyCheck-$(date +%Y%m%d-%H%M%S)"
PROD_ROOT="<生产 production-root>"
CTRL_ROOT="<生产 control-root>"
SRC_REPO="<本地仓库路径>"
```

**步骤 0：基线记录（只读）**
```
launchctl list | grep -i -E "mission|frank|meme" > "$WORK/launchctl.before.txt"
ls "$HOME/Library/LaunchAgents" > "$WORK/launchagents.before.txt"
pgrep -fl "mission_meme_v1" > "$WORK/pids.before.txt" || true
sqlite3 -readonly "$CTRL_ROOT/mission-control.sqlite" ".tables" > "$WORK/control.tables.txt"
```
记录 outbox 相关表的行数（表名以 `.tables` 输出为准），供步骤 9 比对。
预期：三份文件存在，无错误。

**步骤 1：导出精确 SHA，不改动安装目录**
```
mkdir -p "$WORK/src" && git -C "$SRC_REPO" archive 2309beab75e890a22cc8483a274dfae1b9cdddcf | tar -x -C "$WORK/src"
python3 -m venv "$WORK/venv" && "$WORK/venv/bin/pip" install -q -e "$WORK/src/crypto-300-profit-mission/local-agent"
```
预期：`"$WORK/src/crypto-300-profit-mission/local-agent/mission_agent/mission_control/server.py"` 存在；导出目录中的 `static/app.js` 通过 `node --check`。

**步骤 2：只读快照（SQLite 以 `mode=ro` 打开）**
```
"$WORK/venv/bin/python" - <<'PY'
import sqlite3, os
work=os.environ["WORK"]; prod=os.environ["PROD_ROOT"]; ctrl=os.environ["CTRL_ROOT"]
os.makedirs(f"{work}/prod", exist_ok=True); os.makedirs(f"{work}/ctrl", exist_ok=True)
def snap(src, dst):
    s=sqlite3.connect(f"file:{src}?mode=ro", uri=True); d=sqlite3.connect(dst); s.backup(d); d.close(); s.close()
snap(f"{prod}/forward.sqlite", f"{work}/prod/forward.sqlite")
snap(f"{ctrl}/mission-control.sqlite", f"{work}/ctrl/mission-control.sqlite")
print("SNAPSHOT_OK")
PY
```
预期：输出 `SNAPSHOT_OK`。快照是时点副本，不反映生产实时状态。

**步骤 3：启动隔离 Dashboard（只允许 serve）**
```
cd "$WORK/src/crypto-300-profit-mission/local-agent"
"$WORK/venv/bin/python" scripts/mission_meme_v1.py serve --production-root "$WORK/prod" --control-root "$WORK/ctrl" --host 127.0.0.1 --port 8766 > "$WORK/serve.log" 2>&1 &
echo $! > "$WORK/serve.pid"
sleep 3; curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8766/api/frank-observed-watchlist
```
预期：HTTP 200。隔离副本中没有实时写入器的健康文件，因此实时状态字段显示为“不可用”，这是预期结果，不得解释为数据故障。

**步骤 4：只读 HTTP 采集（仅 GET）**
```
curl -fsS http://127.0.0.1:8766/api/frank-observed-watchlist -o "$WORK/watchlist.isolated.json"
curl -fsS http://127.0.0.1:8766/static/app.js -o "$WORK/app.isolated.js"
```
同时记录生产 legacy 的响应，仅用于对比版本差异，不用于判定数据正确性：
```
curl -fsS http://127.0.0.1:8765/api/frank-observed-watchlist -o "$WORK/watchlist.legacy.json" || echo "LEGACY_HTTP_UNAVAILABLE"
```

**步骤 5：断言（只读 Python 脚本）**
- J7 行：`owner_index_gap_status == "DATED_ATA_VS_OWNER_INDEX_SCOPE"`；`ata_outside_index_window_signatures == 0`；`ata_inside_index_window_signatures == 2`；`ata_verified_extra_passive_receipts == 2`。
- BPxx 行：`ata_outside_index_window_signatures == 63`；`ata_inside_index_window_signatures == 3`；`ata_inwindow_failed_signatures == 1`；`ata_inwindow_success_unverified == 1`；`ata_verified_extra_passive_receipts == 1`。
- 所有行：`pnl_usd is None`；`is_follow_signal is False`。
- 所有 `watch_state == "PASSIVE_RECEIPT_ONLY"` 的行：`local_recognized_buys == 0`。
- 与 SQLite 独立比对：用 `sqlite3 -readonly` 对快照执行 `GROUP BY` 计数，与 API 中的 `local_recognized_buys`、`local_recognized_sells` 逐行一致。
- `app.isolated.js` 中不得包含 `历史索引缺口`，也不得包含 `CONFIRMED_HISTORICAL_GAP`。
- `ata_gap_source_status == "DATED_ATA_INDEX_SCOPE_V2"`。

**失败判定**：任一断言不满足即为 NOT_ACCEPTED，记录差异，不做任何修改。

**步骤 6：浏览器渲染（人工，只读）**
- 在 Mac 浏览器打开 `http://127.0.0.1:8766/`，定位 J7 与 BPxx 行。
- 预期文案：“ATA 与主钱包账户键索引覆盖范围不同：窗口前 N 条，窗口内 M 条…”，以及“另有 ATA 验证被动转入 K 笔（不计为主动买入，成本未知）”。
- 不得出现“历史索引缺口”或“主动买入”字样。
- 截图保存到 `"$WORK"`，不得包含钱包地址以外的个人信息。
- 记录为 `MAC_BROWSER_RENDER=PASS/FAIL`。

**步骤 7：RPC 中断注入（不触碰生产，不推送）**
```
cd "$WORK/src/crypto-300-profit-mission/local-agent"
HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 \
  "$WORK/venv/bin/python" -m scripts.frank_ata_backfill \
  --database "$WORK/prod/forward.sqlite" \
  --mint J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump \
  --output "$WORK/rpc-fault.json" --pages-per-ata 1 ; echo "exit=$?"
```
预期：退出码 3；`rpc-fault.json` 存在；`scan_status=PARTIAL_RPC_INTERRUPTED`；`complete_wallet_history=false`；`trading_signal_emitted=false`。
失败判定：退出码 0；无产物；或 `scan_status` 为完整状态。

**步骤 8：证据导出失败演练（不联网，不推送）**
```
cd "$WORK/src/crypto-300-profit-mission/local-agent"
"$WORK/venv/bin/python" - <<'PY'
from pathlib import Path
from mission_agent.mission_control.evidence_sync import EvidenceSpool, GitEvidencePublisher
spool = EvidenceSpool(Path("<WORK>/drill"))  # 替换为实际 $WORK 绝对路径
spool.frank_scan(poll_count=1, health={"last_poll_at": "2026-10-11T00:00:00Z", "status": "DRILL"})
result = GitEvidencePublisher(spool, gh="/nonexistent/gh-drill").sync()
print("status", result["status"], "errors", len(result["errors"]))
print("pending_frank_retained", result["pending_frank"])
PY
```
预期：`status=SYNC_PARTIAL`；`errors` 不为空；`pending_frank_retained >= 1`，本地待发送文件保留。
失败判定：异常中断进程，或待发送文件被删除。
说明：此演练使用合成数据与不存在的 `gh` 路径，不会访问网络或写入 GitHub。

**步骤 9：生产不变性复核（只读）**
```
launchctl list | grep -i -E "mission|frank|meme" > "$WORK/launchctl.after.txt"
ls "$HOME/Library/LaunchAgents" > "$WORK/launchagents.after.txt"
pgrep -fl "mission_meme_v1" > "$WORK/pids.after.txt" || true
diff "$WORK/launchctl.before.txt" "$WORK/launchctl.after.txt"
diff "$WORK/launchagents.before.txt" "$WORK/launchagents.after.txt"
diff "$WORK/pids.before.txt" "$WORK/pids.after.txt"
```
再用只读方式对生产库计数，与步骤 0 对比 outbox 相关表的行数。
预期：LaunchAgent 列表无变化；生产 PID 无变化（或仅为既有的 loop 常规刷新，需说明）；outbox 计数无由本验收引入的变化。
失败判定：出现新的 LaunchAgent；出现新进程指向隔离目录之外的写入路径；outbox 行数异常增加。

**步骤 10：清理**
```
kill "$(cat "$WORK/serve.pid")" 2>/dev/null || true
sleep 2; lsof -nP -iTCP:8766 -sTCP:LISTEN || echo "PORT_8766_FREE"
rm -rf "$WORK/src" "$WORK/prod" "$WORK/ctrl" "$WORK/drill" "$WORK/venv"
```
保留：JSON 结果、日志、截图（去除个人路径后再提交）。

**验收结论格式**：`MAC_READONLY_ACCEPTANCE = PASS | PARTIAL | FAIL`，并逐项列出 `DASHBOARD_RENDER`、`ATA_SCOPE_LABELS`、`NO_BUY_FROM_PASSIVE`、`RPC_PARTIAL_RETENTION`、`EXPORT_FAILURE_RETENTION`、`PRODUCTION_UNCHANGED`。

**不得执行的动作**：自动重启生产 Mission Loop；发送 Gmail；创建或修改 LaunchAgent；修改生产 SQLite 或控制库；开启自动交易；启用 `MISSION_EVIDENCE_EXPORT_ENABLED`；把隔离结果当作生产部署证据。

## 8. 剩余阻塞条件

1. Mac 只读验收完成，并对第 7 节每一项给出实际输出。
2. 当前 main 上 PR31+32+33 组合的 merge-tree 与完整测试通过。
3. 第三方复审对精确 HEAD（或补丁后的新 HEAD）不为 BLOCK。
4. PR 标题与首行状态更新。
5. 合并前决定 N2、N3 补丁是否纳入。
6. 开启导出前完成 L3。

## 9. 交付物

- 本报告：`crypto-300-profit-mission/meme/frank-v2-fifth-independent-review-2026-10-11.md`
- 复现脚本：`crypto-300-profit-mission/meme/validation/frank-v2-fifth-review-2026-10-11/`
- 代码补丁（N2/N3）：`frank-pr31-r5-n2-n3-sanitizer-fix.patch`
- 报告与脚本补丁：`frank-pr31-r5-report-and-validation.patch`
- 推送状态：**NOT_PUSHED**。未做 commit 或 push，未声称已同步到远端。

# Monster first518 — 独立Codex缺1018份Publisher原字节的有限修复交接（2026-10-19）

## 新方案的边界：绕过大文件传输阻断，不重复调原策略

用户提供Codex对唯一固定SHA `eed4ea67e7868770367fbacffc1e9058ce59b635` 的独立审核为 **BLOCKED**。其中Unicode4与Oct18的`4+511=515`原始issuer ZIP/CHECKSUM已经该Codex独立核验，唯独原33,392,878字节的Artifact `12167818438`一直0字节，导致余下**1018组**原始字节无法复核。该独立审查的历史结论保持BLOCKED，不许把新作者侧CI当成Codex已成功独立重放。

与重新采集、重写交易模型或再做历史数据指标调参相比，本修复将**已经存在且曾完整校验的原issuer字节原样拷贝**到8个较小的新GitHub Action Artifacts。每个小包包含互不重叠的ZIP与原旁路CHECKSUM、`manifest.json`内每份SHA256/发布方原receipt校验原值；原始issuer文件不重新打包ZIP本身、不修改行情行、不重算OHLC。来源仅原GitHub run`39212800265`，全程没有新增Binance市场请求。

### 实际代码 / 实际结果

- 原分支：`research/monster-v4-local-discovery-20261010`，PR #30 Draft；固定核心拆分源码 `crypto-300-profit-mission/local-agent/scripts/monster_v4_first518_issuer_artifact_audit_shards.py`（初始提交 `6ae42dbba9a101a7c55041ff987a35cefc8cc297`）。
- 原始报告布尔值常量替换为**字段相等比较得到的布尔值**：`crypto-300-profit-mission/local-agent/scripts/monster_v4_first518_original_shards_computed_review.py`（初始提交 `43db37041c9aba2e7c4457f209830f66cd5535fd`）；**旧已经归档的报告保留不可改写**，另产V2。
- 唯一一次性成功作者-side GHA：[#39235915099](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39235915099)，触发代码SHA `85f3c05c8daf1dc8595077da53838d6591a5bc90`，20/20步骤SUCCESS（包含全部原CI离线测试、旧原档下载、1018发行方日档SHA/微秒1440行逐份验证、8个新Artifact上传、由8个拆分包+原515对继续完整回放1533份/2,207,520根、518轮D0/D1与同源经济结果、Git归档）。CI之后结果Git归档 `67c10315180e678e8303a3b8829e2f9806bbfe46`。
- [新计算结果V2永久Git证据](evidence/monster_first518_split1018_sha_validated_computed_comparison_v2_20261019.json)，Git Blob `806232981ed759bd7df05328125ffb19f4f828bc`：`original_1533_full_source_verified_from_shards`、`replay_events_identical_to_pre_fix`、`economics_8_8_all_horizons_identical_to_pre_fix`、`operator_snapshot_identical_to_previous_archive`、`all_8_early_watches_and_8_setups`、`all_8_expired_d2_not_captured_no_buy` 均由真实字节/JSON比较**计算出true**，并在false时CI会FAIL，不是 `True` 常量。所有收益及右删失数字仍与旧结论相同，盈利仍没有通过。
- 新增 **独立审核者本机一次性脚本** `crypto-300-profit-mission/local-agent/scripts/monster_v4_first518_independent_audit_from_shards.py`（初始提交 `94f15a318d6a2a02d6da9e05e54b0c5a75ead79e`）。由审核者在自己的隔离checkout中主动执行：逐个从新run下载8个小包，单独下载旧Unicode4和Oct18原始515对，核对8份manifest SHA、1018对真实ZIP/CHECKSUM原SHA，然后本机独立调用原`fifo8_bridge.py`与`postsignal_economics.py`；将实际运行/比较结果写到其指定`--out-dir`。该脚本不连接Binance，绝不发邮件或交易，也不修改Git、现有Frank、Mac定时服务/生产SQLite。

### Codex需要的8个小包（2026-10-19真实Artifact列表）

单一来源run：`39235915099`，名称统一前缀`monster-first518-issuer-original1018-shard-`，分为`00`.. `07`。

| 分片 | Artifact ID | 原issuer交易对日期文件对数 | GitHub压缩包字节 |
|---|---:|---:|---:|
| 00 | `12179201081` | 128 | 4,125,143 |
| 01 | `12179755728` | 127 | 3,934,235 |
| 02 | `12180030471` | 127 | 4,250,334 |
| 03 | `12180010458` | 127 | 3,824,937 |
| 04 | `12179745784` | 128 | 4,495,073 |
| 05 | `12178876469` | 127 | 4,067,628 |
| 06 | `12179271080` | 127 | 4,256,121 |
| 07 | `12180035460` | 127 | 4,173,649 |

另有仅约10.9 KB的比较与回放证据Artifact `12179126146`：`monster-first518-original-shards-computed-source-proof-v2`。**不要将只下载这个小报告当作独立拿到1018个issuer ZIP/CHECKSUM。**

### 审核者实际命令（隔离checkout、无额外依赖或补丁）

在原仓库对应独立checkout中固定核对最新版审核SHA（具体checkout由审核者单独建好）后，可直接运行下列唯一数据恢复+原两脚本回放命令。要求机上`gh auth status`有效，Python3能执行原仓库脚本：

```zsh
python3 -B crypto-300-profit-mission/local-agent/scripts/monster_v4_first518_independent_audit_from_shards.py --out-dir /tmp/monster_first518_split8_codex_raw_review
```

脚本不进行后台工作、没有自动任务；目标目录存在则拒绝覆盖，审核者应选择自己的全新目录。运行后必须由Codex独立读`independent_raw_source_and_replay_actual_result.json`、`independently_replayed_bridge.json`、`independently_replayed_economics.json`，核对原SHA、8+8唯一事件、EXPIRED与D2 NO_BUY、价格代理、4个持有期与右删失。切勿把作者侧第二次跑结果/manifest SHA当作原始字节独立证明。

### 核心业务边界与停止条件

- 成功独立重放后，审核范围仅限**固定数据源+518轮新研究代码/运营只读查询**；不是新Spot完整七日OOS，不是G4可成交利润证明。
- 此次候选仍**8 WATCH / 8 SETUP，全部历史查询EXPIRED，全部D2 NOT_CAPTURED，实际收益短时为负**。原T0 511 Source/原D0有效509与两个Unicode异常照实保留，不能静默删掉两币或声称全市场健康。
- 新Codex若下载8个4MB包依旧失败：立刻按`INDEPENDENT_SOURCE_DOWNLOAD_BLOCKED`记录环境问题；不循环增加新stage或人为改已批准经济数值。新审查者可按官方 Binance Publisher 原URL独立取得对应原字节并验Git receipt SHA（适用时），而不是伪造通过。
- 下一商业开发优先事项仍是D2真实盘口可操作性、509/511全市场健康对用户展示的实际影响，以及七日来源发布后3360轮的预注册负例比较；当前`G0 PARTIAL / G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`保持不变。

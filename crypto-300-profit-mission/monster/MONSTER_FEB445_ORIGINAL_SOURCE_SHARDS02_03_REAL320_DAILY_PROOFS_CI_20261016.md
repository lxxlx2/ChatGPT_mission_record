# Monster 445 原source-complete池新采集 shard02+03：真实320份官方日档案、6/6 CI（2026-10-16）

本轮是在独立Codex批准 `ef30be7bc67588b39efe552b39ab240843253846` V2研究变体工程P1/P2关闭之后，按照[代码前source batch冻结协议](MONSTER_ZEROQUOTE_V2_CODEX_APPROVE_EF30BE7_SOURCE445_BATCH_NEXT_20261016.md)开展的**历史原数据来源采集**，不是新盈利模型、不是全445单库D0/D1回放，也没有新的交易策略。原758个尝试研究标的中2026-02-04 source-complete=445、原来源不完整/缺失=313，名单来自原Stage26归档二次锁定而非当年PIT。

## 真实批次/固定版本

- Workflow源码/测试/对应源reader固定触发SHA：`8c544629c6432aecaf681c391d8ab517827444da`。
- GitHub Actions [#38866315025](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38866315025)：**6/6 Job success**（batch frozen validation、Ubuntu/macOS原source SHA/28分片fail-closed各7 tests/py_compile、两份各16币真实issuer source采集、最终同一次CI重下两份新的内部Artifact解包核SHA并推Git小proof）。
- 原始两份真实Source GitHub Actions Artifact，按workflow `retention-days:60`、不写重型source Git：
  - **shard02** GHA Artifact ID **`12031203151`**，Artifact存储`2,684,234` bytes；真正内层source原始ZIP`2,678,424` bytes，SHA256 `857e45040b83fd55b230e33bcc8060de77d9f6132cfeb1b057d18405668c2fd8`；固定字典序`API3USDT`至`AUCTIONUSDT`共16币×10日**160**份发行者Spot1m ZIP/.CHECKSUM回执；原分钟**每币12960条1m，已核验**。轻量机器[shard02 Git proof](evidence/monster_feb445_shard02.proof.json)，blob`6a273ead4f30da03b06c4a8f164f5805b578c697`。
  - **shard03** GHA Artifact ID **`12031003792`**，Artifact存储`2,807,128` bytes；真正内层source原始ZIP`2,799,736` bytes，SHA256 `7dbc5a607f27f79dffc03f9e2a3f3f9db4c62ef4ad65dc2029a5095c3e8403b1`；`AUDIOUSDT`至`BATUSDT`共16币×10日**160**份发行者Spot1m ZIP/.CHECKSUM回执；每币12960条1m。轻量机器[shard03 Git proof](evidence/monster_feb445_shard03.proof.json)，blob`9a0c00da2f2542839a8060a2ce328ec4565d61e5`。

源SHA+内部manifest SHA均在这两份proof中，archiver通过 `read_archive` 比较原bin ZIP和全部每币JSON sha、行数、成员freeze identity以及十天发行者SHA与proof逐条一致，来源身份 `source_origin_verified_at_collection=True`、`trigger_commit_sha`精确一致。此前已有`shard00` Artifact`12021352471`、`shard01` Artifact`12021445690`，均16币×10个发行者日行情。由此现在真正来源封存数量：

| 指标 | 严格已确认 |
|---|---:|
| 已真实存档的分片 | **4/28**：00、01、02、03 |
| 原完整来源池已存档的不同币 | **64/445** |
| 原完整来源池仍缺少源ZIP档案的币 | **381/445** |
| 尚未执行的原固定分片 | **24份**：04–27 |
| 已采的逐日Spot1m发行者ZIP/.CHECKSUM回执 | **640份**（每币10份） |
| 原当年来源不完整/缺失不填零 | **313币** |
| 是否完成445全池一库D0/D1 | **NO** |
| 已有前32币真实共享D0+研究V2 D1 | **YES**：WATCH29、EVALUATED27、SOURCE_UNSUPPORTED2、LATE0，最大WATCH同时7仍未碰限额8 |

## 门禁和接下来的准确执行

Source shards02/03为后来真实额外采集的原分钟历史价格，不作任何stage28 WATCH注入、不人工筛选“赢家”、不声称历史当时预提交所有原单日SHA。发行者的下载ZIP+同host CHECKSUM验证的只是同一来源自洽，不能冒充独立第三方签名；Git proof和CI成功不是原生产策略或新pipeline的独立AI代码批准。

以后用 **同一个GitHub手动Workflow** `.github/workflows/monster-v4-445-manual-two-original-source-shards.yml`，下一批按冻结名单**04/05**，后续**06/07……26/27**，一次且只能两份，`max-parallel=1`、每片`workers=2`。Workflow首次push的`02/03`已经跑完，以后严禁通过反复编辑workflow来隐式连锁自动下载或接入Stage99，必须显示人工发起 `workflow_dispatch`，且每批全部真实source严格SHA校验和归档后才累计。由于Actions Artifact 60天会过期，完整445共池组装之前需确认所有28原Source ZIP Artifact仍存在；过期则按冻结原source实际重采或保留`SOURCE_UNAVAILABLE`，**不能将只剩SHA的小proof自封完整origin source**。

需要另一个AI对新batch workflow固定源码SHA`8c5446...`做独立源码/来源证据二审：[精准审查协议](MONSTER_445_ORIGINAL_SOURCE_TWO_SHARD_CI_INDEPENDENT_REVIEW_PINNED_8C54462_20261016.md)。如没有报告就不能写APPROVE。后续全部445正式共享D0→D1还需重新设计如何明确隔离旧原production D1 zeroquote的fatal与V2研究变体，不能因单币 source-complete 就推断盈利可执行性。原Stage28 98同时WATCH/91 LATE来自逐币D0 WATCH注入，尚不能等同真实445共有D0；未来在一份共同SQLite每轮8评预算里才可检验。

**所有业务限制不变**：`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`；`G0 PARTIAL`、`G1 NOT_SCORABLE`、`G2/G3 NOT_PASSED`、`G4 UNKNOWN`、`G5_RELEASE NOT_PASSED`、`G6 NO_GO`。PR #30仍Draft/Open；不改变Frank/Stage99/Mac生产SQLite。

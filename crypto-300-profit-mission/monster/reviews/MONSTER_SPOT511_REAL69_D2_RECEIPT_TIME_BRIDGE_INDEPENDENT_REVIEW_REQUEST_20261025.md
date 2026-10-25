# Monster 原始69条D1→D2时点报价证据桥：其他AI独立审核请求（2026-10-25）

请直接在其他AI（Claude网页或Codex）执行独立只读复审，**审核固定源码SHA `342fc476a49c25640e6c8c47302338b56c69316a`，不能用移动PR HEAD或文档SHA代替**；仓库`lxxlx2/ChatGPT_mission_record`，Draft PR #30，分支`research/monster-v4-local-discovery-20261010`。

## 目标与批准边界

本轮只研究预注册新D1得到的69个冻结WATCH和47个研究SETUP，在旧 `2026-10-17T22:04:46.929464Z` 已取得原始Binance Spot T0盘口回执背景下，能否证明这些信号时的**盘口来源可见性**。不估值、不默认买卖金额、不获取私有账户/交易、不启动自动采集与通知，不从历史Minute HIGH推算盈利。

代码：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_spot511_d2_signal_receipt_coverage.py`
- `crypto-300-profit-mission/local-agent/tests/test_monster_v4_spot511_d2_signal_receipt_coverage.py`
- `.github/workflows/monster-spot511-real69-d2-receipt-time-bridge-once.yml`
只读旧源：
- `local-agent/scripts/monster_v4_stage163_spot_t0_quote_friction.py`，Stage163原始ZIP `monster/evidence/monster_stage163_spot_original_http_t0_actual/source_raw_http.zip` 和原回执 `source_receipts.json`，原source_zip_SHA256 `b47e206345c0a04b16b37c38795d726553ef83ca679f443f9fba89805483216b`。
- 新研究账本[原GitHub Actions #40191914954](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40191914954) Artifact `12597793739`，`real69.json`固定SHA256 `2f5e27d37c2b7ae333079b08155e392d78413212571bc681d149b4e91a1cf84c`；属于已曝光历史，原G0/PIT及成功窗口分类仍有不足，不能拿来证明真实已发送的告警。

## 已有实际验收，不等于你的独立Review

[GitHub Actions #40193435581](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40193435581) `SUCCESS`，Python3.11，新增9项+原Stage163定向12项，合计 **21 PASS**；实际下载旧Artifact并校验固定SHA、官方ZIP与SHA/回执；原69条WATCH和47条研究SETUP逐事件做D2旧源对照。新证据Artifact **`12599195855`**，`real69-d2-time-receipt-coverage.json`原字节SHA256 `9bd81c0303d082885c79c8d282c53eb879e4eea712dbe1840be03001d708c077`。

**实测**：原T0回执早于所有69条WATCH和47条SETUP，69/69的WATCH和47/47的D1盘口皆超过独立工程诊断`max-age=180000ms`，对应 `ARCHIVED_QUOTE_STALE_AT_EVENT_CLOCK`。WATCH到该旧回执间隔最小`32653071ms`，最大`588673071ms`，既不是同步实盘口，也不证明这69只币不能交易。`G4_signal_time_bidask_proven=0`、`G4=UNKNOWN`、`G6=NO_GO`。Stage163是历史收到的旧**L1** bookTicker，不是订单深度/当时合约成交价格或以后的退出Bid。输入研究金额仍`UNSPECIFIED`。

独立可重复命令（若具备固定repo和artifact文件）：

```sh
export PYTHONPATH=crypto-300-profit-mission/local-agent/scripts
python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_spot511_d2_signal_receipt_coverage.py -v
python3 -B -m unittest discover -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_stage163_spot_t0_quote_friction.py -v
python3 -B crypto-300-profit-mission/local-agent/scripts/monster_v4_spot511_d2_signal_receipt_coverage.py --real69-v2-json real69.json --output /tmp/monster-d2-offline-result.json --max-receipt-age-ms 180000
```

## 必须独立思考及攻击的点

1. 检查旧raw ZIP、回执起止时间与原始字节SHA验证是否真实由Stage163执行（只信原始文件、不信生成的JSON），引用真实Binance Spot bookTicker接口不带每交易对的精确交易所事件时间，避免当作信号时的同步盘口。
2. 核对首次WATCH、所有69条的时间/完整性、47个研究D1升级同原回放一致，是否有状态丢失/重复，是否错误将旧T0元数据当成10月18–24的动态Listing PIT。
3. 在反例里将报价回执放在WATCH之后、之前一毫秒、正好180000ms与180001ms过期；严格核对时间界限且无未来信息。检查`source_quote_age`是否把已曝光历史推导的WATCH时间伪装成真实当时已收到的提醒。
4. 检查符号缺失、坏签名、篡改Artifact、非法时钟、未定义用户订单金额、缺少未来卖出Bid仍却误判G4 PASS的路径。
5. 注意源级局限：这个工具**不是**新Spot/USD-M D0/D1模型，不得因为21项测试PASS升级G0、G1/G2/G3/G4门槛。虽其本地开发阈值180000ms有来源诊断价值，属于工程年龄过滤器，不允许替换ADR005冻结模型阈值。
6. 检查无schedule、不可下单或发信、没有改变Frank、真实SQLite及生产代码。请列出其无法解决的下一步高价值输入：在未来实际信号时收集的来源一致的买入盘口、可能的委托手续费、后续实际退出盘口/深度和订单金额（用户自主决定），至少30个独立完整双侧案例才可初步重审G4。

输出固定结构：**`APPROVE | REQUEST_CHANGES | BLOCKED`**、具体审查模型及环境、准确固定SHA、实际执行命令与原始数据证据、P0/P1/P2文件行号与复现、每G0–G6逐一判断、是否独立核验全部实际ZIP还是只看来源选样、批准范围及`NO_MERGE/NO_DEPLOY/NO_AUTOMATIONS/NO_GMAIL/NO_TRADES/NO_NEW_RPC`继续有效。**只有真正收到独立审核意见，才可标注本新D2桥接G5通过。**

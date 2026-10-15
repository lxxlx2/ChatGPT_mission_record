# Monster 共享Spot D0→D1：Claude独立 REQUEST_CHANGES 修复及真实证据

2026-10-16 Asia/Bangkok。用户粘贴的另一个AI Claude（准确底层型号`UNVERIFIED`）固定审核SHA `0ffe44ece8644443757b5f6ac0cd19e0f5d1999e`，`REQUEST_CHANGES`：新增3 P1（缺失源与758分母、可自证官方FULL、758名单原预注册身份缺口）及多个P2（OHLC、源失败变重试、census负向、历史逐日SHA等）。Claude对归档ZIP需GitHub认证、官方ZIP网络在其环境不可达，独立ZIP级验证为`UNVERIFIED`；用户转述的Claude测试13/13成功但这不是当前版本批准。本轮修复**尚未取得其他AI独立APPROVE**。

冻结顺序：先提交[本轮缺源与身份事前修复协议](MONSTER_SHARED_SPOT_CLAUDE_P1_SOURCE_IDENTITY_CENSOR_FREEZE_20261016.md)，commit `64080ec23a7f8154f264df6c44c174d36772eb4e`，再从原已Git双SHA核实的Stage26 36个Artifact派生**2026-10-16二次固定**的完整758字符串及六日期可用币名/缺源总量，Git固定文件[原758 roster和六日期全部source status](evidence/monster_shared_spot_stage26_original758_secondary_freeze_20261016.json)，blob `8467bfc0db7cb888f805f30eaae301a812fbb20d`，名字sha256 `cea49caae4245dad910cc096bdaea953387bdfea64667a49916756d12297074a`。**不能回填当年不存在的逐币预注册身份**。原旧文件只有`current 504`+`archive-only 254`=758、另记`2 unsupported unicode`，无法凭这个计数证明原Unicode身份和映射，额外两个不在SHA锁定758 ASCII尝试名单内；不是把人数算成760或自行代入代理地址。

## 固定源码版本和完整真实GitHub CI

修复后**唯一待另一AI审核的代码+测试+工作流SHA = `6e2897c4602ce554b57634fe05d25e7244068316`**。真实[GitHub Actions #38812571412](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38812571412)已由GitHub读取`completed/success`，触发固定SHA精准一致；**5/5 Job SUCCESS**，Ubuntu24.04/macOS各`20/20 tests OK`+py_compile。源Job重新下载原Stage26 **36个Artifact ZIP和其内部JSON**逐份与先前Git proof的两个SHA256匹配；另一源Job经Stage26原官方`data.binance.vision` daily Spot1m ZIP+CHECKSUM读取 BTC/ETH 各十日历史，按单一原SQLite、3360轮原生产D0/D1真实运行（当日原两大币零WATCH），同时核对已经Git封存的20份官方daily SHA并输出20个独立收据。本次CI最后源码/测试/工作流与触发提交Git blob逐一校验未漂移，实际`MONSTER_SHARED_SPOT_REAL_ORIGINAL_SOURCE_PROOFS_PINNED_GIT_PASS`后才提交新机器结果到原PR。没有新市场定时采集/真实Mac探针、邮件或交易。

机器Git结果：[来源人口摘要](evidence/monster_shared_spot_stage26_36_source_census.json) blob `25d932d5e1ee72c4e6956f6fc3dfacf0df2dc43e`；[BTC/ETH官方20天逐日SHA+真实共享D0/D1](evidence/monster_shared_spot_real_BTC_ETH_20260204.json) blob `9f74c5a1144806c916cb6803b3eb00aad05e5145`，新引擎SHA256 `d1fff2ee97b7375528e9de3e0d02ab3f4432838e3dc9f188c233e5b6063b50f3`，两个机器文件皆记固定触发SHA `6e2897c...`。原20个daily HASH附新[BTC/ETH官方逐日原ZIP SHA二次预定锚点](evidence/monster_shared_spot_BTC_ETH_20_publisher_daily_sha_secondary_pin_20261016.json) Git blob `08fdc8cf8054ad93089a93bcd1e3e6d26877367f`；其**首次下载之后才二次冻结**，不能称原始pre-download commit证明，但新的重放即在源码中要求相符。

## 3个P1各自怎么关，不能扩大范围

**P1-1** 原始758分母每日来源不齐：完整216h历史来源的币种依次`433/440/445/438/478/485`，合计2719/4548，缺1829。新的`original_758_coverage(day,roster)`从Git blob锁住的名单读取并每日期列**758条原身份记录**，每个唯一币分类为`OFFICIAL_VERIFIED_AND_REPLAYED_SUBSET`（只能经受控真实官方读取者）、`SOURCE_COMPLETE_AT_STAGE26_NOT_REPLAYED`、`CENSORED_SOURCE_MISSING_OR_INCOMPLETE_AT_STAGE26`。直接缓存输入只能标`PRELOADED_CACHE_REPLAYED_ORIGIN_UNATTESTED`，不能骗成官方。2026-02官方二币实跑：758分母=2真实官方来源已回放+443原来源完整但未回放+313缺源/不完整；**不是758次完整模型回放**。不能为313个缺失币编造历史价格或把它们当作WATCH阴性。现阶段严格禁用`FULL_758_OFFICIAL_VERIFIED`，触发`SHARED_SPOT_FULL_758_NOT_VERIFIED_SOURCE_CENSORED`，即使传入758符号和自证的frozen_verified_roster也拒绝。真实高压445 SOURCE_COMPLETE 子集尚未跑。

**P1-2** 通用`run_shared`无权认证传入SQLite cache和用户编造的`verified_published_sha256`布尔标志：永远返回`source_origin_verified=false`，标签明确`UNATTESTED_SUBSET_CACHE`和`PRELOADED...`，真官方成功只允许经`run_official_subset`路径调用之前已SHA锁定的`old.read_complete_216h`→官方 ZIP+CHECKSUM parser之后设`source_origin_verified=true`、`OFFICIAL_VERIFIED_SUBSET_ONLY`，且标记`STAGE26_PUBLISHER_ZIP_SHA256_CHECKSUM_VERIFIED_AT_RUN_TIME`。这证明同一官方host提供的ZIP与checksum自洽，不是发行者另行加密签名、也不是所有未来币种SHA事前在Git锁定。BTC/ETH新重复下载已与原Git留存的20个Sha精确同日同币匹配；其他币尚无二次逐日SHA锚点则标`NO_PRIOR_PER_DAY_SHA_PIN_UNVERIFIED_HISTORICAL_SOURCE`。

**P1-3** 二次冻结实际SHA来源名单及当日状态，源码硬锁Git file blob和758 roster SHA，严禁用户仅把任意758个字符串传给`frozen_verified_roster`就“通过”官方FULL。**历史2026-10-11事前完整逐币名单身份根本没保存**，本轮不会虚称它已恢复；后续必须保持`point_in_time_listing=UNVERIFIED`，Unicode2历史映射UNKNOWN。

## P2 及更完整的拒绝测试

- 单条官方1m行严格`low <= open, close <= high`并全部OHLC正数、quote非负；源温度错、源时间漂移、缺tick必须拒绝。
- 如果共享D1 fetch时缓存的8根已闭合5m不连续或没有严格按时闭合，抛`RuntimeError SHARED_SPOT_ORIGINAL_D1_SOURCE_MISSING_OR_UNCLOSED`，不被旧生产`process_queue`只用于真实请求错误的`(ValueError/...)→D1 deferred`处理器吃掉；不更改原冻结生产代码。
- Census多加独立合成负测：36个原分片少一件/日期跨日roster篡改/官方完整数篡改/原ZIP bytes SHA不符合原proof。另对用户缓存虚构官方标志、全758自行自证、冻结758源文件Git漂移、官方日SHA伪造及日期错位、OHLC坏数据、历史5m闭合数据破坏进行了独立负测，两个OS 20项通过。
- Stage152已单独于`71a041405352c9e2210d93dff9c2685149809e52`获Codex上轮限定`APPROVE`，不与Claude未完成的旧SHA审查混同；本轮不重写Stage152摘要，不扩大其批准范围。
- Github CI会将证据提交令HEAD前移，**但固定源码SHA审查只看确切源+两脚本+workflow**；其他AI须比较后续仅machine JSON/docs，而不得静默审核当前PR HEAD。

## 研发主线真实下一门槛

本阶段 **2026-02真实全445币共享D0+D1负载尚未执行**，Stage26的历史98突发来自逐币隔离D0，仍不是本引擎的98币同钟因果证据。2025-11普通433也尚未新共用D0回放。不能把本轮官方二币零信号当正例、原真实758完整或利润策略G4/G6通过。下一步只在Stage26 SHA锁定原455? 实际445 完整子集和真实官方1m SHA获得后进行335...真实共享时钟验证，不能凭历史WATCH偷偷注入。

门禁 `G0 PARTIAL/G1 NOT_SCORABLE/G2/G3 NOT_PASSED/G4 UNKNOWN/G5_RELEASE NOT_PASSED/G6 NO_GO`；`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`、Frank不动、Stage99不恢复、没有新定时任务。本轮待另一AI独立`APPROVE | REQUEST_CHANGES | BLOCKED`，不能作者自评APPROVE。

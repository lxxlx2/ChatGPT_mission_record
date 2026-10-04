# Frank V2 joint model interaction and OOS validation — 2026-10-04

V2_CANDIDATE = NEED_MORE_DATA。开发集 J3=22 ACC / 15 MULT：complex新增目标仍有ACC/MULT，rolling恢复STONK原MULT及另外4个MULT。OOS只有114笔可验证durable记录、0个complex reconstruction候选，无法估计该修复precision；rolling仅恢复1个已知7Vert episode。信号更多不等于模型更好，本轮不设计或实施production V2。

## Freeze / scope

Rules frozen at 2026-10-04T10:42:29.043175+00:00，freeze SHA256 `25ed4cad225316e16933ba45a67aeb6d1d2572bc88ce8d7b4fd2a0aefb489ff9`；before OOS snapshot。

只复用前两轮research模块，原complex_candidate/research_market_record/reconstruct及HistoricalHFTEngine/rolling_fail不变。原production policy、amount、T0、ACC、persistence、inventory、distribution、freshness、rapid-roundtrip veto、原clock schedule均不改。R0/R5/R15保持0/300/900秒，inclusive 60秒窗口>=3笔用户ACTIVE才成立；signature最多一笔，不按CPI计数。恢复仅在原ACTIVE/hourly evaluation时观察，不插入额外恢复tick。

开发集J1/J3复用前轮M3的9笔SOL SELL金额代理以保证精确body parity；OOS current SOL quote ACTIVE=0，所以OOS无额外SOL金额路径差异。无新SOL阈值或汇率规则。所有quote legs保留，历史价格receipt沿用冻结缓存。

没有新增precision/noise gate。用户给的是定性V2条件，没有冻结数值接受标准；不在看到OOS结果后发明精度百分比、sell ratio或turnover阈值。

## Development historical matrix

2026-09-03T16:32:58+00:00 → 2026-09-30T09:39:20+00:00，6874 signatures、raw missing=0、hash verified=6874。available verified subset，不是wallet lifetime。CURRENT/complex/rolling旧结果均进行完整signal identity/body parity，全部PASS。

| Model | ACTIVE | ACC | MULT | Episodes | HFT ever episodes |
|---|---:|---:|---:|---:|---:|
| J0 | 634 | 21 | 10 | 180 | 31 |
| J1 | 653 | 22 | 10 | 188 | 35 |
| J2 | 634 | 21 | 14 | 180 | 31 |
| J3 | 653 | 22 | 15 | 188 | 35 |
| J3-R5 | 653 | 22 | 15 | 188 | 35 |
| J3-R15 | 653 | 22 | 15 | 188 | 35 |

J3=R0。R5/R15与R0的signal身份、trigger时间及signature均相同；不是仅总数相同。HFT ever包含原rapid-roundtrip veto，与60秒burst单独概念区分。

| Identity comparison | New | Lost | Trigger change |
|---|---:|---:|---:|
| J1_vs_J0 | 2 | 1 | 1 |
| J2_vs_J0 | 4 | 0 | 0 |
| J3_vs_J0 | 6 | 0 | 1 |
| J3_vs_J1 | 5 | 0 | 0 |
| J3_vs_J2 | 2 | 0 | 1 |

new/lost按episode+signal type计算，machine evidence保留全部signal_id、mint、episode、trigger/signature及before/after。J1新增2个身份（1ACC+1MULT），消失1MULT；J3 vs J1新增5MULT，其中1个恢复原STONK、4个在J0从未出现。J3 vs J2新增2个身份（complex目标ACC+MULT）。complex+rolling-only身份=0；本样本没有只能靠二者联合才出现、且在J1与J2均不存在的新信号。

## STONK / PAID / new target

### STONK

Mint `6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx`；observed episodes=2。

| Model | ACC | MULT |
|---|---:|---:|
| J0 | 1 | 1 |
| J1 | 1 | 0 |
| J2 | 1 | 1 |
| J3 | 1 | 1 |

### PAID

Mint `98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump`；observed episodes=5。

| Model | ACC | MULT |
|---|---:|---:|
| J0 | 3 | 1 |
| J1 | 3 | 1 |
| J2 | 3 | 3 |
| J3 | 3 | 3 |

### 4K1m7g

Mint `4K1m7gAMDKzrxQn68yuZAd767w57Fw7Ykw69dG3umeta`；observed episodes=1。

| Model | ACC | MULT |
|---|---:|---:|
| J0 | 0 | 0 |
| J1 | 1 | 1 |
| J2 | 0 | 0 |
| J3 | 1 | 1 |

STONK：J1补齐4笔早期BUY引发sticky HFT丢失MULT，J3恢复。J3 MULT epoch=1788668315（2026-09-06T04:18:35+00:00），trigger signature `4sTTVMgVS68TgiAXR2JFNCNxDSGyrXUcEnW1u9Eohk3c6tUtudBoNNcY8v9YdKNhnbKTh8A7PjJLfx1V7MYN9h36`；相对J0 delay=0秒、signature相同。ACC从1788661771提前至1788661718，提前53秒，触发signature改变但signal identity保持。

PAID：5个observed episodes；J0/J1=3ACC/1MULT，J2/J3=3ACC/3MULT，两次额外MULT保持上一轮结果。complex没有进一步改变它。

4K1m7g…meta：J0/J2无信号，J1/J3均1ACC+1MULT。两笔BUY分别15000/10000 USDC、间隔8秒；只有2笔所以没有60秒>=3的HFT burst。ACC epoch1790097169、hourly Path A MULT epoch1790101740，J1/J3时间及signature完全一致。single-large-buy仍NOT_ACCUMULATION。没有因结果或已知利润改变模型。

## Development rolling recovery follow-up

以下仅为signal生成后的事后行为诊断，不参与gate。原rapid-roundtrip veto保持。混合买卖不自动等于套利/高turnover，没有冻结经济turnover定义，不能造一个新接受门槛。

| Mint | Recovered MULT at | Later BUY | Later SELL | First SELL delay seconds | Sell / trigger inventory | Final state |
|---|---:|---:|---:|---:|---|---|
| 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump | 1790386140 | 2 | 5 | 64761 | 1.137472040043014272428482786 | INVENTORY_UNDETERMINED |
| CbcyNo7m1amFWqEQm2m4PLv1UNvpcL3C1Ujm6AkzpKoU | 1790454994 | 1 | 3 | 9462 | 1.047013779833417777566529559 | INVENTORY_UNDETERMINED |
| UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids | 1790221637 | 0 | 41 | 29105 | 1 | CLOSED |
| 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump | 1790457075 | 1 | 4 | 7513 | 1.064099537139635313923503877 | INVENTORY_UNDETERMINED |
| 6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx | 1788668315 | 8 | 9 | 234527 | 1.432305426386230540309583856 | CLOSED |

开发集这5个恢复MULT均有后续SELL，最终2个CLOSED、3个INVENTORY_UNDETERMINED；最早后续SELL在触发7513秒后。不能从mixed BUY/SELL直接推断套利或立即高turnover，也不能据此宣称rolling无噪声。

## OOS data / provenance

实际raw窗口：2026-10-02T21:59:40+00:00 → 2026-10-04T10:41:15+00:00；114 unique signatures，raw missing=0、raw hash verified=114。本轮backfilled=0。

缺口：2026-09-30T09:39:20+00:00之后至2026-10-02T21:59:40+00:00之前没有本轮可验证连续数据；不能声称完整Sep30–Oct4覆盖。原snapshot finalized model clock=2026-10-04T10:42:03+00:00，用于原hourly tick；raw最晚交易时间与evaluation horizon分别记录。

来源：78笔现代ORIGINALLY_DURABLE_FORWARD；1笔额外旧ORIGINALLY_DURABLE_LEGACY_FORWARD；35笔INHERITED_DURABLE_BOOTSTRAP（也能在旧source中找到，duplicate provenance保留）。严格分组durable-forward=79、bootstrap=35；全部在本轮前已存在，未调用RPC补raw。旧source capture可包含启动catch-up，不能用durable这个词证明其近实时原生采集。现代detection时间与旧observations时间均在manifest保留。

只读mode=ro source连接、SQLite backup到private隔离目录；不读取或复用live model state作为研究状态，不修改source DB、cursor/outbox/health。raw hash、signature、slot、blockTime逐笔重新核验，再调用production classifier。原scanner配置为finalized；raw JSON本身无独立commitment receipt，因此finality依据是原始采集政策及hash绑定，不声称本轮独立RPC链核验。

OOS是TEMPORAL_OOS_NOT_UNTOUCHED_HOLDOUT：7Vert之前已在这个工作区审计；本轮冻结后不根据10月结果调整criteria/HFT/recovery。不能将再次看到7Vert包装为盲测成功。

同时跑OOS-only cold start与development-prefix causal seeded replay；两者本次signal identities、trigger、count一致。历史缺口仍存在，prefix不是完整仓位恢复；旧prehistory-only且没有OOS事件/evaluation的episode不充作新样本。

| OOS model | ACTIVE | ACC | MULT | Episodes | HFT ever episodes |
|---|---:|---:|---:|---:|---:|
| J0 | 30 | 1 | 0 | 13 | 1 |
| J1 | 30 | 1 | 0 | 13 | 1 |
| J2 | 30 | 1 | 1 | 13 | 1 |
| J3 | 30 | 1 | 1 | 13 | 1 |
| J3-R5 | 30 | 1 | 1 | 13 | 1 |
| J3-R15 | 30 | 1 | 1 | 13 | 1 |

OOS production classifications：ACTIVE30、UNKNOWN24、ATA16、PASSIVE39、FAILED5。OOS 24 UNKNOWN没有任何满足冻结 signed-opposing-flow候选的case；它们没有计作coverage miss。

## OOS complex precision / HFT

proposed reconstruction=0、confirmed=0、false positive=0、unresolved proposed=0；confirmed/proposed=null（0/0不可计算），不是100%。没有complex候选不是precision已通过，也不能排除未覆盖程序下的潜在漏记。

OOS sticky HFT episode=1；rolling恢复MULT episode=1；R0/R5/R15同一signal identity与trigger。high-turnover recovered=UNDETERMINED_NO_FROZEN_ECONOMIC_TURNOVER_METRIC，精确后续BUY/SELL及inventory比率留存；没有发明sell ratio gate。

恢复mint `7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump`，episode `cc83c4825134e955929eaa6522cfa7a6c499952d1a90fd262df51fe7ace67753`，MULT在 2026-10-03T17:29:00+00:00，trigger signature `2NLzWYrLCGL3XA1TR71HxUEtAWwAb37goWVfoiQ8Mu3RyqcweYyzbghSk23TeVGBSx7pE9o92EnYErHE2cvePfVy`。

Trigger kind=HOURLY_29；buy_count=5、sell_count=0、quote spent={'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': '71079.393003'}、inventory=10096062.259242。各gate：`{"accumulation_amount": "FAIL", "accumulation_buy_count": "FAIL", "cumulative_amount": "PASS", "distribution": "PASS", "freshness": "PASS", "hft": "PASS", "inventory": "PASS", "persistence": "PASS", "prior_accumulation": "PASS", "t0": "PASS"}`。

随后已记录BUY=1、SELL=0；final state=OPEN；CLOSED=false；inventory undetermined=False；rapid-roundtrip=False。dataset observed through=2026-10-04T10:42:03+00:00；last token trade=2026-10-03T18:18:47+00:00。

7Vert后续仅记录一笔25000 USDC BUY，没有记录立即大量SELL或CLOSED；这是右截尾、非连续覆盖样本，不能证明其不存在未来高turnover，更不能判断盈利。PNL_UNAVAILABLE。

## V2 decision

V2_CANDIDATE=NEED_MORE_DATA。开发集确认改善真实行为coverage并恢复原sticky veto的信号，但OOS complex precision无分母、窗口缺口、只有一个已知rolling恢复case且右截尾，无法充分判断false-positive/noise。COMBINED_MODEL_NOISE_RISK=NEED_MORE_DATA。开发集mixed BUY/SELL诊断保留，不用更多信号或后来的PnL替代验证。

缺失项：连续Sep30–Oct4 verified raw/采集provenance；新的未看过complex reconstruction样本；足够rolling recovered episodes的后续完整交易与可审计经济turnover/PnL；独立事前定义的V2 precision/noise接受标准。本轮不增加gate，也不挑R0/R5/R15最佳版本。V2_CANDIDATE不是YES，未设计或实现正式production V2。

## Production boundary / tests / reproduction

11个protected production文件SHA前后完全一致，完整SHA列表见machine evidence。包括classifier/evaluator/engine/scanner/policy/store/parser/rpc/V1 config/registry/service。

| Health | Before | After |
|---|---|---|
| pid | 85524 | 85524 |
| restart_count | 3 | 3 |
| code_commit | 46c989c3ef35d63fc02808c519f73aa3e6ea1513 | 46c989c3ef35d63fc02808c519f73aa3e6ea1513 |
| last_successful_poll | 2026-10-04T10:42:15.232009+00:00 | 2026-10-04T10:49:46.121783+00:00 |
| source_drift | False | False |
| raw_pending | 0 | 0 |
| model_unprocessed | 0 | 0 |
| loaded_source_sha256 | 599f2f05f197725a25fd85a82501504a772f253866c0556183bbfd82da00a0ce | 599f2f05f197725a25fd85a82501504a772f253866c0556183bbfd82da00a0ce |

PRODUCTION_FILES_CHANGED=NO；LIVE_SERVICE_RESTARTED=NO；LIVE_SIGNAL_SENT=NO；Gmail/notification/automation/main merge/live DB mutation/production signal injection=NO；PRODUCTION_TRADING=NO_GO。

Validation：11 research tests passed；full suite 581 passed, 3 skipped，三个skip为其他Monster测试缺numpy。覆盖identity替换、相同ID时间/signature变化、complex-caused HFT loss+rolling recovery集成、raw signature/hash约束、OOS boundary与missing raw fail closed。开发基线三模型都进行完整signal body parity而非仅count比较。

starting HEAD `20d1c218425d5071bb889c0d0959f1218cf1d703`，branch codex/frank-only-local-signals；ending/remote HEAD以承载本报告的提交与最终回复为准，避免自引用commit。

从local-agent运行（fresh private work，source为只读快照；raw/SQLite留private）：

```sh
python -m scripts.frank_v2_joint_oos_validation --work <NEW_PRIVATE_WORK> --development-source <private>/history-shadow-ledger-verified.sqlite --forward-snapshot <frozen>/forward-snapshot.sqlite --legacy-snapshot <frozen>/legacy-forward-snapshot.sqlite --legacy-raw-root <legacy>/frank/shadow/raw --hft-evidence ../meme/evidence/frank-hft-sticky-vs-rolling-2026-10-04.json --freeze <frozen>/rules-freeze.json --coverage-evidence ../meme/evidence/frank-trade-coverage-sol-usdt-complex-2026-10-04.json --policy config/frank_local_signal_v1.json --price-cache <private>/frank-trade-coverage-historical-replay-20261004/price-receipts --output ../meme/evidence/frank-v2-joint-oos-validation-2026-10-04.json
```

helper生成模型与逐episode机器证据。production boundary、真实tests与报告是本轮封存结果；rerun应重新核验边界，不能把旧health当当前状态。

## Appendix: every development episode identity matrix

时间为UTC epoch seconds；—表示无该类型signal。完整signal_id、trigger signature、before/after与state变化在JSON。所有188个episode均列出，不只选择获益case。

| Mint | Episode ID | J0 ACC/MULT | J1 ACC/MULT | J2 ACC/MULT | J3 ACC/MULT | Categories |
|---|---|---|---|---|---|---|
| 6VZeAen9vxRYNMpCJ5SrS9qjeE2JeYoeufunFrHrdT7w | 00102d600a1a12fb7f62e06bdbc3396a0fdc1d4c06492b9aa301a6eb88829262 | —/— | —/— | —/— | —/— | UNCHANGED |
| 88t4EdAjiuUDzHujJnK5nywitQzYQWEJq2ouUgRGpump | 019beb88e1c5f3c5c7acdb3ec87117586e3bc007c0090df1afe4900212adeb2a | —/— | —/— | —/— | —/— | UNCHANGED |
| Ax5dAamJPeuaLpFUzs9FdcpoUhHDcxyjPzxCJQidjups | 01a89668442ddb24a0a93ec03350f23166f38dcbd6544026db7355774a6b8df1 | —/— | —/— | —/— | —/— | UNCHANGED |
| AdfCFpku5yhixaJXvxdNpJcHqEWX4iMstueY4us2h3eJ | 01c3a1cc607445e9994fc64faf9e1520a03da00ccab16c98381bd7a407dec2c4 | —/— | —/— | —/— | —/— | UNCHANGED |
| 2JWwT27J4QMob8NaAj58FJdpYUDHQy5wmqyeJ7VoTgUM | 02233686c262334da96727d87b244ab1c16d3af33e562b1da60d141852e2e00f | —/— | —/— | —/— | —/— | UNCHANGED |
| Adgt7dseCq71eN6GDuoUgpsNQp81ZNhq24nrF7pxpump | 02498b5dabbce27a539d84a0213b5ae2c7a9f401aa77390617e2e18d122422b9 | —/— | —/— | —/— | —/— | UNCHANGED |
| 2xA3qTFvkVELTMek93QSdmxYUiNRy3d1Ca7jV5c5LPP6 | 0310bdcc5bded22a16fac20937d595a0e05273ac20ddd98da2d385f065727f28 | —/— | —/— | —/— | —/— | UNCHANGED |
| 777XNvfVmvumMEc6M9yxJQJQnQtjbUYJyx53cqrwo777 | 05159ed8211ca32387c50255d016c05957a2aff3d03d2edbf76257c5fa139775 | —/— | —/— | —/— | —/— | UNCHANGED |
| 6TcFqnzyxFE6bZPqNL7MimUsvggheDQrjwKUhGUKJFXY | 0764431b73679568ef2ad76c84a1dc1e9babadcad1987b438c9c91d855b12b5c | —/— | —/— | —/— | —/— | UNCHANGED |
| 4P8ZC4cGTBPz4TPsFHtuoyLT8ftDcf8J9pzmJrUMoNb8 | 07f05304c515002a5289fe68f349bc9f6e0ab61aef1f71029e61658951f3043f | —/— | —/— | —/— | —/— | UNCHANGED |
| 2pouN3by7twkiZGy5aEKYUpf78ALDpKRTNu2WsQkpkqt | 090a1c8434bd2720bee762aa537f541cb6415cd72f1a2f66ae3fb86365838880 | —/— | —/— | —/— | —/— | UNCHANGED |
| 67rVP2rxtgJR5kgHCmm1UwJNPuuemyhcng86J4WMyGXU | 0a006d206d171b5646e08bdceedbdfd9d43df7e401ddb41554cf00c2b01f7100 | —/— | —/— | —/— | —/— | UNCHANGED |
| 3RTC33FgYgtbhEzXdRgNb2oaVuGPTSyUMkwWPJLx7NBX | 0a9d3bc46b8664187ab7cb541a05616606076f17de5c47a2515e63dfb515a220 | —/— | —/— | —/— | —/— | UNCHANGED |
| 9U1f18idDeySFnYrurxqT1f5n5nE4g4Uk5LLzP69bh1 | 0b9df438648e5cf58d02ddaa2e23ccfbf5f0a501d56e8c6d7efb5cf12dc8d38d | —/— | —/— | —/— | —/— | UNCHANGED |
| 9GGVdGxG4tJyNCePX9Q5MpHoZ7Fgb8Pr83Aa3QDnpaid | 0ca4ab483e508bffcae757e63808a467a5336db018ab1ea2aab98f57ece2ab09 | —/— | —/— | —/— | —/— | UNCHANGED |
| GY9mZfyPpxXxBXBxS2hB2XjhP3kfUsywTvgveozxpump | 0d6f801e4c62d2d37a91fe65502bafdf226fd1cdf5cdbb438ec6df87f83dc71f | —/— | —/— | —/— | —/— | UNCHANGED |
| 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump | 0fc2c485fe94776708fe3fa98597d675874a0e09f781031bed58d50f9f6e9098 | 1790381047/— | 1790381047/— | 1790381047/1790386140 | 1790381047/1790386140 | ROLLING_RECOVERS_SIGNAL |
| JE3HT7SbCgXDQWV6xp3oiiAisDzq4HyZ8wyEVBDCs45Z | 11a596fd4b4ce6f1294bd0ecccca1e0630b9b0110098c67a85acab91489179f6 | —/— | —/— | —/— | —/— | UNCHANGED |
| 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump | 14439f5c03dae54b422cae5974f1a813bb41d0a515c385010dfdfb94f97b0264 | 1789567874/1789572540 | 1789567874/1789572540 | 1789567874/1789572540 | 1789567874/1789572540 | UNCHANGED |
| FfFEszstujrteEmNK1SzS7CXyWiuiKUKjrRLov7eLtQ3 | 15b0921d1d6382cff96061b033ad3bc0bf2874c54de6fec885b39d01b272c541 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8e8N2w3QW1ibAVcuKiAWymFB9QbQecJyJnpthME4mPRx | 18054c191aa994d05c0ae63c1837c1a9b5095923a938b868ddac1488c7dbadc5 | —/— | —/— | —/— | —/— | UNCHANGED |
| 7vSG4GX8qz5V36noSde5Z9xV8xAXAGqivDyaNytPVDJf | 18cf7d87198c192300ba4667797f9cbbac46cb210a849a5bc464094e0735b596 | —/— | —/— | —/— | —/— | UNCHANGED |
| 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump | 18d00a62e30c82d8c5f10c6d4fd6f458ea9caea76ab4755fd0d7a863c365e451 | —/— | —/— | —/— | —/— | UNCHANGED |
| 6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx | 19a8e21dc0d4f2c9fc899cc5886a96f5762cd6101f458d80d55c84de31d17241 | —/— | —/— | —/— | —/— | UNCHANGED |
| MukLDtJ8Cx9DxLbeyLRSWPSposTMWuwHANbuaudpump | 1a894b5b9f825330170474ae871b6ed2ec053e2c46b350bbef874c5cc705165e | 1788642055/1788642055 | 1788642055/1788642055 | 1788642055/1788642055 | 1788642055/1788642055 | UNCHANGED |
| 7MYpDaZ1Uorg1QtkjWK25X2K4UoNk88854jfopAXxNKs | 1ad0b1681cd3459a436f2c13b318492b9ce18b103068f922740e67f77dc406d7 | —/— | —/— | —/— | —/— | UNCHANGED |
| GLRyB95LzCyyY8TVfwZVDyrVcZuSJPJJoaPTnyWs89mv | 1ad2c71246260ff0011eb62e2a0a1304bab95434d9e8800461586bfd7ee793bb | —/— | —/— | —/— | —/— | UNCHANGED |
| FSJfPYF6VjuDuUxMFdUrCEkVr96bhC5oXKhv4o6JJxiK | 205e7bf8fa75f754032046d8fce058c66ce4bd2a6e27c1c9679fefbd482db340 | —/— | —/— | —/— | —/— | UNCHANGED |
| AUZrzyaejPs4zqGQ7xpPrSz9qs2rq4WhvtKANXvaWupT | 222479a68e860e3643dd0af68f1767ac4de3c15f4f49e13d4aa170a03a6430c6 | —/— | —/— | —/— | —/— | UNCHANGED |
| AGi2s9zPRPHs3zEDPhPTroumTEXK5ufymYSfEFndCSSW | 222631c7b3efef3c0d3c870de917b62e58beb63e40a4d9a129b4d7e29eb82516 | —/— | —/— | —/— | —/— | UNCHANGED |
| 7uvLyn87LSxW2GdwdEeiwmSJwQLVrcVyo7SRVcLbbtGc | 2350fb130ff90119a21ec165d29be52f7b6e3d492da8be4bd98d5dcdc337f6d0 | —/— | —/— | —/— | —/— | UNCHANGED |
| FRBrpR2K5g77VjbSjKFS2V4huAddxVmhD7g2oobcLmmM | 239583c86e6b26adbc8fbb7b3284b14c227610e81257a5ee3f57e9c5036b0b42 | —/— | —/— | —/— | —/— | UNCHANGED |
| Bs5PmEnm1ugySurQCohqQP5oJyQRw83BgEArNrkzL5p4 | 240ba5db096ddfdcb073430578583f8ce6a9c6e7f6d1270e06c5f1581dc1cf54 | —/— | —/— | —/— | —/— | UNCHANGED |
| 4MMQY9bwkxxTtsK3W227Q5ABT6yFY8Pmn9Ze7wmAXKY8 | 25a8fd116ce885abbc50955c2839e6601997521a455806c085f395af928baeaa | 1789160162/— | 1789160162/— | 1789160162/— | 1789160162/— | UNCHANGED |
| Hy1LfQLL4zLQihmiQKZm7DQzXm5K8aVSfKtdHFYXbKMm | 26c351b038faacf7c847c4701e736d0bb3c8f09e833b41bd1b12a399a13a4676 | —/— | —/— | —/— | —/— | UNCHANGED |
| HCy7vxTApN2Lcv6Rw1MZazXsEofXFLxWCVbJBhF8pump | 26cc86fcc98ae04c1aeb2bf4c8e3c961b0d316c980c77a1f1a3427caca65b8ec | —/— | —/— | —/— | —/— | UNCHANGED |
| Hg5Ja55T5wESq4vyFoiVCMeHXtGyVA69X2UHq8hgpump | 270e474cf9bf8936ed907f80244abcaaaf9f98c0d991a187119081908409171e | —/— | —/— | —/— | —/— | UNCHANGED |
| H1kXUqEPkQNNeNjGNN5tuHf3nsQK2vB1jUA9c4RggpUf | 2991a5300c0c9476e86a362320bf5feb757ed8e1c624580eef577794ee75c7b0 | —/— | —/— | —/— | —/— | UNCHANGED |
| CbcyNo7m1amFWqEQm2m4PLv1UNvpcL3C1Ujm6AkzpKoU | 2a3367bd6f19bc12537367583b170847f736887ca80c4e3b8467477b1c2dd192 | 1790452015/— | 1790452015/— | 1790452015/1790454994 | 1790452015/1790454994 | ROLLING_RECOVERS_SIGNAL |
| 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump | 2b35c6d7eb84c6303b7543d978a2bec9b98ac28dd44c0e316163869e2e40b28a | —/— | —/— | —/— | —/— | UNCHANGED |
| BGbzLQAF4AGou24pZCRVYdAb1yCmobKAPFPtb5zfs6My | 2bb690164d69593fcec5921a544486ab25e5182b67e81fe4f7b7da00c3b47044 | —/— | —/— | —/— | —/— | UNCHANGED |
| 7hJ2SM9jnxfGwveud9XtCtYA2uBmXco2uRA8KX6mpaid | 2dc1569948b073403dbf6ee03e9145db4e33b92f7cb9124c3ca4861bcf2009ad | —/— | —/— | —/— | —/— | UNCHANGED |
| 5eLcW9sTax56Hpr45yiXu82TyuUWi5xGgLchuH3apump | 2e4bbc44f861647446202054e58555789a20e1b65fd21704a27a2e4ed8c5f0f9 | —/— | —/— | —/— | —/— | UNCHANGED |
| 6HU4CmRb15C2nQDx8Ld2f2W2wTdmog6aZiiXdrT5Pzi8 | 2f9db4d48d814599f0050674e643e06edb13c84a4a3d7d574154c63700bcbe64 | —/— | —/— | —/— | —/— | UNCHANGED |
| 4K1m7gAMDKzrxQn68yuZAd767w57Fw7Ykw69dG3umeta | 32e5cdb79080580d60f21e728998079c511c218886352bfd3f95065153189f88 | —/— | 1790097169/1790101740 | —/— | 1790097169/1790101740 | COMPLEX_ADDS_SIGNAL |
| 7cXWSNTq71PZREBmGCBvZirkNwoGokWBQz9fWferViiV | 337052ad724d2f295b19f681c22051b2dd4d6b04d5c5f5d378f4b72ece1e1991 | —/— | —/— | —/— | —/— | UNCHANGED |
| 6cryqwcRfbWURXxGGuhA5oTvHo2aezrs1UGw1UgyqWhs | 358b27e615cb9cc44e3b0ce2feac0529ca95ee4460bdd2a692708ed47e7b398e | —/— | —/— | —/— | —/— | UNCHANGED |
| ASoQZA3Dee2HU34Vwx3b5SAtTaczJtZcyx1T413nDALL | 3927e47dfdfb6a4674d5f34f16fae2998f686446a1fb8f6b9839003c18d2bb29 | —/— | —/— | —/— | —/— | UNCHANGED |
| 7zW2s4GE5i4y3MCCmFSEh7n2CB7S8aRDfvJpYYAtsQ1H | 394b1ea9189ab8c59fdcbee99f987303ce99446df6937db77e757dc02c68104b | —/— | —/— | —/— | —/— | UNCHANGED |
| 4ajeoXCv352quoiH26neS2JuKRgwv9mkDsM2o6Axpump | 39a09a1f990cdde8508de37fcc86ee53d98fe9078b3b6e5b59b8f6fc2edc6caa | —/— | —/— | —/— | —/— | UNCHANGED |
| UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids | 3a666709f0f1edca33435d4e4c1e483473866332c01a779e849de4d3508014a8 | 1790216860/— | 1790216860/— | 1790216860/1790221637 | 1790216860/1790221637 | ROLLING_RECOVERS_SIGNAL |
| 9DdHxVe1BSPaTy3iGEwvWsooRchNLK61XFAvzot59FwD | 3bcf2ddff386cea7d4efa3e69c7e2b44bbffb57278470ee3e94b69c75afe2f2d | —/— | —/— | —/— | —/— | UNCHANGED |
| 91ryaCo5yGpYZM3bs6GUPs97VWJQj7RozBmqPULgpump | 3d73ac75a189c12377dbeeaa605fbf41abd556f1b9b4bbac595a73bb3f129d96 | —/— | —/— | —/— | —/— | UNCHANGED |
| G2KDX81e31T6pZbkrJLPKAXqKcd8VoE3UEp83rRtpump | 410edf1a5cf72504bf2da6403106a24c1dbe638052b0c8d6f2d85e1537490aae | —/— | —/— | —/— | —/— | UNCHANGED |
| ZesMGYmokFiEuDvNzWeMhB7jxF6eUW8c512vwSKSTNK | 4239b6128b22a8217bbbf73855f114dcb45c910a0995d5759dd5d6599a1117ec | —/— | —/— | —/— | —/— | UNCHANGED |
| Hg5Ja55T5wESq4vyFoiVCMeHXtGyVA69X2UHq8hgpump | 427f74730177447564faddc6d92fe7370bb5f62d6a7055990dcd6d6c3db97bed | —/— | —/— | —/— | —/— | UNCHANGED |
| Chzj5YkKzgtqFkgonmxGeSeyJLHqjMAJFhX4So3MEF4k | 42cf7a2d4c71b1223fa5f2f5f7db587598df77f24d8376c02e0b39ca2aa36e01 | —/— | —/— | —/— | —/— | UNCHANGED |
| GTBxUiw6wJdmmkCGZgRHLyYxqu1vG4KtRpeox6yDpump | 42d6ad9e58abdf01accaaf1970de2c175d1e3f9ff5ddeccc24663c5e79356000 | 1789856570/— | 1789856570/— | 1789856570/— | 1789856570/— | UNCHANGED |
| ANM35KbUcfKdEVBXzSjZBoT6ceSwYRs3fuc79fp7kRqP | 444e2a27421125dfd762da6cceb53f18be3cc570479944c76200c2305142f81f | —/— | —/— | —/— | —/— | UNCHANGED |
| 5HZHzdeCtPUdzxz31W255uB6Umugu9kfe3bxbrya4DP2 | 44bbd6e1e35c7d853497255fd532d7fc5e232c18c62aee49adf7c72a7922a75c | —/— | —/— | —/— | —/— | UNCHANGED |
| DD5beYpSCWoerXvGgD5hqf4qpphsFMBXphNYoSYUW53 | 496d416e4fc40797581a0ffd320f7fdfe43f26f0bd73e30c10b708677e3d05a4 | —/— | —/— | —/— | —/— | UNCHANGED |
| CgFVAx2G5AZFX1LT2wnSpEScuVc9rDQcoiRyiwFgymBx | 4cee51cbcb6b4e6530f7428f414e3acfd16f176b8604481f11a54ced0f0be236 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8xH8ikqGXNTSYmmUVakCE2tVwU7aYJwz2JZkqAjW88sG | 4e34963ab9dd1bdecb07974c02f80492e34035f4c7799d293b6abcb45e87ff97 | —/— | —/— | —/— | —/— | UNCHANGED |
| DEW9dSN6QpWyNthphCpMmAbZP1Q4cEKR9xQXAri98WDP | 4f89bccc35e92432e80de1b89c3f0faa9704c7c60adee308d3d30441e346d285 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8LstZpZuR9Dy7JCZC3YwPEWtbYhuDVFAYV37r6ZAcuHz | 4fa09d9f0eed28d4acfcb155a7e3b320b6069bce110058d0fb518743b8a52d24 | —/— | —/— | —/— | —/— | UNCHANGED |
| CARDSccUMFKoPRZxt5vt3ksUbxEFEcnZ3H2pd3dKxYjp | 54e5898fbda7f750a0770fd41b3b9be4b90221896dc2a9ca80997e9ce141db65 | 1790627749/— | 1790627749/— | 1790627749/— | 1790627749/— | UNCHANGED |
| EA4J89CHKrdfasv9rta5vb2vKngYb1JjijejeU8Apump | 5959544849a0c155d0e68641ad56a1d90a331c6fb48b5d4ada7f43ea7b159ccd | —/— | —/— | —/— | —/— | UNCHANGED |
| CbyTNf7UPzvewHh4Zp6umogM2RWahhmGRJWLJnPwpump | 5cadb05af5e9c082108f7178f155979d0cb448ac925ba1da034b828fe9ca3e0f | 1789403948/— | 1789403948/— | 1789403948/— | 1789403948/— | UNCHANGED |
| 2RSbZYTwWchqaj2CvzQmRDPzVJhR1hZoVtpurVA2pump | 5d7146f1f622e64763fdc22b6bd4d866e38f5daf54f3c979599b1fbe8e4f7567 | —/— | —/— | —/— | —/— | UNCHANGED |
| F8Sc8HoZvJcMrTY6vBsetTqGPv6XQmM2XgVAZo1sSTNK | 5ea0c2b16e74460d7f31496b6a7d2c0bc48e5f2fb43d624522539a8d47dd8f52 | —/— | —/— | —/— | —/— | UNCHANGED |
| 4nCmpwne7hCoWTSpAd54uENmCgHJrHTyn4DMPCEMpump | 6177045a3d28946e067193488b552e52ed1207b7b7d0058e2734679e46d16081 | —/— | —/— | —/— | —/— | UNCHANGED |
| 6UtY9iTZMQQ5QZVrbzFnNaJntV7oySm9k97mvwnuZcxr | 61f9cacf0a21f0e3a0993e3b400a543095d78d51212942f297c8abab5442d3fe | —/— | —/— | —/— | —/— | UNCHANGED |
| GJSfEpiK9RnmRt9AnZi3FL1b2K6AApcW1SzTs2FeHGis | 63812659930a81ac5a62dae90ae5666907c61a923d3020112470ad02f7f612f9 | —/— | —/— | —/— | —/— | UNCHANGED |
| 6LDU8HoZ3oAJ2hxvYADh8boWmEZV3sfyUb5TyC5Rpump | 64f75f19cb48298d739ab04244c949c2134d0cf9aa8781d2b61184b102b684f0 | —/— | —/— | —/— | —/— | UNCHANGED |
| Fhxcx7cHmhDkfwziHyCwN8vQRvEFRK3zezokaE8gL5q7 | 6670c5bfae35987c3335841db4cb580196893da76412bf772a5b05ae0557f636 | —/— | —/— | —/— | —/— | UNCHANGED |
| DvdmEnztCmXwBnAbedD48XVGZJSxq31zNvnyftXdpump | 6a41656986c586e9f26720100a3205cc73672b93d554ad324fe91ce1fc39f302 | —/— | —/— | —/— | —/— | UNCHANGED |
| 6rHkNb7HCtkpvdnVJsBCZHH5dw3AndqEjfmbEGhooR7t | 6b669bf2d225a0f6f0f97fd56914b76da436031732dbf77c425f004b3ce558ac | —/— | —/— | —/— | —/— | UNCHANGED |
| JoBxYVvPhPSkiZNiUjZdty1uR6TaNneuQvE3zZ2pump | 6e72404ad4da88ef4c59cf31687d74ca6f29924c2b4770ec1d0ed3df37ce22e3 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8iBSN84vSpZAhMCin81YS9FBgiuQhKns2udaZ8qTzkh5 | 711313df5822aa6752a3738b30d9b176bd516ba2fee9311014a4cb09eb1ec5c0 | —/— | —/— | —/— | —/— | UNCHANGED |
| EgrQxdckmSBEzKXzMD6PxjYdwsMcBpJjW8dx3RBWx4By | 739495dd369ea28b0d270978cc4f3a5f792f70287f1de8152b1583dcfbc95ea1 | —/— | —/— | —/— | —/— | UNCHANGED |
| CbcyNo7m1amFWqEQm2m4PLv1UNvpcL3C1Ujm6AkzpKoU | 74ea2f7b6f5ee5ec2b19cfd4868697aa78223f232da9275e4e555c3e0337b57c | —/— | —/— | —/— | —/— | UNCHANGED |
| 7M3gDRgozcumFsiTeXwjB8cYxpg7Q9R7rH7rkw2Fpump | 7595025cd31ed98fb34624afa84abf63ac53621173de071aaf24653e8e2788eb | —/— | —/— | —/— | —/— | UNCHANGED |
| 6dBrKbJdAzkwJvkWEWTJb3iWY7aNbrZKLsrKUCnXxWsM | 78d208f39865999f7e3e98a6b41547ab0662ce27a05eeba5eacd6cfcb61a225e | —/— | —/— | —/— | —/— | UNCHANGED |
| 44JcD4XMTxo6jy9yczrRkFQv91yzrvNAKG8XpnaL2tLF | 790a8ac1e09f2154a5fa7e7216509745c4ff82ea068d860483409095f45a7438 | —/— | —/— | —/— | —/— | UNCHANGED |
| 3kmygWKZBkCYrgZHKfiuB9UFKTcDLTFFsKo3BWpmpump | 79e9bb0d6a06efaa0c665c4cddb70535671307bea23e7f82a5546e8af231acf2 | —/— | —/— | —/— | —/— | UNCHANGED |
| ELYfhvSgsdkLvhG9b6ZByrzgwPebegbdX9rLBNH2VNRp | 7c6ef546568f3f74ac9c2fb758597638407e148da39e6908c32f17f6b9b45cd1 | —/— | —/— | —/— | —/— | UNCHANGED |
| EKtmPPLaCbEEKiwoHHtV7TsRsmPXs5CMGtQtZFSiinsc | 7e99973991ca394802195b87aec8cc1694f8d413663b014e12d607d42f3d9f9c | —/— | —/— | —/— | —/— | UNCHANGED |
| CbyTNf7UPzvewHh4Zp6umogM2RWahhmGRJWLJnPwpump | 8019fd66dbe385dd4595db03cfe736a77df4215a96957364572da4e1f54649ba | —/— | —/— | —/— | —/— | UNCHANGED |
| G5im68AmQ8c6C56Kdapufyu8dZddYkMBGoLbqtb98j7 | 80e46d09e07b24a2bb83a8d1073a43c2d2719aa4bdcf453db64e5a9af6d74692 | —/— | —/— | —/— | —/— | UNCHANGED |
| 4xSfWrG9VkyNbnCNvB6opKEex2ebXmCZCiied84fZisB | 81cbf56429f7180c47987e6f52944d6a0dcfeafaf565b6ae5bdfe898669cf06b | —/— | —/— | —/— | —/— | UNCHANGED |
| DvdmEnztCmXwBnAbedD48XVGZJSxq31zNvnyftXdpump | 8287560367f58284484e6770752d190770e99b7747cdd52ddd4f0e1a4b21cf83 | —/— | —/— | —/— | —/— | UNCHANGED |
| 6UtY9iTZMQQ5QZVrbzFnNaJntV7oySm9k97mvwnuZcxr | 8345a6b51d4296a286102ab3f1ea4a9cfa4756e4b430496d15a59dbca7925789 | —/— | —/— | —/— | —/— | UNCHANGED |
| 5A6CJfJfgupDh5J2s26NUisY5xwC6BpDAndDiye7tS5a | 83a8bb491027f419087faf8aeb5cdffbd28ba6bf23282c09e088566d3b0908ea | —/— | —/— | —/— | —/— | UNCHANGED |
| 9h5AzEQzYu9CV5K6uLtFRMD1KcbxZSFNxZEgBTNfw5Na | 844411f8a2675be3263980faa0d765e1399b2dfb31728444f9e1e1c8df559c35 | —/— | —/— | —/— | —/— | UNCHANGED |
| 9DdHxVe1BSPaTy3iGEwvWsooRchNLK61XFAvzot59FwD | 84c794643a65db57002c3c643e536a26324e9af4e11b704b891ac3c33d7639fe | —/— | —/— | —/— | —/— | UNCHANGED |
| 7Q5vqMfVjx8kkWE19zfbG7M9NuoWUAKeWXMFXVqenwbQ | 8585b9e27db6c4f69dab4e246f3316841efde606cdfe4d8ebc38c54174f4a6ee | —/— | —/— | —/— | —/— | UNCHANGED |
| HTmQz7My6MehV7bjhJ6jde8nDND1yvsz68d24LP7YgUQ | 86490e85f27715d1ff9367d3f6fc51666ed5c2ccccbc424778b27fb5cc0e88ea | —/— | —/— | —/— | —/— | UNCHANGED |
| HHig4peAgZqdAV17XuuAdojYSYLhsctjTEvT2kq9FkNA | 87a9a1a5b8e13b1577f4e5f699d646bbdb6e403d7c3857205577899495c323e8 | —/— | —/— | —/— | —/— | UNCHANGED |
| BHS8LHW11NKxzxyCtqz9NJbTkh3h94WqeMVYgTY5pump | 889d584bfa2838cf92f2b372a60c730f543533313be8b2e14ca0bab72f68c14f | —/— | —/— | —/— | —/— | UNCHANGED |
| DFmkM8ZhfvkuzWz5gyMEkH2ocLP7qxyCaSme9TYqGczN | 892196ac6067b89137095a413298dec6c1b6e1df144900a7b0fdfc348060936f | —/— | —/— | —/— | —/— | UNCHANGED |
| 376aP7F8uph5jaw3axSAqWYK4t23weXkSVzkuNoQYCCV | 8a21db7873ab3e9430a744baf3606e9c3c36c06d6cbaeb6882807e1f47844deb | —/— | —/— | —/— | —/— | UNCHANGED |
| Hg5Ja55T5wESq4vyFoiVCMeHXtGyVA69X2UHq8hgpump | 8a5edea6451adea61956fd29b336da0a8b394d150dbfc61c9013902305f00c47 | 1789586338/1789590540 | 1789586338/1789590540 | 1789586338/1789590540 | 1789586338/1789590540 | UNCHANGED |
| CFNRDaxFcvRwRSNnA5cHrCCr6AHhk9dNkHWpRUjNupFL | 8a67d5691f268f8bc6d6f1962e37b51656f94860dd1be38a334f600def24251e | —/— | —/— | —/— | —/— | UNCHANGED |
| 5wZDE8f5uKHbVaHAyz84Lgz7xefAkCpvcwoWYaRCrfn | 8b017c32486420d5d03a48bae988ed6d718b52ca227ab7b697cbc4901c0a6eac | —/— | —/— | —/— | —/— | UNCHANGED |
| 2CFiKwy5ATZZQkjrVtrvXPFaa5WZddv2uJ25Acs8uz6J | 8cdfe95f919df7ee9d92173ef0edc9cf1ce8e718ef04a5f845f59b84f19b7330 | —/— | —/— | —/— | —/— | UNCHANGED |
| 4zPrgVNqVgCw5FFHYsURnHboTjKgESXvuTbQGzzapump | 8d8a4855095b83b19cf189e768568ec46195251ced04042c82829bd920f26d77 | —/— | —/— | —/— | —/— | UNCHANGED |
| A7iQ8N5jKDrg1YUxJ7v8aN5AtkwJaUTNhq1jZ8YLFrAJ | 8ea9a554cdb82323a61ffa00e2c0297895c0c71d8499a5259ce3bda34bfb49eb | —/— | —/— | —/— | —/— | UNCHANGED |
| CbcyNo7m1amFWqEQm2m4PLv1UNvpcL3C1Ujm6AkzpKoU | 8f1f62ae6a26121781696a4c92a8d9d249f4f82bbad8b1b1ebf514a3a65ebce3 | 1790393170/1790396940 | 1790393170/1790396940 | 1790393170/1790396940 | 1790393170/1790396940 | UNCHANGED |
| AN82CufiuZt19HoQZzbCoVfR5DSftf46EkWeYg5TRS4r | 8f46d33c5f7266fddbf1ace95f4fa1d21c6068271be4f4d3055fca7fe743e14c | —/— | —/— | —/— | —/— | UNCHANGED |
| HwCG1Jr6RbAVsKX1qTaH6JtFYGeE6zaLd13W44YGpump | 8f8847ad60625dea4d3fef7a90a9fd93c137f1ec1d5a64e56288b31a66996375 | —/— | —/— | —/— | —/— | UNCHANGED |
| E4Ap4icMLwKot8rkkTbq5JkS5kZxt5XCE3yfxbzYBjHx | 93f61181786349f529902926590fe3b5650b32e9d20a22d4f03f4ad7efe6bee0 | 1789097042/— | 1789097042/— | 1789097042/— | 1789097042/— | UNCHANGED |
| 6HQdAaugomYDk5yBdFGv4uLDjRtrH23o3oZh8tywpump | 982cfd97eeac85e09d207f8e0cbf8c43ef9844a9efde1f95435ac4976aa633dd | —/— | —/— | —/— | —/— | UNCHANGED |
| GZik7vJSnDAao9tbbcLrMGKfxLu7VCjoAtkDhsv8A3iE | 9844cb48af4480919a22e149be6f94f2c3c7722076483885e9356e7f6ddc17a6 | —/— | —/— | —/— | —/— | UNCHANGED |
| 31nQQSUfBJ7cGG7xTBZEiSUQje6QfzebyLcmgN4xpump | 9a04fed3814406196888f839aef07b8aae42b7f4c251d3adb3786346b11e5fe2 | —/— | —/— | —/— | —/— | UNCHANGED |
| CXXpHyiwAzuwwxD9aGJCA3L6gjjJ4wMXoGYYjczKpump | 9c9ca141bb8935bb3f1a020d8257c62a50d518064fbe68791b7bb20cefe31118 | —/— | —/— | —/— | —/— | UNCHANGED |
| EMBKvWhkjywZ2w3Y5wjKjZNQPY61FhUDdF5RDRPsVkfC | 9d9f60c188b98e7e3f533f8638ec551bb0d85e300bfcfa7bed1887bbbc05e8d2 | —/— | —/— | —/— | —/— | UNCHANGED |
| 5qSo7XuuMJ16iqHqVMEwgvG3BTREuHXXBGkpipw8uVD7 | 9dfee3df24b5a1ee6efc22a32d4a7b6fd722a1669dff21e24f91e9a8e666c9eb | —/— | —/— | —/— | —/— | UNCHANGED |
| 5Cw3aUR8NMrQ1xpka537zR4WDpBfqQfKEZdyXwAdB7na | 9f1d19a5829e7e78c399a8b05cf19e537df353ea1e9a8b48b8b842aa5c84ec7b | —/— | —/— | —/— | —/— | UNCHANGED |
| GY9mZfyPpxXxBXBxS2hB2XjhP3kfUsywTvgveozxpump | a193f567638cfbf221e7900ebe0a602bf37bcb17bc986a2530c8bc77efd3c088 | —/— | —/— | —/— | —/— | UNCHANGED |
| HcRLc9VDgjLeK154xDawfb1dmVJ98DoSqcwTHGqiDeJR | a26e0ae867bade4c29a87b246cf92d21da7ee269d8f570c07ccdb5bda4056f2d | 1788723248/1788730140 | 1788723248/1788730140 | 1788723248/1788730140 | 1788723248/1788730140 | UNCHANGED |
| GtPuLjZUvEyrTXZzNAUQWBNVcgf3YNCgJDKZ7kippump | a36e8fc20bcd2663a9ad40d6e3b083961c93a2577b9a487b7c09a48925c7a6b5 | —/— | —/— | —/— | —/— | UNCHANGED |
| BPxxfRCXkUVhig4HS1Lh7kZqV6SPJhzfEk4x6fVBjPCy | a47f853423854cb969e307ddc46e86bcf4d4d43c37ecb2e49a5e595d99f134d7 | 1789930581/1789930581 | 1789930581/1789930581 | 1789930581/1789930581 | 1789930581/1789930581 | UNCHANGED |
| DEW9dSN6QpWyNthphCpMmAbZP1Q4cEKR9xQXAri98WDP | a48f9a0e5d6227fb62d3d80e4e4a7ecf125b4ed1838b01d6b27e49e341b51a66 | 1790205235/1790209740 | 1790205235/1790209740 | 1790205235/1790209740 | 1790205235/1790209740 | UNCHANGED |
| 85PW3rahEa5HjSForgd6AzvHxNUKq2pwchQP1pe2ARGu | a5f3db9fa3e2b1b064e4c48eecab68d1976813752b3b5aa9069adb71f87112c5 | —/— | —/— | —/— | —/— | UNCHANGED |
| 5kepRxgAULaifxKVge1Mg13cCppAiwKMQhNr2Z7dBdpE | a7bb0f673272596ce92ea67ba0ec74b4381e807e13d0f667d98306ee15331bfe | —/— | —/— | —/— | —/— | UNCHANGED |
| 3iUTyNYW6xKv5kZUjtbrEDTsuJTrSVwvB3bQtxkLpump | a994f49678f894e31bb665e4137a42f67ac23a34c7e361fed464d89f6f91a502 | —/— | —/— | —/— | —/— | UNCHANGED |
| fvHLJUwsynVHJrssbZ8MLNyku9jt2izUspbBD4Spump | ab3c5d76332237015799b5f528e6a291622a1e52366f18caf635ca848aae9927 | —/— | —/— | —/— | —/— | UNCHANGED |
| E4Ap4icMLwKot8rkkTbq5JkS5kZxt5XCE3yfxbzYBjHx | ac66419f6bd29d5a2849d4f11029618a748c283fb22cfd65d9fd22b092949188 | —/— | —/— | —/— | —/— | UNCHANGED |
| 3GXtoGmXaZHYEASkeDxejdrSWpeqqRWxCdzUVAagpump | add0d2babf682321d69d5eb3fc95a8e41b95f29e7585abe2e24831009bb33a93 | —/— | —/— | —/— | —/— | UNCHANGED |
| H8fav2oZUgSvWQkB5cvGY5X6FWsAtoHbr3vyLG7CMWHD | ae72cf1d10d534aef2b4fda2f1e99b3fa54bc7bba65a8aa7199d8a0f84bdf0cd | —/— | —/— | —/— | —/— | UNCHANGED |
| FPPGF5RNgCvNzqrRqWrkgkL4YQhzqKMNVtD1kWk1ooqg | af082121be0d58b5c5ae7d8ae5abf676eb5ab445cebad6bcfda28bdda254d03c | —/— | —/— | —/— | —/— | UNCHANGED |
| EKtmPPLaCbEEKiwoHHtV7TsRsmPXs5CMGtQtZFSiinsc | b4d41b7fa8abb3112f82a16818a6524b0cd25f2065ab1dd4851264b354735a2e | 1789947715/— | 1789947715/— | 1789947715/— | 1789947715/— | UNCHANGED |
| A4j77ZgCEW3i4k94jBDQY5XwPikBB41WYi2vCQqSpump | b660faefd52e61429a43ff9cfc965cc91df44a00452b6e9ebfb0a024d8522e22 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8RAFGyzajpYX96ppL7MXEL5DwjBSnbAqjBTfhUXDhVYj | b680c004d75121809d64661032efa6782fde1c6e15a35ce00fd6e21c51af0429 | —/— | —/— | —/— | —/— | UNCHANGED |
| 3937Rsye62a53Y5o3UVG6gDPk8whAnKq1sxCV3Xu8YLP | b75b1590435da9942f76e0218e3e71d891006022df4e7ecd59cefe07e5a7b066 | —/— | —/— | —/— | —/— | UNCHANGED |
| 4ZRp2QrXjZ58XinbUzTjyhuFh8gAaHYeag4LnRUmpump | b795e560852f3b429ca46089a2ec55f6ada52de528c116c690241937f8328117 | —/— | —/— | —/— | —/— | UNCHANGED |
| CdixZU5dNFGXZ2jojQjree5EyynrsJ4GjDdXvZEVSLyX | b7d58856d1dc08a6b65296e6478ab54420771e3792aa5e8dffc9672ecb91d15e | —/— | —/— | —/— | —/— | UNCHANGED |
| PerPsCe2SJ7Q25CN4R5TTX4fmBdmknE2hQmqCt96fHL | ba70bd2771f97e9b3912181181a3102faeaf0f0799a1965199b735a2bd69bfff | 1789231035/1789237740 | 1789231035/1789237740 | 1789231035/1789237740 | 1789231035/1789237740 | UNCHANGED |
| 3RTC33FgYgtbhEzXdRgNb2oaVuGPTSyUMkwWPJLx7NBX | babc830164b62b60712aae38ee01623193b8c1d05036ac21fb775642ef689c91 | —/— | —/— | —/— | —/— | UNCHANGED |
| Hk8Uiq8CeNdmZzu1aPaT7MhvujtJifFS9kKhfpXmpaid | bc13f9224c235b58805bf081c94051311c4cc1f8dda457506eebaf2582e49283 | —/— | —/— | —/— | —/— | UNCHANGED |
| AGi2s9zPRPHs3zEDPhPTroumTEXK5ufymYSfEFndCSSW | bc323eb2d46138bae5f1a5c4a90e4a635a4ef4bc0bee123275719c623621df5b | —/— | —/— | —/— | —/— | UNCHANGED |
| G1jonmoSEbMJSwEg1AmgDAJq2utmuBSZct8oqttBf9rT | bcfa760468506f005bf377c0d85f38ad2b2f7a4548a03a9d763d4fef52177773 | —/— | —/— | —/— | —/— | UNCHANGED |
| A2oMu6cYg6kJpiJ8kSLvRWoDL9SdEQmGj2tFpBsiXBni | be08b8c95066bd9a2c381966a3540166314409abb299a2a4727974ac6d5761dc | —/— | —/— | —/— | —/— | UNCHANGED |
| FzEh8uAxjUWRgGhzb4TGGBBsKUzsZn8zoSoZGmEppump | be29712b3c04c16793392cd3010260e1ecd5ee94eb8aecb8cf1a04a7bfece479 | —/— | —/— | —/— | —/— | UNCHANGED |
| uuxWwFL6G9UjiYRZvWxJrSB18V1oKBgYrmueamREK57 | c1d99d26463a3ae58ed94101c2a55754352451cd469933627dfe42975aebc129 | —/— | —/— | —/— | —/— | UNCHANGED |
| 9GGGhze1NnQwcABTzxdxx89BEFLFtDueHhkwh6japump | c369d2c5a72eaddf6d4944a3ef6376754457a152f53372b72335c44103733dba | —/— | —/— | —/— | —/— | UNCHANGED |
| DFSDCFBDewhETTit5iYnLJzytJe1J1X7SepSSyxKgT9K | c3c03b5e87d534b27407fb0c082a4a2836acf931901eb3b8c91a7cd09baf8683 | —/— | —/— | —/— | —/— | UNCHANGED |
| FiXDsziPrJvEg8CVsFsHa6rykx6Sk7rckZi39nfVtDwj | c5067db9a6e02fc276d3b72e20a2792eb095248442d11b7e9d621819b2a71ff1 | —/— | —/— | —/— | —/— | UNCHANGED |
| 2pouN3by7twkiZGy5aEKYUpf78ALDpKRTNu2WsQkpkqt | c64a7367dae3fb41b0716229ed590fc4550f25a9d5b55e961ee141ae224f0824 | —/— | —/— | —/— | —/— | UNCHANGED |
| CNWxmoBSQZo2Sgp5KSAK5m9FwSqDbXQRP4CNMuoe78Gm | c6d944dd3d5ec345b3091238fd2d2da4a62e5ae90d5ebcf9f2ecc38c60ac5c2f | —/— | —/— | —/— | —/— | UNCHANGED |
| C1mBfBoDkwWfd6uTFZp62ARHLjeVp3bDpCDMfMZtPngE | c9eb82e5e37b310be85716b5a93a266e53caa6b30e90d0d236045c43f5398f51 | —/— | —/— | —/— | —/— | UNCHANGED |
| J36mBMBFnGznSibqSemkCFnT2BNvaxNsxDMNS2mYLeA9 | cbc72c45f6dbb4ff6d3c16bacd2fc912bc7e153a448449d963cb910d6d157e21 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8WgQ9XpJYCfnwmSmMTdVioUuxxwnMdYuRvSn9osXSTNK | cee9ff8b4d9e2856bcffd9c5e7da0f6d3a92f85d98931409a211335539d02f33 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8K5X85PAJHAAVSvYaAzgVPPAPsqqHmvx16ZyBiscYF8L | d3948393a2eec40b758548c9004c7dafac38f7181a96710d16cb5b891339caba | —/— | —/— | —/— | —/— | UNCHANGED |
| 8K5X85PAJHAAVSvYaAzgVPPAPsqqHmvx16ZyBiscYF8L | d71d1b65d505cd20f582b506567c0545378d119fc7729a5b5dc74f173e03313f | 1788835337/— | 1788835337/— | 1788835337/— | 1788835337/— | UNCHANGED |
| 4R2vepDVY7Gdcm2VKuAy6EbBfWsYSEsDJou1QGKuMfnf | d801aaf5f68a9064fcf0ce938c5ed1a1e599c78f5fad21db1071a509f9a24602 | —/— | —/— | —/— | —/— | UNCHANGED |
| Ax5dAamJPeuaLpFUzs9FdcpoUhHDcxyjPzxCJQidjups | d8cbe92684eaaa9d5bf52a41f6b7e73f8a73e66cfecd37091da7caade1fb2add | —/— | —/— | —/— | —/— | UNCHANGED |
| C9ybLz9i1nLm1S6ztrCRS8vGdetbpwTYeq7vCAxBps3B | dc64343dca19ab68ff6a803a546d3da1e234c756a76bda1e52b0b88301be04a3 | —/— | —/— | —/— | —/— | UNCHANGED |
| Ffbq7n4yHbGABdRTdNsuBKVSz4f2mV7HoVG4UwRGgYvn | dea7982d17d09ba2915039ab3ff2302b568c853ad0086bd9d2143701319f0289 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8VsFryV6n8tNfU49L1GmaDp9LU1ubz6DbgjqKBMF3G3G | df1a504c1321f580d748c4740778cd3a9bd74167fb5aa5703488216d150ed3df | —/— | —/— | —/— | —/— | UNCHANGED |
| 5dRHKSymMTTx64YmtdjDqeqt2PPt5MTaTSthToDD94NW | e0215603d63fa2a26b6ac655a4674f98c148a4145a3fb8b8b1fb51b04d46ba5e | —/— | —/— | —/— | —/— | UNCHANGED |
| A71Uf3jwg57fNedSao9eFwm9eKSLYFbVJ85T4fuXpump | e184302bf803a368abe060f52d1cb5ec30065ad71013cb7f92fa78df36391a6a | —/— | —/— | —/— | —/— | UNCHANGED |
| H4scGEd64jRY67EcDmEK9XuMnBbkkE2tNtFM2Ni3pump | e1877a04a2e2bad5dc68e9b884a08745ac3d4707eb259595a58fb8a7dc2d676d | —/— | —/— | —/— | —/— | UNCHANGED |
| Hg5Ja55T5wESq4vyFoiVCMeHXtGyVA69X2UHq8hgpump | e57a62bc18f585c017980d325b667b54d70d8afbcc7598b2a3357d18bbe9d33e | —/— | —/— | —/— | —/— | UNCHANGED |
| 7XiFJgX4nkER8gTH1LXUX1VEBJrLRSZfFXuzDy8ccWGT | e623d9b9961bef5fb98eb1a2cef0aecc9b14b7dc4cc56c2dd36aa073eed05d2b | —/— | —/— | —/— | —/— | UNCHANGED |
| HYH6YQjX2Y9B1qLkQUYXeqbxVTsCA11nYzXAC8pcxVud | e71e60807788badd7764c0223c2af3d867a4ca151ec8d1ac257770a48715b298 | —/— | —/— | —/— | —/— | UNCHANGED |
| A9AHYeqb7nQk7LZUraw7rBCzYRjy2DRvE6NqWfFHKRdH | e752ec2111ea1cab508805988116c42e8bdaeafdba3ab50a077fabc769b780c0 | —/— | —/— | —/— | —/— | UNCHANGED |
| 8TSUhXRhpEFtUVfDFAQdYCwgp2mEbs2jQk7tAYc1pump | e7589eb9c63114fecd8d513400f858aae48b0d389948a6306108276098d8399d | —/— | —/— | —/— | —/— | UNCHANGED |
| 98kfF7rmsg1QDUEoCqNE7g7M1FdrTt92TEp2CLzypump | e8023ff4c14194e30ad8757c0a0b96ae376c17d8bdf4978c7acd5511604e55b3 | 1790452140/— | 1790452140/— | 1790452140/1790457075 | 1790452140/1790457075 | ROLLING_RECOVERS_SIGNAL |
| 7Gh4XxuvvMLxxmryEFLAPkeuzrSTEB71eF9jx9FXQi3S | e86124ada3ce76321ac9f848e17a5c70587cf3f05f6daee845cb3bd421e00636 | —/— | —/— | —/— | —/— | UNCHANGED |
| 9GyRGm8GGmRZyyQ2hEnazDvCSV8mXiMAHmjKwVHMvVpo | eaaaef49b5eafe77eeed49771480ba4ee24a47422f667b4676d7e66192b098d2 | —/— | —/— | —/— | —/— | UNCHANGED |
| 3RLe3pfHSv2KpPTzPmS4hLzWyjPSCXhP3ZaFQ7Rxi18j | eb4270c9f3976a1d8105412e62bb883a13494474f30811ab2bc679c583566be1 | —/— | —/— | —/— | —/— | UNCHANGED |
| 95pCcNPexz8rg1Sazi2GscfAGSFy3NXSPDL9TdEMZE2V | eb9c79dc0bd5e526ff3dad278eeb51efae6c98759376faa728c0ed47bef5e351 | —/— | —/— | —/— | —/— | UNCHANGED |
| Hg5Ja55T5wESq4vyFoiVCMeHXtGyVA69X2UHq8hgpump | ecbae1d4c22018a95ec41f9517a9645229a9873eff719e06d745ec18edac217f | 1789404327/1789410540 | 1789404327/1789410540 | 1789404327/1789410540 | 1789404327/1789410540 | UNCHANGED |
| 6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx | ed4e4398ce0f05b838084b443803aaeb7a7231873186cf9b6503ba1b0403d94c | 1788661771/1788668315 | 1788661718/— | 1788661771/1788668315 | 1788661718/1788668315 | COMPLEX_REMOVES_SIGNAL_VIA_HFT |
| GNq9jVow6MayA3xM2AfGygh58gMu1vY6wajiXDXZCZu | f335885ea2e1fdf573a45a206578f30fd266418fce4df40673350d675bece8b8 | —/— | —/— | —/— | —/— | UNCHANGED |
| CbyTNf7UPzvewHh4Zp6umogM2RWahhmGRJWLJnPwpump | f43db920fcd727592ab4f260ec4603903e3baa0123524a14400de05c7ace7d87 | —/— | —/— | —/— | —/— | UNCHANGED |
| CRnmkD9UwUdMGNftBmE4DrFqKZ5NVi5ACDA4hQjwpump | f44dbc54e8736722cc3e0e1d28b3ab13656611aa444346f6418c6a3a62a47bb2 | —/— | —/— | —/— | —/— | UNCHANGED |
| HoK7vodcoVYQepStM1dDVyX5iMp2q5narY9bammuGPpe | f6f97a3f63065379117aa568c133c94b49cce9958e84d015e4be7fe94cd79709 | —/— | —/— | —/— | —/— | UNCHANGED |
| 5Zspimi8VD6LctJLtaSjLqaSUvmh3Rs849iPtGocpump | f744c701890334377a2e9b9acd825a189767abbd488f96b8af611aae09af1600 | —/— | —/— | —/— | —/— | UNCHANGED |
| CGEDT9QZDvvH5GmVkWJH2BXiMJqMJySC9ihWyr7Spump | f834e6a5a1607b88c31089fac2f91383d9cc6d53327bf45bf086d00aa58a6e31 | —/— | —/— | —/— | —/— | UNCHANGED |
| ZesMGYmokFiEuDvNzWeMhB7jxF6eUW8c512vwSKSTNK | f8e199c377a66158ef4d57d82ba2c7dd0baf564d384ecf5730e752a80a4d9433 | —/— | —/— | —/— | —/— | UNCHANGED |
| HxQhDGYqyjorgogMJx7YbBHADEDxuHhLnMMmr6VYpyn | f8ec981c05886e0f9d8a79dc76fabc7ac2ff957d4ef693bbce885b47cec28002 | —/— | —/— | —/— | —/— | UNCHANGED |
| B2or5WpZMW1MYzKqyicAzXTpgb6Rp4Bsc9vkRxn5LiDN | f9678e363ac7fc35bb9319ff165c1df2d9ca1d8ee3385bc16ec87d74207dbfb9 | —/— | —/— | —/— | —/— | UNCHANGED |
| 4i5FqkfYDAPcEVcXyuVyaaBcz3bpwJPqDkmaF36kpump | fb8c624036044de9e2c1fe3539366528c3968f97f42659827958a973b4c94500 | —/— | —/— | —/— | —/— | UNCHANGED |
| 7uvLyn87LSxW2GdwdEeiwmSJwQLVrcVyo7SRVcLbbtGc | fc607694d3632832ab0ec2bcab4feba5258eda619fae7ff4cb1759928127eed4 | —/— | —/— | —/— | —/— | UNCHANGED |
| A9AHYeqb7nQk7LZUraw7rBCzYRjy2DRvE6NqWfFHKRdH | fe4b6f8a3fb9e89f09ea05a126df8f0bc167b6c239290bf0614359e9d829411f | —/— | —/— | —/— | —/— | UNCHANGED |
| B5vZ3sppLppLfnurc19JBphtgJijdX18LYfc36xCeUWW | ffdca895328965971d2c760ca4760c4187d9c9b90a0db87752b4bbf8d270d311 | —/— | —/— | —/— | —/— | UNCHANGED |

## Appendix: every OOS episode identity matrix

| Mint | Episode ID | J0 ACC/MULT | J1 ACC/MULT | J2 ACC/MULT | J3 ACC/MULT |
|---|---|---|---|---|---|
| 4mkNDiEALDutn8Py1GmJnvVuTdHVuL9y6AmcL9KTZx7F | 1518bb172ba9430b09a7bfb316d247410ff6b727843837af0fff101bee0a53c9 | —/— | —/— | —/— | —/— |
| 9bsHPggRK5Drw8sR7QBcx5pXrHH7Mc6haLmiR2d7aY2a | 165317cd565363ac2b190319f3c4a2b823e5671e8c57ebbb1c1d8f3c97115e4b | —/— | —/— | —/— | —/— |
| H7TuvDxEKygh27zGfGcjKG8JGWgrbyKpPtvJEpGosfas | 2bd008481bd7bc8e2d0ef1c46959743dbb90191f1c96977ef68a64caaabda964 | —/— | —/— | —/— | —/— |
| 7Xgc5RacHtGzfhw2HukUBk5V986yBbvshr7rrCoopump | 33f6c6d811ae8083e5f27153195598afe6b6bd2c31b1d05560953895698e78af | —/— | —/— | —/— | —/— |
| CbcyNo7m1amFWqEQm2m4PLv1UNvpcL3C1Ujm6AkzpKoU | 67cc89159cf58f18347ea37b6aaf85fee73522a29b4cb3017d70e2060947648b | —/— | —/— | —/— | —/— |
| BXoHJddsWJLHtAopeiSbKUSELsu8hSFMs8baGMDkpump | ad9cb81da4e6a527da96bc630e43a95a75d2f508c301531bd3e53ad4e8af2a29 | —/— | —/— | —/— | —/— |
| 2AVjqmGbMqg7rSyHVv2deVdggsBgBtu1Bi69BUvE5WRv | c680656476ac1632b7576ecde322eb0e045e04661d83b585a04c5a8da402c1ee | —/— | —/— | —/— | —/— |
| 7VertkgF9KLhxxJXHX6uaWuoYZTP9LdGj2bWmVXVpump | cc83c4825134e955929eaa6522cfa7a6c499952d1a90fd262df51fe7ace67753 | 1791044803/— | 1791044803/— | 1791044803/1791048540 | 1791044803/1791048540 |
| 9dSMwFfPezQ8WPcW1uZV7ns4rcviEj2LssSAg75WBLXd | ce8a1aad00847b7290d3e7c15886e5a490172868f6a4309399db3e0c3b0d9615 | —/— | —/— | —/— | —/— |
| 9fJAWKQpkY93hfuZxrHfh5wEh2AV9vjkWNQfzfbziHd2 | d3cbbb683af1ec155b10ac75679fea695fb644b9c8347570bd27e347f7eb8787 | —/— | —/— | —/— | —/— |
| 2AVjqmGbMqg7rSyHVv2deVdggsBgBtu1Bi69BUvE5WRv | e40d82f5b628c4641397ef518c98c7b42d90ca6fc70af8cebd5ee23a8574cc2f | —/— | —/— | —/— | —/— |
| 3Dgwn5E7H5a8k6iGrz3qirkaJqUaJrKHEZ2xPcLRpump | f0462a1c0cedecb8463de12a0ae5e9fe48c052b5ec9408ef51f5febecb770317 | —/— | —/— | —/— | —/— |
| GTBxUiw6wJdmmkCGZgRHLyYxqu1vG4KtRpeox6yDpump | f87158c1918cd37a74bbb51351f419cd3620313e6bbed3ce37c0049e711008ba | —/— | —/— | —/— | —/— |

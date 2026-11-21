# [B] 首项后端交付：完整索引流水范围、分页与筛选

代码固定 `7bc564b074aa1fe87d809883d0d1364194a92562`；父审计提交 `bcfc28e3233e9b34965183e049af4be7410c56b5`，原产品基线ee81。本轮只改后端、测试和离线复核脚本，没有改页面，没有本地部署。整体59项清单的baseline状态保留；本页记录首项实际增量。

## 行为变化

原API仅1/7天，30/all实际HTTP400；D1默认最多5000，满窗失败。新代码支持1/7/30/all完整本地索引范围，默认无总行数截断，旧1/7完整响应兼容。显式`max_rows`诊断调用仍可自行要求失败保护，不是默认查询总配额。

相同`/api/frank-signed-activity`增加`limit/cursor/kind/mint`：limit只控制单次响应容量，可反复取到结束，不限制历史总量。稳定排序为事件时间及本地行ID；游标固定查询截止时刻、来源文件身份、过滤条件和初始rowid上界，新追加/回填记录不挤入原分页。已有行可能被源写入者更新，明确不是冻结数据库快照，不承诺跨页更新不可见。游标是查询定位信息，不是权限或完整性信任根。

Mint筛选包含源交易腿及钱包本人所属的余额明细，排除同交易中其他钱包资产。BUY/SELL筛选要求源分类ACTIVE_TRADE及对应腿，保留交易的全部腿，不把签名数当买入腿数。来源字段增加wallet/slot/首次索引时点/raw哈希/解析版本/钱包Mint，原始私有路径和RPC URL不输出；缺来源字段仍null。原MATCHED_OR_NOT_APPLICABLE保留兼容，新增字段分清MATCHED与NOT_APPLICABLE。

示例只读GET（需在采用本代码的隔离Handler或未来安装版使用，当前8766仍旧ee81）：

```text
/api/frank-signed-activity?days=30
/api/frank-signed-activity?days=all&limit=137
/api/frank-signed-activity?days=all&limit=137&cursor=<previous-next_cursor>
/api/frank-signed-activity?days=all&kind=BUY&limit=100
/api/frank-signed-activity?days=all&mint=<exact-Mint>&limit=100
```

无效参数/游标400；来源文件被替换后游标409，调用方须明确重新开始读取；不触发来源扫描/POST。

## 实际验收

固定代码161 Python通过/1.09秒/socket0，含强制实际Git捕获1720签名/224Mint回归；212 Node通过，无失败/跳过。新增用例包括5103行跨旧限制、同时间分页、分页期间追加旧时间记录、跨来源/过滤游标拒绝、对方账户Mint不混入、无时间戳、其他人物和未来事件隔离、来源字段及实际Handler分发。初次合成测试因测试签名编码碰撞1失败/24通过，修正fixture后25通过，最终固定源码重新运行161通过。

私有一致快照SHA256 `98d27fe8d8cad983bf91fc6eaf4141efac7fa8659ca5c6cb1b8f8409cb7afb05`，8697签名/197交易行/76交易Mint。as-of固定1794724251：1天319条/3页，7天1850/14页，30天5772/43页，全部8697/64页（每页137）。全部76个交易Mint逐个过滤与独立Python解析源行的所属Mint集合相符，6类过滤检查通过；各范围与独立SQL集合完全一致，无丢失/重复，原文件哈希不变，socket0，实际Handler分发PASS。总复核19.18秒。

这证明本地索引后端能力，未重新验证底层链上分类，不是76个CA的完整链上查询，也不证明全链历史、当前余额、PnL、收益或通知送达。当前安装版尚未切换，当前余额/行情、多CA深度/冷查询等主线仍待推进。

Python实际由禁网审计入口调用pytest.main，完整参数、环境与退出码见机器回执；以下为实际Node及捕获复核脚本命令（私有路径用变量代称）：

```sh
node --test tests/test_frank_ca_get_resume.mjs tests/test_frank_ca_report_render.mjs tests/test_frank_d2_ingress_ui.mjs tests/test_frank_ca_rpc_budget_ui.mjs
python -B scripts/frank_indexed_activity_audit.py --agent "$FRANK_AGENT" --expected-sha 7bc564b074aa1fe87d809883d0d1364194a92562 --snapshot "$FRANK_PRIVATE_INDEX_SNAPSHOT" --as-of 1794724251 --summary "$FRANK_AUDIT_SUMMARY"
```

完整脱敏回执见[acceptance-20261115.json](acceptance-20261115.json)。未发RPC/CA、未修改生产库/通知/Scanner/Loop/端口、未合并或部署。后续先新鲜完整钱包余额和市场接线，再按代表CA矩阵验证整体功能，不回到CRAWL单样本循环。

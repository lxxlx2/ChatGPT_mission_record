# Monster — Publisher HTTP redirect P2 限域失败的定向修复冻结（2026-10-19）

## 事实与阻断范围

其他AI Codex 用户提交的固定 SHA 审核 `REQUEST_CHANGES`：
- 固定审核代码 `e6fb680b868d52a9a0d77d80920b6049fa36252d`；比较基线 `f557780d9ad4ea27a69b1bebe7c9c67065790b5d`；独立 Codex 底层精确模型 `UNVERIFIED`。
- 仅1项可复现P2：`monster_v4_forward_spot511_official_publisher_acquire.py:fetch_one_url` 使用标准 `urllib.request.urlopen()`，在调用 `response.geturl()` 前已自动访问HTTP 302的非发行方目标，违背只读HTTP仅允许发往官方数据地址的协议。
- 审核方实际用两台本地 HTTP 服务器证明：来源302跳转到非官方地址后，虽然函数最后报错，目标服务已收到一次GET。旧代码网络边界不能通过审查。
- 审核者**独立核验原1533份ZIP/CHECKSUM及2207520行真实1m数据全部通过**；该P2不废除来源真实性，但采集器软件 `REVIEW=REQUEST_CHANGES`，不可写已APPROVE。

## 冻结修复及验证范围

唯一修复：让Python urllib `HTTPRedirectHandler` 的 `redirect_request()` 在构造/发出任何第二请求**之前**立即以明确异常拒绝301/302/303/307/308等HTTP redirect；使用 `build_opener(RejectRedirectHandler)` 的 `.open()` 替换自动跟随的 `urlopen()`，保留原 `response.geturl()==originalURL` 二次校验。**不改变源官方域名/名单、原始HTTP SHA/CSV校验、Unicode percent encoding、请求次数/大小/并发/重试、404和错误source的统计**。

必须以真实本机HTTP两个`ThreadingHTTPServer`启动允许来源和被拒绝目标，用未模拟的 `fetch_one_url(url)` 访问允许服务器302，断言：
1. 允许服务器确实看到首个请求，**第二台目标服务器GET数严格为0**；
2. 抛出明确`PUBLISHER_REDIRECT_BLOCKED_BEFORE_FOLLOW`，不得接受假源；
3. 额外测试允许源200正常成功，保持正常主链路可用；
4. 旧10项pytest/unittest的官方ZIP+CHECKSUM、511 population、4 Unicode、原源不可覆写测试不退化；
5. **禁止**为跑定向修复CI重新采集1,533份已经经过独立核验的原档案。新增单次push-only workflow只触发自身路径，不带下载任务，不设schedule/cron/Gmail/Mac/Frank/交易。需要CI原始日志并钉死实际修复 SHA，再以固定SHA和本P2范围回请独立AI复审。

研究证据仍保留：
- [真实三日1533完整publisher来源证明](evidence/monster_forward_spot511_oct16_18_1533_actual_issuer_source_reconciled_v1.json)；
- [原报告](MONSTER_FORWARD_SPOT511_20261016_18_TRUE_PUBLISHER_FIRST_OOS_RESULTS_20261019.md)。
- 不触碰已审Stage165/166、300U历史有限现金、原D0/D1或七日OOS主线阈值。新2026-10 Spot 7日仍不成熟；真实timestamp级ticker24、上市变动、L2、可执行净利润均`UNVERIFIED`，不能放宽交易门禁。

`G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

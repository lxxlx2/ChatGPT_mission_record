# Issue #165：一次性新双 Program owner finalized 原始证据采集

**FRESH_DUAL_PROGRAM_SOURCE_REPLAY_VERIFIED_DATED**

依据[有条件授权 #6362854245](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6362854245)，先核实 Mac 实际密钥与真实套餐/免费额度后，实际只发 **2次** RPC，均成功。随后使用固定PR60代码零网络回放成功。没有生产导入或持仓功能部署。

## 零额外费用前置门禁：实际 Mac 账户，不以连接器团队统计替代

- 读取本机既有HTTPS配置，host为 `solana-mainnet.g.alchemy.com`，唯一配置条目；未新增key或换源。
- 使用已登录Mac浏览器实际应用控制台，将页面完整API key在只读DOM中计算SHA256，与本地实际key的SHA256核对一致，仅输出布尔值；不是只比较hostname或掩码后缀。实际匹配应用为 ChatGPT Crypto Monitor All Chains（app ID `h6m5pairkgzet7vz`），团队身份已本地核验；不发布key、key指纹、邮箱、付款信息或私有URL。
- 执行前重新读回真实 Billing：**Active Plan: Free**；月上限 **30,000,000 CU**；已用 **1,663,912 CU**，剩余 **28,336,088 CU**；PAYG未启用。
- “Set limit”打开的是“Upgrade to Pay As You Go with Spending Limit”升级/付款面板，而不是已启用的付费超额账户；只查看后关闭，未提交升级、未添加付款方式、未更改任何计费设置。保持Free月度上限，付费用量需另行升级；本次没有启用任何超额付费路径。
- [官方方法价表](https://www.alchemy.com/docs/reference/compute-unit-costs)列出 `getTokenAccountsByOwner=10 CU`；实际2次按公布方法费率为 **20 CU**，远低于已核实剩余免费额度。该次额外收费 **$0**，没有购买额度或套餐。[官方套餐说明](https://www.alchemy.com/docs/reference/pricing-plans)区分Free 30M和PAYG计费。
- 这是方法费率计算的20 CU，**不是**独立账单计量回执；没有用额外RPC核算计费。原后台仍正常运行，不能把整个账户后续用量变化全部归到本次2次请求。
- 连接器usage summary返回70,466 CU/$0、截至10:30Z；真实Mac Billing稍后为上述1,663,912 CU。两者口径/时点不一致，**没有用70,466数字作为额度或实际key归属的证明**，门禁依据为完整key匹配后的真实Mac Billing/Usage。

## 固定执行代码与严格停止器

PR60固定SHA **`e4529ba7069e5499d12323a7160ceac08c481fae`**；独立detached checkout，执行前确认PR60 HEAD一致、checkout无补丁。使用原始 `_wire_rpc`、`_load_verified_reply`、`collect_owner_full_receipts`、`replay_owner_full_receipts`，没有改审核源码。

独立临时外层执行器：

1. 验证实际key未变、Free费用门禁未过期、owner来自固定Frank registry。
2. 一次性 exclusive latch，已启动的授权运行不能重入。
3. 传输前累计调用数；第2条仅在第1条完整原始字节、HTTP/JSON/owner/program/账户/slot验证成功后放行。使用PR60原始完整验证函数先验证再向采集器返回，失败抛出不被原采集器普通异常catch吞掉的终止信号，防止原collector继续第二条。
4. 固定官方program顺序；第2条minContextSlot必须等于第1条slot；任何情况下禁止第三条，禁止重试/备用源。
5. 原始transport每条timeout25s、上限12,000,000 bytes，拒绝重定向/HTTP错误/歧义framing/长度不符/截断/超限。实际两条均约0.5秒内返回，远未达上限。

执行前离线测试 **9/9 PASS、真实RPC=0**：transport error、bad JSON、RPC error、wrong ID、missing context、owner mismatch、program mismatch、duplicate account全部证明只有第一条模拟调用、无第二条；另验证双成功顺序/minContextSlot与第三条拒绝。初始离线临时目录受Mac `/tmp` symlink门禁拒绝，改为真实resolved路径后通过；无真实请求被用作测试或探针。

## 实际请求与回执

方法均 `getTokenAccountsByOwner`，owner为已注册Frank钱包，无Mint过滤，`encoding=jsonParsed, commitment=finalized`。

|序号|program|请求开始UTC|完整响应到达UTC|finalized slot|账户数|原始字节|
|---|---|---|---|---:|---:|---:|
|1|SPL Token|2026-10-23T14:46:32.788099+00:00|2026-10-23T14:46:33.226647+00:00|460482174|1875|994150|
|2|Token-2022|2026-10-23T14:46:33.285807+00:00|2026-10-23T14:46:33.773530+00:00|460482176|2273|1326616|

第2条 `minContextSlot=460482174`。两program上下文slot相差2，**same_slot_atomic=false**；不能宣称一个共同slot的原子钱包快照。采集和回放完成于 `2026-10-23T14:46:34.008872+00:00`（曼谷2026-10-23 21:46:34）。

- SPL原始响应SHA256：`f77120c050a6d014dd53d41fd9d0e8392f34ab31b91155bfa30e18334ab3b682`
- Token-2022原始响应SHA256：`a327bf34f0e5bf10994662e937704d74098464cc5fddeb2ab4ce77e9ac2c58c2`
- manifest SHA256：`f06df53ccfb8b96e1b92f428620311cf62bd6bb44f9b83fd7e126f2ee5b1f88b`
- capture指纹：`016b99ff42c3b155316bd46bec5850ff9dbfb9437bbfd5c3c28414d58fef4f08`

**实际调用2／验证成功2；无重试、无备用RPC、无额外探测请求。** 共4,148账户、4,148不同Mint，3,275 Mint非零。账户数量不等于主动买入数，不证明这些token有市价或可出售。

PR60初次回放通过后，进一步在socket连接被阻止的审计进程中独立回放，结果逐字段一致，原始文件hash未变。全部原始字节、完整账户/Mint/raw/decimals及私有执行记录保留本机专属0700目录，文件0600。**GitHub不上传raw、账户pubkey或全账户明细**。

## 相比2026-10-17历史组

旧组记录时间 `2026-10-17T22:19:21.466690+00:00`，独立slots458199733/458199735。

|指标|旧组|本次|
|---|---:|---:|
|账户数 / 不同Mint数|3,548 / 3,548|4,148 / 4,148|
|非零Mint|2,680|3,275|
|相对旧组新增账户|—|601|
|旧组账户本次不再返回|—|1|
|两组共同账户|—|3,547|
|共同账户raw变化|—|15|
|共同账户decimals变化|—|0|
|目标32非零 / 零|8 / 24|8 / 24|
|目标32 raw变化|—|2|

未返回的旧账户仅表示本次完整program响应不包含它；未追加链上查询解释关闭/迁移原因，不把差异自动解释为买卖或清仓。也不将新增账户等同新主动建仓。

## 目标32：按Mint汇总的脱敏变化（非账户明细）

32/32均有账户记录，无缺失账户行；数量以raw整数记录，未用浮点余额。下表仅公开Mint SHA256前12位和该Mint汇总，不公开账户地址。

|Mint哈希前缀|旧raw|新raw|raw差额|decimals|本次slot|
|---|---:|---:|---:|---:|---:|
|`5e83acc43c03`|0|0|0|6|460482174|
|`f3e91760ad21`|0|0|0|9|460482174|
|`2980a1f1bcd7`|0|0|0|6|460482174|
|`42370c25ac86`|0|0|0|6|460482176|
|`c70d3f501219`|7263953506555|7263953506555|0|6|460482176|
|`3767258429ec`|0|0|0|6|460482176|
|`d527f0555369`|0|0|0|6|460482174|
|`f12b8928ba72`|0|0|0|6|460482176|
|`eab478af01ca`|22246999|22246999|0|6|460482176|
|`8e68a07f56a3`|29551841|29551841|0|6|460482176|
|`cdf80fe14d81`|0|0|0|6|460482176|
|`a422964cc1ea`|0|0|0|6|460482176|
|`1bf7ae1570ed`|0|0|0|6|460482176|
|`6c61a8e69f81`|12043213758361|12043213758361|0|6|460482176|
|`627ac0f2a75c`|0|0|0|6|460482176|
|`7175dcb95b38`|0|0|0|6|460482176|
|`039455d3cdd1`|0|1062360522|1062360522|9|460482174|
|`9e040ad5ed06`|52736752|0|-52736752|6|460482176|
|`dfd42fb00c17`|0|0|0|6|460482176|
|`88fad0dfe522`|0|0|0|6|460482176|
|`7e834b723ba7`|0|0|0|6|460482176|
|`b893d3daa499`|9090666|9090666|0|6|460482176|
|`1032be2a4eb8`|0|0|0|6|460482176|
|`e225a43e974d`|50017498|50017498|0|6|460482176|
|`c80ba527afdb`|0|0|0|6|460482176|
|`36aa002a6fdf`|0|0|0|6|460482176|
|`0b877749a3f8`|3411999978741|3411999978741|0|6|460482176|
|`2b2a4c3dafcf`|0|0|0|6|460482176|
|`9bdd899388ae`|0|0|0|6|460482176|
|`432c049d3cd0`|0|0|0|6|460482176|
|`142e500c3320`|0|0|0|6|460482174|
|`06a4ac1b17c1`|0|0|0|6|460482174|

## 边界与停止

本证据只支持 **BALANCE_AT_OBSERVED_FINALIZED_SLOTS**，不是永久当前余额、同slot原子portfolio、native SOL、完整交易历史、估值、利润、可卖性或全钱包产品验收。精确账户明细仅存本地，报告未泄露RPC凭据。

没有Sidecar/生产数据库导入、Dashboard/V1/MC Loop重启或部署、策略变更、CA POST、额外RPC、通知/邮件、交易/签名、merge或新定时任务。生产 `SNAPSHOT_NOT_PRESENT` 不因本次采集自动改变；本轮没有向生产导入该源。

**一次性采集完成后停止。不自动开始D2产品集成或部署。**

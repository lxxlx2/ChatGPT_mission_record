# Monster 一次性Mac公共RPC历史Factory探针：独立AI审查包（2026-10-19）

请在固定Git SHA 812fe2ba9103d40246ae4f13cbfc6f8e02b32ede 审核 GitHub https://github.com/lxxlx2/ChatGPT_mission_record 的 Draft PR #30，research/monster-v4-local-discovery-20261010 分支。对比旧提交5555960c98e7a52a64b3e68a2f100a0ab9aacb2a。此审查只包含新的一次性只读RPC脚本及6项离线回归、原探针合同新增条款；不要拿后续PR HEAD代替固定SHA。

核对三个文件：
- crypto-300-profit-mission/local-agent/scripts/monster_early_venue_factory_rpc_roster_probe.py
- crypto-300-profit-mission/local-agent/tests/test_monster_early_venue_factory_rpc_roster_probe.py
- crypto-300-profit-mission/monster/MONSTER_EARLY_VENUE_30_PIT_SOURCE_PROBE_BUDGET_AND_STOP_20261019.md

研究缘由：历史CEX动量原策略不能证明正期望；新的30例先检查历史真实可交易来源。当前连接器受阻，不可称链上历史数据不存在。作者实际调用Alchemy Base免费2000块eth_getLogs收到“最多10块”错误；Blockscout Base 402额度不足；BSC未支持该连接器。BNB Chain官方文档明确其列出的公用主网RPC禁用eth_getLogs。Base RPC限速。此代码默认只在用户Mac前台手动执行能力探针，不安装常驻任务，不调用账号签名/交易。没有30个项目母体、没有真实Mac源回执、没有新盈利策略、尚未开展外部独立AI代码审查。作者只完成离线synthetic 6/6，非GitHub CI。

请实际执行：python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_early_venue_factory_rpc_roster_probe.py，并记录完整退出码。独立检查：
1. Base8453及BSC56 chain ID；Uniswap V3 PoolCreated与Pancake V2 PairCreated工厂地址、topic0、indexed token0/token1、pool数据字布局以及区块/交易/日志排序。历史UTC时间二分是否严格形成全日连续闭区间。
2. 按固定源顺序抽30个互异CA，过滤是事前报价资产池匹配而不是按未来涨幅找赢家；创建Pool本身绝不是流动性、Swap、代币新部署或可买卖D2证明。
3. probe模式只能测试2000与10区块，不可报告整日覆盖；scan需完整连续Factory原始响应，分段raw字节SHA256与完整manifest，断点续跑防缺口/重叠/跨chain/错误source；提供篡改、网络拒绝、HTTP429、来源限额、错时钟、错链、空结果/部分覆盖的反例。最大requests超额只能PARTIAL、NOT_SCORABLE，不能创造0/30。
4. 只允许读取eth_chainId、eth_blockNumber、eth_getBlockByNumber、eth_getLogs，无实盘、钱包签名、Mac服务、Frank、schedule或Gmail。API key不能因日志或输出泄漏；响应SHA只保证本地字节未被更改，不等于RPC独立真实性证明。
5. 历史入口标签按部署、DEX池+Mint/Swap+同刻容量、Alpha、USD-M、Spot区分。合同预冻结Base 0.5 WETH/1000 USDC及BSC 2 WBNB/1000 USDT可观察首小时池报价侧初步准入门槛，不是用户授权金额，也不保证真成交。未满足、缺源、后来归零的样本必须留在分母；门槛可见时间不能倒填至池创建时点。
6. 不要重审原1533官方Issuer数据或518轮已批准的旧策略研究。固定SHA并没有产品G0-G6通过或真实利润，Mac本地联网必须等真实设备输出才可声称。

请返回APPROVE / REQUEST_CHANGES / BLOCKED、固定审核SHA和比较基线、模型真实版本或UNVERIFIED、实际运行命令及退出码、发现的P0/P1/P2对应代码行和可复现反例、必要最小修复与剩余限制。即使APPROVE也只涵盖新只读研究源工具，不批准实盘、自动通知、部署、合并。NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE继续，PR保持Draft，G0 PARTIAL、G4 UNKNOWN、G6 NO_GO。

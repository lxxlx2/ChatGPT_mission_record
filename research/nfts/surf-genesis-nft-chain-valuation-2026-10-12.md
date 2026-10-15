# Surf / SurfBoards Genesis NFT 链上候选、发行进度与 Kaito 估值对比（2026-10-12）

更新日期：2026-10-15（第 9 节为当前 SurfBoard 链上事实，覆盖前面待交付状态；早期章节属于历史快照）。独立核查，优先官方与链上；未将历史聊天结论当作证据。区分官方确认、链上事实、推断及情景估值。

## 1. SurfBoards 官方 NFT 站最新状态

官方入口：https://nft.asksurf.ai/
Surf 官方主站：https://asksurf.ai/

- 官方 NFT 站标题 `The Genesis of Surf`，称 `SurfBoards` 是 Surf 生态的 original assets。
- 页面显示 `Trading and member claims open in ...` 的动态倒计时；2026-10-12 查看到约 2 天 13 小时。此数字会变化，不视为保证的铸造/认领时刻。
- 页上写 `Earning` 并展示 SPY、NVDA、SPCX、META、GOOGL；这是项目展示的方向，尚未找到每枚 NFT 可分到多少股票代币、分配周期、来源、领取条件或智能合约保证。不得解读成已经实现收益、持有即自动分红。
- **2026-10-13 官方首页已明确给出计划总量 6,666 SurfBoards**；尚未找到正式 CA 白名单、实际可卖地板与每枚股票代币的分配明细。
- Surf 官网将其链接为 `Surf’s Genesis NFT`。

证据：https://nft.asksurf.ai/ ； https://asksurf.ai/

## 2. NFT 在什么链：核查层级

**2026-10-13 已在 Robinhood Chain 4663 实际核查 NFT/ERC20 相关合约、Uniswap v4 交互及同一 NFT ID 的销毁再铸造；链上 tokenURI 指向 Surf 官方 metadata 子域。官方最终 CA 白名单仍未核实，第 7 节给出证据。**

链上使用 Blockscout 查询 4663 链上的 `SurfBoard` 名称（2026-10-12）：

| 地址 | 链上名称 / 标准 | 首次部署时间 UTC | 持有地址数（查询时） | 核实结论 |
|---|---|---|---:|---|
| `0x6A044021bb41f4B06193cA9B42946c20918aA4f3` | SurfBoard / SURFBOARD / ERC-721 | 2026-09-30 12:46:45 | 200 | 合约真实存在、未验证源码；**未确认由官方发行** |
| `0xf5a24bd9648f180E306B57bb5B2349bb7908C28` | **无效地址** | 未验证 | 未验证 | **此字符串仅 41 个字符（含 0x），无法构成合法 EVM 地址，旧报告错误，作废** |

两份合约的创建者不同，且搜索结果同时含同名 ERC-20；**仅名称相似不能排除冒牌合约或独立 collection**。任何 mint/买卖/授权都必须待 Surf 官方明确给出 CA 后验证。
- 第一份部署者：`0x110b550faDBe13ceC30f75199e1aad7c3f056A2c`，implementation `0x3cB802dCeDd7A9d016c8b0CeB2a2FFa8a3a93171`，未验证。
- 旧记录的第二份部署者和 implementation 因原候选地址本身不合法，均**不再视为已核实链上事实**。
- Robinhood Chain 官方 https://docs.robinhood.com/chain/ 确认它是 Ethereum L2、gas 为 ETH。
- 一个第三方公开 X 帖子称 Surf NFT 在 Robinhood Chain 发放：https://x.com/LensMoso/status/2107001523733668208 ，这是**第三方口径而不是 Surf 官方证据**。
- 主网 Ethereum 和 Arbitrum 的名称搜索未发现可认证的 AskSurf 官方 NFT；**缺少搜到不能证明不存在**。
- 最终判断所需证据：`nft.asksurf.ai` 的真实 mint chainId / 合约地址或 Surf 官方 X/官网明确公告，配合区块浏览器交叉校验。

## 3. Surf 公司基本面：官方披露

- 2025-12-11 Surf 正式公告融资 **USD 15 million**，Pantera Capital 领投；Coinbase Ventures、Digital Currency Group 参与。新闻稿并未给出公司估值或 NFT 的利润分配权。
- 2025-12-11 公告称自当年 7 月起有 **80,000+ users**、**1,000,000+ research reports**，属于 Surf 官方口径，不等于订阅付费用户。
- 2026-05 Surf Research 2.0 文章提及其产品覆盖 **500,000+ users**（官方口径，口径不同未独立审计）；业务包括加密数据、金融市场 AI 研究、Studio、API/MCP、企业/机构研究产品。
- 2026 年与机构、交易所存在公开整合报道：2026-07 IOSG 官方案例称研究 Agent 已接入 Surf API；2026-09-01 Bithumb 官方联名案例显示 Surf 在 Bithumb app 为 **450+ KRW 交易对**提供 AI 研究分析。Surf 官方报告提到 500M+ 数据点、2.5M 推理/校验任务、750K+ 结构化输出，这些数字是**项目方生产指标，不是审计过的公司收入**；**Bithumb 的 8M+ 注册用户和 2M 日活并非 Surf 独立用户**。
- 无审计收入/利润、付费转化率、留存和 NFT 资产负债支持数据，不能凭 $15M 融资推算 NFT 权益价值。

证据：https://asksurf.ai/blog/en/surf-raises-15m-to-scale-the-first-ai-model-purpose-built-for-digital-assets
官网：https://asksurf.ai/ ; 近期更新：https://asksurf.ai/blog

## 4. Kaito 同阶段历史演进与 SURF Genesis 峰值情景（2026-10-12 修订）

**估值框架纠错：研究 Surf pre-token / Genesis NFT 时，应将 Kaito 2024-12 发行至 2025-02 TGE 前后的价格形成过程、投机峰值与空投兑现后回撤作为主对照，不应以 2026-10 Kaito 接近 0.1 ETH 的成熟衰退阶段地板作为 Surf 的主要增长空间基准。下述数值是情景模拟，绝非 Surf 的实际报价、保底价值或预言。**

### 历史同阶段事实与强度

- **Kaito Genesis 铸造：** OpenSea 原始 Mint 页面记录 allowlist 2024-12-20、二阶段 12-22、公售 12-24 至 12-25；共 **1,500** 枚，2024-12 阶段 Mint 参考 **0.1 ETH/枚**（Mint UI 当前美元换算是随 ETH 变动的，不应将该页面 USD 值当作 2024-12 实收 USD）。
- **KAITO TGE：** XT 交易所官方公告与 The Block 2025-02-20 报道确认 KAITO 已开始领取/交易。2024-12-20 首轮 Mint 到 2025-02-20 TGE **约 62 天**，这一时间间隔是历史案例，不是对 Surf 的日历预测。
- **Kaito NFT TGE 热度峰值：** DappRadar 2025-03-06 发布的 2025-02 市场复盘记录 Genesis **7.65 ETH 地板历史高点**；此前叙述“一律不应用早期高点”不符合用户希望衡量峰值机会的投资研究目的。其他报道出现 **10.2 ETH、11.6 ETH、11.9399 ETH**，但采样、成交和时点互相冲突，尤其部分 CoinGecko/OpenSea 的 11.9399 ETH 报价源已经陈旧数月；**没有独立成交证据时不将更高报价当成可实现峰值**。
- **权益机制差异：** Kaito 持有人被纳入 2025-02 的 KAITO 空投分配，Kaito NFT 的高价反映当时空投预期、流通性和生态影响力；SURF 的 SPY/NVDA 等股票代币展示属于官方宣传，尚未验证每枚收益承诺，也尚未确认 SURF 代币 TGE。Kaito 的投机价格不能线性视为 Surf 的基本面公允价值。

历史证据：
- https://opensea.io/collection/kaito-genesis/overview?search%5BsortAscending%5D=true&search%5BsortBy%5D=UNIT_PRICE&search%5Btoggles%5D%5B0%5D=BUY_NOW&tab=items
- https://dappradar.com/blog/nft-winter-returns-market-shrinks-50-as-crypto-prices-fall
- https://xtsupport.zendesk.com/hc/en-us/articles/43707220957081-XT-Announcement-on-the-Initial-Listing-of-KAITO-KAITO
- https://www.theblock.co/news/ecosystems/2025-02-20-kaito-token-airdrop-claims-base-342379
- https://www.coingecko.com/en/nft/kaito-genesis

### 2026-10-13 供应量纠偏与同阶段峰值敏感性

Surf 官网确认系列总量为 **6,666**，此前 1,000/1,500/3,000/5,000/10,000 的假设供应行已过时。按 Kaito 历史地板峰值 7.65 ETH × 1,500 = 11,475 ETH，用 **情景假设 ETH=$2,700** 换算名义集合总价值约 $30,982,500。假设 Surf 达到这一集合峰值的 10%/25%/50%/100%，则按 6,666 平均分摊的单枚名义价格为 **$464.78 / $1,161.96 / $2,323.92 / $4,647.84**；相对 $228 成本约 **2.04× / 5.10× / 10.19× / 20.39×**。这些都是极强行情的条件压力测试，不是现货价格、发生概率或实际可成交收益。链上存在不同等级随机票据，**平均值无法替代 #691 实际等级估值**。

**研究分层**：
1. **筹备/初上市阶段：** 优先关注已确认交付、总量、官方成交和 bid 深度，市场价格尚未形成时只列成本和候选定价；Kaito 2024-12 的 0.1 ETH Mint 是历史起点。
2. **权益披露/上市后的早期发现：** 比较官方 NFT utility 和真实买盘、稀缺性，以 Kaito 从 0.1 ETH 起步并随热度上行的历史路径描述潜在重新定价，而不预设 Surf 一定复制。
3. **可能的代币/分发催化剂：** 仅在 SURF 正式确认 TGE、快照、allocation 和 claim 后才模拟空投贴现价值；Kaito 2025-02 的 7.65 ETH 是强行情**峰值压力测试**。
4. **权益兑现或失败后的回撤：** Kaito 2026-10 约 $240-$270 旧市场价属于这层的回撤尾部参照，应保留为极端下行情景，而非早期公平价锚。

**未解决的核心缺口：** SurfBoards 总量**已确认计划为 6,666**；尚缺实际铸造数量、团队/保留配额、每个 #691 的兑现条款、二级出价/成交、股票代币池的法律与实际资金来源、SURF 代币存在性及分配比例。融资 $15M 与公司用户数据能支持公司基础真实性，不能推算上述未知变量。

## 5. 来源和证据限制

- Surf NFT 官网：https://nft.asksurf.ai/
- Surf 官网：https://asksurf.ai/
- Surf 官方融资公告：https://asksurf.ai/blog/en/surf-raises-15m-to-scale-the-first-ai-model-purpose-built-for-digital-assets
- Surf × Bithumb 官方案例：https://asksurf.ai/blog/en/how-surf-built-korea-s-first-ai-centric-trading-experience-with-bithumb
- Surf × IOSG 官方案例：https://asksurf.ai/blog/en/announcing-our-system-design-partnership-with-iosg-ai-native-venture-capital-connecting-western-technology-and-asian-finance
- Kaito NFT OpenSea：https://opensea.io/collection/kaito-genesis/overview
- Robinhood Chain 官方文档：https://docs.robinhood.com/chain/
- 第三方 Surf NFT 链声明：https://x.com/LensMoso/status/2107001523733668208
- Blockscout 4663 candidate A: https://robinhoodchain.blockscout.com/address/0x6A044021bb41f4B06193cA9B42946c20918aA4f3 （Blockscout 官方 Robinhood Chain 主网浏览器）
- Blockscout 4663 candidate B: https://robinhoodchain.blockscout.com/address/0xf5a24bd9648f180E306B57bb5B2349bb7908C28 （Blockscout 官方 Robinhood Chain 主网浏览器）
- Kaito collection：在 OpenSea 官方 collection 页面核价（流动性、真实成交与挂单须区分）。

以上只包含公开资料，未包括用户钱包和私密信息。

## 6. 2026-10-12 #691 SurfBoards 已购买权益与链上交付状态（用户确认修正）

资料口径：Git `crypto-300-profit-mission/portfolio/current.md` 的 2026-10-12 状态，官方 Surf 页面及上述公开证据；这是一项**研究口径纠偏**，未操作钱包、监控、交易或自动化。

- Git 原始资产提交 [14ed597c8afcd2758b2766ea00991313dd7042e2](https://github.com/lxxlx2/ChatGPT_mission_record/commit/14ed597c8afcd2758b2766ea00991313dd7042e2) 记录：**2025-08-31 13:38** 通过 **DaimoPay** 支付 **USD 228**，购买 **Surf Limited Edition NFT #691** 一枚，2026-10-05 在途/待 airdrop 到用户主钱包，预期 RB 链。**2026-10-12 用户明确确认该已购买权益就是官方新公布的 SurfBoards / The Genesis of Surf NFT**，故以 `USER_CONFIRMED` 认定为同一个项目发行权益，不再把二者作为互不相关资产假设。官方尚未核实的只是具体链上交付、CA、token ID、转让与兑付条件。另有 **Surf 28,600 Points** 独立记录，不可自动转换为 NFT 份额或已兑现现金收益。
- 新的 **SurfBoards / The Genesis of Surf** 官网明确写有 `Trading and member claims open in ...`，Surf 主站也直接链接至这个入口。这仅确认项目页面与官方关联、领取/交易倒计时宣传存在，**用户已确认 #691 与 SurfBoards 属同一发行权益，但 #691 是否就是链上 ERC-721 token ID、是否已铸造、到账以及股票代币的具体分配权仍待官方/链上核验**。
- **历史时点（2026-10-12）** 尚未核实的官方 contract、总量、#691 的映射及权益，在 **2026-10-13 第 7 节** 已取得部分突破：官方总量 6,666、Robinhood 4663 第一组 ERC721/ERC20 合约实际链上核查与 Surf 官方 metadata 子域链接；另一个旧候选地址无效。最终官方 CA 白名单、#691 交付和兑付条款仍未确认。
- 2026-10-12 重新查阅 Surf 的 2025-12-11 融资公告，确认公告称募资 USD 15M、Pantera 领投、Coinbase Ventures 与 DCG 参与；2026-09-01 Bithumb 产品材料所列活跃用户和生产指标均为项目/合作方披露，**不能推导 Surf NFT 的利润分配、公司股权或保底回报**。
- Kaito Yapybaras 的 1,500 总量及约 USD 240 至 270 地板参考为历史公开页面快照；历史页面还展示真实成交和 top offer，随时会变化。对 Surf 的比较必须按同时间点的**最高真实买单、实际成交、挂牌地板**三种不同口径，不把挂牌总估值当作可清算市值。
- 研究状态：**Surf 公司产品/融资披露有据、用户的 #691 对应 SurfBoards 已获用户确认；官方链上 CA、交付和兑付条款仍未验证，故投机价值研究为 `WATCH / ONCHAIN_DELIVERY_UNRESOLVED`。用户 #691 仍是待交付历史成本权益，不能计入有可执行报价的 NFT 流动 NAV。** `ACTIVE` 仅可描述用户已有经济敞口，绝不授予任何交易或授权权限。
- 相关历史状态纠正：`research/nfts/jack-credits/jack-credits-nft-position.md` 是 2026-09-27 快照，其中写的“2 active”已经被 2026-10-10 直接链上核查的 **Credits 0 枚持有**覆盖；UNICRED #230 也已在 2026-10-10 标记 `CLOSED / NOT_OWNED`。此处不修改历史成交和当时报告。

后续研究核验顺序：**官方 SurfBoards chainId 和 contract → #691 交付凭据及链上 token ID → 总供应和领取资格 → 股票代币的每枚金额、法律属性、领取与锁定条款 → 真实订单簿和成交 → 按用户的 USD 228 成本计算可执行净回款**。不据此开启 NFT 监控任务。


## 7. SurfBoards 官方 6,666 总量和 Robinhood Chain 链上证据（2026-10-13）

证据层级：**官方网页 / 直接链上 / 推断与未确认**。本节更新旧结论，不新增任何监控。

**官方：** Surf [主站](https://asksurf.ai/) 出现原文 `6,666 Surfboards. The original assets of the Surf ecosystem.`，并链接 [官方 NFT 站](https://nft.asksurf.ai/)，展示 SPY、NVDA、SPCX、META、GOOGL 股票代币相关权益。官网显示 `Trading and member claims open in ...` 倒计时；具体 UTC 开放时间、每枚权益、股票代币支付频率、资金来源、兑付合同及 KYC 限制**未核实**。Surf 2025-12 官方声明 $15M 融资，2026-05 声明 Research 2.0 服务 500K+ 用户；这些不构成 NFT 已有现金流。官网另有订阅 Mystery Box 促销，不能与 NFT 分配条款直接混同。

**Robinhood 4663 直接链上：**
- NFT [ERC-721 `0x6A044021bb41f4B06193cA9B42946c20918aA4f3`](https://robinhoodchain.blockscout.com/address/0x6A044021bb41f4B06193cA9B42946c20918aA4f3)：2026-09-30 12:46:45Z 首次部署，创建者 `0x110b550faDBe13ceC30f75199e1aad7c3f056A2c`；索引显示 **200 个持有地址、940 条 NFT transfer（包括铸造和销毁，不是 940 笔销售）**。合约源代码未验证。
- 配对 [ERC-20 `0xA1687eF94012FF5B37cd7dCffE512DFA8e16b5c5`](https://robinhoodchain.blockscout.com/address/0xA1687eF94012FF5B37cd7dCffE512DFA8e16b5c5)：同一部署者、2026-09-30 12:46:36Z 创建，18 位小数；直接读取索引供应 **6,653 SURFBOARD**，**46 holders**，**不能把 ERC20 supply 当成已铸造的 NFT 数量**。
- ERC20 头两大持仓：第一大 `0xB13FdD73492e49B6A9fC8839C83B6E51F97b1315` **4,873 枚**，为同一创建者部署的合约；第二大 `0xe31Ef2594ffcB184530f4f58791e04222c0B2e5B` **1,477 枚**，合计 **95.45% 的 ERC20 供应**。未验证用途及控制关系，不能叫作已确定团队筹码或实际抛压。
- NFT `tokenURI(738)` 真实返回 `https://metadata.asksurf.ai/nfts/stock-nft-shadow/20260930/opened/738.json`；Blockscout 读取 #738 metadata 为 `SurfBoard · Pro ticket`，字段 `State=Closed / Ticket=Pro`；文字描述为借助 **drand beacon** 从 normal bag 随机抽取等级。另有 #482 元数据为 `Max ticket`。官方子域增强对应关系，但 `stock-nft-shadow` 的 shadow 命名、metadata 状态差异及未验证源码意味着仍需核对正式发行部署。
- **#738 同一 Token ID 的完整四步历史：** 2026-09-30 13:02Z [Mint](https://robinhoodchain.blockscout.com/tx/0x80d9a695363294a465eda2f68bc3ab7b76c171938baee81d3516fe74fd442a83) → 2026-09-30 20:06Z [Burn](https://robinhoodchain.blockscout.com/tx/0xf2fa8d2923e56c2be02684e291ec110bcace09231dd759eae0e52b0ddb34d102) → 2026-10-08 07:04Z [同 ID 再 Mint](https://robinhoodchain.blockscout.com/tx/0x80c2864f2103a63465a06b3517a7d229757d1699601a187e3bea18b98cc3729f) → 2026-10-08 07:15Z [转移](https://robinhoodchain.blockscout.com/tx/0x1605f4b2a4c61fdcb1e052efcfd9f322935b40be77fccb9b3ae4d6cb627ddebd)。**截图的重铸说法获得直接转移事件验证**。
- **Uniswap v4：** Uniswap [官方部署表](https://developers.uniswap.org/deployments) 确认 Robinhood 4663 PoolManager `0x8366a39CC670B4001A1121B8F6A443A643e40951`。[2026-10-09 23:49Z 交易](https://robinhoodchain.blockscout.com/tx/0x176af9eb1d023d58cd6c5eea27db5942ce79f1bcd0d00418284b5b9f1e8b4bd9) 同笔出现 NFT #482 **burn**、**0.451 SURFBOARD ERC20 转入 v4 PoolManager**、WETH 转移。另有 `buyExactEth` Mint 交易。证明兑换/燃烧的真实交互，但**未核实特定池 ID、TVL、可执行卖出深度和 NFT 地板价**。
- **原第二候选合约字符串有误：** `0xf5a24bd9648f180E306B57bb5B2349bb7908C28` 含前缀仅 41 字符，Blockscout 合约查询因格式错误而失败，旧报告“第二链上 ERC721”结论作废。

**用户 #691 交付：** 原始 Git 购买证据为 2025-08-31 经 DaimoPay 支出 **$228**，用户明确确认对应 SurfBoards 发行权益。但在上述 ERC-721 执行 `ownerOf(691)` 返回 **`reverted: unminted`**；#691 的浏览器实例虽有预生成的 `Pro ticket` 元数据，owner 为零地址，**未 Mint 的元数据不是已拥有 Pro 级别的证据**。主 EVM 钱包在 Robinhood 4663 的 NFT 持仓读取为空。**已付的待交付权益照旧保留 $228 成本，不列为已持有可交易 NFT，也不记作零价值/损失**。

**研究判断：** `ACTIVE` 仅代表用户已付款权益；NFT 可执行交易仍 `WATCH`。确认 6,666、链上 burn/remint、官方子域及 v4 交互使项目真实性判断上升；正式 CA、#691 交付、drand 奖池与等级概率、股票代币真实收益、链上流动性、安全权限和官方索赔条款仍 `UNRESOLVED`。禁止创建监控、进行任何签名或交易。


## 8. 2026-10-13 官方 Genesis 8/8 规则与 PRO 会员的领取及收益决策

**研究范围仅为 NFT 投资分析。** 取证顺序：用户提供的 [SurfAIHQ 2026-10-13 官方 8/8 thread](https://x.com/SurfAIHQ/status/2109852363892879632) 整理原文（X 页面在本次浏览工具不可直接读取，以下细节以**官方声明的用户转述**列出）、[Surf 官方 NFT 站](https://nft.asksurf.ai/) 及主站（官方项目入口和倒计时可读取）、CoinNess 与 Binance News 英文新闻（独立报道与用户转述大体一致）、用户的 **2025-08-31 Surf 付款成功官方邮件**及 **2026-10-06 Surf 领取资格官方邮件**（经连接账户直接读取原文）。记录中**不包含邮箱、订单号、原文敏感凭据**。

### 8.1 更正用户实际购买关系与会员等级（一级证据）

- 2025-08-31 **Surf 官方付款成功邮件**直接写明：`Surf PRO Annual Subscription`，金额 **$228**，服务有效至 2026-08-31。**因此这个 $228 是 PRO 一年期会员购买款，不应被错误分类为单独购买了 $228 NFT**。SurfBoard 是会员随附的一枚免费领取权益（新机制下的额外发行/claim 费用是否有 gas，应在交互前读取）。
- 2026-10-06 **Surf 官方定向邮件**明确写：`Every member holding an annual membership number, Pro or Max, active or lapsed, can claim one free NFT`，2026-09-16 之前购买年会员符合资格，**已过期会员仍可领取**；如果 9/16 前续费第二年则有两份。本次仅找到用户 **一笔 $228 PRO 年订阅**的直接付款证据；没有证明第二次续费，默认只计算 **1 份 Pro ticket 资格**。邮件还要求在 Surf 绑定钱包。
- 先前 `Surf Limited Edition #691` 是用户的原会员购买/领取权益编号，**不能仅凭该编号认定生成的 ERC-721 tokenId 必然也是 #691**；2026-10-13 对早期候选 ERC721 的 `ownerOf(691)` 读到 `unminted`，并不否认会员 1 张免费票的资格。
- 增量 NFT 获取成本：**0 美元的额外销售 Mint 费（按照官方免费票规则），gas 尚待交互显示**。追踪历史现金支出仍保留 **$228 订阅费用**；计算 NFT 纯新增回报时不得把已消费的全年 AI 服务费用直接全部计入 NFT 的专属投资成本，也不得重复创造一笔 $228 NFT 买入记录。
- 邮件中的 `Bind your wallet` 链接正文呈现 `#WALLET-BINDING-LINK-TODO` 占位文本；操作应从 Surf **官方主站登录后**找账户钱包绑定，不要依赖邮件内占位链接。选择绑定的 EVM 地址是否为最终 Claim 收件地址，必须以账户 UI 为准。

### 8.2 发行与权益（用户转述的 Surf 官方 2026-10-13 thread）

- **主网**：Robinhood Chain `4663`，gas 为 ETH。**总量 6,666**。**公开 Claim / 交易开放**：2026-10-15 **03:00 UTC = Bangkok 10:00 = Beijing 11:00**，在上链操作前再次核实官方页面实时状态。
- **等级与计划配额**：`Pro-1 3,500`、`Pro-2 1,800`、`Pro-3 860`、`Max 500`、`Ultra 6`，合计 `6,666`。按比例分别约 52.51%、27.00%、12.90%、7.50%、0.09% 的**全系列配额占比**，**不是持 Pro Ticket 抽到各级的已知概率**。用户 Pro Ticket 对应 Pro 发行路径；确切 Pro-1/2/3 等级概率/保底/剩余奖池算法未经合约审计，禁止借全系列占比推算。
- 约 **130,000** artwork 组合；抽出 tier 后不同收益权重，具体流量/金额与 grade 的比值未公开核验。官网列出的股票代币方向：NVDA、SPY、META、GOOGL、SPCX。
- 老会员可以用 Pro/Max **Ticket** 领取；第二渠道为买 **1 SURFBOARD ERC20 token** Reveal，按剩余奖池随机取等级。用户已有免费票，**不应在未验证资格或回报时重复花钱买 1 ERC20**。9/16 之后临时升级 Max 年会员不能视为 retroactive Max Ticket。
- **未 Reveal**：股票代币累积为零；**Reveal 后**：开始累计，且不可逆。已揭开的 NFT 可在 OpenSea 转移，已累计股票代币权利随 NFT 走。**Unopened ERC20** 本身可流转。暂未独立核实 Ticket 本身是否可转让。
- **Redeem**：NFT 被 Burn，持有人得到累积股票代币的 **95%**，其余 **5%** 分给所有已揭开的 SurfBoards。未见官方细则描述是否等权分发、收费/税及 token 交易限制，不能擅自补充。

### 8.3 收益最大化的行动决策（研究意见）

**初始默认优先级：**
1. **2026-10-13/14：** 在官方 `https://asksurf.ai/` 用购买时账户登录，确认 **PRO 会员编号 #691 / 1 张 Ticket / 钱包绑定的收件地址**；无需新开会员，先确认原持有资格。必要时仅为真实 claim/reveal 准备少量 Robinhood 4663 ETH gas。Robinhood 官方手动加网 RPC `https://rpc.mainnet.chain.robinhood.com`，ChainID `4663`，币种 ETH。
2. **2026-10-15 10:00 Bangkok：** 先确认 official claim 与钱包弹窗合约地址，走 **Pro Ticket 免费 Claim**；当确认揭晓不会丧失可实现的高额未揭晓出售溢价或重要权益后，**尽早 Reveal** 开始股票累积。Claim 和 Reveal 可能是不同操作，不能把领取看作已开始累积。不要因为编号 #691 而认定 ERC721 的 Token ID #691 必须出现。
3. **Reveal 后：** 按真实生成的 Pro 子级、美元计价的 stock token 累计、日均到账速率、合约持有人转让机制及 OpenSea **已成交/最高实际 bid** 决策。留存 NFT 持续收益及未来 5% 再分配期权，不在奖励很少时过早 Redeem。
4. **卖出 vs 赎回二选一（不能重复计价）**：`Sell_net = executable_bid - sale_fees - gas`；`Redeem_net = 0.95 * executable_value(accrued_stocks) - gas - stocks_liquidation_cost`；二者都失去 NFT 未来收益。持有继续积累的备选方案需计入未来配额、基金实际资金及变现风险。如果未来停发或者 NFT 交易长期严重折价，再考虑 Redeem。
5. **额外买 SURFBOARD：`NO_BUY_PENDING_VERIFICATION`**。需要官方股票收益发放量/权重/资金来源、可持续分发机制、可执行 token 买价/深度、合约权限和合规限制后，才能形成真实净收益模型。团队 `raise $0 from NFT sale` 不证明持续奖励有足额外部资金。

**数学估值：** 如果累计股份代币当前可变现美元价值为 `A`，赎回上限毛额为 `0.95 × A`（还要扣 gas/税与出售成本），并且必须交出 NFT。所谓 5% 再分配属于其他人赎回时支付的内部价值转移，不是协议额外增加 5% 收益或保证年化 5%。可写 `FutureValue(hold) = expected NFT net bid at H + future stock accrual + redemption-redistribution option`，不得将二级售出 NFT 时已经包含的 stock entitlement 再单独加一遍。

**实质性估值缺口：** 目前尚无官方可复核的每 Tier 每日/每区块发放率、总库存 stock token 的数量、资金来源、持续期限、最后发放时点、合约可执行 redemption 细节、OpenSea 可成交 bid。因此**无法核实 Pro Ticket 的年化收益、达 $228 的时间或投资价值精确值**。Kaito 的 2025-02 炒作峰值仅用于尾部极端价格路径压力测试；当前 Surf 应按真实收益折现及同阶段订单簿重新定价。

**经济和法律风险：** Robinhood 官方文件指出 Robinhood Chain 股权代币属于 **tokenized debt securities**，提供相应股票的经济敞口，**不赋予持有人对底层美股的法定或实益所有权**；最终可赎回/交易规则、地区与身份限制须看 Surf/RH 实际执行条款。不可把“持有 NFT 收集 stocks”描述成持有上市公司股权分红。

**执行边界：** 只做主动请求的 NFT 研究，不启用定时/本地监控，不操作钱包，不自动下单，不直接签名。官网未到 Claim 时刻不伪称已领取，交易/分红数据未上线不伪称验证成功。


## 9. SurfBoard #5396 开包后主钱包、分配资金池及系列活动链上实证（2026-10-15）

> **当前优先事实：** 2026-10-15 04:43:55 UTC（曼谷 11:43:55），Robinhood Chain **block 88,947,414** / `0x54d3ad6` 为**统一冻结只读统计区块**。交易证据来自 Alchemy Robinhood Mainnet JSON-RPC receipts、`eth_call`、ERC-20/ERC-721 owner/transfer 查询，并与 Blockscout 原始索引、Surf 官方账户截图交叉核对。对同区块的所有核心计数使用 `eth_call(blockTag=0x54d3ad6)`，避免不断变化的现场数字互相矛盾。

### 9.1 用户主钱包已领取、铸造、开包并揭晓（直接链上确认）

主 EVM：`0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`，Chain ID 4663。

正式发行的全新 V04（区别于 2026-09-30 的 shadow/早期候选）部署：
- **ERC-721 SurfBoardMirror** `0x18c9719AB6AE4E1a6f95F281eF288e3AF5d58602`，implementation `0x8A0F0aBc2E992299146535B3d0b070A60bC01C5D`，Blockscout 标示合约已验证、实现代码 `SurfBoardMirror`。
- **ERC-20 SurfBoard404 Core** `0x5aBCaa98e19c0BAB678C458F229191Bd16b87a32`，implementation `0x60BCB639bC7Cc7Bfede0dcb2f340De7EEF93F7a7`，已验证实现 `SurfBoard404`。
- **股票权益/赎回 SurfReflections** `0xF1ddD8eE0ABab932d9394E138beF2D4ca945C64e`，implementation `0xD6E3338c4306C479DAD0B620B388FdF5A0da5434`，已验证实现 `SurfReflections`。
- 三份合约都记录同一创建者 `0x0fE67Ce3E36cCC9f4355a23BCa6EDCce28b13994`。此前 2026-09-30 的合约 `0x6A0440...` 属于另一代部署，**不可再用旧合约 ownerOf(691) 的 `unminted` 推断用户 2026-10-15 的持仓**。

用户三笔真实交易：
1. [`0xfaffd46a5a7da9854b2a28262e54ef275cf4251a7686324f61b3bd17cfb6c104`](https://robinhoodchain.blockscout.com/tx/0xfaffd46a5a7da9854b2a28262e54ef275cf4251a7686324f61b3bd17cfb6c104)，**2026-10-15 04:20:28Z**：通过领取操作，从零地址**铸造 ERC-721 Token ID #5396 到主钱包**；同笔有 1 SURFBOARD ERC-20 转入钱包及 `Airdropped`、`Materialized` 相关事件，代表会员票的实际领取。#691 是历史 Surf PRO 订阅/权益编号，最终 NFT 链上 ID 为 **5396**。
2. [`0xc84f1bfb8594d5dd1c2804066f74d766d39b5560ab875e53ef91bf9653ea9fd3`](https://robinhoodchain.blockscout.com/tx/0xc84f1bfb8594d5dd1c2804066f74d766d39b5560ab875e53ef91bf9653ea9fd3)，**04:22:11Z**：钱包调用 Core `open(5396)` 成功，销毁 1 SURFBOARD ERC-20；Core 发出 `Opened`，Mirror 发出 `MetadataUpdate(5396)`。
3. [`0x85c98979c86fd217cd2fbf3fe6709ef42d63f6d80b77f46761426298fd77a0bc`](https://robinhoodchain.blockscout.com/tx/0x85c98979c86fd217cd2fbf3fe6709ef42d63f6d80b77f46761426298fd77a0bc)，**04:22:18Z**：Core 真实 `Revealed` 事件含 `id=5396`、owner=主钱包、`tier=1`；SurfReflections 同笔发出 `Opened`，分配权重 `100`。两笔成功交易共同证明打开和随机分层已完成。

`ownerOf` 经 Alchemy `getOwnersForNFT` 返回主钱包；`isOpened(5396)=true`、`tierOf(5396)=1`、`isRedeemed(5396)=false`、`SurfReflections.weightOf(5396)=100`、`floorOf(5396)=1`。**主钱包当前拥有一枚真实 ERC721 SurfBoard #5396，已开包等级 Common、分成权重 ×1、分配池 NVDA；没有卖出或赎回记录**。

**动态 metadata 修复辨析：** Alchemy/Blockscout 的缓存 NFT 描述仍出现 `Closed / Pro ticket`，但是对当前正式合约 ERC721 Mirror 和 Core 直接读取 `tokenURI(5396)` 都返回 **`https://metadata.asksurf.ai/nfts/surfboard/opened/5396.json`**。加上不可撤销的开包和揭晓事件，链上真实状态为 **OPENED**，缓存 Closed 属于索引延迟，不能误报未开。

### 9.2 统一区块全系列真实进度及五等级

在 **block 88947414 / 2026-10-15 04:43:55Z**：
- `economicUnits() = 6,666`，初始经济单位总量。
- `totalSupply() = 5,367 × 10^18`，尚未消耗/转换的 SURFBOARD ERC-20 经济单位。**这不是 5,367 枚尚未 Mint 的 ERC721，也不是 5,367 张个人会员 Ticket。**
- `totalOpened() = 1,295`，当前已开启未 Redeem 的数量，其中 `openQueueLength() = 2` 仍待随机揭晓；故 **已揭晓且仍有效 = 1,293**。
- `totalRedeemed() = 4`，已经赎回并 burn 的累计 NFT 数量。
- `tierRevealedCount(tier=1..5)` = **[833, 207, 90, 165, 2]**，**历史已揭晓合计 1,297**，含其后被 Redeem 的部分。Tier 0 = 0。
- 守恒复核：**5,367 ERC-20 未转换 + 1,293 活跃已揭晓 + 2 已 Open 等揭晓 + 4 已 Redeem = 6,666**；历史揭晓 1,297 = 活跃已揭晓 1,293 + 已 Redeem 4。
- `poolSize() = 4,393`，是 Core 余下的 ID 池数据，**不能直接叫作 4,393 个未领取会员 NFT**。准确的“所有当前未开包、且已经铸造成 ERC721 的 NFT 张数”未由这些聚合器单独确认，不能编造。
- `SurfReflections.tierWeights(1..5) = [100,200,300,1000,2000]`，相对权重 **×1、×2、×3、×10、×20**；这是分配权重而非收益保证。上一轮用户提供等级名 Pro-1/2/3、Max、Ultra 与网站开启后的 Common 等 UI 名字应区别记录，链上以 tier numeric 1..5 为准。

### 9.3 股票代币是真实入金合约记账，未直接到用户钱包

`SurfReflections` 代码已验证，主要实际读取接口：
- `floorStocks(0..4)` 对应 **SPY、NVDA、SPCX、META、GOOGL**。
- `onOpen(id)` 记录某 id 的股票池 `floorOf` 和 tier 权重 `weightOf`；`notifyFees(floorIdx,amount)` 接受相应入金通知，`pending(id)` / `pendingAll(id)` 直接从合约计算可提取的股票代币数量。
- 主钱包对这五种已核查 ERC-20 的**可转账余额全部为零**，因此之前 UI 的“资产明细 NVDA”是 **NFT 绑定的待兑现合约权益**，不能把它当作已单独发到钱包的 NVDA 股票代币。
- 查询时收益合约真实托管余额，18 decimals（跨若干时点，非 9.2 统一区块）：SPY **3.346712703363217717**、NVDA **11.770682045438922719**、SPXC/合约 symbol `SPCX` **17.161529585982972870**、META **3.507999432267819506**、GOOGL **7.506433805489896813**。这些**是资金池全体余额，不能归属用户单枚，也不能当美元相加**。
- 真实 [交易 `0x2a72f7050d6d3eb012ab37fb5f5d8da10dfdbd8746b165ed95605be116b3807c`](https://robinhoodchain.blockscout.com/tx/0x2a72f7050d6d3eb012ab37fb5f5d8da10dfdbd8746b165ed95605be116b3807c) 中，地址 `0x570b9f1abf9982692eac97f131d97f1bc4f13dc0` 确有五种股票代币转入收益合约，其中 NVDA **0.04329973048669609** 枚。确证真实资金入金；**尚未逐笔核清收入是否全部源自 DEX 手续费，不能宣称稳定持续收益率**。
- `pending(5396)` 在 9.2 冻结区块返回 **745771759040394 raw**，根据 NVDA Robinhood Token **18 decimals** 得 **0.000745771759040394 NVDA**；按用户截图显示 NVDA **$219.3** 仅作同日参考，约 **$0.164**，**不是可实时成交保证价格**。不满 **$1**，遵守 Mission 单项 $1 过滤，不计入流动 NAV，成本仍保存。
- `redeemPaused()=false`、`inflowsPaused()=false` 在快照时读取成立，不代表无管理权限或永久无法暂停。

### 9.4 Redeem 已真实发生，并且 95%/5% 比例直接闭合

- `REDEEM_SHARE_BPS() = 500`（5% 分给他人）。
- [tx `0x8253fe5c76fc67714463e3360782951db56c2dfbb3766d286f4c436456aa7dd5`](https://robinhoodchain.blockscout.com/tx/0x8253fe5c76fc67714463e3360782951db56c2dfbb3766d286f4c436456aa7dd5)：SurfBoard NFT **#6281** 直接从拥有者转零地址销毁，Core 发出 `Redeemed(6281,owner)`；收益合约发出 `Redeemed`，同交易将 **0.002306228430480203 NVDA** 转给该 NFT 持有人，日志的 shared 为 **0.000121380443709484 NVDA**；合计 **0.002427608874189687 NVDA**，严格 **95% / 5%**。
- 另有收益合约真实向持有人转出 SPY、GOOGL 等 ERC20 的其他样例；用户自己的 **#5396 没有 Redeem，不可把其他人收入算为用户收入**。

### 9.5 ERC20 买卖、领取和 NFT 二级成交的证据边界

- **Claim/领取真实示例：** 用户自己的 `0xfaffd46...` 在 V04 正式系列将 1 个 SURFBOARD 经济单位和 ERC721 #5396 实际交付钱包，此钱包没有支付新的额外 228 美元 NFT mint 金额，历史 $228 是 2025 PRO 一年会员订阅成本。
- **ERC20 进出 Uniswap v4 PoolManager 的样例：** [`0xabeebd2f1c1bb8a30f1ceabab411983220e36d8d6903229268618c164ee07a16`](https://robinhoodchain.blockscout.com/tx/0xabeebd2f1c1bb8a30f1ceabab411983220e36d8d6903229268618c164ee07a16) 出现 **1 SURFBOARD** 从 Uniswap v4 `0x8366a39CC670B4001A1121B8F6A443A643e40951` 到协议路由器；[`0xb077d11cc4cd7d579e5ccf465b14bf16626d0d9358583ba1b8206a966a922a3e`](https://robinhoodchain.blockscout.com/tx/0xb077d11cc4cd7d579e5ccf465b14bf16626d0d9358583ba1b8206a966a922a3e) 有 **1 SURFBOARD** 从用户地址进入 PoolManager。它们证明真实双向资金池转移，**仅凭转账还不能把最终成交价格、净得 WETH、最终买家与 NFT 二级交易额推断出来**。
- **NFT OpenSea 市场买/卖：** 经尝试 OpenSea Collection `surfboard-557503128` 和 #5396 商品页，当前网页渠道无法读取真实订单；Alchemy NFT Sales 接口返回 `404 This API endpoint has been deprecated`。因此**真实成交量、可卖最佳 bid、系列地板与本人 NFT 可能卖出的成交价 = UNVERIFIED**，禁止冒用 ERC20 买卖量或 NFT 普通转账数量冒充 OpenSea 成交。
- EIP2981 `royaltyInfo(5396, salePrice=1_000_000)` 返回 royalty **50_000（5%）**，这是合约返回的版权费报价，真实平台是否强制代扣需订单验证，**区别于 Redeem 的 5% 再分配**。
- NFT 合约 ABI 包含暂停、黑名单、转移限制、管理员紧急恢复及重新配置的管理方法；尚需单独审计权限治理及变更风险，代码已验证不等于已经过独立安全审计。

### 9.6 当前投资结论与边界

- `ACTIVE`：用户已经由 **2025-08-31 $228 Surf Pro Annual** 会员权益，真正 Claim 并持有 **SurfBoard #5396，Common / tier1 / 100 权重 / NVDA，OPENED / NOT_REDEEMED**。#691 是会员原始编号，**不能继续标为“2026-10-15 尚未交付 NFT”**。
- `WATCH`：对是否卖出或继续累积收益的价值判断仍缺 **真实 NFT executable bid**、未来资金流持续性、手续费与持有人分配总权重变化。无法从约 21 分钟收益 extrapolate 年化。
- 用户持有一枚 NFT，但它的**当前可靠二级清算报价未核验**，因而不在当前标价投资 NAV；`pending` NVDA 约 **$0.164（仅截图价格参考）**，也低于 $1 排除阈值。严禁把 $228 历史服务费重复记为 NFT 的当前市场价值。
- 本轮只读检索 Git、链上及用户提供截图；**未操作任何交易、签名、申领、赎回、钱包发送或监控/automation**。以上用户成功交易均系用户本人在此之前独立执行，未由 ChatGPT 发起。


## 10. 2026-10-15 股票收益池管理员与持续性风险核查

调查性质：**只读风险评估**。核验 Robinhood Chain 主网 `4663` 合约状态、所有者角色、代理实现，使用未上链的模拟调用测试权限边界。没有签名、链上交易、暂停、转移、操作客户资产或增加监控。

**托管及所有权事实**

- 已收到的股票代币由 SurfReflections 收益合约 `0xF1ddD8eE0ABab932d9394E138beF2D4ca945C64e` 持有。NFT #5396 的 pending NVDA 是合约内对应权益，用户钱包直接股票代币余额仍为零。具体余额和历史入金交易见第 9 节。
- 读取收益合约的 `owner` 与 `depositor`、SurfBoard404 的 `owner` / `blacklistGuardian` / `recoveryAdmin`、SurfBoardMirror 的 `owner`，**全部是同一地址** `0x3ee626ade66be28470425d6c19f47fdf8579173a`。
- 该地址的主网代码查询返回 `0x`，是**普通外部账户（EOA）**，没有链上多签约束或可识别的 timelock。私钥由几人管理无法核实。收益合约 notifier 当前为 `0x570b9f1abf9982692eac97f131d97f1bc4f13dc0`，属于另一个有代码的合约地址。

**暂停、权限与封存实际核查**

- 直接状态：`redeemPaused=false`，`inflowsPaused=false`，Core `paused=false`、`transfersLocked=false`；主钱包 `blacklisted=false`。`wiringSealed=true`、`attributesSealed=true`、`stocksSet=true`。
- 只读模拟证实相应 EOA 管理者可操作**暂停赎回、暂停入金、暂停协议及黑名单设置**；普通用户无同样暂停权限。即使已封存线路，收益通知和被授权入金地址仍可由管理员修改；已设置的五种股票代币资产列表存在额外修改限制。
- 在当前链状态，对已开包的 #5396 尝试验证紧急转移权限时，模拟返回回退：**未证明管理员可以通过该普通紧急接口无条件直接拿走用户的 NFT**。各项只读检查结束后，实际状态仍显示未暂停、未黑名单、持仓未变。

**代理升级风险是核心发现**

- 三个正式合约都属于 ERC-7760 可升级代理，运行实现保存在 EIP-1967 implementation slot。部署所用的代理工厂为 `0x0fE67Ce3E36cCC9f4355a23BCa6EDCce28b13994`。
- 直接查询工厂对三份合约的授权控制者，均为同一个 `0x3ee626...` EOA。只读模拟证实该管理员**可以授权执行合约实现更新**，而普通钱包被拒绝；本轮在不改变实现的模拟之后重新读取存储槽，**三份实现地址全部保持原样**。
- 由于升级权限未撤销，当前实现代码已验证、参数已封存，并**不能确保未来逻辑永远不变**。在恶意升级或管理员密钥受损的条件下，收益池托管的股票代币、赎回及分配逻辑可能遭到修改。没有发现项目方已经恶意提款/暂停/升级的证据。也没有完整的独立安全审计可据以排除所有风险。

**股票代币的第二层信用风险**

- Robinhood 官方文档称 Robinhood Stock Tokens 由 Robinhood Assets (Jersey) Limited 发行，法律性质是**代币化债务证券**，提供价格经济敞口，不附带底层上市公司股东权利。官方声明与托管基础资产一一对应；直接向发行人赎回可能受到身份审核和地区限制。
- Surf 合约端的收益/可兑换性风险与 Robinhood 发行人、托管、流动性及法律规则风险相互独立。参考：https://docs.robinhood.com/chain/stock-tokens/ 与 https://robinhood.com/rhj/stocktokens/ 。

**决定性结论**：当前实际收益分配存在、没有证据显示恶意提款；未来入金没有已验证最低保证，管理员能够停止未来入金及暂停赎回，三合约的可升级架构还意味着收益合约库存面临项目管理员密钥的信任风险。因此研究评级为 **HIGH: SINGLE_EOA_ADMIN + UPGRADEABLE_CUSTODY + UNGUARANTEED_FUTURE_FLOWS**。#5396 当前持仓、Common/NVDA 及原始 Surf PRO 历史成本事实均不变；继续保留免费领取的 NFT 可以观察收益，但**在补齐治理、升级约束、真实成交深度之前不建议新增购买**。
